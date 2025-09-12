import feedparser
import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.db import transaction
from bs4 import BeautifulSoup
from ai_engine.models import DataSource, DataIngestionRecord
from news.models import NewsArticle, NewsCategory
# from news.news_analyzer import NewsAnalyzer  # แทนที่ด้วย analyzer_switcher
import re
from datetime import datetime

class Command(BaseCommand):
    help = 'ดึงข่าวจาก RSS feeds และใช้ระบบกรองใหม่วิเคราะห์'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='จำนวนข่าวต่อ feed ที่จะดึง (default: 20)'
        )
        
        parser.add_argument(
            '--source',
            type=str,
            help='ดึงจาก DataSource เฉพาะ (ระบุชื่อ)'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        source_name = options.get('source')
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting RSS feed scraping (limit {limit} articles per source)')
        )
        
        # กำหนด category หรือสร้างถ้ายังไม่มี
        category, created = NewsCategory.objects.get_or_create(
            name='ข่าวทั่วไป',
            defaults={'slug': 'general', 'description': 'ข่าวทั่วไปจาก RSS feeds'}
        )
        
        # ดึง Data Sources
        if source_name:
            sources = DataSource.objects.filter(name__icontains=source_name, is_active=True)
        else:
            sources = DataSource.objects.filter(source_type='news', is_active=True)
        
        if not sources:
            self.stdout.write(
                self.style.WARNING('No active RSS feeds found')
            )
            return
        
        # สร้าง analyzer สำหรับประเมินข่าว
        # analyzer = NewsAnalyzer()  # แทนที่ด้วย analyzer_switcher
        from news.analyzer_switcher import AnalyzerSwitcher
        analyzer = AnalyzerSwitcher(preferred_analyzer='groq')
        
        total_processed = 0
        total_high_score = 0
        
        for source in sources:
            self.stdout.write(f'\n📡 ดึงข่าวจาก: {source.name}')
            self.stdout.write(f'🔗 URL: {source.url}')
            
            try:
                # ดึง RSS feed
                feed = feedparser.parse(source.url)
                
                if feed.bozo:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  RSS feed มีปัญหา: {source.name}')
                    )
                    continue
                
                entries = feed.entries[:limit]
                self.stdout.write(f'📰 พบข่าว: {len(entries)} ข่าว')
                
                source_processed = 0
                source_high_score = 0
                
                for entry in entries:
                    try:
                        with transaction.atomic():
                            # ดึงเนื้อหาข่าว
                            title = entry.title
                            link = getattr(entry, 'link', '')
                            
                            # ดึง content
                            content = self._extract_content(entry)
                            if len(content) < 50:  # ข่าวสั้นเกินไป
                                continue
                            
                            # ตรวจสอบข่าวซ้ำ
                            if NewsArticle.objects.filter(title=title).exists():
                                continue
                            
                            # วิเคราะห์ด้วยระบบใหม่
                            temp_article = type('TempArticle', (), {
                                'title': title,
                                'content': content
                            })()
                            
                            analysis = analyzer.analyze_article(temp_article)
                            
                            # ใช้ Insight-AI วิเคราะห์เพิ่มเติม
                            import sys
                            sys.path.insert(0, '/app/mcp_dream_analysis')
                            from specialized_django_integration import extract_news_numbers_for_django
                            
                            insight_result = extract_news_numbers_for_django(f"{title}\n\n{content}")
                            
                            # เฉพาะข่าวที่มีเลขจากทั้ง 2 ระบบถึงจะบันทึก
                            has_news_numbers = analysis['numbers'] and len(analysis['numbers']) > 0
                            has_insight_entities = insight_result.get('extracted_entities') and len(insight_result.get('extracted_entities', [])) > 0
                            
                            if has_news_numbers and has_insight_entities:
                                # สร้างข่าว
                                article = NewsArticle.objects.create(
                                    title=title[:200],  # จำกัดความยาว
                                    content=content,
                                    intro=content[:500],
                                    category=category,
                                    source_url=link,
                                    status='published',
                                    published_date=timezone.now(),
                                    # ใช้ข้อมูลจากระบบใหม่
                                    lottery_relevance_score=analysis['confidence'],
                                    lottery_category=analysis.get('category', 'general'),
                                    extracted_numbers=','.join(analysis['numbers'][:10]),
                                    confidence_score=analysis['confidence']
                                )
                                
                                source_processed += 1
                            else:
                                # ข้ามข่าวที่ไม่มีเลขจากทั้ง 2 ระบบ
                                if not has_news_numbers:
                                    self.stdout.write(f'⏭️ ข้ามข่าวไม่มีเลข (AI Analyzer): {title[:50]}...')
                                elif not has_insight_entities:
                                    self.stdout.write(f'⏭️ ข้ามข่าวไม่มีเลข (Insight-AI): {title[:50]}...')
                                else:
                                    self.stdout.write(f'⏭️ ข้ามข่าวไม่มีเลข: {title[:50]}...')
                                continue
                            
                            # นับข่าวคะแนนสูง
                            if analysis['confidence'] >= 80:
                                source_high_score += 1
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f'🎯 ข่าวคะแนนสูง: {title[:50]}... '
                                        f'(คะแนน: {analysis["confidence"]}, หมวด: {analysis["category"]})'
                                    )
                                )
                            elif analysis['confidence'] >= 60:
                                self.stdout.write(f'* {title[:50]}... (Score: {analysis["confidence"]})')
                            else:
                                self.stdout.write(f'📰 {title[:50]}... (คะแนน: {analysis["confidence"]})')
                            
                            # บันทึกใน DataIngestionRecord
                            DataIngestionRecord.objects.create(
                                data_source=source,
                                raw_content=f"{title}\\n{content}",
                                processed_content=content,
                                title=title,
                                extracted_numbers=analysis['numbers'],
                                relevance_score=analysis['confidence'],
                                processing_status='completed'
                            )
                            
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Error: {entry.title[:30]}... - {str(e)}')
                        )
                        continue
                
                # อัปเดตเวลาสุดท้าย
                source.last_scraped = timezone.now()
                source.save()
                
                total_processed += source_processed
                total_high_score += source_high_score
                
                self.stdout.write(
                    f'OK {source.name}: {source_processed} articles (High score: {source_high_score})'
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error at {source.name}: {str(e)}')
                )
                continue
        
        # สรุปผลลัพธ์
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(f'🎯 ดึงข่าวเสร็จสิ้น!')
        )
        self.stdout.write(f'📰 ข่าวทั้งหมด: {total_processed} ข่าว')
        self.stdout.write(f'🔥 ข่าวคะแนนสูง (≥80): {total_high_score} ข่าว')
        
        if total_high_score > 0:
            percentage = (total_high_score / total_processed) * 100 if total_processed > 0 else 0
            self.stdout.write(
                self.style.SUCCESS(f'📊 อัตราข่าวคุณภาพ: {percentage:.1f}%')
            )
        
        # สถิติหมวดหมู่
        self._show_category_stats()
    
    def _extract_content(self, entry):
        """สกัดเนื้อหาจาก RSS entry"""
        content = ''
        
        # ลองหา content จากแหล่งต่างๆ
        if hasattr(entry, 'content'):
            content = entry.content[0].value if entry.content else ''
        elif hasattr(entry, 'summary'):
            content = entry.summary
        elif hasattr(entry, 'description'):
            content = entry.description
        
        # ทำความสะอาด HTML
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            content = soup.get_text().strip()
            
            # ลบ whitespace เกิน
            content = re.sub(r'\\s+', ' ', content)
            
        return content or 'ไม่สามารถดึงเนื้อหาได้'
    
    def _show_category_stats(self):
        """แสดงสถิติหมวดหมู่"""
        from django.db.models import Count
        
        stats = NewsArticle.objects.values('lottery_category').annotate(
            count=Count('id')
        ).order_by('-count')
        
        if stats:
            self.stdout.write('\\n📊 สถิติหมวดหมู่:')
            category_names = {
                'accident': '🔥 อุบัติเหตุ',
                'celebrity': '* Celebrity',
                'economic': '📈 เศรษฐกิจ',
                'general': '📰 ทั่วไป'
            }
            
            for stat in stats:
                category = stat['lottery_category']
                count = stat['count']
                name = category_names.get(category, category)
                self.stdout.write(f'  {name}: {count} ข่าว')
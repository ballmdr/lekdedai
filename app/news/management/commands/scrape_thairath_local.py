# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import datetime
import time
import re

from news.models import NewsArticle, NewsCategory
from news.analyzer_switcher import AnalyzerSwitcher
from lekdedai.utils import generate_unique_slug

class Command(BaseCommand):
    help = 'ดึงข่าวจาก Thairath Local News และวิเคราะห์ด้วย Groq AI'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='จำนวนข่าวที่จะดึง (default: 20)'
        )
        parser.add_argument(
            '--min-score',
            type=int,
            default=70,
            help='คะแนนขั้นต่ำที่จะบันทึกข่าว (default: 70)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=2.0,
            help='หน่วงเวลาระหว่างการ scrape (วินาที, default: 2.0)'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        min_score = options['min_score']
        delay = options['delay']
        
        self.stdout.write(
            self.style.SUCCESS('🚀 เริ่มดึงข่าว Thairath Local News')
        )
        self.stdout.write(f'📊 จำกัด: {limit} ข่าว, คะแนนขั้นต่ำ: {min_score}, หน่วงเวลา: {delay}s')
        
        # สร้าง analyzer
        try:
            analyzer = AnalyzerSwitcher(preferred_analyzer='groq')
            self.stdout.write(self.style.SUCCESS('✅ เชื่อมต่อ Groq AI สำเร็จ'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ ไม่สามารถเชื่อมต่อ Groq AI: {e}'))
            return
        
        # หา/สร้าง category
        category, created = NewsCategory.objects.get_or_create(
            name='ข่าวท้องถิ่น',
            defaults={
                'slug': 'local',
                'description': 'ข่าวท้องถิ่นจาก Thairath'
            }
        )
        
        # เริ่มดึงข่าว
        scraped_count = 0
        saved_count = 0
        analyzed_count = 0
        
        try:
            # 1. ดึงรายการข่าวจากหน้าแรก
            news_list = self.scrape_news_list(limit)
            
            if not news_list:
                self.stdout.write(self.style.WARNING('⚠️ ไม่พบข่าวใดๆ'))
                return
            
            self.stdout.write(f'📰 พบ {len(news_list)} ข่าว')
            
            # 2. ดึงรายละเอียดแต่ละข่าว
            for i, news_item in enumerate(news_list, 1):
                self.stdout.write(f'\\n🔍 [{i}/{len(news_list)}] {news_item["title"][:50]}...')
                
                try:
                    # ตรวจสอบว่ามีข่าวนี้ใน database แล้วไหม
                    if NewsArticle.objects.filter(source_url=news_item['url']).exists():
                        self.stdout.write('   ⏭️ มีข่าวนี้แล้ว - ข้าม')
                        continue
                    
                    # ดึงเนื้อหาข่าว
                    content_data = self.scrape_news_content(news_item['url'])
                    if not content_data:
                        self.stdout.write('   ❌ ไม่สามารถดึงเนื้อหาได้')
                        continue
                    
                    scraped_count += 1
                    
                    # วิเคราะห์ด้วย Groq
                    self.stdout.write('   🤖 วิเคราะห์ด้วย Groq AI...')
                    analysis = analyzer.analyze_news_for_lottery(
                        content_data['title'], 
                        content_data['content']
                    )
                    
                    analyzed_count += 1
                    
                    if analysis.get('success'):
                        relevance_score = analysis.get('relevance_score', 0)
                        numbers = analysis.get('numbers', [])
                        
                        self.stdout.write(f'   📊 คะแนน: {relevance_score}/100')
                        self.stdout.write(f'   🔢 เลข: {", ".join(numbers[:10])}')
                        
                        # ตรวจสอบว่าผ่านเกณฑ์ไหม
                        if relevance_score >= min_score and numbers:
                            # บันทึกข่าว
                            try:
                                article = self.save_article(content_data, analysis, category)
                                saved_count += 1
                                self.stdout.write(
                                    self.style.SUCCESS(f'   ✅ บันทึกสำเร็จ: {len(numbers)} เลข')
                                )
                                self.stdout.write(f'   🔗 URL: {article.get_absolute_url()}')
                            except Exception as save_error:
                                self.stdout.write(
                                    self.style.ERROR(f'   ❌ Error saving: {save_error}')
                                )
                        else:
                            reason = "ไม่มีเลข" if not numbers else f"คะแนน {relevance_score} < {min_score}"
                            self.stdout.write(
                                self.style.WARNING(f'   ⚠️ ไม่ผ่านเกณฑ์: {reason}')
                            )
                    else:
                        error_msg = analysis.get('error', 'Unknown error')
                        self.stdout.write(
                            self.style.ERROR(f'   ❌ วิเคราะห์ล้มเหลว: {error_msg}')
                        )
                    
                    # หน่วงเวลา
                    if delay > 0:
                        time.sleep(delay)
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'   ❌ Error processing: {e}')
                    )
                    continue
        
        except KeyboardInterrupt:
            self.stdout.write('\\n⏹️ หยุดการทำงานโดยผู้ใช้')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Fatal error: {e}'))
        
        # สรุปผล
        self.stdout.write('\\n=== สรุปผลการทำงาน ===')
        self.stdout.write(f'📰 ดึงข่าว: {scraped_count} ข่าว')
        self.stdout.write(f'🤖 วิเคราะห์: {analyzed_count} ข่าว')  
        self.stdout.write(f'💾 บันทึก: {saved_count} ข่าว')
        self.stdout.write(self.style.SUCCESS('🎉 เสร็จสิ้น!'))

    def scrape_news_list(self, limit):
        """ดึงรายการข่าวจากหน้าแรก Thairath Local"""
        url = "https://www.thairath.co.th/news/local"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'th,en-US;q=0.7,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # หา elements ข่าว (ต้องปรับตาม structure จริงของ Thairath)
            news_items = []
            
            # ลองหา pattern ต่างๆ สำหรับ Thairath
            selectors = [
                'article a[href*="/news/"]',  # Links ในแต่ละ article
                '.news-item a',               # Class news-item
                '.content-card a',            # Class content-card  
                'a[href*="/news/local/"]',    # Local news links
                '.post-item a',               # Class post-item
                '[data-href*="/news/"]'       # Data attributes
            ]
            
            for selector in selectors:
                links = soup.select(selector)
                if links:
                    self.stdout.write(f'   ✅ พบข่าวด้วย selector: {selector} ({len(links)} items)')
                    break
            else:
                # Fallback: หาทุก link ที่มี /news/ 
                links = soup.find_all('a', href=re.compile(r'/news/'))
                self.stdout.write(f'   🔍 Fallback: พบ {len(links)} news links')
            
            # ประมวลผล links
            seen_urls = set()
            for link in links:
                href = link.get('href', '')
                if not href:
                    continue
                
                # สร้าง absolute URL
                if href.startswith('/'):
                    full_url = 'https://www.thairath.co.th' + href
                elif href.startswith('http'):
                    full_url = href
                else:
                    continue
                
                # กรองเฉพาะข่าว local
                if '/news/local/' not in full_url:
                    continue
                
                # ป้องกันซ้ำ
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)
                
                # หา title
                title = ''
                if link.get('title'):
                    title = link['title'].strip()
                elif link.text:
                    title = link.text.strip()
                elif link.find('img') and link.find('img').get('alt'):
                    title = link.find('img')['alt'].strip()
                
                if title and len(title) > 10:  # ต้องมี title ที่มีความหมาย
                    news_items.append({
                        'title': title,
                        'url': full_url,
                        'scraped_at': timezone.now()
                    })
                
                if len(news_items) >= limit:
                    break
            
            return news_items[:limit]
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error scraping news list: {e}'))
            return []

    def scrape_news_content(self, url):
        """ดึงเนื้อหาข่าวจาก URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # ลบ elements ที่ไม่ต้องการ
            for element in soup(['script', 'style', 'nav', 'footer', 'aside', 'header']):
                element.decompose()
            
            # หา title
            title = ''
            title_selectors = ['h1', '.article-title', '.post-title', 'title']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if len(title) > 10:  # Title ที่มีความหมาย
                        break
            
            # หา content
            content = ''
            content_selectors = [
                '.article-content', '.post-content', '.entry-content',
                '[class*="content"]', 'article', '.detail', 'main'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # ลบ ads, social sharing
                    for unwanted in content_elem(['iframe', '.ads', '.social', '.share']):
                        unwanted.decompose()
                    
                    content = content_elem.get_text(separator=' ', strip=True)
                    if len(content) > 200:  # Content ที่มีความหมาย
                        break
            
            # ถ้าหา content ไม่ได้ ใช้ body
            if not content:
                body = soup.find('body')
                if body:
                    content = body.get_text(separator=' ', strip=True)
            
            # ทำความสะอาด content
            content = self.clean_content(content)
            
            if title and content and len(content) > 100:
                return {
                    'title': title.strip(),
                    'content': content[:2000],  # จำกัด 2000 ตัวอักษร
                    'url': url
                }
            
            return None
            
        except Exception as e:
            self.stdout.write(f'   ❌ Error scraping content: {e}')
            return None

    def clean_content(self, content):
        """ทำความสะอาดเนื้อหา"""
        if not content:
            return ""
        
        # ลบขยะเว็บไซต์
        junk_keywords = [
            'logo thairath', 'สมาชิก', 'ค้นหา', 'light', 'dark', 
            'ฟังข่าว', 'แชร์ข่าว', 'facebook', 'twitter', 'line'
        ]
        
        content_lower = content.lower()
        if any(keyword in content_lower for keyword in junk_keywords):
            # หาจุดเริ่มต้นเนื้อหาจริง
            start_markers = [
                'ที่ผ่านมา', 'เมื่อ', 'วันที่', 'เวลา', 'นาย', 'ดร.', 
                'เกิดเหตุ', 'รายงาน', 'แหล่งข่าว'
            ]
            
            for marker in start_markers:
                if marker in content:
                    start_pos = content.find(marker)
                    if start_pos > 50:  # ต้องมีขยะพอสมควร
                        content = content[start_pos:]
                        break
        
        # ลบเว้นวรรคเกิน, newlines เกิน
        content = re.sub(r'\\s+', ' ', content)
        content = re.sub(r'\\n+', '\\n', content)
        
        return content.strip()

    def save_article(self, content_data, analysis, category):
        """บันทึกข่าวลง database"""
        # สร้าง slug ที่ไม่ซ้ำ
        slug = generate_unique_slug(NewsArticle, content_data['title'], None)
        
        # เตรียม insight_entities สำหรับ Groq analysis
        insight_entities = []
        for item in analysis.get('detailed_numbers', []):
            insight_entities.append({
                'value': item.get('number', ''),
                'entity_type': 'number',
                'reasoning': item.get('source', ''),
                'significance_score': item.get('confidence', 0) / 100,
                'analyzer_type': 'groq'
            })
        
        # บันทึกข่าว
        article = NewsArticle.objects.create(
            title=content_data['title'],
            slug=slug,
            category=category,
            intro=content_data['content'][:300] + '...' if len(content_data['content']) > 300 else content_data['content'],
            content=content_data['content'],
            extracted_numbers=','.join(analysis['numbers'][:15]),
            confidence_score=min(analysis.get('relevance_score', 50), 100),
            lottery_relevance_score=analysis.get('relevance_score', 50),
            lottery_category=analysis.get('category', 'other'),
            status='published',
            published_date=timezone.now(),
            source_url=content_data['url'],
            
            # Groq AI analysis data
            insight_summary=analysis.get('reasoning', ''),
            insight_impact_score=analysis.get('relevance_score', 0) / 100,
            insight_entities=insight_entities,
            insight_analyzed_at=timezone.now()
        )
        
        return article
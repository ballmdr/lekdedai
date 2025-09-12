# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from news.models import NewsArticle
from news.groq_lottery_analyzer import GroqLotteryAnalyzer

class Command(BaseCommand):
    help = 'วิเคราะห์ข่าวที่มีอยู่ด้วย Groq Llama 3.1 8B Instant'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='จำนวนข่าวที่จะวิเคราะห์ (default: 10)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='วิเคราะห์ข่าวย้อนหลังกี่วัน (default: 1)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='บังคับวิเคราะห์ใหม่แม้ว่าจะมีผลการวิเคราะห์แล้ว'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        days = options['days']
        force = options['force']

        self.stdout.write(
            self.style.SUCCESS(f'🤖 เริ่มวิเคราะห์ข่าวด้วย Groq Llama 3.1 8B Instant')
        )
        self.stdout.write(f'📊 จำกัด: {limit} ข่าว, ย้อนหลัง: {days} วัน, บังคับใหม่: {force}')

        # Query ข่าวที่จะวิเคราะห์
        since_date = timezone.now() - timedelta(days=days)
        
        queryset = NewsArticle.objects.filter(
            created_at__gte=since_date,
            status='published'
        ).order_by('-created_at')

        if not force:
            # ข้ามข่าวที่วิเคราะห์ด้วย Groq แล้ว
            queryset = queryset.exclude(
                insight_entities__contains=[{'analyzer_type': 'groq'}]
            )

        articles = queryset[:limit]

        if not articles:
            self.stdout.write(
                self.style.WARNING('⚠️ ไม่พบข่าวที่ต้องวิเคราะห์')
            )
            return

        self.stdout.write(f'📰 พบ {len(articles)} ข่าวที่จะวิเคราะห์')

        # สร้าง Groq analyzer
        try:
            analyzer = GroqLotteryAnalyzer()
            self.stdout.write(self.style.SUCCESS('✅ เชื่อมต่อ Groq API สำเร็จ'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ ไม่สามารถเชื่อมต่อ Groq API: {e}')
            )
            return

        # วิเคราะห์ทีละข่าว
        success_count = 0
        error_count = 0

        for i, article in enumerate(articles, 1):
            self.stdout.write(f'\n📑 [{i}/{len(articles)}] {article.title[:50]}...')
            
            try:
                # วิเคราะห์ด้วย Groq
                result = analyzer.analyze_news_for_lottery(
                    article.title,
                    article.content or article.intro
                )

                if result['success']:
                    if result.get('is_relevant') and result.get('numbers'):
                        # อัพเดทผลการวิเคราะห์
                        article.extracted_numbers = ','.join(result['numbers'][:15])
                        article.lottery_relevance_score = result.get('relevance_score', 50)
                        article.lottery_category = result.get('category', 'other')
                        article.insight_summary = result.get('reasoning', '')
                        article.insight_impact_score = result.get('relevance_score', 0) / 100

                        # เพิ่มผล Groq analysis เข้าไปใน insight_entities
                        groq_entities = [
                            {
                                'value': item['number'],
                                'entity_type': 'number',
                                'reasoning': item['source'],
                                'significance_score': item['confidence'] / 100,
                                'analyzer_type': 'groq'
                            } for item in result.get('detailed_numbers', [])
                        ]

                        # รวมกับข้อมูลเดิม (ถ้ามี)
                        existing_entities = article.insight_entities or []
                        
                        # ลบข้อมูล Groq เก่าออก (ถ้า force=True)
                        if force:
                            existing_entities = [
                                e for e in existing_entities 
                                if e.get('analyzer_type') != 'groq'
                            ]
                        
                        article.insight_entities = existing_entities + groq_entities
                        article.save()

                        self.stdout.write(
                            self.style.SUCCESS(f'   ✅ เลข: {", ".join(result["numbers"])}, คะแนน: {result.get("relevance_score", 0)}')
                        )
                        success_count += 1
                    else:
                        self.stdout.write(
                            self.style.WARNING('   ⚠️ ไม่เกี่ยวข้องกับหวยหรือไม่พบเลขเด็ด')
                        )
                else:
                    error_msg = result.get('error', 'Unknown error')
                    if result.get('error') == 'RATE_LIMIT_EXCEEDED':
                        self.stdout.write(
                            self.style.ERROR('   ❌ Groq API Rate Limit - หยุดการทำงาน')
                        )
                        break
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'   ❌ การวิเคราะห์ล้มเหลว: {error_msg}')
                        )
                        error_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Error: {e}')
                )
                error_count += 1

        # สรุปผล
        self.stdout.write(f'\n=== สรุปผลการวิเคราะห์ ===')
        self.stdout.write(
            self.style.SUCCESS(f'✅ สำเร็จ: {success_count} ข่าว')
        )
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f'❌ ล้มเหลว: {error_count} ข่าว')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'🎉 เสร็จสิ้นการวิเคราะห์ด้วย Groq!')
        )
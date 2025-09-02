from django.core.management.base import BaseCommand
from django.db import transaction
from news.models import NewsArticle
from news.news_analyzer import NewsAnalyzer

class Command(BaseCommand):
    help = 'วิเคราะห์และให้คะแนนข่าวเก่าที่มีอยู่ด้วยระบบใหม่'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='จำนวนข่าวที่จะประมวลผลต่อครั้ง (default: 50)'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='บังคับประมวลผลข่าวที่มีคะแนนแล้ว'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        force = options['force']
        
        self.stdout.write(
            self.style.SUCCESS(f'🚀 เริ่มวิเคราะห์ข่าวด้วยระบบใหม่ (จำกัด {limit} ข่าว)')
        )
        
        # ตัวกรองข่าว
        if force:
            # ประมวลผลข่าวทั้งหมด
            queryset = NewsArticle.objects.filter(status='published')
            self.stdout.write('⚠️  โหมดบังคับ: ประมวลผลข่าวทั้งหมด')
        else:
            # ประมวลผลเฉพาะข่าวที่ยังไม่มีคะแนน
            queryset = NewsArticle.objects.filter(
                status='published',
                lottery_relevance_score=0
            )
            
        articles = queryset.order_by('-published_date')[:limit]
        
        if not articles:
            self.stdout.write(
                self.style.WARNING('❌ ไม่มีข่าวที่ต้องประมวลผล')
            )
            return
            
        self.stdout.write(f'📰 พบข่าวที่ต้องประมวลผล: {articles.count()} ข่าว')
        
        # เริ่มประมวลผล
        analyzer = NewsAnalyzer()
        processed_count = 0
        error_count = 0
        
        # สถิติหมวดหมู่
        category_stats = {
            'accident': 0,
            'celebrity': 0, 
            'economic': 0,
            'general': 0
        }
        
        for article in articles:
            try:
                with transaction.atomic():
                    self.stdout.write(f'🔍 วิเคราะห์: {article.title[:50]}...')
                    
                    # วิเคราะห์ด้วยระบบใหม่
                    analysis_result = analyzer.analyze_article(article)
                    
                    # อัปเดตข้อมูลในฐานข้อมูล
                    article.lottery_relevance_score = analysis_result['confidence']
                    article.lottery_category = analysis_result.get('category', 'general')
                    
                    # อัปเดตเลขที่สกัดได้ (ถ้ามี)
                    if analysis_result['numbers']:
                        article.extracted_numbers = ','.join(analysis_result['numbers'][:10])
                    
                    article.save(update_fields=[
                        'lottery_relevance_score', 
                        'lottery_category',
                        'extracted_numbers'
                    ])
                    
                    # นับสถิติ
                    category_stats[article.lottery_category] += 1
                    processed_count += 1
                    
                    # แสดงผลลัพธ์
                    self.stdout.write(
                        f'✅ คะแนน: {article.lottery_relevance_score} '
                        f'หมวด: {article.lottery_category} '
                        f'เลข: {len(analysis_result["numbers"])}'
                    )
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'❌ ข้อผิดพลาด: {article.title[:30]}... - {str(e)}')
                )
                continue
        
        # สรุปผลลัพธ์
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(f'🎯 ประมวลผลเสร็จสิ้น!')
        )
        self.stdout.write(f'✅ สำเร็จ: {processed_count} ข่าว')
        self.stdout.write(f'❌ ข้อผิดพลาด: {error_count} ข่าว')
        
        # สถิติหมวดหมู่
        self.stdout.write('\n📊 สถิติหมวดหมู่:')
        for category, count in category_stats.items():
            if count > 0:
                category_name = {
                    'accident': '🔥 อุบัติเหตุ',
                    'celebrity': '⭐ คนดัง',
                    'economic': '📈 เศรษฐกิจ',
                    'general': '📰 ทั่วไป'
                }.get(category, category)
                
                self.stdout.write(f'  {category_name}: {count} ข่าว')
        
        # ข้อเสนอแนะ
        high_score_count = NewsArticle.objects.filter(
            lottery_relevance_score__gte=80
        ).count()
        
        if high_score_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n🎉 มีข่าวคะแนนสูง (≥80): {high_score_count} ข่าว')
            )
        else:
            self.stdout.write(
                self.style.WARNING('\n⚠️  ไม่มีข่าวคะแนนสูง แนะนำให้เพิ่มข่าวอุบัติเหตุหรือคนดัง')
            )
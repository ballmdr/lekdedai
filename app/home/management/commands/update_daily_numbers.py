from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import logging

from news.models import NewsArticle
from ai_engine.models import EnsemblePrediction

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update daily lucky numbers from news and AI predictions'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if numbers already exist for today'
        )
    
    def handle(self, *args, **options):
        today = timezone.now().date()
        self.stdout.write(f'🎯 อัพเดทเลขประจำวัน {today}')
        
        # 1. อัพเดทเลขจากข่าว 24 ชั่วโมงล่าสุด
        news_count = self.update_news_numbers()
        
        # 2. อัพเดทเลข AI predictions
        ai_count = self.update_ai_predictions()
        
        # 3. สร้างรายงาน
        self.generate_report(news_count, ai_count)
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ อัพเดทเสร็จสิ้น: ข่าว {news_count} บทความ, AI {ai_count} การทำนาย')
        )
    
    def update_news_numbers(self):
        """อัพเดทเลขจากข่าว 24 ชั่วโมงล่าสุด"""
        cutoff_time = timezone.now() - timedelta(hours=24)
        
        recent_news = NewsArticle.objects.filter(
            status='published',
            published_date__gte=cutoff_time
        ).order_by('-published_date')
        
        self.stdout.write(f'📰 พบข่าวใหม่ {recent_news.count()} บทความ')
        
        all_numbers = []
        for article in recent_news:
            numbers = article.get_extracted_numbers_list()
            # เอาเฉพาะเลข 2 หลัก
            two_digit_numbers = [num for num in numbers if len(num) == 2]
            all_numbers.extend(two_digit_numbers[:2])  # สูงสุด 2 เลขต่อบทความ
        
        unique_numbers = list(set(all_numbers))[:6]  # สูงสุด 6 เลข
        
        if unique_numbers:
            self.stdout.write(f'🔢 เลขจากข่าว: {", ".join(unique_numbers)}')
        else:
            self.stdout.write('⚠️  ไม่มีเลขใหม่จากข่าว')
            
        return recent_news.count()
    
    def update_ai_predictions(self):
        """อัพเดทเลขจาก AI predictions"""
        ai_predictions = EnsemblePrediction.objects.filter(
            session__status__in=['completed', 'locked'],
            overall_confidence__gte=0.70
        ).order_by('-prediction_timestamp')
        
        self.stdout.write(f'🤖 พบการทำนาย AI {ai_predictions.count()} รายการ')
        
        all_numbers = []
        for prediction in ai_predictions[:3]:
            if hasattr(prediction, 'get_top_two_digit_numbers') and prediction.get_top_two_digit_numbers:
                numbers = [
                    item.get('number', item) if isinstance(item, dict) else item 
                    for item in prediction.get_top_two_digit_numbers[:2]
                ]
                all_numbers.extend(numbers)
        
        # แปลงเป็นเลข 2 หลัก
        unique_numbers = list(set([
            str(num).zfill(2) for num in all_numbers 
            if str(num).isdigit()
        ]))[:3]
        
        if unique_numbers:
            self.stdout.write(f'🔢 เลข AI: {", ".join(unique_numbers)}')
        else:
            self.stdout.write('⚠️  ไม่มีเลขใหม่จาก AI')
            
        return ai_predictions.count()
    
    def generate_report(self, news_count, ai_count):
        """สร้างรายงานสรุป"""
        today = timezone.now()
        self.stdout.write('\n📊 รายงานสรุป:')
        self.stdout.write(f'   วันที่: {today.strftime("%d/%m/%Y %H:%M")}')
        self.stdout.write(f'   ข่าวที่ประมวลผล: {news_count} บทความ')
        self.stdout.write(f'   การทำนาย AI: {ai_count} รายการ')
        self.stdout.write(f'   สถานะ: พร้อมใช้งาน ✅')
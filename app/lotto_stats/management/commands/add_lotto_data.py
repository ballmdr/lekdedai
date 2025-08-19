from django.core.management.base import BaseCommand
from lotto_stats.models import LotteryDraw
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Add sample lottery data'
    
    def handle(self, *args, **options):
        # สร้างข้อมูลตัวอย่าง 30 งวด
        base_date = datetime.now().date()
        
        sample_data = []
        for i in range(30):
            # ย้อนหลังทุก 15 วัน (2 งวดต่อเดือน)
            draw_date = base_date - timedelta(days=i*15)
            
            # สุ่มเลข
            first_prize = str(random.randint(0, 999999)).zfill(6)
            two_digit = str(random.randint(0, 99)).zfill(2)
            
            # เลข 3 ตัวหน้า (2 ชุด)
            three_front = []
            for _ in range(2):
                three_front.append(str(random.randint(0, 999)).zfill(3))
            
            # เลข 3 ตัวหลัง (2 ชุด)
            three_back = []
            for _ in range(2):
                three_back.append(str(random.randint(0, 999)).zfill(3))
            
            # สร้างหรืออัพเดต
            LotteryDraw.objects.update_or_create(
                draw_date=draw_date,
                defaults={
                    'draw_round': f"{draw_date.strftime('%d/%m/%Y')}",
                    'first_prize': first_prize,
                    'two_digit': two_digit,
                    'three_digit_front': ', '.join(three_front),
                    'three_digit_back': ', '.join(three_back),
                }
            )
            
            self.stdout.write(f"Added draw for {draw_date}")
        
        self.stdout.write(self.style.SUCCESS('Successfully added sample lottery data'))


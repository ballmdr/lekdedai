from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from lottery_checker.lotto_service import LottoService
from utils.lottery_dates import LOTTERY_DATES

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'ล้างข้อมูลหวยทั้งหมดและดึงข้อมูลใหม่จาก API'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days-back',
            type=int,
            default=30,
            help='จำนวนวันที่ย้อนหลัง (ค่าเริ่มต้น: 30)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='บังคับล้างข้อมูลโดยไม่ถามยืนยัน',
        )
    
    def handle(self, *args, **options):
        days_back = options['days_back']
        force = options['force']
        
        service = LottoService()
        
        if not force:
            confirm = input(f'คุณแน่ใจหรือไม่ที่จะล้างข้อมูลหวยทั้งหมดและดึงข้อมูลใหม่ {days_back} วัน? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write('ยกเลิกการดำเนินการ')
                return
        
        # ล้างข้อมูลทั้งหมด
        self.stdout.write('🗑️  กำลังล้างข้อมูลหวยทั้งหมด...')
        if service.clear_all_data():
            self.stdout.write(
                self.style.SUCCESS('✅ ล้างข้อมูลหวยทั้งหมดสำเร็จ')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ ไม่สามารถล้างข้อมูลได้')
            )
            return
        
        # ดึงข้อมูลใหม่ (เฉพาะวันหวยออกตาม LOTTERY_DATES เพื่อลดจำนวน API call)
        draw_date_strs = LOTTERY_DATES.get_recent_draw_dates(days_back)
        self.stdout.write(f'🌐 กำลังดึงข้อมูลหวย {len(draw_date_strs)} งวดล่าสุดจาก API...')
        
        success_count = 0
        error_count = 0
        
        for date_str in reversed(draw_date_strs):
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            date = target_date.day
            month = target_date.month
            year = target_date.year
            
            self.stdout.write(f'📅 ดึงข้อมูลวันที่ {date:02d}/{month:02d}/{year}...')
            
            result = service.get_or_fetch_result(date, month, year)
            
            if result['success']:
                success_count += 1
                source = result['source']
                self.stdout.write(f'   ✅ สำเร็จ ({source})')
            else:
                error_count += 1
                self.stdout.write(f'   ❌ ล้มเหลว: {result["error"]}')
        
        # สรุปผล
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('📊 สรุปผลการดำเนินการ')
        self.stdout.write('=' * 50)
        self.stdout.write(f'✅ สำเร็จ: {success_count} งวด')
        self.stdout.write(f'❌ ล้มเหลว: {error_count} งวด')
        self.stdout.write(f'📅 รวม: {len(draw_date_strs)} งวด')
        
        if success_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n🎉 ดึงข้อมูลหวยสำเร็จ {success_count} วัน')
            )
        else:
            self.stdout.write(
                self.style.WARNING('\n⚠️  ไม่สามารถดึงข้อมูลหวยได้')
            )

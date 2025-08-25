import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from lottery_checker.models import LottoResult
from lotto_stats.models import LotteryDraw
from utils.lottery_dates import LOTTERY_DATES

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'ซิงค์ข้อมูลหวยจาก lottery_checker ไปยัง lotto_stats'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days-back',
            type=int,
            default=30,
            help='จำนวนวันที่ต้องการดึงข้อมูลย้อนหลัง (default: 30)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='บังคับอัปเดตข้อมูลที่มีอยู่แล้ว'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='ล้างข้อมูลเดิมใน lotto_stats ก่อนซิงค์'
        )
    
    def handle(self, *args, **options):
        """จัดการคำสั่ง"""
        days_back = options['days_back']
        force = options['force']
        clear_existing = options['clear_existing']
        
        if clear_existing:
            self.stdout.write("🗑️ ล้างข้อมูลทั้งหมดใน lotto_stats...")
            LotteryDraw.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("✅ ล้างข้อมูลเสร็จสิ้น"))
        
        # ใช้ LotteryDates แทนการคำนวณแบบเดิม
        self.stdout.write(f"🔄 เริ่มซิงค์ข้อมูลหวยตามวันที่ออกที่กำหนด...")
        
        # ดึงวันที่หวยออกย้อนหลังตามจำนวนวันที่ระบุ
        recent_draw_dates = LOTTERY_DATES.get_recent_draw_dates(days_back)
        
        if not recent_draw_dates:
            self.stdout.write(
                self.style.WARNING(f"⚠️ ไม่พบวันที่หวยออกใน {days_back} วันล่าสุด")
            )
            return
        
        self.stdout.write(f"📊 พบวันที่หวยออก {len(recent_draw_dates)} รายการ")
        
        synced_count = 0
        updated_count = 0
        error_count = 0
        
        for date_str in recent_draw_dates:
            try:
                # แปลง string เป็น date
                draw_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                # ดึงข้อมูลจาก lottery_checker
                lotto_result = LottoResult.objects.filter(draw_date=draw_date).first()
                
                if not lotto_result:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️ ไม่พบข้อมูลใน lottery_checker สำหรับวันที่ {date_str}")
                    )
                    error_count += 1
                    continue
                
                # แปลงข้อมูลจาก JSON เป็นรูปแบบที่ lotto_stats ต้องการ
                converted_data = self.convert_lotto_data(lotto_result)
                
                if not converted_data:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️ ไม่สามารถแปลงข้อมูลวันที่ {date_str} ได้ (ไม่มีข้อมูลรางวัล)")
                    )
                    error_count += 1
                    continue
                
                # สร้างหรืออัปเดตข้อมูล
                lottery_draw, created = LotteryDraw.objects.update_or_create(
                    draw_date=draw_date,
                    defaults=converted_data
                )
                
                if created:
                    synced_count += 1
                    self.stdout.write(f"✅ สร้างข้อมูลใหม่: {date_str}")
                else:
                    if force:
                        updated_count += 1
                        self.stdout.write(f"🔄 อัปเดตข้อมูล: {date_str}")
                    else:
                        self.stdout.write(f"⏭️ ข้ามข้อมูลที่มีอยู่แล้ว: {date_str}")
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ เกิดข้อผิดพลาดสำหรับวันที่ {date_str}: {e}")
                )
                error_count += 1
        
        # สรุปผล
        self.stdout.write("\n" + "="*50)
        self.stdout.write("📊 สรุปการซิงค์ข้อมูล")
        self.stdout.write("="*50)
        self.stdout.write(f"✅ สร้างใหม่: {synced_count} รายการ")
        if force:
            self.stdout.write(f"🔄 อัปเดต: {updated_count} รายการ")
        self.stdout.write(f"❌ เกิดข้อผิดพลาด: {error_count} รายการ")
        self.stdout.write(f"📋 รวมทั้งหมด: {synced_count + updated_count} รายการ")
        
        if error_count == 0:
            self.stdout.write(self.style.SUCCESS("🎉 ซิงค์ข้อมูลสำเร็จ!"))
        else:
            self.stdout.write(self.style.WARNING("⚠️ ซิงค์ข้อมูลเสร็จสิ้น แต่มีข้อผิดพลาดบางส่วน"))
    
    def convert_lotto_data(self, lotto_result):
        """แปลงข้อมูลจาก LottoResult เป็นรูปแบบที่ LotteryDraw ต้องการ"""
        try:
            result_data = lotto_result.result_data
            
            if not isinstance(result_data, dict):
                return None
            
            # ตรวจสอบว่ามีข้อมูลรางวัลหรือไม่
            if not self._has_lottery_data(result_data):
                return None
            
            # ดึงข้อมูลรางวัลที่ 1
            first_prize = self._extract_first_prize(result_data)
            if not first_prize:
                return None
            
            # ดึงเลข 2 ตัว (เลขท้ายของรางวัลที่ 1)
            two_digit = first_prize[-2:] if len(first_prize) >= 2 else ''
            
            # ดึงเลข 3 ตัวหน้า (จากรางวัลที่ 2, 3) - จำกัดจำนวนเพื่อไม่ให้เกิน field length
            three_digit_front = self._extract_three_digit_front(result_data)
            three_digit_front_str = self._limit_field_length(three_digit_front, 100)
            
            # ดึงเลข 3 ตัวหลัง (จากรางวัลที่ 4, 5) - จำกัดจำนวนเพื่อไม่ให้เกิน field length
            three_digit_back = self._extract_three_digit_back(result_data)
            three_digit_back_str = self._limit_field_length(three_digit_back, 100)
            
            # สร้างข้อมูลที่แปลงแล้ว
            converted_data = {
                'draw_round': lotto_result.draw_date.strftime('%d/%m/%Y'),
                'first_prize': first_prize,
                'two_digit': two_digit,
                'three_digit_front': three_digit_front_str,
                'three_digit_back': three_digit_back_str,
            }
            
            return converted_data
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการแปลงข้อมูล: {e}")
            return None
    
    def _has_lottery_data(self, result_data):
        """ตรวจสอบว่ามีข้อมูลรางวัลหรือไม่"""
        # ตรวจสอบรูปแบบต่างๆ
        if 'first' in result_data and result_data['first']:
            return True
        if 'response' in result_data and result_data['response']:
            response_data = result_data['response']
            if isinstance(response_data, dict) and 'first' in response_data:
                return True
        if 'data' in result_data and result_data['data']:
            data = result_data['data']
            if isinstance(data, dict) and 'first' in data:
                return True
        return False
    
    def _extract_first_prize(self, result_data):
        """ดึงรางวัลที่ 1 จากข้อมูล"""
        # รูปแบบที่ 1: first อยู่ในระดับบน
        if 'first' in result_data and result_data['first']:
            first_data = result_data['first']
            if isinstance(first_data, dict) and 'number' in first_data:
                numbers = first_data['number']
                if isinstance(numbers, list) and numbers:
                    return numbers[0].get('value', '')
                elif isinstance(numbers, str):
                    return numbers
            elif isinstance(first_data, str):
                return first_data
        
        # รูปแบบที่ 2: first อยู่ใน response
        if 'response' in result_data and result_data['response']:
            response_data = result_data['response']
            if isinstance(response_data, dict) and 'first' in response_data:
                first_data = response_data['first']
                if isinstance(first_data, dict) and 'number' in first_data:
                    numbers = first_data['number']
                    if isinstance(numbers, list) and numbers:
                        return numbers[0].get('value', '')
                    elif isinstance(numbers, str):
                        return numbers
                elif isinstance(first_data, str):
                    return first_data
        
        # รูปแบบที่ 3: first อยู่ใน data
        if 'data' in result_data and result_data['data']:
            data = result_data['data']
            if isinstance(data, dict) and 'first' in data:
                first_data = data['first']
                if isinstance(first_data, dict) and 'number' in first_data:
                    numbers = first_data['number']
                    if isinstance(numbers, list) and numbers:
                        return numbers[0].get('value', '')
                    elif isinstance(numbers, str):
                        return numbers
                elif isinstance(first_data, str):
                    return first_data
        
        return None
    
    def _extract_three_digit_front(self, result_data):
        """ดึงเลข 3 ตัวหน้า (จากรางวัลที่ 2, 3)"""
        three_digit_front = []
        
        for prize_type in ['second', 'third']:
            numbers = self._extract_prize_numbers(result_data, prize_type)
            if numbers:
                three_digit_front.extend(numbers)
        
        return three_digit_front
    
    def _extract_three_digit_back(self, result_data):
        """ดึงเลข 3 ตัวหลัง (จากรางวัลที่ 4, 5)"""
        three_digit_back = []
        
        for prize_type in ['fourth', 'fifth']:
            numbers = self._extract_prize_numbers(result_data, prize_type)
            if numbers:
                three_digit_back.extend(numbers)
        
        return three_digit_back
    
    def _extract_prize_numbers(self, result_data, prize_type):
        """ดึงเลขรางวัลตามประเภท"""
        numbers = []
        
        # รูปแบบที่ 1: อยู่ในระดับบน
        if prize_type in result_data and result_data[prize_type]:
            prize_data = result_data[prize_type]
            numbers.extend(self._parse_prize_data(prize_data))
        
        # รูปแบบที่ 2: อยู่ใน response
        if 'response' in result_data and result_data['response']:
            response_data = result_data['response']
            if isinstance(response_data, dict) and prize_type in response_data:
                prize_data = response_data[prize_type]
                numbers.extend(self._parse_prize_data(prize_data))
        
        # รูปแบบที่ 3: อยู่ใน data
        if 'data' in result_data and result_data['data']:
            data = result_data['data']
            if isinstance(data, dict) and prize_type in data:
                prize_data = data[prize_type]
                numbers.extend(self._parse_prize_data(prize_data))
        
        return numbers
    
    def _parse_prize_data(self, prize_data):
        """แปลงข้อมูลรางวัลเป็นรายการเลข"""
        numbers = []
        
        if isinstance(prize_data, list):
            for item in prize_data:
                if isinstance(item, dict):
                    if 'value' in item:
                        numbers.append(str(item['value']))
                    elif 'number' in item:
                        numbers.append(str(item['number']))
                elif isinstance(item, str):
                    numbers.append(item)
        elif isinstance(prize_data, str):
            numbers.append(prize_data)
        elif isinstance(prize_data, dict):
            if 'number' in prize_data:
                number_data = prize_data['number']
                if isinstance(number_data, list):
                    for item in number_data:
                        if isinstance(item, dict) and 'value' in item:
                            numbers.append(str(item['value']))
                        elif isinstance(item, str):
                            numbers.append(str(item))
                elif isinstance(number_data, str):
                    numbers.append(number_data)
        
        return numbers

    def _limit_field_length(self, numbers, max_length):
        """จำกัดความยาวของ field ให้ไม่เกิน max_length"""
        if not numbers:
            return ''
        
        # เริ่มต้นด้วยตัวแรก
        result = [str(numbers[0])]
        current_length = len(result[0])
        
        # เพิ่มตัวถัดไปถ้าความยาวยังไม่เกิน
        for number in numbers[1:]:
            number_str = str(number)
            # +2 สำหรับ ", " ที่จะเพิ่ม
            if current_length + len(number_str) + 2 <= max_length:
                result.append(number_str)
                current_length += len(number_str) + 2
            else:
                break
        
        return ', '.join(result)

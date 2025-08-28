from django.utils import timezone
from datetime import datetime, timedelta
import logging
from django.db import transaction

from .models import LotteryDraw
from lottery_checker.models import LottoResult
from utils.lottery_dates import LOTTERY_DATES

logger = logging.getLogger(__name__)

class LottoSyncService:
    """บริการซิงค์ข้อมูลหวยจาก lottery_checker ไปยัง lotto_stats"""
    
    def __init__(self):
        self.last_sync_time = None
    
    def sync_recent_data(self, days_back=30, force_update=False):
        """ซิงค์ข้อมูลล่าสุดตามจำนวนวันที่ระบุ"""
        try:
            # ใช้ LotteryDates แทนการคำนวณแบบเดิม
            recent_draw_dates = LOTTERY_DATES.get_recent_draw_dates(days_back)
            
            if not recent_draw_dates:
                return {
                    'success': False,
                    'error': f'ไม่พบวันที่หวยออกใน {days_back} วันล่าสุด'
                }
            
            synced_count = 0
            error_count = 0
            results = []
            
            for date_str in recent_draw_dates:
                try:
                    # แปลง string เป็น date
                    draw_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    # ซิงค์ข้อมูลสำหรับวันที่นี้
                    result = self.sync_specific_date(draw_date, force_update)
                    
                    if result['success']:
                        synced_count += 1
                        results.append(f"✅ {date_str}: {result['message']}")
                    else:
                        error_count += 1
                        results.append(f"❌ {date_str}: {result['error']}")
                        
                except Exception as e:
                    error_count += 1
                    results.append(f"❌ {date_str}: เกิดข้อผิดพลาด - {str(e)}")
            
            return {
                'success': True,
                'message': f'ซิงค์ข้อมูลเสร็จสิ้น: {synced_count} สำเร็จ, {error_count} ไม่สำเร็จ',
                'synced_count': synced_count,
                'error_count': error_count,
                'total_dates': len(recent_draw_dates),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการซิงค์ข้อมูลล่าสุด: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def sync_all_draw_dates(self, force_update=False):
        """ซิงค์ข้อมูลทั้งหมดตามวันที่หวยออกที่กำหนด"""
        try:
            all_draw_dates = LOTTERY_DATES.get_all_draw_dates()
            
            synced_count = 0
            error_count = 0
            results = []
            
            for date_str in all_draw_dates:
                try:
                    # แปลง string เป็น date
                    draw_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    # ซิงค์ข้อมูลสำหรับวันที่นี้
                    result = self.sync_specific_date(draw_date, force_update)
                    
                    if result['success']:
                        synced_count += 1
                        results.append(f"✅ {date_str}: {result['message']}")
                    else:
                        error_count += 1
                        results.append(f"❌ {date_str}: {result['error']}")
                        
                except Exception as e:
                    error_count += 1
                    results.append(f"❌ {date_str}: เกิดข้อผิดพลาด - {str(e)}")
            
            return {
                'success': True,
                'message': f'ซิงค์ข้อมูลทั้งหมดเสร็จสิ้น: {synced_count} สำเร็จ, {error_count} ไม่สำเร็จ',
                'synced_count': synced_count,
                'error_count': error_count,
                'total_dates': len(all_draw_dates),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการซิงค์ข้อมูลทั้งหมด: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def sync_specific_date(self, date, force_update=False):
        """ซิงค์ข้อมูลสำหรับวันที่เฉพาะ"""
        try:
            if isinstance(date, str):
                date = datetime.strptime(date, '%Y-%m-%d').date()
            elif isinstance(date, datetime):
                date = date.date()
            
            # ดึงข้อมูลจาก lottery_checker
            lotto_result = LottoResult.objects.filter(draw_date=date).first()
            
            if not lotto_result:
                return {
                    'success': False,
                    'error': f'ไม่พบข้อมูลใน lottery_checker สำหรับวันที่ {date}'
                }
            
            # แปลงข้อมูล
            converted_data = self._convert_lotto_data(lotto_result)
            
            if not converted_data:
                return {
                    'success': False,
                    'error': f'ไม่สามารถแปลงข้อมูลวันที่ {date} ได้'
                }
            
            # สร้างหรืออัปเดตข้อมูล
            lottery_draw, created = LotteryDraw.objects.update_or_create(
                draw_date=date,
                defaults=converted_data
            )
            
            action = 'สร้างใหม่' if created else 'อัปเดต'
            
            return {
                'success': True,
                'message': f'{action}ข้อมูลวันที่ {date} สำเร็จ',
                'action': action,
                'data': converted_data
            }
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการซิงค์วันที่ {date}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_sync_status(self):
        """ดึงสถานะการซิงค์ข้อมูล"""
        try:
            # ข้อมูลล่าสุดใน lotto_stats
            latest_lotto_stats = LotteryDraw.objects.order_by('-draw_date').first()
            
            # ข้อมูลล่าสุดใน lottery_checker
            latest_lotto_checker = LottoResult.objects.order_by('-draw_date').first()
            
            # ข้อมูลเก่าสุดใน lotto_stats
            oldest_lotto_stats = LotteryDraw.objects.order_by('draw_date').first()
            
            # ข้อมูลเก่าสุดใน lottery_checker
            oldest_lotto_checker = LottoResult.objects.order_by('draw_date').first()
            
            status = {
                'lotto_stats': {
                    'total_records': LotteryDraw.objects.count(),
                    'latest_date': latest_lotto_stats.draw_date.isoformat() if latest_lotto_stats else None,
                    'oldest_date': oldest_lotto_stats.draw_date.isoformat() if oldest_lotto_stats else None,
                },
                'lottery_checker': {
                    'total_records': LottoResult.objects.count(),
                    'latest_date': latest_lotto_checker.draw_date.isoformat() if latest_lotto_checker else None,
                    'oldest_date': oldest_lotto_checker.draw_date.isoformat() if oldest_lotto_checker else None,
                },
                'last_sync': self.last_sync_time.isoformat() if self.last_sync_time else None,
                'is_synced': False
            }
            
            # ตรวจสอบว่าข้อมูลซิงค์กันหรือไม่
            if (latest_lotto_stats and latest_lotto_checker and 
                latest_lotto_stats.draw_date == latest_lotto_checker.draw_date):
                status['is_synced'] = True
            
            return status
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการดึงสถานะ: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _convert_lotto_data(self, lotto_result):
        """แปลงข้อมูลจาก LottoResult เป็นรูปแบบที่ LotteryDraw ต้องการ"""
        try:
            result_data = lotto_result.result_data
            
            if not isinstance(result_data, dict):
                return None
            
            # ตรวจสอบว่ามีข้อมูลรางวัลหรือไม่
            if not self._has_lottery_data(result_data):
                logger.warning(f"ไม่มีข้อมูลรางวัลในวันที่ {lotto_result.draw_date}")
                return None
            
            # ดึงข้อมูลรางวัลที่ 1
            first_prize = self._extract_first_prize(result_data)
            if not first_prize:
                return None
            
            # ดึงเลข 2 ตัว (จาก last2 field)
            two_digit_numbers = self._extract_prize_numbers(result_data, 'last2')
            two_digit = two_digit_numbers[0] if two_digit_numbers else (first_prize[-2:] if len(first_prize) >= 2 else '')
            
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
            if isinstance(response_data, dict):
                # ตรวจสอบใน response.result.data
                if 'result' in response_data and response_data['result']:
                    result = response_data['result']
                    if isinstance(result, dict) and 'data' in result and result['data']:
                        data = result['data']
                        if isinstance(data, dict) and 'first' in data and data['first']:
                            return True
                # ตรวจสอบใน response โดยตรง
                if 'first' in response_data:
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
        
        # รูปแบบที่ 2: first อยู่ใน response.result.data (GLO API format)
        if 'response' in result_data and result_data['response']:
            response_data = result_data['response']
            if isinstance(response_data, dict) and 'result' in response_data:
                result = response_data['result']
                if isinstance(result, dict) and 'data' in result:
                    data = result['data']
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
        
        # รูปแบบที่ 3: first อยู่ใน response โดยตรง
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
        
        # รูปแบบที่ 4: first อยู่ใน data
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
        """ดึงเลข 3 ตัวหน้า (จาก last3f)"""
        return self._extract_prize_numbers(result_data, 'last3f')
    
    def _extract_three_digit_back(self, result_data):
        """ดึงเลข 3 ตัวหลัง (จาก last3b)"""
        return self._extract_prize_numbers(result_data, 'last3b')
    
    def _extract_prize_numbers(self, result_data, prize_type):
        """ดึงเลขรางวัลตามประเภท"""
        numbers = []
        
        # รูปแบบที่ 1: อยู่ในระดับบน
        if prize_type in result_data and result_data[prize_type]:
            prize_data = result_data[prize_type]
            numbers.extend(self._parse_prize_data(prize_data))
        
        # รูปแบบที่ 2: อยู่ใน response.result.data (GLO API format)
        if 'response' in result_data and result_data['response']:
            response_data = result_data['response']
            if isinstance(response_data, dict) and 'result' in response_data:
                result = response_data['result']
                if isinstance(result, dict) and 'data' in result:
                    data = result['data']
                    if isinstance(data, dict) and prize_type in data:
                        prize_data = data[prize_type]
                        numbers.extend(self._parse_prize_data(prize_data))
        
        # รูปแบบที่ 3: อยู่ใน response โดยตรง
        if 'response' in result_data and result_data['response']:
            response_data = result_data['response']
            if isinstance(response_data, dict) and prize_type in response_data:
                prize_data = response_data[prize_type]
                numbers.extend(self._parse_prize_data(prize_data))
        
        # รูปแบบที่ 4: อยู่ใน data
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

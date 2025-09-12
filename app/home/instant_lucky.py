import re
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import Counter
from django.utils import timezone
from django.db.models import Q
from django.core.cache import cache

from news.models import NewsArticle
# from news.news_lottery_scorer import NewsLotteryScorer  # ลบไฟล์แล้ว


class InstantLuckyNumberGenerator:
    """
    เครื่องกำเนิดเลขเด็ดทันใจ - ไม่เก็บข้อมูลผู้ใช้
    รวมเลขจากวันที่สำคัญ + ข่าวล่าสุด + อัลกอริทึมพิเศษ
    """
    
    def __init__(self):
        # self.lottery_scorer = NewsLotteryScorer()  # ใช้ AI analyzer แทน
        from news.analyzer_switcher import AnalyzerSwitcher
        self.analyzer = AnalyzerSwitcher(preferred_analyzer='groq')
        self.cache_timeout = 300  # 5 นาที
    
    def generate_lucky_numbers(self, significant_date: Optional[str] = None, selected_news_ids: Optional[List[int]] = None) -> Dict:
        """
        สร้างเลขเด็ดทันใจ
        
        Args:
            significant_date: วันที่สำคัญ (YYYY-MM-DD) หรือ None = วันปัจจุบัน
            selected_news_ids: รายการ ID ของข่าวที่เลือก หรือ None = ใช้ข่าวล่าสุดอัตโนมัติ
            
        Returns:
            Dict: ข้อมูลเลขเด็ดและรายละเอียด
        """
        
        # ใช้วันปัจจุบันถ้าไม่ระบุ
        if not significant_date:
            target_date = timezone.now().date()
        else:
            try:
                target_date = datetime.strptime(significant_date, "%Y-%m-%d").date()
            except ValueError:
                target_date = timezone.now().date()
        
        # สร้าง cache key ที่ไม่ระบุตัวตน (รวม selected_news_ids ด้วย)
        news_key = str(sorted(selected_news_ids)) if selected_news_ids else "auto"
        cache_key = f"instant_lucky:{target_date.strftime('%Y%m%d')}:{news_key}"
        
        # ตรวจสอบ cache
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # ส่วนที่ 1: เลขจากวันที่ (40%)
        date_numbers = self._extract_date_numbers(target_date)
        
        # ส่วนที่ 2: เลขจากข่าวล่าสุด (50%)
        news_numbers = self._extract_recent_news_numbers(selected_news_ids)
        
        # ส่วนที่ 3: เลขผสม (10%)
        mixed_numbers = self._generate_mixed_numbers(target_date, date_numbers, news_numbers)
        
        # รวมและคัดเลือกเลขที่ดีที่สุด
        final_lucky_numbers = self._combine_and_select_numbers(
            date_numbers, news_numbers, mixed_numbers, target_date
        )
        
        # จัดเตรียมผลลัพธ์
        result = {
            'lucky_numbers': final_lucky_numbers,
            'generated_at': timezone.now().isoformat(),
            'significant_date': target_date.strftime('%Y-%m-%d'),
            'components': {
                'date_contribution': len(date_numbers),
                'news_contribution': len(news_numbers),
                'mixed_contribution': len(mixed_numbers)
            },
            'insights': self._generate_insights(final_lucky_numbers, target_date),
            'disclaimer': 'เลขเด็ดสำหรับความบันเทิง ไม่เก็บข้อมูลส่วนตัว'
        }
        
        # บันทึกลง cache
        cache.set(cache_key, result, timeout=self.cache_timeout)
        
        return result
    
    def _extract_date_numbers(self, target_date: datetime.date) -> List[Dict]:
        """สกัดเลขจากวันที่สำคัญ"""
        
        numbers = []
        day = target_date.day
        month = target_date.month
        year = target_date.year
        
        # เลขจากวัน
        if day < 10:
            numbers.append({
                'number': f'0{day}',
                'source': 'day',
                'confidence': 85,
                'reason': f'วันที่ {day}'
            })
        else:
            numbers.append({
                'number': str(day),
                'source': 'day', 
                'confidence': 90,
                'reason': f'วันที่ {day}'
            })
            # แยกหลักด้วย
            numbers.append({
                'number': f'{str(day)[0]}0',
                'source': 'day_tens',
                'confidence': 70,
                'reason': f'หลักสิบของวันที่'
            })
        
        # เลขจากเดือน
        if month < 10:
            numbers.append({
                'number': f'0{month}',
                'source': 'month',
                'confidence': 80,
                'reason': f'เดือนที่ {month}'
            })
        else:
            numbers.append({
                'number': str(month),
                'source': 'month',
                'confidence': 85,
                'reason': f'เดือนที่ {month}'
            })
        
        # เลขจากปี (2 หลักท้าย)
        year_2digit = year % 100
        numbers.append({
            'number': f'{year_2digit:02d}',
            'source': 'year',
            'confidence': 75,
            'reason': f'ปี {year}'
        })
        
        # เลขรวม (วัน + เดือน)
        date_sum = day + month
        if date_sum > 99:
            date_sum = date_sum % 100
        numbers.append({
            'number': f'{date_sum:02d}',
            'source': 'date_sum',
            'confidence': 80,
            'reason': f'ผลรวมวัน+เดือน ({day}+{month})'
        })
        
        # เลขจากวันในสัปดาห์
        weekday = target_date.weekday()  # 0=Monday
        thai_weekday_numbers = ['01', '02', '03', '04', '05', '06', '07']
        numbers.append({
            'number': thai_weekday_numbers[weekday],
            'source': 'weekday',
            'confidence': 65,
            'reason': f'วัน{["จันทร์", "อังคาร", "พุธ", "พฤหัส", "ศุกร์", "เสาร์", "อาทิตย์"][weekday]}'
        })
        
        return numbers
    
    def _extract_recent_news_numbers(self, selected_news_ids: Optional[List[int]] = None) -> List[Dict]:
        """สกัดเลขจากข่าวล่าสุด หรือข่าวที่เลือก"""
        
        if selected_news_ids:
            # ใช้ข่าวที่เลือกเฉพาะ
            selected_news = NewsArticle.objects.filter(
                id__in=selected_news_ids,
                status='published'
            ).order_by('-lottery_relevance_score', '-published_date')
        else:
            # หาข่าวล่าสุดที่มีคะแนนความเหมาะสมสูง (แบบเดิม)
            recent_cutoff = timezone.now() - timedelta(hours=48)
            selected_news = NewsArticle.objects.filter(
                status='published',
                lottery_relevance_score__gte=70,
                published_date__gte=recent_cutoff
            ).order_by('-lottery_relevance_score', '-published_date')[:5]
            
            # ถ้าไม่มีข่าวคะแนนสูง ใช้ข่าวล่าสุดธรรมดา
            if not selected_news:
                selected_news = NewsArticle.objects.filter(
                    status='published',
                    published_date__gte=recent_cutoff
                ).order_by('-published_date')[:3]
        
        numbers = []
        
        for article in selected_news:
            # ใช้เลขที่สกัดไว้แล้ว
            extracted_nums = article.get_extracted_numbers_list()
            
            for num_str in extracted_nums[:3]:  # เอาแค่ 3 เลขแรกต่อข่าว
                if num_str and num_str.isdigit() and len(num_str) >= 2:
                    # ปรับเป็นเลข 2 หลัก
                    if len(num_str) > 2:
                        formatted_num = num_str[:2]
                    else:
                        formatted_num = num_str.zfill(2)
                    
                    confidence = min(article.lottery_relevance_score, 95)
                    
                    numbers.append({
                        'number': formatted_num,
                        'source': 'news',
                        'confidence': confidence,
                        'reason': f'จากข่าว: {article.title[:30]}...',
                        'news_category': article.lottery_category or 'general'
                    })
        
        # เรียงตามความเชื่อมั่น
        numbers.sort(key=lambda x: x['confidence'], reverse=True)
        
        return numbers[:8]  # เอาแค่ 8 เลขที่ดีที่สุด
    
    def _generate_mixed_numbers(self, target_date: datetime.date, 
                              date_numbers: List[Dict], 
                              news_numbers: List[Dict]) -> List[Dict]:
        """สร้างเลขผสมจากการรวมกัน"""
        
        mixed = []
        
        # ใช้วันที่เป็น seed สำหรับความสอดคล้อง
        date_hash = int(hashlib.md5(target_date.strftime('%Y%m%d').encode()).hexdigest()[:8], 16)
        
        # ผสมเลขจากวันที่กับข่าว
        if date_numbers and news_numbers:
            date_num = int(date_numbers[0]['number'])
            news_num = int(news_numbers[0]['number'])
            
            # ผลรวม
            sum_result = (date_num + news_num) % 100
            mixed.append({
                'number': f'{sum_result:02d}',
                'source': 'mixed_sum',
                'confidence': 70,
                'reason': f'รวม {date_num:02d}+{news_num:02d}'
            })
            
            # ผลต่าง
            diff_result = abs(date_num - news_num)
            mixed.append({
                'number': f'{diff_result:02d}',
                'source': 'mixed_diff', 
                'confidence': 65,
                'reason': f'ต่าง |{date_num:02d}-{news_num:02d}|'
            })
        
        # เลขจาก hash วันที่
        hash_numbers = []
        for i in range(0, 6, 2):
            hash_slice = (date_hash >> i) % 100
            if 10 <= hash_slice <= 99:
                hash_numbers.append(hash_slice)
        
        for hash_num in hash_numbers[:2]:
            mixed.append({
                'number': f'{hash_num:02d}',
                'source': 'hash',
                'confidence': 60,
                'reason': 'อัลกอริทึมพิเศษ'
            })
        
        return mixed
    
    def _combine_and_select_numbers(self, date_numbers: List[Dict], 
                                  news_numbers: List[Dict],
                                  mixed_numbers: List[Dict],
                                  target_date: datetime.date) -> List[Dict]:
        """รวมและคัดเลือกเลขที่ดีที่สุด"""
        
        all_numbers = date_numbers + news_numbers + mixed_numbers
        
        # ลบซ้ำโดยดูที่เลข แต่รักษาข้อมูลที่ดีที่สุด
        unique_numbers = {}
        for num_info in all_numbers:
            number = num_info['number']
            if number not in unique_numbers or num_info['confidence'] > unique_numbers[number]['confidence']:
                unique_numbers[number] = num_info
        
        # แปลงกลับเป็น list และเรียงตามความเชื่อมั่น
        final_numbers = list(unique_numbers.values())
        final_numbers.sort(key=lambda x: x['confidence'], reverse=True)
        
        # คัดเลือกเลข 6-8 ตัวที่ดีที่สุด
        selected = final_numbers[:8]
        
        # ให้แน่ใจว่ามีเลขจากทุกส่วน
        sources_count = Counter(num['source'] for num in selected)
        
        # ถ้าขาดเลขจากวันที่ ให้เพิ่ม
        if 'day' not in [num['source'] for num in selected] and date_numbers:
            selected.append(date_numbers[0])
        
        # ถ้าขาดเลขจากข่าว ให้เพิ่ม  
        if 'news' not in [num['source'] for num in selected] and news_numbers:
            selected.append(news_numbers[0])
        
        return selected[:8]  # จำกัดไว้ที่ 8 เลข
    
    def _generate_insights(self, lucky_numbers: List[Dict], target_date: datetime.date) -> Dict:
        """สร้าง insights เกี่ยวกับเลขที่ได้"""
        
        insights = {
            'total_numbers': len(lucky_numbers),
            'confidence_range': {
                'highest': max(num['confidence'] for num in lucky_numbers) if lucky_numbers else 0,
                'lowest': min(num['confidence'] for num in lucky_numbers) if lucky_numbers else 0,
                'average': sum(num['confidence'] for num in lucky_numbers) / len(lucky_numbers) if lucky_numbers else 0
            },
            'source_breakdown': {},
            'special_patterns': [],
            'thai_message': self._get_thai_fortune_message(target_date)
        }
        
        # แยกตามแหล่งที่มา
        for num_info in lucky_numbers:
            source = num_info['source']
            if source not in insights['source_breakdown']:
                insights['source_breakdown'][source] = 0
            insights['source_breakdown'][source] += 1
        
        # หารูปแบบพิเศษ
        numbers_only = [int(num['number']) for num in lucky_numbers]
        
        # เลขคู่/คี่
        even_count = sum(1 for n in numbers_only if n % 2 == 0)
        if even_count > len(numbers_only) / 2:
            insights['special_patterns'].append('มีเลขคู่เด่น')
        
        # เลขซ้ำ
        digit_freq = Counter()
        for num in numbers_only:
            digit_freq.update(str(num).zfill(2))
        
        most_common = digit_freq.most_common(1)
        if most_common and most_common[0][1] > 2:
            insights['special_patterns'].append(f'หลัก {most_common[0][0]} ปรากฏบ่อย')
        
        return insights
    
    def _get_thai_fortune_message(self, target_date: datetime.date) -> str:
        """สร้างข้อความดวงโชคแบบไทยๆ"""
        
        weekday = target_date.weekday()
        day = target_date.day
        
        messages = [
            "วันนี้ดวงเลขเด่น เสี่ยงโชคแล้วจะได้ดี",
            "เลขจากดวงดาว ส่องทางให้โชคลาภ", 
            "ข่าวดี เลขดี มาพร้อมกันในวันนี้",
            "ตัวเลขมงคล จากธรรมชาติและสถานการณ์",
            "เลขเด่นวันนี้ มาจากพลังแห่งข่าวสารและวันเวลา"
        ]
        
        # เลือกข้อความตามวัน
        message_index = (weekday + day) % len(messages)
        return messages[message_index]


# Helper function สำหรับ view
def get_instant_lucky_numbers(significant_date: Optional[str] = None, selected_news_ids: Optional[List[int]] = None) -> Dict:
    """
    Function หลักสำหรับเรียกใช้จาก view
    """
    generator = InstantLuckyNumberGenerator()
    return generator.generate_lucky_numbers(significant_date, selected_news_ids)
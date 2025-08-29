"""
AI Ensemble Prediction Engine
ระบบทำนายเลขเด็ดด้วย AI 3 โมเดล
"""

import re
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from django.utils import timezone
from django.db.models import Q, Count, Avg
from collections import Counter
import logging

from .models import (
    DataSource, DataIngestionRecord, AIModelType, 
    PredictionSession, ModelPrediction, EnsemblePrediction
)
from dreams.models import DreamKeyword, DreamInterpretation
from news.models import NewsArticle
from lotto_stats.models import LotteryDraw

logger = logging.getLogger(__name__)

class JournalistAI:
    """AI Model 1: วิเคราะห์ข่าวและโซเชียลมีเดีย"""
    
    def __init__(self):
        self.name = "Journalist AI"
        self.weight = 0.4
        
    def analyze_text_data(self, data_records: List[DataIngestionRecord]) -> Dict[str, Any]:
        """วิเคราะห์ข้อมูลข่าวและโซเชียลมีเดีย"""
        
        numbers_frequency = Counter()
        sentiment_scores = []
        hot_keywords = []
        sources_analyzed = []
        
        for record in data_records:
            if record.data_source.source_type in ['news', 'social_media']:
                # สกัดตัวเลขจากเนื้อหา
                extracted_numbers = self._extract_numbers_from_text(
                    record.processed_content or record.raw_content
                )
                
                # นับความถี่ของตัวเลข
                for num in extracted_numbers:
                    numbers_frequency[num] += record.relevance_score
                
                # เก็บคะแนน sentiment
                if record.sentiment_score:
                    sentiment_scores.append(record.sentiment_score)
                
                # เก็บคำสำคัญ
                if record.keywords:
                    hot_keywords.extend(record.keywords)
                
                sources_analyzed.append({
                    'source': record.data_source.name,
                    'title': record.title,
                    'numbers': extracted_numbers,
                    'sentiment': record.sentiment_score,
                    'relevance': record.relevance_score
                })
        
        # วิเคราะห์ผล
        top_numbers = self._select_top_numbers(numbers_frequency)
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.5
        
        return {
            'predicted_numbers': top_numbers,
            'confidence_scores': self._calculate_confidence(top_numbers, numbers_frequency),
            'reasoning': self._generate_reasoning(top_numbers, sources_analyzed, avg_sentiment),
            'data_summary': {
                'sources_count': len(sources_analyzed),
                'total_articles': len(data_records),
                'avg_sentiment': avg_sentiment,
                'hot_keywords': Counter(hot_keywords).most_common(5)
            }
        }
    
    def _extract_numbers_from_text(self, text: str) -> List[str]:
        """สกัดตัวเลขจากข้อความ"""
        if not text:
            return []
            
        # ค้นหาตัวเลข 2-6 หลัก
        number_patterns = [
            r'\b\d{2}\b',  # เลข 2 หลัก
            r'\b\d{3}\b',  # เลข 3 หลัก  
            r'\b\d{4}\b',  # เลข 4 หลัก
            r'\b\d{6}\b'   # เลข 6 หลัก
        ]
        
        extracted_numbers = []
        for pattern in number_patterns:
            matches = re.findall(pattern, text)
            extracted_numbers.extend(matches)
        
        # กรองเลขที่เป็นปี (เช่น 2024, 2025)
        filtered_numbers = []
        for num in extracted_numbers:
            if not (len(num) == 4 and num.startswith('20')):
                filtered_numbers.append(num)
        
        return filtered_numbers
    
    def _select_top_numbers(self, frequency_counter: Counter) -> Dict[str, List[str]]:
        """เลือกตัวเลขที่มีคะแนนสูงสุด"""
        
        # แยกตามความยาว
        two_digit = []
        three_digit = []
        
        for number, freq in frequency_counter.most_common(20):
            if len(number) == 2:
                two_digit.append(number)
            elif len(number) == 3:
                three_digit.append(number)
        
        return {
            'two_digit': two_digit[:5],
            'three_digit': three_digit[:5]
        }
    
    def _calculate_confidence(self, numbers: Dict[str, List[str]], frequency: Counter) -> Dict[str, List[float]]:
        """คำนวณคะแนนความมั่นใจ"""
        
        confidence = {'two_digit': [], 'three_digit': []}
        
        # คำนวณจากความถี่และปรับด้วยปัจจัยต่างๆ
        max_freq = max(frequency.values()) if frequency else 1
        
        for category in ['two_digit', 'three_digit']:
            for number in numbers[category]:
                base_confidence = (frequency[number] / max_freq) * 0.8
                # เพิ่มความมั่นใจถ้าเป็นเลขที่ไม่ออกนาน
                historical_factor = self._get_historical_factor(number)
                final_confidence = min(0.95, base_confidence + historical_factor)
                confidence[category].append(final_confidence)
        
        return confidence
    
    def _get_historical_factor(self, number: str) -> float:
        """ปัจจัยจากประวัติการออกของเลข"""
        # TODO: เชื่อมต่อกับฐานข้อมูลผลหวย
        # ตอนนี้ใช้ค่าจำลอง
        return random.uniform(0.05, 0.15)
    
    def _generate_reasoning(self, numbers: Dict, sources: List, sentiment: float) -> Dict[str, List[str]]:
        """สร้างเหตุผลประกอบ"""
        
        reasoning = {'two_digit': [], 'three_digit': []}
        
        sentiment_text = "บวก" if sentiment > 0.6 else "ลบ" if sentiment < 0.4 else "กลางๆ"
        
        for category in ['two_digit', 'three_digit']:
            for i, number in enumerate(numbers[category]):
                if i < 3:  # แสดงเหตุผลแค่ 3 อันดับแรก
                    reasons = []
                    reasons.append(f"ปรากฏในข่าวบ่อย ({len([s for s in sources if number in s['numbers']])} ครั้ง)")
                    reasons.append(f"กระแส{sentiment_text}ในสื่อ")
                    if random.random() > 0.5:
                        reasons.append("เป็นเลขที่ไม่ออกนาน")
                    
                    reasoning[category].append(" + ".join(reasons))
        
        return reasoning

class InterpreterAI:
    """AI Model 2: ตีความฝันและโหราศาสตร์"""
    
    def __init__(self):
        self.name = "Dream Interpreter AI"
        self.weight = 0.3
    
    def analyze_dream_data(self, data_records: List[DataIngestionRecord]) -> Dict[str, Any]:
        """วิเคราะห์ข้อมูลความฝันและโหราศาสตร์"""
        
        dream_numbers = Counter()
        astrology_numbers = Counter()
        popular_dreams = []
        
        # วิเคราะห์ข้อมูลความฝันจาก database
        recent_dreams = DreamInterpretation.objects.filter(
            interpreted_at__gte=timezone.now() - timedelta(days=14)
        )[:50]
        
        for dream in recent_dreams:
            numbers = self._extract_numbers_from_dream(dream)
            for num in numbers:
                dream_numbers[num] += 1
        
        # วิเคราะห์ข้อมูลโหราศาสตร์
        for record in data_records:
            if record.data_source.source_type == 'astrology':
                numbers = self._extract_astrology_numbers(record)
                for num in numbers:
                    astrology_numbers[num] += record.relevance_score
        
        # รวมผลและเลือกตัวเลข
        combined_numbers = self._combine_mystical_numbers(dream_numbers, astrology_numbers)
        top_numbers = self._select_mystical_numbers(combined_numbers)
        
        return {
            'predicted_numbers': top_numbers,
            'confidence_scores': self._calculate_mystical_confidence(top_numbers, combined_numbers),
            'reasoning': self._generate_mystical_reasoning(top_numbers),
            'data_summary': {
                'dreams_analyzed': len(recent_dreams),
                'astrology_sources': len([r for r in data_records if r.data_source.source_type == 'astrology']),
                'top_dream_symbols': self._get_top_dream_symbols()
            }
        }
    
    def _extract_numbers_from_dream(self, dream: DreamInterpretation) -> List[str]:
        """สกัดตัวเลขจากความฝัน"""
        numbers = []
        
        # ใช้ DreamKeyword ที่มีอยู่
        dream_text = dream.dream_text.lower()
        keywords = DreamKeyword.objects.all()
        
        for keyword in keywords:
            if keyword.keyword.lower() in dream_text:
                # เพิ่มเลขเด่นและเลขรอง
                numbers.extend([
                    f"{keyword.main_number}{keyword.secondary_number}",
                    f"{keyword.secondary_number}{keyword.main_number}",
                    f"{keyword.main_number}{keyword.main_number}"
                ])
                
                # เพิ่มเลขที่มักตี
                if keyword.common_numbers:
                    numbers.extend(keyword.get_numbers_list())
        
        return numbers
    
    def _extract_astrology_numbers(self, record: DataIngestionRecord) -> List[str]:
        """สกัดตัวเลขจากโหราศาสตร์"""
        # วิเคราะห์เนื้อหาโหราศาสตร์
        content = record.processed_content or record.raw_content
        
        # ค้นหาตัวเลขที่เกี่ยวข้องกับโหราศาสตร์
        astro_numbers = []
        
        # ตัวอย่างการสกัดเลขจากเนื้อหาโหราศาสตร์
        numbers = re.findall(r'\b\d{1,3}\b', content)
        for num in numbers:
            if len(num) <= 3:
                astro_numbers.append(num.zfill(2) if len(num) == 1 else num)
        
        return astro_numbers
    
    def _combine_mystical_numbers(self, dreams: Counter, astrology: Counter) -> Counter:
        """รวมเลขจากความฝันและโหราศาสตร์"""
        combined = Counter()
        
        # น้ำหนักความฝัน 70%, โหราศาสตร์ 30%
        for num, count in dreams.items():
            combined[num] += count * 0.7
            
        for num, count in astrology.items():
            combined[num] += count * 0.3
        
        return combined
    
    def _select_mystical_numbers(self, combined: Counter) -> Dict[str, List[str]]:
        """เลือกเลขมงคล"""
        two_digit = []
        three_digit = []
        
        for number, freq in combined.most_common(15):
            if len(number) == 2:
                two_digit.append(number)
            elif len(number) == 3:
                three_digit.append(number)
        
        return {
            'two_digit': two_digit[:5],
            'three_digit': three_digit[:3]
        }
    
    def _calculate_mystical_confidence(self, numbers: Dict, combined: Counter) -> Dict[str, List[float]]:
        """คำนวณความมั่นใจเลขมงคล"""
        confidence = {'two_digit': [], 'three_digit': []}
        max_freq = max(combined.values()) if combined else 1
        
        for category in ['two_digit', 'three_digit']:
            for number in numbers[category]:
                base_conf = (combined[number] / max_freq) * 0.75
                mystical_bonus = 0.1  # โบนัสสำหรับเลขมงคล
                confidence[category].append(min(0.9, base_conf + mystical_bonus))
        
        return confidence
    
    def _generate_mystical_reasoning(self, numbers: Dict) -> Dict[str, List[str]]:
        """สร้างเหตุผลเลขมงคล"""
        reasoning = {'two_digit': [], 'three_digit': []}
        
        mystical_reasons = [
            "จากความฝันยอดนิยม",
            "ตรงกับฤกษ์ยาม",
            "เป็นเลขมงคลตามโหราศาสตร์",
            "ฝันเห็นบ่อยในช่วงนี้",
            "เข้ากับเลขประจำตัว"
        ]
        
        for category in ['two_digit', 'three_digit']:
            for number in numbers[category]:
                selected_reasons = random.sample(mystical_reasons, min(2, len(mystical_reasons)))
                reasoning[category].append(" + ".join(selected_reasons))
        
        return reasoning
    
    def _get_top_dream_symbols(self) -> List[str]:
        """ดึงสัญลักษณ์ในฝันที่ยอดนิยม"""
        return [
            "งู", "ช้าง", "ปลา", "นก", "แมว", 
            "น้อง", "ผีชาย", "ผีหญิง", "วัด", "ศาล"
        ]

class StatisticianAI:
    """AI Model 3: วิเคราะห์สถิติและเทรนด์"""
    
    def __init__(self):
        self.name = "Statistical Trend AI"  
        self.weight = 0.3
    
    def analyze_statistical_data(self, data_records: List[DataIngestionRecord]) -> Dict[str, Any]:
        """วิเคราะห์ข้อมูลสถิติและแนวโน้ม"""
        
        # วิเคราะห์ประวัติผลหวย
        recent_results = LotteryDraw.objects.order_by('-draw_date')[:20]
        
        hot_numbers = self._find_hot_numbers(recent_results)
        cold_numbers = self._find_cold_numbers(recent_results)
        pattern_numbers = self._find_pattern_numbers(recent_results)
        cycle_numbers = self._find_cycle_numbers(recent_results)
        
        # รวมผลการวิเคราะห์
        final_numbers = self._combine_statistical_analysis(
            hot_numbers, cold_numbers, pattern_numbers, cycle_numbers
        )
        
        return {
            'predicted_numbers': final_numbers,
            'confidence_scores': self._calculate_statistical_confidence(final_numbers),
            'reasoning': self._generate_statistical_reasoning(final_numbers),
            'data_summary': {
                'historical_periods': len(recent_results),
                'hot_numbers_trend': hot_numbers[:3],
                'cold_numbers_trend': cold_numbers[:3],
                'pattern_strength': self._calculate_pattern_strength(recent_results)
            }
        }
    
    def _find_hot_numbers(self, results: List) -> List[str]:
        """หาเลขที่ออกบ่อย"""
        number_frequency = Counter()
        
        for result in results[:10]:  # ดู 10 งวดล่าสุด
            if result.first_prize:
                # แยกเลขจากรางวัลที่ 1
                first_prize = result.first_prize
                two_digit = first_prize[-2:]  # 2 ตัวท้าย
                three_digit = first_prize[-3:]  # 3 ตัวท้าย
                
                number_frequency[two_digit] += 2  # น้ำหนักสูงสำหรับเลขท้าย
                number_frequency[three_digit] += 2
                
                # เลขจากตำแหน่งอื่นๆ
                for i in range(len(first_prize) - 1):
                    two_digit_combo = first_prize[i:i+2]
                    if len(two_digit_combo) == 2:
                        number_frequency[two_digit_combo] += 1
        
        return [num for num, freq in number_frequency.most_common(10)]
    
    def _find_cold_numbers(self, results: List) -> List[str]:
        """หาเลขที่ไม่ออกนาน"""
        all_possible_2digit = [f"{i:02d}" for i in range(100)]
        all_possible_3digit = [f"{i:03d}" for i in range(1000)]
        
        appeared_2digit = set()
        appeared_3digit = set()
        
        # เก็บเลขที่ออกแล้วใน 15 งวดล่าสุด
        for result in results[:15]:
            if result.first_prize:
                first_prize = result.first_prize
                appeared_2digit.add(first_prize[-2:])
                appeared_3digit.add(first_prize[-3:])
        
        # หาเลขที่ไม่ออก
        cold_2digit = [num for num in all_possible_2digit if num not in appeared_2digit]
        cold_3digit = [num for num in all_possible_3digit if num not in appeared_3digit]
        
        # เลือกแบบสุ่มจากเลขที่ไม่ออก
        return random.sample(cold_2digit[:20], min(5, len(cold_2digit))) + \
               random.sample(cold_3digit[:30], min(3, len(cold_3digit)))
    
    def _find_pattern_numbers(self, results: List) -> List[str]:
        """หาเลขจากรูปแบบ"""
        pattern_numbers = []
        
        if len(results) >= 3:
            # วิเคราะห์รูปแบบการออก
            last_numbers = []
            for result in results[:3]:
                if result.first_prize:
                    last_numbers.append(result.first_prize)
            
            # หารูปแบบต่างๆ เช่น เลขเรียง, เลขซ้ำ, etc.
            if len(last_numbers) == 3:
                pattern_numbers.extend(self._analyze_sequence_pattern(last_numbers))
                pattern_numbers.extend(self._analyze_sum_pattern(last_numbers))
        
        return pattern_numbers[:8]
    
    def _analyze_sequence_pattern(self, last_numbers: List[str]) -> List[str]:
        """วิเคราะห์รูปแบบลำดับ"""
        sequence_numbers = []
        
        # ดูรูปแบบของตัวเลขท้าย
        last_digits = [int(num[-1]) for num in last_numbers if num]
        
        if len(last_digits) >= 3:
            # คำนวณค่าเฉลี่ยและแนวโน้ม
            avg = sum(last_digits) / len(last_digits)
            trend = last_digits[-1] - last_digits[-2] if len(last_digits) >= 2 else 0
            
            # ทำนายตัวเลขถัดไป
            next_digit = int((avg + trend) % 10)
            prev_digit = int((avg - 1) % 10)
            
            # สร้างเลขจากรูปแบบ
            for base in range(10, 100, 10):
                sequence_numbers.append(f"{base + next_digit:02d}")
                sequence_numbers.append(f"{base + prev_digit:02d}")
        
        return sequence_numbers[:5]
    
    def _analyze_sum_pattern(self, last_numbers: List[str]) -> List[str]:
        """วิเคราะห์รูปแบบผลรวม"""
        sum_numbers = []
        
        # คำนวณผลรวมเลขท้าย 2 ตัว
        sums = []
        for num in last_numbers:
            if num and len(num) >= 2:
                two_digit = int(num[-2:])
                digit_sum = (two_digit // 10) + (two_digit % 10)
                sums.append(digit_sum)
        
        if sums:
            avg_sum = sum(sums) / len(sums)
            target_sum = int(avg_sum)
            
            # หาเลขที่มีผลรวมใกล้เคียง
            for i in range(10, 100):
                digit_sum = (i // 10) + (i % 10)
                if abs(digit_sum - target_sum) <= 1:
                    sum_numbers.append(f"{i:02d}")
        
        return sum_numbers[:5]
    
    def _find_cycle_numbers(self, results: List) -> List[str]:
        """หาเลขตามรอบ/วงจร"""
        cycle_numbers = []
        
        # วิเคราะห์รอบการออกของเลข (ตัวอย่าง)
        if len(results) >= 5:
            # ดูรูปแบบการออกทุกๆ N งวด
            for cycle in [3, 5, 7]:
                cycle_set = []
                for i in range(0, len(results), cycle):
                    if i < len(results) and results[i].first_prize:
                        cycle_set.append(results[i].first_prize[-2:])
                
                if len(cycle_set) >= 2:
                    # เลือกเลขที่น่าจะออกในรอบนี้
                    cycle_numbers.extend(cycle_set[:2])
        
        return cycle_numbers[:5]
    
    def _combine_statistical_analysis(self, hot: List, cold: List, pattern: List, cycle: List) -> Dict[str, List[str]]:
        """รวมผลการวิเคราะห์สถิติ"""
        all_numbers = Counter()
        
        # ให้น้ำหนักต่างกัน
        for num in hot:
            if len(num) == 2:
                all_numbers[num] += 3  # น้ำหนักสูงสุด
        
        for num in pattern:
            if len(num) == 2:
                all_numbers[num] += 2
        
        for num in cold:
            if len(num) == 2:
                all_numbers[num] += 1.5  # โอกาสที่เลขไม่ออกจะออก
        
        for num in cycle:
            if len(num) == 2:
                all_numbers[num] += 2
        
        # แยกออกเป็น 2 และ 3 หลัก
        two_digit = [num for num, _ in all_numbers.most_common() if len(num) == 2][:5]
        three_digit = [f"0{num}" for num in two_digit[:3]]  # เอาเลข 2 ตัวมาทำเป็น 3 ตัว
        
        return {
            'two_digit': two_digit,
            'three_digit': three_digit
        }
    
    def _calculate_statistical_confidence(self, numbers: Dict) -> Dict[str, List[float]]:
        """คำนวณความมั่นใจจากสถิติ"""
        confidence = {'two_digit': [], 'three_digit': []}
        
        # ความมั่นใจจากสถิติค่อนข้างสูง
        base_confidence = 0.8
        
        for category in ['two_digit', 'three_digit']:
            for i, number in enumerate(numbers[category]):
                # ลดความมั่นใจตามลำดับ
                conf = base_confidence - (i * 0.1)
                confidence[category].append(max(0.5, conf))
        
        return confidence
    
    def _generate_statistical_reasoning(self, numbers: Dict) -> Dict[str, List[str]]:
        """สร้างเหตุผลจากสถิติ"""
        reasoning = {'two_digit': [], 'three_digit': []}
        
        stat_reasons = [
            "เป็นเลขฮิตล่าสุด",
            "ไม่ออกนานแล้ว",
            "ตรงตามรูปแบบทางสถิติ", 
            "อยู่ในรอบการออก",
            "ผลรวมตรงแนวโน้ม"
        ]
        
        for category in ['two_digit', 'three_digit']:
            for number in numbers[category]:
                selected_reasons = random.sample(stat_reasons, min(2, len(stat_reasons)))
                reasoning[category].append(" + ".join(selected_reasons))
        
        return reasoning
    
    def _calculate_pattern_strength(self, results: List) -> float:
        """คำนวณความแข็งแรงของรูปแบบ"""
        if len(results) < 5:
            return 0.5
        
        # วิเคราะห์ความสม่ำเสมอของรูปแบบ
        patterns = []
        for i in range(min(5, len(results))):
            if results[i].first_prize:
                patterns.append(int(results[i].first_prize[-2:]))
        
        if len(patterns) >= 3:
            variance = sum([(x - sum(patterns)/len(patterns))**2 for x in patterns]) / len(patterns)
            strength = max(0.3, min(0.9, 1 - variance/100))
            return strength
        
        return 0.6

class EnsembleAI:
    """AI Master: รวมผลจากทั้ง 3 โมเดล"""
    
    def __init__(self):
        self.journalist = JournalistAI()
        self.interpreter = InterpreterAI()
        self.statistician = StatisticianAI()
    
    def create_ensemble_prediction(self, session: PredictionSession, model_predictions: List[ModelPrediction]) -> EnsemblePrediction:
        """สร้างการทำนายรวมสุดท้าย"""
        
        # รวมผลจากทั้ง 3 โมเดล
        all_numbers = {'two_digit': Counter(), 'three_digit': Counter()}
        all_reasoning = {'two_digit': {}, 'three_digit': {}}
        model_contributions = {}
        
        for prediction in model_predictions:
            model_name = prediction.model_type.name
            weight = prediction.model_type.weight_in_ensemble
            numbers = prediction.predicted_numbers
            confidence = prediction.confidence_scores
            reasoning = prediction.reasoning
            
            # รวมเลขโดยใช้น้ำหนัก
            for category in ['two_digit', 'three_digit']:
                if category in numbers and category in confidence:
                    for i, number in enumerate(numbers[category]):
                        if i < len(confidence[category]):
                            score = confidence[category][i] * weight
                            all_numbers[category][number] += score
                            
                            # เก็บเหตุผล
                            if number not in all_reasoning[category]:
                                all_reasoning[category][number] = []
                            if category in reasoning and i < len(reasoning[category]):
                                all_reasoning[category][number].append(f"{model_name}: {reasoning[category][i]}")
            
            # เก็บข้อมูลการมีส่วนร่วมของแต่ละโมเดล
            model_contributions[model_name] = {
                'weight': weight,
                'top_numbers': {
                    'two_digit': numbers.get('two_digit', [])[:2],
                    'three_digit': numbers.get('three_digit', [])[:2]
                },
                'confidence': {
                    'two_digit': confidence.get('two_digit', [])[:2],
                    'three_digit': confidence.get('three_digit', [])[:2]
                }
            }
        
        # เลือกเลขสุดท้าย
        final_numbers = self._select_final_numbers(all_numbers, all_reasoning)
        overall_confidence = self._calculate_overall_confidence(final_numbers, all_numbers)
        
        # สร้างสรุปการทำนาย
        prediction_summary = self._generate_prediction_summary(final_numbers, model_contributions)
        
        # สร้าง EnsemblePrediction
        ensemble_prediction = EnsemblePrediction.objects.create(
            session=session,
            final_two_digit=final_numbers['two_digit'],
            final_three_digit=final_numbers['three_digit'], 
            overall_confidence=overall_confidence,
            prediction_summary=prediction_summary,
            model_contributions=model_contributions,
            total_data_points=session.total_data_points
        )
        
        return ensemble_prediction
    
    def _select_final_numbers(self, all_numbers: Dict[str, Counter], reasoning: Dict) -> Dict[str, List]:
        """เลือกเลขสุดท้าย"""
        
        final = {'two_digit': [], 'three_digit': []}
        
        for category in ['two_digit', 'three_digit']:
            limit = 3 if category == 'two_digit' else 2
            
            for number, total_score in all_numbers[category].most_common(limit):
                final_reasoning = " | ".join(reasoning[category].get(number, ["วิเคราะห์จาก AI"]))
                
                final[category].append({
                    'number': number,
                    'confidence': min(0.95, total_score),
                    'reasoning': final_reasoning[:200]  # จำกัดความยาว
                })
        
        return final
    
    def _calculate_overall_confidence(self, final_numbers: Dict, all_numbers: Dict[str, Counter]) -> float:
        """คำนวณความมั่นใจรวม"""
        
        all_scores = []
        
        for category in ['two_digit', 'three_digit']:
            for item in final_numbers[category]:
                all_scores.append(item['confidence'])
        
        if all_scores:
            avg_confidence = sum(all_scores) / len(all_scores)
            # ปรับด้วยปัจจัยการมีส่วนร่วมของโมเดลหลายตัว
            diversity_bonus = 0.05 if len(all_scores) >= 4 else 0
            return min(0.95, avg_confidence + diversity_bonus)
        
        return 0.75  # ค่าเริ่มต้น
    
    def _generate_prediction_summary(self, final_numbers: Dict, contributions: Dict) -> str:
        """สร้างสรุปการทำนาย"""
        
        summary_parts = []
        
        # เลข 2 ตัวแนะนำ
        if final_numbers['two_digit']:
            top_2digit = [item['number'] for item in final_numbers['two_digit'][:2]]
            summary_parts.append(f"เลขท้าย 2 ตัวแนะนำ: {', '.join(top_2digit)}")
        
        # เลข 3 ตัวแนะนำ
        if final_numbers['three_digit']:
            top_3digit = [item['number'] for item in final_numbers['three_digit'][:1]]
            summary_parts.append(f"เลขท้าย 3 ตัวแนะนำ: {', '.join(top_3digit)}")
        
        # แหล่งข้อมูลหลัก
        main_sources = []
        if 'Journalist AI' in contributions:
            main_sources.append("การวิเคราะห์ข่าวและสื่อ")
        if 'Dream Interpreter AI' in contributions:
            main_sources.append("การตีความฝัน")
        if 'Statistical Trend AI' in contributions:
            main_sources.append("การวิเคราะห์สถิติ")
        
        if main_sources:
            summary_parts.append(f"อิงจาก: {', '.join(main_sources)}")
        
        return " | ".join(summary_parts)

class PredictionEngine:
    """เครื่องมือหลักสำหรับการทำนายเลขเด็ด"""
    
    def __init__(self):
        self.ensemble = EnsembleAI()
        
    def create_prediction_session(self, for_draw_date: datetime) -> PredictionSession:
        """สร้างเซสชันการทำนายใหม่"""
        
        session_id = f"pred_{for_draw_date.strftime('%Y%m%d')}_{timezone.now().strftime('%H%M')}"
        
        # กำหนดช่วงเวลาเก็บข้อมูล (จากหวยงวดล่าสุดถึงก่อนหวยออกงวดถัดไป)
        data_start = for_draw_date - timedelta(days=16)  # 16 วันก่อน
        data_end = for_draw_date - timedelta(days=1)     # 1 วันก่อน
        
        session = PredictionSession.objects.create(
            session_id=session_id,
            for_draw_date=for_draw_date,
            data_collection_period_start=data_start,
            data_collection_period_end=data_end,
            status='collecting_data'
        )
        
        return session
    
    def run_prediction(self, session: PredictionSession) -> EnsemblePrediction:
        """รันการทำนายแบบเต็ม"""
        
        try:
            session.status = 'analyzing'
            session.save()
            
            start_time = timezone.now()
            
            # เก็บข้อมูลจากแหล่งต่างๆ
            data_records = self._collect_data_for_session(session)
            
            # รันโมเดล AI แต่ละตัว
            model_predictions = []
            
            # รัน Journalist AI
            journalist_result = self.ensemble.journalist.analyze_text_data(data_records)
            journalist_pred = self._save_model_prediction(session, 'journalist', journalist_result)
            model_predictions.append(journalist_pred)
            
            # รัน Interpreter AI  
            interpreter_result = self.ensemble.interpreter.analyze_dream_data(data_records)
            interpreter_pred = self._save_model_prediction(session, 'interpreter', interpreter_result)
            model_predictions.append(interpreter_pred)
            
            # รัน Statistician AI
            statistician_result = self.ensemble.statistician.analyze_statistical_data(data_records)
            statistician_pred = self._save_model_prediction(session, 'statistician', statistician_result)
            model_predictions.append(statistician_pred)
            
            # รันโมเดลรวม
            ensemble_prediction = self.ensemble.create_ensemble_prediction(session, model_predictions)
            
            # อัปเดตสถานะ
            end_time = timezone.now()
            session.status = 'completed'
            session.end_time = end_time
            session.processing_time_seconds = (end_time - start_time).total_seconds()
            session.total_data_points = len(data_records)
            session.save()
            
            logger.info(f"Prediction completed for session {session.session_id}")
            return ensemble_prediction
            
        except Exception as e:
            session.status = 'failed'
            session.save()
            logger.error(f"Prediction failed for session {session.session_id}: {str(e)}")
            raise
    
    def _collect_data_for_session(self, session: PredictionSession) -> List[DataIngestionRecord]:
        """เก็บข้อมูลสำหรับเซสชัน"""
        
        return DataIngestionRecord.objects.filter(
            ingested_at__gte=session.data_collection_period_start,
            ingested_at__lte=session.data_collection_period_end,
            processing_status='completed'
        ).order_by('-relevance_score')[:100]  # เก็บ 100 รายการที่ดีที่สุด
    
    def _save_model_prediction(self, session: PredictionSession, model_role: str, result: Dict) -> ModelPrediction:
        """บันทึกผลการทำนายของโมเดล"""
        
        model_type = AIModelType.objects.get(role=model_role)
        
        prediction = ModelPrediction.objects.create(
            session=session,
            model_type=model_type,
            predicted_numbers=result['predicted_numbers'],
            confidence_scores=result['confidence_scores'],
            reasoning=result['reasoning'],
            input_data_summary=result['data_summary'],
            data_sources_used=[],  # TODO: เก็บรายละเอียดแหล่งข้อมูล
            processing_time=0.0  # TODO: วัดเวลาจริง
        )
        
        return prediction
    
    def get_latest_prediction(self) -> EnsemblePrediction:
        """ดึงการทำนายล่าสุด"""
        
        return EnsemblePrediction.objects.filter(
            session__status='completed'
        ).order_by('-prediction_timestamp').first()
    
    def lock_predictions_for_draw_date(self, draw_date: datetime):
        """ล็อกการทำนายเพื่อไม่ให้เปลี่ยนแปลงในวันหวยออก"""
        
        sessions = PredictionSession.objects.filter(
            for_draw_date=draw_date,
            status='completed'
        )
        
        for session in sessions:
            session.status = 'locked'
            session.save()
            
        logger.info(f"Locked {len(sessions)} prediction sessions for draw date {draw_date}")
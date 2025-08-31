import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
from collections import Counter
from lotto_stats.models import LotteryDraw
from news.models import NewsArticle
from news.news_analyzer import NewsAnalyzer

class LotteryAIEngine:
    """AI Engine สำหรับทำนายเลขเด็ด"""
    
    def __init__(self, model_type='pattern_analysis'):
        self.model_type = model_type
        self.factors = {
            'date_pattern': 1.5,      # รูปแบบวันที่
            'historical_hot': 2.0,    # เลขฮอตในอดีต
            'historical_cold': 1.2,   # เลขเย็น
            'seasonal': 1.0,          # ฤดูกาล
            'lunar_phase': 0.8,       # ข้างขึ้นข้างแรม
            'special_events': 1.3,    # วันพิเศษ
            'news_sentiment': 1.1,    # อารมณ์ข่าว
            'user_lucky': 0.9,        # เลขนำโชคส่วนตัว
        }
    
    def predict(self, target_date=None, user_data=None):
        """ทำนายเลขเด็ด"""
        if target_date is None:
            target_date = datetime.now().date() + timedelta(days=1)
        
        # เตรียมข้อมูล
        features = self._prepare_features(target_date, user_data)
        
        # ทำนายด้วยวิธีต่างๆ
        if self.model_type == 'pattern_analysis':
            predictions = self._pattern_analysis_predict(features)
        elif self.model_type == 'statistical':
            predictions = self._statistical_predict(features)
        elif self.model_type == 'neural_network':
            predictions = self._neural_network_predict(features)
        else:
            predictions = self._random_forest_predict(features)
        
        # คำนวณ confidence
        confidence = self._calculate_confidence(predictions, features)
        
        # จัดรูปแบบผลลัพธ์
        result = {
            'two_digit': predictions['two_digit'][:10],
            'three_digit': predictions['three_digit'][:5],
            'confidence': confidence,
            'factors': features,
            'reasoning': self._generate_reasoning(features, predictions)
        }
        
        return result
    
    def _prepare_features(self, target_date, user_data):
        """เตรียม features สำหรับการทำนาย"""
        features = {}
        
        # Date features
        features['day_of_month'] = target_date.day
        features['month'] = target_date.month
        features['day_of_week'] = target_date.weekday()
        features['is_buddhist_day'] = 1 if target_date.weekday() in [2, 5] else 0
        features['is_month_end'] = 1 if target_date.day >= 28 else 0
        
        # Historical patterns
        historical_data = self._get_historical_patterns()
        features.update(historical_data)
        
        # Lunar calendar (simplified)
        features['lunar_phase'] = self._calculate_lunar_phase(target_date)
        
        # Special events
        features['is_holiday'] = self._is_holiday(target_date)

        # News analysis
        last_draw_date = LotteryDraw.objects.order_by('-draw_date').first().draw_date if LotteryDraw.objects.exists() else target_date - timedelta(days=15)
        recent_news = NewsArticle.objects.filter(published_date__gte=last_draw_date, published_date__lte=target_date)
        
        news_analysis_results = []
        analyzer = NewsAnalyzer()
        for article in recent_news:
            analysis = analyzer.analyze_article(article)
            if analysis['numbers']:
                news_analysis_results.append({
                    'title': article.title,
                    'numbers': analysis['numbers'],
                    'keywords': analysis['keywords'],
                    'confidence': analysis['confidence']
                })
        
        features['news_analysis'] = news_analysis_results
        
        # User personalization
        if user_data:
            features['user_birth_date'] = user_data.get('birth_date')
            features['user_lucky_numbers'] = user_data.get('lucky_numbers', [])
        
        return features
    
    def _pattern_analysis_predict(self, features):
        """วิเคราะห์รูปแบบและทำนาย"""
        predictions = {
            'two_digit': [],
            'three_digit': []
        }
        
        # วิเคราะห์เลขจากวันที่
        date_numbers = self._analyze_date_pattern(features)
        predictions['two_digit'].extend(date_numbers['two_digit'])
        
        # วิเคราะห์เลขฮอต/เย็น
        hot_cold_numbers = self._analyze_hot_cold_pattern(features)
        predictions['two_digit'].extend(hot_cold_numbers['hot'][:5])
        predictions['two_digit'].extend(hot_cold_numbers['cold'][:3])
        
        # วิเคราะห์รูปแบบพิเศษ
        special_patterns = self._analyze_special_patterns(features)
        predictions['two_digit'].extend(special_patterns)

        # วิเคราะห์จากข่าว
        if 'news_analysis' in features:
            for analysis in features['news_analysis']:
                predictions['two_digit'].extend(analysis['numbers'])
        
        # สร้างเลข 3 ตัว
        predictions['three_digit'] = self._generate_three_digits(predictions['two_digit'])
        
        # จัดเรียงตามความน่าจะเป็น
        predictions['two_digit'] = self._rank_numbers(predictions['two_digit'], features)
        
        return predictions
    
    def _statistical_predict(self, features):
        """ทำนายด้วยวิธีทางสถิติ"""
        # ดึงข้อมูลสถิติ
        stats = self._get_statistical_data()
        
        predictions = {
            'two_digit': [],
            'three_digit': []
        }
        
        # คำนวณความน่าจะเป็น
        probabilities = {}
        for num in range(100):
            num_str = str(num).zfill(2)
            prob = self._calculate_probability(num_str, features, stats)
            probabilities[num_str] = prob
        
        # เลือกเลขที่มีความน่าจะเป็นสูง
        sorted_nums = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        predictions['two_digit'] = [num for num, prob in sorted_nums[:15]]
        
        # สร้างเลข 3 ตัว
        predictions['three_digit'] = self._generate_three_digits(predictions['two_digit'])
        
        return predictions
    
    def _neural_network_predict(self, features):
        """ทำนายด้วย Neural Network (Simplified)"""
        # Simulate neural network prediction
        # ในระบบจริงจะใช้ TensorFlow/PyTorch
        
        predictions = {
            'two_digit': [],
            'three_digit': []
        }
        
        # Input layer
        input_vector = self._features_to_vector(features)
        
        # Hidden layers (simplified)
        hidden1 = np.tanh(input_vector * 0.7 + 0.3)
        hidden2 = np.tanh(hidden1 * 0.5 + 0.2)
        
        # Output layer
        output = self._vector_to_predictions(hidden2)
        
        predictions['two_digit'] = output['two_digit']
        predictions['three_digit'] = output['three_digit']
        
        return predictions
    
    def _random_forest_predict(self, features):
        """ทำนายด้วย Random Forest (Simplified)"""
        predictions = {
            'two_digit': [],
            'three_digit': []
        }
        
        # สร้าง trees
        trees = []
        for i in range(10):
            tree_pred = self._single_tree_predict(features, seed=i)
            trees.append(tree_pred)
        
        # รวมผลจากทุก trees
        all_two_digits = []
        for tree in trees:
            all_two_digits.extend(tree['two_digit'])
        
        # นับความถี่
        counter = Counter(all_two_digits)
        predictions['two_digit'] = [num for num, count in counter.most_common(15)]
        
        # สร้างเลข 3 ตัว
        predictions['three_digit'] = self._generate_three_digits(predictions['two_digit'])
        
        return predictions
    
    def _analyze_date_pattern(self, features):
        """วิเคราะห์เลขจากรูปแบบวันที่"""
        numbers = {'two_digit': [], 'three_digit': []}
        
        day = features['day_of_month']
        month = features['month']
        
        # เลขจากวันที่
        numbers['two_digit'].append(str(day).zfill(2))
        numbers['two_digit'].append(str(month).zfill(2))
        
        # เลขกลับ
        numbers['two_digit'].append(str(day).zfill(2)[::-1])
        
        # ผลรวม
        sum_num = (day + month) % 100
        numbers['two_digit'].append(str(sum_num).zfill(2))
        
        # เลขคู่/คี่
        if day % 2 == 0:
            numbers['two_digit'].extend(['00', '22', '44', '66', '88'])
        else:
            numbers['two_digit'].extend(['11', '33', '55', '77', '99'])
        
        return numbers
    
    def _analyze_hot_cold_pattern(self, features):
        """วิเคราะห์เลขฮอต/เย็น"""
        try:
            from lotto_stats.stats_calculator import StatsCalculator
            calculator = StatsCalculator()
            
            hot_numbers = calculator.get_hot_numbers(limit=10, days=90, number_type='2D')
            cold_numbers = calculator.get_cold_numbers(limit=10, number_type='2D')
            
            return {
                'hot': [n['number'] for n in hot_numbers],
                'cold': [n['number'] for n in cold_numbers]
            }
        except:
            # Fallback ถ้าไม่มีข้อมูล
            return {
                'hot': ['23', '45', '67', '89', '12'],
                'cold': ['01', '34', '56', '78', '90']
            }
    
    def _analyze_special_patterns(self, features):
        """วิเคราะห์รูปแบบพิเศษ"""
        special_numbers = []
        
        # วันพระ
        if features.get('is_buddhist_day'):
            special_numbers.extend(['07', '70', '16', '61'])
        
        # สิ้นเดือน
        if features.get('is_month_end'):
            special_numbers.extend(['30', '31', '00', '99'])
        
        # วันหยุด
        if features.get('is_holiday'):
            special_numbers.extend(['25', '52', '88', '99'])
        
        # ข้างขึ้น/ข้างแรม
        lunar = features.get('lunar_phase', 0)
        if lunar <= 15:  # ข้างขึ้น
            special_numbers.extend(['15', '51', '45', '54'])
        else:  # ข้างแรม
            special_numbers.extend(['30', '03', '69', '96'])
        
        return special_numbers
    
    def _generate_three_digits(self, two_digits):
        """สร้างเลข 3 ตัวจากเลข 2 ตัว"""
        three_digits = []
        
        for i, num1 in enumerate(two_digits[:5]):
            # เพิ่มเลขด้านหน้า
            three_digits.append(f"{num1[0]}{num1}")
            
            # เพิ่มเลขด้านหลัง  
            three_digits.append(f"{num1}{num1[1]}")
            
            # ผสมกับเลขอื่น
            if i < len(two_digits) - 1:
                num2 = two_digits[i + 1]
                three_digits.append(f"{num1[0]}{num2}")
        
        # ลบซ้ำและจำกัดจำนวน
        return list(dict.fromkeys(three_digits))[:10]
    
    def _rank_numbers(self, numbers, features):
        """จัดอันดับเลขตามความน่าจะเป็น"""
        scored_numbers = []
        
        for num in numbers:
            score = self._calculate_number_score(num, features)
            scored_numbers.append((num, score))
        
        # เรียงตามคะแนน
        scored_numbers.sort(key=lambda x: x[1], reverse=True)
        
        # คืนเฉพาะเลข
        return [num for num, score in scored_numbers]
    
    def _calculate_number_score(self, number, features):
        """คำนวณคะแนนของเลข"""
        score = 1.0
        
        # วันที่ตรงกับเลข
        if str(features['day_of_month']).zfill(2) == number:
            score *= 1.5
        
        # เลขซ้ำ
        if number[0] == number[1]:
            score *= 1.2
        
        # เลขกลับ
        if number == number[::-1]:
            score *= 1.1
        
        return score
    
    def _calculate_confidence(self, predictions, features):
        """คำนวณความมั่นใจ"""
        base_confidence = 50.0
        
        # เพิ่มจากจำนวน factors
        active_factors = sum(1 for k, v in features.items() if v)
        base_confidence += active_factors * 2
        
        # เพิ่มจากความสอดคล้องของผลทำนาย
        if len(predictions['two_digit']) >= 10:
            base_confidence += 10
        
        # จำกัดไม่เกิน 95%
        return min(base_confidence, 95.0)
    
    def _generate_reasoning(self, features, predictions):
        """สร้างคำอธิบายการทำนาย"""
        reasoning = []
        
        if features.get('is_buddhist_day'):
            reasoning.append("วันนี้เป็นวันพระ มีโอกาสออกเลขคู่หรือเลขมงคล")
        
        if features.get('day_of_month') in predictions['two_digit'][:5]:
            reasoning.append(f"เลขวันที่ {features['day_of_month']} มีโอกาสสูง")
        
        if features.get('is_month_end'):
            reasoning.append("ช่วงสิ้นเดือนมักออกเลขท้าย 0 หรือ 9")
        
        hot_numbers = features.get('hot_numbers', [])
        if hot_numbers:
            reasoning.append(f"เลขฮอตช่วงนี้: {', '.join(hot_numbers[:3])}")

        if features.get('news_analysis'):
            reasoning.append("เลขเด่นจากข่าวดัง:")
            for analysis in features['news_analysis'][:3]: # Show top 3 news
                reasoning.append(f"- ข่าว '{analysis['title'][:30]}...' ให้เลขเด่น {', '.join(analysis['numbers'][:3])}")
        
        return reasoning
    
    def _get_historical_patterns(self):
        """ดึงข้อมูลรูปแบบในอดีต"""
        patterns = {}
        
        try:
            # ดึงข้อมูลจากฐานข้อมูล
            recent_draws = LotteryDraw.objects.all()[:30]
            
            if recent_draws:
                # หาเลขที่ออกบ่อย
                all_numbers = []
                for draw in recent_draws:
                    all_numbers.append(draw.two_digit)
                
                counter = Counter(all_numbers)
                patterns['hot_numbers'] = [num for num, count in counter.most_common(5)]
            else:
                patterns['hot_numbers'] = []
                
        except:
            patterns['hot_numbers'] = []
        
        return patterns
    
    def _calculate_lunar_phase(self, date):
        """คำนวณข้างขึ้นข้างแรม (simplified)"""
        # สูตรคำนวณแบบง่าย
        year = date.year
        month = date.month
        day = date.day
        
        if month < 3:
            year -= 1
            month += 12
        
        a = year // 100
        b = a // 4
        c = 2 - a + b
        e = int(365.25 * (year + 4716))
        f = int(30.6001 * (month + 1))
        jd = c + day + e + f - 1524.5
        
        days_since_new = (jd - 2451549.5) % 29.53059
        
        return int(days_since_new)
    
    def _is_holiday(self, date):
        """ตรวจสอบวันหยุด"""
        # วันหยุดที่สำคัญ
        holidays = [
            (1, 1),   # ปีใหม่
            (4, 13),  # สงกรานต์
            (4, 14),
            (4, 15),
            (5, 1),   # แรงงาน
            (12, 5),  # วันพ่อ
            (12, 10), # รัฐธรรมนูญ
            (12, 31), # สิ้นปี
        ]
        
        return (date.month, date.day) in holidays
    
    def _features_to_vector(self, features):
        """แปลง features เป็น vector"""
        vector = np.zeros(20)
        
        vector[0] = features.get('day_of_month', 0) / 31.0
        vector[1] = features.get('month', 0) / 12.0
        vector[2] = features.get('day_of_week', 0) / 7.0
        vector[3] = features.get('is_buddhist_day', 0)
        vector[4] = features.get('is_month_end', 0)
        vector[5] = features.get('lunar_phase', 0) / 30.0
        vector[6] = features.get('is_holiday', 0)
        
        return vector
    
    def _vector_to_predictions(self, vector):
        """แปลง vector เป็นการทำนาย"""
        predictions = {
            'two_digit': [],
            'three_digit': []
        }
        
        # Generate numbers based on vector values
        for i in range(10):
            num = int((vector[i % len(vector)] * 100) % 100)
            predictions['two_digit'].append(str(num).zfill(2))
        
        predictions['three_digit'] = self._generate_three_digits(predictions['two_digit'])
        
        return predictions
    
    def _single_tree_predict(self, features, seed=0):
        """ทำนายด้วย tree เดียว"""
        random.seed(seed)
        
        predictions = {
            'two_digit': [],
            'three_digit': []
        }
        
        # Random selection based on features
        for _ in range(8):
            num = random.randint(0, 99)
            predictions['two_digit'].append(str(num).zfill(2))
        
        return predictions
    
    def _calculate_probability(self, number, features, stats):
        """คำนวณความน่าจะเป็นของเลข"""
        prob = 0.01  # Base probability
        
        # Increase if matches date
        if number == str(features.get('day_of_month', 0)).zfill(2):
            prob += 0.05
        
        # Check historical frequency
        if number in stats.get('frequent_numbers', []):
            prob += 0.03
        
        # Special patterns
        if number[0] == number[1]:  # เลขซ้ำ
            prob += 0.02
        
        return prob
    
    def _get_statistical_data(self):
        """ดึงข้อมูลสถิติ"""
        return {
            'frequent_numbers': ['23', '45', '67', '89', '12', '34', '56', '78'],
            'rare_numbers': ['01', '10', '20', '30', '40']
        }

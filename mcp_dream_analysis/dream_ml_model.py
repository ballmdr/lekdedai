"""
เครื่องจักรการเรียนรู้สำหรับการวิเคราะห์ความฝันและทำนายเลข
Machine Learning Model for Dream Analysis and Number Prediction
"""
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
import joblib
import os
import re
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import json

class DreamNumberMLModel:
    """ML Model สำหรับทำนายเลขจากความฝัน"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 3),
            stop_words=None,
            lowercase=True
        )
        
        # Multi-output models for different number types
        self.main_secondary_model = MultiOutputRegressor(
            RandomForestRegressor(n_estimators=100, random_state=42)
        )
        self.combination_model = GradientBoostingRegressor(
            n_estimators=100, 
            random_state=42
        )
        
        self.is_trained = False
        self.feature_names = []
        self.model_path = model_path or "dream_ml_model.pkl"
        
        # Thai text preprocessing patterns
        self.thai_patterns = {
            'animals': r'งู|ช้าง|เสือ|หมู|ไก่|ปลา|กบ|นก|แมว|หมา|วัว|ควาย',
            'people': r'พระ|เณร|ผู้หญิง|ผู้ชาย|เด็ก|คนแก่|ทารก|แม่|พ่อ',
            'objects': r'เงิน|ทอง|รถ|บ้าน|วัด|โบสถ์|ไฟ|น้ำ|ต้นไม้|ดอกไม้',
            'emotions': r'กลัว|ดีใจ|เศร้า|โกรธ|ตกใจ|สุข|ทุกข์|ห่วง',
            'actions': r'วิ่ง|เดิน|บิน|ว่าย|กิน|ดื่ม|นอน|ตื่น|ขึ้น|ลง',
            'colors': r'แดง|เขียว|น้ำเงิน|เหลือง|ขาว|ดำ|ม่วง|ส้ม|ชมพู',
            'numbers': r'\d+'
        }
        
        # Weight mappings for different dream elements
        self.element_weights = {
            'animals': 0.3,
            'people': 0.25,
            'objects': 0.2,
            'emotions': 0.1,
            'actions': 0.1,
            'colors': 0.05
        }

    def extract_thai_features(self, text: str) -> Dict[str, float]:
        """สกัดคุณลักษณะจากข้อความไทย"""
        features = {}
        text_lower = text.lower()
        
        for category, pattern in self.thai_patterns.items():
            matches = re.findall(pattern, text_lower)
            features[f'{category}_count'] = len(matches)
            features[f'{category}_weight'] = len(matches) * self.element_weights.get(category, 0.1)
        
        # Text length features
        features['text_length'] = len(text)
        features['word_count'] = len(text.split())
        
        # Special number extractions
        numbers_found = re.findall(r'\d+', text)
        features['explicit_numbers_count'] = len(numbers_found)
        
        return features

    def prepare_training_data(self, dream_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """เตรียมข้อมูลสำหรับการฝึกสอน"""
        texts = []
        main_secondary_targets = []
        combination_targets = []
        
        for data in dream_data:
            text = data['dream_text']
            main_num = int(data.get('main_number', 0))
            secondary_num = int(data.get('secondary_number', 0))
            combinations = data.get('combinations', [])
            
            texts.append(text)
            main_secondary_targets.append([main_num, secondary_num])
            
            # Convert combinations to single target (average or most frequent)
            if combinations:
                combination_target = np.mean([int(c) % 100 for c in combinations if c.isdigit()])
            else:
                combination_target = (main_num * 10 + secondary_num) % 100
                
            combination_targets.append(combination_target)
        
        # Create TF-IDF features
        tfidf_features = self.tfidf_vectorizer.fit_transform(texts).toarray()
        
        # Extract Thai-specific features
        thai_features = []
        for text in texts:
            thai_feat = self.extract_thai_features(text)
            thai_features.append(list(thai_feat.values()))
        
        # Combine features
        thai_features = np.array(thai_features)
        combined_features = np.hstack([tfidf_features, thai_features])
        
        return combined_features, np.array(main_secondary_targets), np.array(combination_targets)

    def train(self, dream_data: List[Dict], test_size: float = 0.2):
        """ฝึกสอนโมเดล ML"""
        print("🤖 เริ่มการฝึกสอนโมเดล ML สำหรับการวิเคราะห์ความฝัน...")
        
        # Prepare data
        X, y_main_sec, y_combinations = self.prepare_training_data(dream_data)
        
        # Split data
        X_train, X_test, y_ms_train, y_ms_test, y_comb_train, y_comb_test = train_test_split(
            X, y_main_sec, y_combinations, test_size=test_size, random_state=42
        )
        
        # Train main/secondary number model
        print("📊 ฝึกสอนโมเดลเลขเด่น/เลขรอง...")
        self.main_secondary_model.fit(X_train, y_ms_train)
        
        # Train combination model
        print("🔢 ฝึกสอนโมเดลเลขผสม...")
        self.combination_model.fit(X_train, y_comb_train)
        
        # Evaluate models
        ms_pred = self.main_secondary_model.predict(X_test)
        comb_pred = self.combination_model.predict(X_test)
        
        ms_mae = mean_absolute_error(y_ms_test, ms_pred)
        comb_mae = mean_absolute_error(y_comb_test, comb_pred)
        
        print(f"✅ เสร็จสิ้นการฝึกสอน!")
        print(f"📈 MAE เลขเด่น/รอง: {ms_mae:.2f}")
        print(f"📈 MAE เลขผสม: {comb_mae:.2f}")
        
        self.is_trained = True
        return {'main_secondary_mae': ms_mae, 'combination_mae': comb_mae}

    def predict(self, dream_text: str, num_predictions: int = 6) -> Dict:
        """ทำนายเลขจากความฝัน"""
        if not self.is_trained:
            raise ValueError("โมเดลยังไม่ได้รับการฝึกสอน กรุณาเรียก train() ก่อน")
        
        # Prepare input
        tfidf_features = self.tfidf_vectorizer.transform([dream_text]).toarray()
        thai_features = np.array([list(self.extract_thai_features(dream_text).values())])
        combined_features = np.hstack([tfidf_features, thai_features])
        
        # Predict main/secondary numbers
        ms_pred = self.main_secondary_model.predict(combined_features)[0]
        main_num = max(0, min(9, round(ms_pred[0])))
        secondary_num = max(0, min(9, round(ms_pred[1])))
        
        # Predict combination numbers
        comb_pred = self.combination_model.predict(combined_features)[0]
        base_combination = max(0, min(99, round(comb_pred)))
        
        # Generate number combinations
        combinations = self._generate_combinations(main_num, secondary_num, base_combination, num_predictions)
        
        # Calculate confidence scores
        confidence = self._calculate_confidence(combined_features, ms_pred, comb_pred)
        
        return {
            'main_number': main_num,
            'secondary_number': secondary_num,
            'combinations': combinations,
            'confidence': confidence,
            'model_prediction': {
                'main_secondary_raw': ms_pred.tolist(),
                'combination_raw': float(comb_pred)
            }
        }

    def _generate_combinations(self, main: int, secondary: int, base: int, count: int) -> List[str]:
        """สร้างชุดเลขจากการทำนาย"""
        combinations = []
        
        # Basic combinations from main/secondary
        combinations.extend([
            f"{main}{secondary}",
            f"{secondary}{main}",
            f"{main}{main}",
            f"{secondary}{secondary}"
        ])
        
        # Variations of base combination
        base_str = f"{base:02d}"
        combinations.append(base_str)
        combinations.append(base_str[::-1])  # Reverse
        
        # Generate variations
        for i in range(count - len(combinations)):
            variation = (base + i * 7) % 100  # Use prime number for variation
            combinations.append(f"{variation:02d}")
        
        # Remove duplicates and limit count
        unique_combinations = list(dict.fromkeys(combinations))
        return unique_combinations[:count]

    def _calculate_confidence(self, features: np.ndarray, ms_pred: np.ndarray, comb_pred: float) -> float:
        """คำนวณความมั่นใจในการทำนาย"""
        # Simple confidence based on prediction consistency
        ms_consistency = 1.0 / (1.0 + np.std(ms_pred))
        combination_strength = min(1.0, abs(comb_pred) / 50.0)  # Normalize to 0-1
        
        # Factor in feature density
        feature_density = np.mean(features > 0)
        
        confidence = (ms_consistency + combination_strength + feature_density) / 3
        return min(95.0, max(15.0, confidence * 100))  # Scale to 15-95%

    def save_model(self, filepath: Optional[str] = None):
        """บันทึกโมเดล"""
        filepath = filepath or self.model_path
        
        model_data = {
            'tfidf_vectorizer': self.tfidf_vectorizer,
            'main_secondary_model': self.main_secondary_model,
            'combination_model': self.combination_model,
            'is_trained': self.is_trained,
            'thai_patterns': self.thai_patterns,
            'element_weights': self.element_weights,
            'timestamp': datetime.now().isoformat()
        }
        
        joblib.dump(model_data, filepath)
        print(f"💾 บันทึกโมเดลแล้ว: {filepath}")

    def load_model(self, filepath: Optional[str] = None):
        """โหลดโมเดล"""
        filepath = filepath or self.model_path
        
        if not os.path.exists(filepath):
            print(f"⚠️  ไม่พบไฟล์โมเดล: {filepath}")
            return False
        
        try:
            model_data = joblib.load(filepath)
            
            self.tfidf_vectorizer = model_data['tfidf_vectorizer']
            self.main_secondary_model = model_data['main_secondary_model'] 
            self.combination_model = model_data['combination_model']
            self.is_trained = model_data['is_trained']
            self.thai_patterns = model_data.get('thai_patterns', self.thai_patterns)
            self.element_weights = model_data.get('element_weights', self.element_weights)
            
            print(f"✅ โหลดโมเดลสำเร็จ: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ ไม่สามารถโหลดโมเดล: {str(e)}")
            return False

    def analyze_dream_advanced(self, dream_text: str) -> Dict:
        """วิเคราะห์ความฝันแบบละเอียด พร้อม ML และ Traditional"""
        # ML prediction
        ml_result = self.predict(dream_text) if self.is_trained else None
        
        # Traditional keyword matching (fallback)
        traditional_result = self._traditional_analysis(dream_text)
        
        # Combine results
        if ml_result and traditional_result:
            combined_numbers = list(set(ml_result['combinations'] + traditional_result['numbers']))
            confidence = (ml_result['confidence'] + traditional_result['confidence']) / 2
        elif ml_result:
            combined_numbers = ml_result['combinations']
            confidence = ml_result['confidence']
        else:
            combined_numbers = traditional_result['numbers']
            confidence = traditional_result['confidence']
        
        return {
            'success': True,
            'ml_prediction': ml_result,
            'traditional_analysis': traditional_result,
            'combined_numbers': combined_numbers[:12],
            'confidence': confidence,
            'analysis_method': 'hybrid' if (ml_result and traditional_result) else ('ml' if ml_result else 'traditional')
        }

    def _traditional_analysis(self, dream_text: str) -> Dict:
        """การวิเคราะห์แบบดั้งเดิม (สำรอง)"""
        # Simplified traditional analysis
        numbers = []
        confidence = 50.0
        
        # Extract any numbers from text
        explicit_numbers = re.findall(r'\d{1,2}', dream_text)
        numbers.extend(explicit_numbers[:3])
        
        # Basic keyword matching
        if 'งู' in dream_text:
            numbers.extend(['56', '89', '08'])
        if 'ช้าง' in dream_text:
            numbers.extend(['91', '19', '01'])
        if 'เงิน' in dream_text or 'ทอง' in dream_text:
            numbers.extend(['82', '28', '88'])
        
        # Default numbers if none found
        if not numbers:
            numbers = ['07', '23', '45']
            confidence = 30.0
        
        return {
            'numbers': list(dict.fromkeys(numbers))[:6],  # Remove duplicates
            'confidence': confidence,
            'keywords': ['งู', 'ช้าง', 'เงิน'] if any(k in dream_text for k in ['งู', 'ช้าง', 'เงิน']) else []
        }
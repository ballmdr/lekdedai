"""
AI Model #1: The Dream Interpreter (DreamSymbol_Model)
เฉพาะทางสำหรับการตีความเชิงสัญลักษณ์จากความฝัน
"""
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.multioutput import MultiOutputClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import joblib
import os
import re
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import json

try:
    from pythainlp import word_tokenize, corpus
    from pythainlp.util import normalize
    PYTHAINLP_AVAILABLE = True
except ImportError:
    PYTHAINLP_AVAILABLE = False
    print("Warning: PyThaiNLP not available. Using basic tokenization.")

from .expert_dream_interpreter import ExpertDreamInterpreter

class DreamSymbolModel:
    """
    AI Model สำหรับตีความความฝันเป็นเลข
    เฉพาะทางด้าน Symbolic Interpretation
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "dream_symbol_model.pkl"
        
        # Initialize Expert Dream Interpreter
        self.expert_interpreter = ExpertDreamInterpreter()
        
        # TF-IDF Vectorizer optimized for Thai dream interpretation
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=2000,
            ngram_range=(1, 3),
            lowercase=True,
            tokenizer=self._thai_tokenize,
            stop_words=self._get_thai_stopwords()
        )
        
        # Multi-output classifier for number prediction
        self.symbol_classifier = MultiOutputClassifier(
            RandomForestClassifier(
                n_estimators=200,
                max_depth=20,
                random_state=42,
                class_weight='balanced'
            )
        )
        
        # Confidence scorer
        self.confidence_model = GradientBoostingClassifier(
            n_estimators=100,
            random_state=42
        )
        
        self.is_trained = False
        self.symbol_mappings = self._load_symbol_mappings()
        
        # Performance metrics
        self.training_metrics = {}
        
    def _thai_tokenize(self, text: str) -> List[str]:
        """Thai tokenization with fallback and tokenization fixes"""
        # แก้ไขปัญหาการตัดคำก่อนการ tokenize
        fixed_text = self._fix_thai_tokenization_issues(text)
        
        if PYTHAINLP_AVAILABLE:
            # Use PyThaiNLP for better Thai tokenization
            normalized = normalize(fixed_text)
            tokens = word_tokenize(normalized, engine='attacut')
            return [token for token in tokens if len(token.strip()) > 0]
        else:
            # Fallback: basic tokenization
            # Split on spaces and common Thai punctuation
            return re.findall(r'[^\s\.,!?;:\(\)\[\]]+', fixed_text)
    
    def _fix_thai_tokenization_issues(self, text: str) -> str:
        """แก้ไขปัญหาการตัดคำพื้นฐาน (เหมือนใน ExpertDreamInterpreter)"""
        # แก้ไข "อย่าง" ที่ถูกตัดเป็น "ย่าง"
        fixed_text = re.sub(r'\bย่าง\b', 'อย่าง', text)
        
        # แก้ไขคำพื้นฐานอื่นๆ
        basic_fixes = [
            (r'\bม่วย\b', 'มี'),
            (r'\bค่วย\b', 'คิว'),
            (r'\bส่วย\b', 'สี'),
        ]
        
        for pattern, replacement in basic_fixes:
            fixed_text = re.sub(pattern, replacement, fixed_text)
        
        return fixed_text
    
    def _get_thai_stopwords(self) -> List[str]:
        """Get Thai stopwords"""
        thai_stopwords = [
            'และ', 'หรือ', 'แต่', 'ที่', 'จาก', 'ใน', 'กับ', 'ของ', 'เป็น', 'ได้', 
            'มี', 'ไม่', 'จะ', 'แล้ว', 'ให้', 'ก็', 'ถึง', 'อยู่', 'นั้น', 'นี้',
            'ว่า', 'เมื่อ', 'ขึ้น', 'ลง', 'ออก', 'เข้า', 'มา', 'ไป', 'ได้', 'คือ'
        ]
        
        if PYTHAINLP_AVAILABLE:
            try:
                # Add PyThaiNLP stopwords if available
                thai_stopwords.extend(corpus.thai_stopwords())
            except:
                pass
        
        return list(set(thai_stopwords))
    
    def _load_symbol_mappings(self) -> Dict:
        """Load symbolic mappings for dream interpretation"""
        return {
            # Animals - สัตว์
            'animal_symbols': {
                'งู': {'primary': 5, 'secondary': 6, 'combinations': ['56', '89', '08', '65']},
                'พญานาค': {'primary': 8, 'secondary': 9, 'combinations': ['89', '98', '08', '90']},
                'ช้าง': {'primary': 9, 'secondary': 1, 'combinations': ['91', '19', '01', '90']},
                'เสือ': {'primary': 3, 'secondary': 4, 'combinations': ['34', '43', '03', '30']},
                'หมู': {'primary': 2, 'secondary': 7, 'combinations': ['27', '72', '02', '70']},
                'ไก่': {'primary': 1, 'secondary': 8, 'combinations': ['18', '81', '01', '80']},
                'หมา': {'primary': 4, 'secondary': 5, 'combinations': ['45', '54', '04', '50']},
                'แมว': {'primary': 6, 'secondary': 7, 'combinations': ['67', '76', '06', '70']},
                'วัว': {'primary': 0, 'secondary': 2, 'combinations': ['02', '20', '00', '22']},
                'ควาย': {'primary': 0, 'secondary': 3, 'combinations': ['03', '30', '00', '33']},
            },
            
            # People - บุคคล
            'people_symbols': {
                'พระ': {'primary': 8, 'secondary': 9, 'combinations': ['89', '98', '08', '99']},
                'เณร': {'primary': 9, 'secondary': 0, 'combinations': ['90', '09', '99', '00']},
                'แม่': {'primary': 2, 'secondary': 8, 'combinations': ['28', '82', '22', '88']},
                'พ่อ': {'primary': 1, 'secondary': 9, 'combinations': ['19', '91', '11', '99']},
                'เด็ก': {'primary': 1, 'secondary': 3, 'combinations': ['13', '31', '11', '33']},
                'ทารก': {'primary': 1, 'secondary': 0, 'combinations': ['10', '01', '11', '00']},
                'คนแก่': {'primary': 7, 'secondary': 8, 'combinations': ['78', '87', '77', '88']},
                'ผู้หญิง': {'primary': 2, 'secondary': 5, 'combinations': ['25', '52', '22', '55']},
                'ผู้ชาย': {'primary': 4, 'secondary': 6, 'combinations': ['46', '64', '44', '66']},
            },
            
            # Objects - สิ่งของ
            'object_symbols': {
                'เงิน': {'primary': 8, 'secondary': 2, 'combinations': ['82', '28', '88', '22']},
                'ทอง': {'primary': 9, 'secondary': 8, 'combinations': ['98', '89', '99', '88']},
                'รถ': {'primary': 4, 'secondary': 0, 'combinations': ['40', '04', '44', '00']},
                'บ้าน': {'primary': 6, 'secondary': 8, 'combinations': ['68', '86', '66', '88']},
                'วัด': {'primary': 8, 'secondary': 0, 'combinations': ['80', '08', '88', '00']},
                'โบสถ์': {'primary': 8, 'secondary': 7, 'combinations': ['87', '78', '88', '77']},
                'ไฟ': {'primary': 3, 'secondary': 7, 'combinations': ['37', '73', '33', '77']},
                'น้ำ': {'primary': 2, 'secondary': 6, 'combinations': ['26', '62', '22', '66']},
                'ต้นไม้': {'primary': 5, 'secondary': 2, 'combinations': ['52', '25', '55', '22']},
                'ดอกไม้': {'primary': 5, 'secondary': 1, 'combinations': ['51', '15', '55', '11']},
            },
            
            # Colors - สี
            'color_symbols': {
                'แดง': {'primary': 3, 'secondary': 0, 'combinations': ['30', '03', '33', '00']},
                'เขียว': {'primary': 5, 'secondary': 0, 'combinations': ['50', '05', '55', '00']},
                'น้ำเงิน': {'primary': 2, 'secondary': 4, 'combinations': ['24', '42', '22', '44']},
                'เหลือง': {'primary': 1, 'secondary': 7, 'combinations': ['17', '71', '11', '77']},
                'ขาว': {'primary': 0, 'secondary': 8, 'combinations': ['08', '80', '00', '88']},
                'ดำ': {'primary': 0, 'secondary': 0, 'combinations': ['00', '90', '99', '09']},
                'ม่วง': {'primary': 6, 'secondary': 3, 'combinations': ['63', '36', '66', '33']},
                'ส้ม': {'primary': 7, 'secondary': 2, 'combinations': ['72', '27', '77', '22']},
                'ชมพู': {'primary': 5, 'secondary': 8, 'combinations': ['58', '85', '55', '88']},
                'ทอง': {'primary': 9, 'secondary': 1, 'combinations': ['91', '19', '99', '11']},
                'เงิน': {'primary': 8, 'secondary': 2, 'combinations': ['82', '28', '88', '22']},
            }
        }
    
    def extract_dream_features(self, dream_text: str) -> Dict[str, float]:
        """Extract features specific to dream symbolism"""
        features = {}
        text_lower = dream_text.lower()
        
        # Count symbolic elements
        all_symbols = {}
        all_symbols.update(self.symbol_mappings['animal_symbols'])
        all_symbols.update(self.symbol_mappings['people_symbols'])
        all_symbols.update(self.symbol_mappings['object_symbols'])
        all_symbols.update(self.symbol_mappings['color_symbols'])
        
        # Symbol presence and frequency
        for symbol in all_symbols:
            count = text_lower.count(symbol)
            features[f'symbol_{symbol}'] = count
        
        # Dream-specific patterns
        dream_patterns = {
            'fear': r'กลัว|ตกใจ|หนี|วิ่งหนี|เสียงใส',
            'joy': r'ดีใจ|สุข|หัวเราะ|ยิ้ม|มีความสุข',
            'interaction': r'เล่น|คุย|พูด|ให้|รับ|จับ',
            'size': r'ใหญ่|เล็ก|มาก|น้อย|ยาว|สั้น',
            'movement': r'บิน|วิ่ง|เดิน|ว่าย|เลื้อย|กระโดด',
            'location': r'บ้าน|วัด|ป่า|น้ำ|ฟ้า|ดิน',
        }
        
        for pattern_name, pattern in dream_patterns.items():
            matches = len(re.findall(pattern, text_lower))
            features[f'pattern_{pattern_name}'] = matches
        
        # Text statistics
        features['text_length'] = len(dream_text)
        features['word_count'] = len(dream_text.split())
        features['symbol_density'] = sum(features[f'symbol_{s}'] for s in all_symbols) / max(len(dream_text.split()), 1)
        
        return features
    
    def prepare_training_data(self, dream_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for training the dream symbol model"""
        texts = []
        targets = []
        
        for data in dream_data:
            texts.append(data['dream_text'])
            
            # Create target vector: [primary_digit, secondary_digit, top_combinations(4)]
            primary = int(data.get('main_number', 1))
            secondary = int(data.get('secondary_number', 0))
            combinations = data.get('combinations', [])
            
            # Convert combinations to numeric targets (top 4)
            combo_targets = []
            for combo in combinations[:4]:
                if combo.isdigit() and len(combo) == 2:
                    combo_targets.append(int(combo))
                else:
                    combo_targets.append(10)  # Default value
            
            # Pad to 4 combinations
            while len(combo_targets) < 4:
                combo_targets.append(10)
            
            target_vector = [primary, secondary] + combo_targets
            targets.append(target_vector)
        
        # Create TF-IDF features
        tfidf_features = self.tfidf_vectorizer.fit_transform(texts).toarray()
        
        # Create symbolic features
        symbolic_features = []
        for text in texts:
            sym_feat = self.extract_dream_features(text)
            symbolic_features.append(list(sym_feat.values()))
        
        # Combine features
        symbolic_features = np.array(symbolic_features)
        combined_features = np.hstack([tfidf_features, symbolic_features])
        
        return combined_features, np.array(targets)
    
    def train(self, dream_data: List[Dict], test_size: float = 0.2):
        """Train the dream symbol model"""
        print("🔮 เริ่มการฝึกสอน DreamSymbol_Model...")
        
        # Prepare data
        X, y = self.prepare_training_data(dream_data)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y[:, 0]  # Stratify by primary digit
        )
        
        print(f"📊 ข้อมูลฝึกสอน: {X_train.shape[0]} samples")
        print(f"📊 ข้อมูลทดสอบ: {X_test.shape[0]} samples")
        
        # Train symbol classifier
        print("🎯 ฝึกสอนตัวจำแนกสัญลักษณ์...")
        self.symbol_classifier.fit(X_train, y_train)
        
        # Train confidence model (predict confidence based on features)
        confidence_targets = np.random.uniform(0.7, 0.95, X_train.shape[0])  # Placeholder
        self.confidence_model.fit(X_train, confidence_targets)
        
        # Evaluate
        y_pred = self.symbol_classifier.predict(X_test)
        
        # Calculate metrics for each output
        metrics = {}
        output_names = ['primary', 'secondary', 'combo1', 'combo2', 'combo3', 'combo4']
        
        for i, name in enumerate(output_names):
            accuracy = accuracy_score(y_test[:, i], y_pred[:, i])
            metrics[f'{name}_accuracy'] = accuracy
        
        overall_accuracy = np.mean([metrics[f'{name}_accuracy'] for name in output_names[:2]])  # Focus on primary/secondary
        
        print(f"✅ การฝึกสอนเสร็จสิ้น!")
        print(f"📈 ความแม่นยำเลขเด่น: {metrics['primary_accuracy']:.3f}")
        print(f"📈 ความแม่นยำเลขรอง: {metrics['secondary_accuracy']:.3f}")
        print(f"📈 ความแม่นยำรวม: {overall_accuracy:.3f}")
        
        self.is_trained = True
        self.training_metrics = metrics
        
        return metrics
    
    def predict(self, dream_text: str, top_k: int = 6) -> List[Dict]:
        """Predict numbers from dream text with confidence scores"""
        
        # Use Expert Dream Interpreter for advanced analysis
        expert_result = self.expert_interpreter.interpret_dream(dream_text)
        
        if expert_result and 'predicted_numbers' in expert_result:
            # Return expert predictions (already in correct format)
            predictions = expert_result['predicted_numbers'][:top_k]
            return predictions
        
        # Fallback to ML model if expert fails and model is trained
        if self.is_trained:
            return self._ml_predict(dream_text, top_k)
        
        # Final fallback
        return [{"number": "07", "score": 0.5, "reason": "เลขเริ่มต้น"}]
    
    def _ml_predict(self, dream_text: str, top_k: int = 6) -> List[Dict]:
        """ML prediction fallback method"""
        try:
            # Prepare features
            tfidf_features = self.tfidf_vectorizer.transform([dream_text]).toarray()
            symbolic_features = np.array([list(self.extract_dream_features(dream_text).values())])
            combined_features = np.hstack([tfidf_features, symbolic_features])
            
            # Predict
            predictions = self.symbol_classifier.predict(combined_features)[0]
            confidence_score = self.confidence_model.predict(combined_features)[0]
            
            # Extract results
            primary = int(predictions[0]) % 10  # Ensure single digit
            secondary = int(predictions[1]) % 10
            combinations = [int(predictions[i]) % 100 for i in range(2, 6)]  # Ensure 2 digits
            
            # Generate final number combinations
            result_numbers = []
            
            # Add primary combinations
            result_numbers.extend([
                f"{primary}{secondary}",
                f"{secondary}{primary}",
                f"{primary}{primary}",
                f"{secondary}{secondary}"
            ])
            
            # Add predicted combinations
            for combo in combinations:
                result_numbers.append(f"{combo:02d}")
            
            # Remove duplicates and format with scores
            unique_numbers = list(dict.fromkeys(result_numbers))
            
            # Assign confidence scores (decreasing)
            results = []
            base_confidence = min(0.95, max(0.6, confidence_score))
            
            for i, number in enumerate(unique_numbers[:top_k]):
                score = base_confidence * (0.95 ** i)  # Decreasing confidence
                results.append({
                    "number": number,
                    "score": round(score, 3),
                    "reason": f"ทำนายโดย ML Model"
                })
            
            return results
            
        except Exception as e:
            return [{"number": "07", "score": 0.5, "reason": f"ML Error: {str(e)}"}]
    
    def save_model(self, filepath: Optional[str] = None):
        """Save the trained model"""
        filepath = filepath or self.model_path
        
        model_data = {
            'tfidf_vectorizer': self.tfidf_vectorizer,
            'symbol_classifier': self.symbol_classifier,
            'confidence_model': self.confidence_model,
            'symbol_mappings': self.symbol_mappings,
            'is_trained': self.is_trained,
            'training_metrics': self.training_metrics,
            'timestamp': datetime.now().isoformat(),
            'model_type': 'DreamSymbol_Model',
            'version': '1.0.0'
        }
        
        joblib.dump(model_data, filepath)
        print(f"💾 DreamSymbol_Model บันทึกแล้ว: {filepath}")
    
    def load_model(self, filepath: Optional[str] = None):
        """Load a trained model"""
        filepath = filepath or self.model_path
        
        if not os.path.exists(filepath):
            print(f"⚠️  ไม่พบไฟล์โมเดล: {filepath}")
            return False
        
        try:
            model_data = joblib.load(filepath)
            
            self.tfidf_vectorizer = model_data['tfidf_vectorizer']
            self.symbol_classifier = model_data['symbol_classifier']
            self.confidence_model = model_data['confidence_model']
            self.symbol_mappings = model_data.get('symbol_mappings', self.symbol_mappings)
            self.is_trained = model_data['is_trained']
            self.training_metrics = model_data.get('training_metrics', {})
            
            print(f"✅ DreamSymbol_Model โหลดสำเร็จ: {filepath}")
            print(f"📊 เวอร์ชัน: {model_data.get('version', 'Unknown')}")
            
            return True
            
        except Exception as e:
            print(f"❌ ไม่สามารถโหลด DreamSymbol_Model: {str(e)}")
            return False
    
    def get_model_info(self) -> Dict:
        """Get model information"""
        return {
            'model_name': 'DreamSymbol_Model',
            'model_type': 'Symbolic Interpretation',
            'version': '1.0.0',
            'is_trained': self.is_trained,
            'training_metrics': self.training_metrics,
            'features': {
                'tfidf_features': self.tfidf_vectorizer.get_feature_names_out().shape[0] if hasattr(self.tfidf_vectorizer, 'get_feature_names_out') else 0,
                'symbolic_features': len(self.extract_dream_features("test")),
                'pythainlp_available': PYTHAINLP_AVAILABLE
            },
            'supported_languages': ['thai'],
            'max_latency_ms': 500,
            'capabilities': [
                'symbolic_interpretation',
                'thai_tokenization',
                'confidence_scoring',
                'multi_output_prediction'
            ]
        }
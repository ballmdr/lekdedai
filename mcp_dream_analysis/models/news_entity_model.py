"""
AI Model #2: The News Extractor (NewsEntity_Model) 
เฉพาะทางสำหรับการสกัด Entity ตัวเลขจากข่าว (Named Entity Recognition)
"""
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, precision_recall_fscore_support
import joblib
import os
import re
from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime
import json
from dataclasses import dataclass

try:
    from pythainlp import word_tokenize, sent_tokenize
    from pythainlp.util import normalize
    PYTHAINLP_AVAILABLE = True
except ImportError:
    PYTHAINLP_AVAILABLE = False

@dataclass
class EntitySpan:
    """Class to represent an entity span"""
    text: str
    start: int
    end: int
    entity_type: str
    confidence: float

class NewsEntityModel:
    """
    AI Model สำหรับสกัด Numerical Entities จากข่าว
    เฉพาะทางด้าน Named Entity Recognition (NER)
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "news_entity_model.pkl"
        
        # Feature extractors for different entity types
        self.feature_extractors = {}
        self.entity_classifiers = {}
        
        # Supported entity types
        self.entity_types = [
            'license_plate',    # ทะเบียนรถ
            'age',             # อายุ  
            'house_number',    # บ้านเลขที่
            'quantity',        # จำนวน/ปริมาณ
            'date',            # วันที่
            'time',            # เวลา
            'lottery_number',  # เลขลอตเตอรี่
            'phone_number',    # เบอร์โทรศัพท์
            'id_number',       # เลขบัตรประชาชน
        ]
        
        self.is_trained = False
        self.training_metrics = {}
        
        # Initialize patterns and rules
        self.entity_patterns = self._init_entity_patterns()
        self.context_patterns = self._init_context_patterns()
    
    def _init_entity_patterns(self) -> Dict[str, List[str]]:
        """Initialize regex patterns for each entity type"""
        return {
            'license_plate': [
                r'[ก-ฮ]{1,2}\s*[\d]{1,4}',  # Thai license plate
                r'[\d]{2,4}',               # Numbers in license context
                r'[A-Z]{1,3}[\d]{1,4}',     # English prefix + numbers
            ],
            
            'age': [
                r'(?:อายุ|ปี)\s*[\d]{1,3}',
                r'[\d]{1,3}\s*(?:ขวบ|ปี|เดือน)',
                r'(?:วัย)\s*[\d]{1,3}',
            ],
            
            'house_number': [
                r'(?:บ้านเลขที่|เลขที่|หมู่ที่)\s*[\d]{1,6}',
                r'[\d]{1,6}\s*(?:/[\d]{1,3})?',  # House number with sub-number
                r'(?:ม\.)\s*[\d]{1,2}',          # หมู่ abbreviation
            ],
            
            'quantity': [
                r'[\d]{1,10}\s*(?:บาท|กิโลกรัม|กิโล|กก\.|ตัว|คน|ใบ|อัน)',
                r'[\d,]{1,15}\s*(?:บาท)',
                r'[\d]{1,8}\s*(?:คน|ครอบครัว)',
            ],
            
            'date': [
                r'[\d]{1,2}[\/\-.][\d]{1,2}[\/\-.]([\d]{2,4})',
                r'(?:วันที่)\s*[\d]{1,2}',
                r'[\d]{1,2}\s*(?:มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม)',
            ],
            
            'time': [
                r'[\d]{1,2}[:\.][\d]{2}\s*(?:น\.|นาฬิกา)',
                r'(?:เวลา)\s*[\d]{1,2}[:\.][\d]{2}',
                r'[\d]{1,2}\s*(?:โมง|นาฬิกา)',
            ],
            
            'lottery_number': [
                r'[\d]{6}',  # 6-digit lottery numbers
                r'[\d]{3}\s*[\d]{3}',
                r'(?:รางวัลที่)\s*[\d]{1,6}',
            ],
            
            'phone_number': [
                r'[\d]{3}[-\s][\d]{3}[-\s][\d]{4}',
                r'[\d]{10}',
                r'(?:โทร|เบอร์)\s*[\d\-\s]{8,15}',
            ],
            
            'id_number': [
                r'[\d]{1}-[\d]{4}-[\d]{5}-[\d]{2}-[\d]{1}',
                r'[\d]{13}',
                r'(?:เลขประจำตัว|บัตรประชาชน)\s*[\d\-]{10,20}',
            ],
        }
    
    def _init_context_patterns(self) -> Dict[str, List[str]]:
        """Initialize context patterns that help identify entities"""
        return {
            'license_plate': [
                'ทะเบียนรถ', 'รถยนต์', 'รถจักรยานยนต์', 'ป้ายทะเบียน', 
                'ขับรถ', 'รถคันนี้', 'ข้าม', 'จอด', 'วิ่ง'
            ],
            
            'age': [
                'อายุ', 'ปี', 'ขวบ', 'วัย', 'เด็ก', 'ผู้ใหญ่', 'คนแก่',
                'เกิด', 'แก่', 'เยาว์', 'วัยรุ่น'
            ],
            
            'house_number': [
                'บ้านเลขที่', 'เลขที่', 'หมู่ที่', 'ตำบล', 'อำเภอ', 'จังหวัด',
                'อยู่', 'ที่อยู่', 'บ้าน', 'หมู่บ้าน', 'ซอย', 'ถนน'
            ],
            
            'quantity': [
                'บาท', 'กิโลกรัม', 'กิโล', 'ตัว', 'คน', 'ใบ', 'อัน',
                'จำนวน', 'ปริมาณ', 'ราคา', 'เงิน', 'ค่า', 'ต้นทุน'
            ],
            
            'date': [
                'วันที่', 'เมื่อ', 'ตั้งแต่', 'จนถึง', 'ใน', 'ช่วง',
                'เดือน', 'ปี', 'วัน', 'เกิดเหตุ'
            ],
            
            'time': [
                'เวลา', 'นาฬิกา', 'โมง', 'นาที', 'วินาที',
                'ตอน', 'ช่วง', 'เมื่อ', 'เวลา'
            ],
        }
    
    def extract_entities_with_patterns(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using regex patterns and context"""
        results = {entity_type: [] for entity_type in self.entity_types}
        
        text_normalized = normalize(text) if PYTHAINLP_AVAILABLE else text.lower()
        
        for entity_type in self.entity_types:
            patterns = self.entity_patterns.get(entity_type, [])
            context_words = self.context_patterns.get(entity_type, [])
            
            for pattern in patterns:
                matches = re.finditer(pattern, text_normalized, re.IGNORECASE)
                
                for match in matches:
                    matched_text = match.group().strip()
                    start, end = match.span()
                    
                    # Check context (50 chars before and after)
                    context_start = max(0, start - 50)
                    context_end = min(len(text_normalized), end + 50)
                    context = text_normalized[context_start:context_end]
                    
                    # Calculate context relevance
                    context_score = sum(1 for word in context_words if word in context.lower())
                    
                    # Extract just the number parts
                    numbers = re.findall(r'\d+', matched_text)
                    
                    for number in numbers:
                        if self._is_valid_entity(number, entity_type):
                            results[entity_type].append({
                                'value': number,
                                'full_match': matched_text,
                                'context_score': context_score,
                                'position': (start, end)
                            })
        
        # Remove duplicates and sort by context score
        for entity_type in results:
            seen = set()
            filtered = []
            
            # Sort by context score (descending)
            results[entity_type].sort(key=lambda x: x['context_score'], reverse=True)
            
            for item in results[entity_type]:
                if item['value'] not in seen:
                    seen.add(item['value'])
                    filtered.append(item['value'])
            
            results[entity_type] = filtered[:5]  # Keep top 5
        
        return results
    
    def _is_valid_entity(self, number: str, entity_type: str) -> bool:
        """Validate extracted numbers based on entity type"""
        if not number.isdigit():
            return False
        
        num_len = len(number)
        
        validation_rules = {
            'license_plate': lambda n: 1 <= len(n) <= 4,
            'age': lambda n: 1 <= int(n) <= 120 and len(n) <= 3,
            'house_number': lambda n: 1 <= len(n) <= 6,
            'quantity': lambda n: 1 <= len(n) <= 10,
            'date': lambda n: len(n) <= 4,  # Year, day, month
            'time': lambda n: len(n) <= 2,   # Hour, minute
            'lottery_number': lambda n: len(n) == 6,
            'phone_number': lambda n: len(n) == 10,
            'id_number': lambda n: len(n) == 13,
        }
        
        validator = validation_rules.get(entity_type, lambda n: True)
        return validator(number)
    
    def extract_features_for_training(self, text: str, entities: Dict[str, List]) -> np.ndarray:
        """Extract features for training the ML models"""
        features = []
        
        # Text statistics
        features.extend([
            len(text),
            len(text.split()),
            text.count('\d') if hasattr(text, 'count') else 0,
        ])
        
        # Entity pattern matches
        for entity_type in self.entity_types:
            patterns = self.entity_patterns.get(entity_type, [])
            total_matches = 0
            
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                total_matches += matches
            
            features.append(total_matches)
        
        # Context word presence
        for entity_type in self.entity_types:
            context_words = self.context_patterns.get(entity_type, [])
            context_count = sum(1 for word in context_words if word.lower() in text.lower())
            features.append(context_count)
        
        return np.array(features)
    
    def prepare_training_data(self, news_data: List[Dict]) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """Prepare training data for all entity types"""
        features = []
        targets = {entity_type: [] for entity_type in self.entity_types}
        
        for data in news_data:
            text = data['news_content']
            entities = data.get('entities', {})
            
            # Extract features
            text_features = self.extract_features_for_training(text, entities)
            features.append(text_features)
            
            # Create targets (binary classification for each entity type)
            for entity_type in self.entity_types:
                has_entity = 1 if entities.get(entity_type) and len(entities[entity_type]) > 0 else 0
                targets[entity_type].append(has_entity)
        
        return np.array(features), {k: np.array(v) for k, v in targets.items()}
    
    def train(self, news_data: List[Dict], test_size: float = 0.2):
        """Train all entity recognition models"""
        print("🔍 เริ่มการฝึกสอน NewsEntity_Model...")
        
        # Prepare data
        X, y_dict = self.prepare_training_data(news_data)
        
        print(f"📊 จำนวนข้อมูลทั้งหมด: {X.shape[0]} samples")
        print(f"📊 จำนวน features: {X.shape[1]}")
        
        # Split data
        X_train, X_test, _, _ = train_test_split(X, X, test_size=test_size, random_state=42)
        
        # Train individual classifiers for each entity type
        self.training_metrics = {}
        
        for entity_type in self.entity_types:
            print(f"🎯 ฝึกสอนตัวจำแนก: {entity_type}...")
            
            y = y_dict[entity_type]
            y_train, y_test, _, _ = train_test_split(
                y, y, test_size=test_size, random_state=42, stratify=y
            )
            
            # Choose classifier based on entity type
            if entity_type in ['license_plate', 'lottery_number']:
                classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            else:
                classifier = LogisticRegression(random_state=42, max_iter=1000)
            
            # Train
            classifier.fit(X_train, y_train)
            
            # Evaluate
            y_pred = classifier.predict(X_test)
            
            precision, recall, f1, _ = precision_recall_fscore_support(
                y_test, y_pred, average='weighted', zero_division=0
            )
            
            self.entity_classifiers[entity_type] = classifier
            self.training_metrics[entity_type] = {
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'accuracy': classifier.score(X_test, y_test)
            }
            
            print(f"   ✅ {entity_type}: F1={f1:.3f}, Accuracy={self.training_metrics[entity_type]['accuracy']:.3f}")
        
        self.is_trained = True
        
        # Overall metrics
        overall_f1 = np.mean([metrics['f1'] for metrics in self.training_metrics.values()])
        overall_accuracy = np.mean([metrics['accuracy'] for metrics in self.training_metrics.values()])
        
        print(f"✅ การฝึกสอนเสร็จสิ้น!")
        print(f"📈 F1-Score รวม: {overall_f1:.3f}")
        print(f"📈 Accuracy รวม: {overall_accuracy:.3f}")
        
        return self.training_metrics
    
    def predict(self, news_content: str) -> Dict[str, List[str]]:
        """Extract entities from news content"""
        # Start with pattern-based extraction
        pattern_results = self.extract_entities_with_patterns(news_content)
        
        # If models are trained, use ML to refine results
        if self.is_trained:
            features = self.extract_features_for_training(news_content, {}).reshape(1, -1)
            
            ml_results = {}
            for entity_type in self.entity_types:
                if entity_type in self.entity_classifiers:
                    classifier = self.entity_classifiers[entity_type]
                    
                    # Predict if this entity type is present
                    has_entity = classifier.predict(features)[0]
                    confidence = classifier.predict_proba(features)[0][1] if hasattr(classifier, 'predict_proba') else 0.5
                    
                    if has_entity and confidence > 0.3:
                        # Keep pattern results if ML says entity is present
                        ml_results[entity_type] = pattern_results.get(entity_type, [])
                    else:
                        # Filter out or reduce pattern results
                        ml_results[entity_type] = pattern_results.get(entity_type, [])[:2]  # Keep only top 2
                else:
                    ml_results[entity_type] = pattern_results.get(entity_type, [])
            
            return ml_results
        else:
            # Return pattern-based results only
            return pattern_results
    
    def save_model(self, filepath: Optional[str] = None):
        """Save the trained model"""
        filepath = filepath or self.model_path
        
        model_data = {
            'entity_classifiers': self.entity_classifiers,
            'entity_patterns': self.entity_patterns,
            'context_patterns': self.context_patterns,
            'entity_types': self.entity_types,
            'is_trained': self.is_trained,
            'training_metrics': self.training_metrics,
            'timestamp': datetime.now().isoformat(),
            'model_type': 'NewsEntity_Model',
            'version': '1.0.0'
        }
        
        joblib.dump(model_data, filepath)
        print(f"💾 NewsEntity_Model บันทึกแล้ว: {filepath}")
    
    def load_model(self, filepath: Optional[str] = None):
        """Load a trained model"""
        filepath = filepath or self.model_path
        
        if not os.path.exists(filepath):
            print(f"⚠️  ไม่พบไฟล์โมเดล: {filepath}")
            return False
        
        try:
            model_data = joblib.load(filepath)
            
            self.entity_classifiers = model_data.get('entity_classifiers', {})
            self.entity_patterns = model_data.get('entity_patterns', self.entity_patterns)
            self.context_patterns = model_data.get('context_patterns', self.context_patterns)
            self.entity_types = model_data.get('entity_types', self.entity_types)
            self.is_trained = model_data.get('is_trained', False)
            self.training_metrics = model_data.get('training_metrics', {})
            
            print(f"✅ NewsEntity_Model โหลดสำเร็จ: {filepath}")
            print(f"📊 เวอร์ชัน: {model_data.get('version', 'Unknown')}")
            
            return True
            
        except Exception as e:
            print(f"❌ ไม่สามารถโหลด NewsEntity_Model: {str(e)}")
            return False
    
    def get_model_info(self) -> Dict:
        """Get model information"""
        return {
            'model_name': 'NewsEntity_Model',
            'model_type': 'Named Entity Recognition (NER)',
            'version': '1.0.0',
            'is_trained': self.is_trained,
            'training_metrics': self.training_metrics,
            'entity_types': self.entity_types,
            'features': {
                'pattern_based': True,
                'ml_enhanced': self.is_trained,
                'pythainlp_available': PYTHAINLP_AVAILABLE
            },
            'supported_languages': ['thai'],
            'capabilities': [
                'numerical_entity_extraction',
                'context_awareness',
                'pattern_matching',
                'ml_classification'
            ]
        }
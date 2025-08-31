"""
Expert Dream Interpreter - อาจารย์ AI ผู้เชี่ยวชาญด้านการทำนายฝัน
Advanced AI system for Thai dream interpretation based on ancient knowledge
"""
import numpy as np
import re
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging

try:
    from pythainlp import word_tokenize, sent_tokenize
    from pythainlp.util import normalize
    PYTHAINLP_AVAILABLE = True
except ImportError:
    PYTHAINLP_AVAILABLE = False

class ExpertDreamInterpreter:
    """
    อาจารย์ AI ผู้เชี่ยวชาญด้านการทำนายฝันและโหราศาสตร์ตัวเลขไทย
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Ancient Thai Dream Knowledge Base
        self.knowledge_base = self._load_ancient_knowledge()
        
        # Context analysis patterns - ปรับปรุงให้รองรับการตัดคำที่ผิด
        self.emotion_patterns = {
            'fear': r'กลัว|ตกใจ|หนี|วิ่งหนี|เสียงใส|น่ากลัว|ขนหัวลุก|ย่างกลัว|ย่างน่ากลัว|เก็บตัว|ประหลาด|น่าสะพรึง',
            'joy': r'ดีใจ|สุข|หัวเราะ|ยิ้ม|มีความสุข|สนุก|เพลิน|ม่วยดี|มีความ.*สุข|ร่าเริง|บินได้|บิน',
            'peaceful': r'สงบ|เงียบ|สงบสุข|ชื่นใจ|สบายใจ|ผ่อนคลาย|สงบสุข|ย่างสงบ|ย่างสบาย',
            'aggressive': r'ไล่|กัด|โจมตี|ทำร้าย|ต่อสู้|รุกราน|ข่มขู่|ขู่|รุนแรง|ร้ายแรง|ย่างดุ|กินคน|กิน.*คน',
            'protective': r'คุ้มครอง|ปกป้อง|ช่วย|ดูแล|เฝ้า|รักษา|ดูแลรักษา|ย่างดี|ใจดี',
            'giving': r'ให้|มอบ|แจก|ประทาน|อวยพร|ส่งมอบ|แบ่งปัน|ย่างใจดี|ย่างดี',
            'losing': r'หาย|สูญ|เสีย|หล่น|ตก|ขาด|พลัด|สูญหาย|ย่างเสียใจ',
            'adventure': r'ผจญภัย|สำรวจ|ข้าม|เดินทาง|ไป.*ถึง|พบเจอ|ค้นพบ|ลึกลับ',
            'magical': r'บิน|บินได้|เวทมนตร์|พิเศษ|วิเศษ|มหัศจรรย์|เหนือธรรมชาติ|ลี้ลับ'
        }
        
        # Size and intensity modifiers - ปรับปรุงให้รองรับการตัดคำที่ผิด
        self.size_patterns = {
            'huge': r'ใหญ่มาก|ยักษ์|ขนาดมหึมา|ตัวโต|มโหฬาร|ย่างใหญ่|มากใหญ่|โตมาก',
            'big': r'ใหญ่|โต|ขนาดใหญ่|ย่างใหญ่|ตัวใหญ่',
            'small': r'เล็ก|น้อย|ขนาดเล็ก|จิ๋ว|ย่างเล็ก|ตัวเล็ก',
            'many': r'หลายตัว|เยอะ|มาก|จำนวนมาก|นับไม่ถ้วน|ย่างเยอะ|หลาย.*ตัว',
            'beautiful': r'สวย|งาม|วิจิตร|น่าดู|สง่า|ปกาศัย|ย่างสวย|สวยงาม|ย่างงาม',
            'strange': r'แปลก|ผิดปกติ|ประหลาด|พิศดาร|ย่างแปลก|แปลก.*ดี'
        }
    
    def _load_ancient_knowledge(self) -> Dict:
        """โหลดตำราทำนายฝันโบราณ"""
        return {
            # 🐘 หมวดสัตว์
            'animals': {
                'กบ': {'main': 8, 'secondary': 9, 'combinations': ['89', '59', '98', '95'], 'meaning': 'โชคลาภจากน้ำ'},
                'ไก่': {'main': 0, 'secondary': 9, 'combinations': ['09', '19', '90', '91'], 'meaning': 'ข่าวสารดี'},
                'ควาย': {'main': 4, 'secondary': 2, 'combinations': ['42', '82', '24', '28'], 'meaning': 'ความอุดมสมบูรณ์'},
                'งู': {'main': 5, 'secondary': 6, 'combinations': ['56', '65', '59', '95'], 'meaning': 'พลังลึกลับ การเปลี่ยนแปลง'},
                'พยานาค': {'main': 8, 'secondary': 9, 'combinations': ['89', '98', '59', '95'], 'meaning': 'พลังศักดิ์สิทธิ์'},
                'ช้าง': {'main': 9, 'secondary': 1, 'combinations': ['91', '19', '90', '10'], 'meaning': 'เกียรติยศ ความมั่งคั่ง'},
                'เสือ': {'main': 3, 'secondary': 4, 'combinations': ['34', '43', '30', '40'], 'meaning': 'อำนาจ ความกล้าหาญ'},
                'หมู': {'main': 2, 'secondary': 7, 'combinations': ['27', '72', '20', '70'], 'meaning': 'ความอุดมสมบูรณ์'},
                'หมา': {'main': 4, 'secondary': 5, 'combinations': ['45', '54', '40', '50'], 'meaning': 'ความจงรักภักดี'},
                'แมว': {'main': 6, 'secondary': 7, 'combinations': ['67', '76', '60', '70'], 'meaning': 'ความเจ้าเล่ห์'},
                'วัว': {'main': 0, 'secondary': 2, 'combinations': ['02', '20', '00', '22'], 'meaning': 'ความขยันหมั่นเพียร'},
                'สัตว์ประหลาด': {'main': 6, 'secondary': 6, 'combinations': ['66', '60', '06', '36'], 'meaning': 'พลังลึกลับและความท้าทาย'},
                'ปีศาจ': {'main': 0, 'secondary': 6, 'combinations': ['06', '60', '66', '00'], 'meaning': 'สิ่งชั่วร้ายที่ต้องระวัง'},
                'มังกร': {'main': 8, 'secondary': 9, 'combinations': ['89', '98', '88', '99'], 'meaning': 'พลังอำนาจสูงสุด'},
                'นก': {'main': 1, 'secondary': 5, 'combinations': ['15', '51', '10', '50'], 'meaning': 'ความเป็นอิสระ การบิน'},
            },
            
            # 👑 หมวดบุคคล
            'people': {
                'กษัตริย์': {'main': 9, 'secondary': 5, 'combinations': ['59', '95', '19', '51'], 'meaning': 'เกียรติยศสูงสุด'},
                'คนตาย': {'main': 0, 'secondary': 4, 'combinations': ['04', '40', '07', '70'], 'meaning': 'การสิ้นสุดและเริ่มต้นใหม่'},
                'เด็กทารก': {'main': 1, 'secondary': 3, 'combinations': ['11', '13', '33', '31'], 'meaning': 'จุดเริ่มต้นใหม่'},
                'พระ': {'main': 8, 'secondary': 9, 'combinations': ['89', '98', '80', '90'], 'meaning': 'พระคุณ ความศักดิ์สิทธิ์'},
                'เณร': {'main': 9, 'secondary': 0, 'combinations': ['90', '09', '99', '00'], 'meaning': 'ความบริสุทธิ์'},
                'แม่': {'main': 2, 'secondary': 8, 'combinations': ['28', '82', '20', '80'], 'meaning': 'ความเมตตา'},
                'พ่อ': {'main': 1, 'secondary': 9, 'combinations': ['19', '91', '10', '90'], 'meaning': 'ความเข้มแข็ง'},
            },
            
            # 🏠 หมวดสิ่งของ / สถานที่
            'objects': {
                'เงิน': {'main': 8, 'secondary': 2, 'combinations': ['28', '82', '68', '86'], 'meaning': 'โชคลาภทางการเงิน'},
                'ทอง': {'main': 8, 'secondary': 2, 'combinations': ['28', '82', '68', '86'], 'meaning': 'ความมั่งคั่ง'},
                'น้ำ': {'main': 0, 'secondary': 2, 'combinations': ['02', '29', '32', '23'], 'meaning': 'ความอุดมสมบูรณ์'},
                'ไฟ': {'main': 3, 'secondary': 7, 'combinations': ['37', '73', '30', '70'], 'meaning': 'พลังงานและการเปลี่ยนแปลง'},
                'วัด': {'main': 8, 'secondary': 0, 'combinations': ['80', '08', '88', '00'], 'meaning': 'ความศักดิ์สิทธิ์'},
                'บ้าน': {'main': 6, 'secondary': 8, 'combinations': ['68', '86', '60', '80'], 'meaning': 'ความมั่นคงในครอบครัว'},
                'รถ': {'main': 4, 'secondary': 0, 'combinations': ['40', '04', '44', '00'], 'meaning': 'การเดินทาง ความก้าวหน้า'},
                'มหาสมุทร': {'main': 0, 'secondary': 7, 'combinations': ['07', '70', '00', '77'], 'meaning': 'ความไร้ขีดจำกัด การผจญภัย'},
                'ทะเล': {'main': 0, 'secondary': 7, 'combinations': ['07', '70', '00', '77'], 'meaning': 'ความลึกลับและพลังงาน'},
                'เกาะ': {'main': 9, 'secondary': 0, 'combinations': ['90', '09', '99', '00'], 'meaning': 'ที่ลี้ภัยและการค้นพบ'},
                'ป่า': {'main': 7, 'secondary': 4, 'combinations': ['74', '47', '70', '40'], 'meaning': 'ความลึกลับของธรรมชาติ'},
                'เขา': {'main': 3, 'secondary': 1, 'combinations': ['31', '13', '30', '10'], 'meaning': 'ความสูงส่งและความท้าทาย'},
            },
            
            # ✈️ หมวดการเคลื่อนไหว / พฤติกรรม
            'actions': {
                'บิน': {'main': 1, 'secondary': 5, 'combinations': ['15', '51', '11', '55'], 'meaning': 'ความเป็นอิสระ การก้าวข้ามขีดจำกัด'},
                'บินได้': {'main': 1, 'secondary': 5, 'combinations': ['15', '51', '11', '55'], 'meaning': 'พลังพิเศษ ความสามารถเหนือธรรมชาติ'},
                'ข้าม': {'main': 4, 'secondary': 8, 'combinations': ['48', '84', '40', '80'], 'meaning': 'การผ่านพ้นอุปสรรค'},
                'วิ่ง': {'main': 2, 'secondary': 6, 'combinations': ['26', '62', '20', '60'], 'meaning': 'ความรวดเร็ว การหลบหนี'},
                'กระโดด': {'main': 3, 'secondary': 9, 'combinations': ['39', '93', '30', '90'], 'meaning': 'การก้าวกระโดด โอกาสใหม่'},
                'ไต่': {'main': 4, 'secondary': 7, 'combinations': ['47', '74', '40', '70'], 'meaning': 'ความมุ่งมั่น การเอาชนะอุปสรรค'},
            },
            
            # 🌿 หมวดธรรมชาติ
            'nature': {
                'ต้นไม้': {'main': 2, 'secondary': 5, 'combinations': ['25', '52', '20', '50'], 'meaning': 'การเจริญเติบโต ความอุดมสมบูรณ์'},
                'ดอกไม้': {'main': 3, 'secondary': 7, 'combinations': ['37', '73', '30', '70'], 'meaning': 'ความงาม โชคลาภ'},
                'ใบไม้': {'main': 7, 'secondary': 3, 'combinations': ['73', '37', '70', '30'], 'meaning': 'ความสดใส การเปลี่ยนแปลง'},
                'ฝน': {'main': 0, 'secondary': 6, 'combinations': ['06', '60', '00', '66'], 'meaning': 'ความอุดมสมบูรณ์ การชำระล้าง'},
                'ฟ้า': {'main': 1, 'secondary': 4, 'combinations': ['14', '41', '10', '40'], 'meaning': 'ความไร้ขีดจำกัด ความหวัง'},
                'หิน': {'main': 4, 'secondary': 8, 'combinations': ['48', '84', '40', '80'], 'meaning': 'ความแข็งแกร่ง ความมั่นคง'},
                'ลม': {'main': 6, 'secondary': 3, 'combinations': ['63', '36', '60', '30'], 'meaning': 'การเปลี่ยนแปลง พลังงานใหม่'},
                'แสงแดด': {'main': 9, 'secondary': 1, 'combinations': ['91', '19', '90', '10'], 'meaning': 'ความสว่างไสว พลังชีวิต'},
            },
            
            # 🎨 หมวดสี
            'colors': {
                'ขาว': {'main': 9, 'secondary': 0, 'combinations': ['09', '90', '19', '91'], 'meaning': 'ความบริสุทธิ์ สงบสุข'},
                'เขียว': {'main': 7, 'secondary': 3, 'combinations': ['73', '37', '03', '30'], 'meaning': 'ความเจริญงอกงาม'},
                'ดำ': {'main': 0, 'secondary': 8, 'combinations': ['08', '80', '18', '81'], 'meaning': 'ความลึกลับ พลังแห่งการป้องกัน'},
                'แดง': {'main': 5, 'secondary': 2, 'combinations': ['52', '25', '02', '20'], 'meaning': 'ความรัก พลังชีวิต'},
                'น้ำเงิน': {'main': 6, 'secondary': 4, 'combinations': ['64', '46', '06', '60'], 'meaning': 'ความสงบ การสื่อสาร'},
                'ทอง': {'main': 9, 'secondary': 1, 'combinations': ['91', '19', '99', '11'], 'meaning': 'ความมั่งคั่ง เกียรติยศ'},
                'เงิน': {'main': 8, 'secondary': 2, 'combinations': ['82', '28', '88', '22'], 'meaning': 'ความมั่งคั่งและโชคลาภ'},
            }
        }
    
    def interpret_dream(self, dream_text: str) -> Dict:
        """
        อาจารย์ AI ตีความฝันแบบเชิงลึกตามตำราโบราณไทย
        ใช้ 5-step Cognitive Workflow:
        1. Symbol Identification
        2. Contextual Analysis 
        3. Emotional Sentiment
        4. Prioritization
        5. Number Synthesis
        """
        try:
            # Normalize and fix tokenization
            if PYTHAINLP_AVAILABLE:
                dream_text = normalize(dream_text)
            fixed_text = self._fix_thai_tokenization(dream_text.lower())
            
            # STEP 1: Symbol Identification
            symbols_found = self._find_symbols(fixed_text)
            
            if not symbols_found:
                return self._handle_no_symbols_found(dream_text)
            
            # STEP 2: Contextual Analysis (คำขยาย)
            context = self._analyze_context(fixed_text)
            
            # STEP 3: Emotional Sentiment (อารมณ์)
            sentiment = self._determine_sentiment(context, symbols_found)
            
            # STEP 4: Prioritization (จัดลำดับความสำคัญ)
            prioritized_symbols = self._prioritize_symbols(symbols_found, context)
            
            # STEP 5: Number Synthesis
            predicted_numbers = self._synthesize_numbers(prioritized_symbols, context, sentiment)
            
            # Generate narrative interpretation
            interpretation = self._generate_detailed_interpretation(prioritized_symbols, context, sentiment)
            
            return {
                "interpretation": interpretation,
                "main_symbols": [symbol['name'] for symbol in prioritized_symbols[:3]],
                "sentiment": sentiment,
                "predicted_numbers": predicted_numbers
            }
            
        except Exception as e:
            self.logger.error(f"Dream interpretation error: {str(e)}")
            return self._get_fallback_response(dream_text, str(e))
    
    def _analyze_context(self, dream_text: str) -> Dict:
        """วิเคราะห์บริบทและอารมณ์ของฝัน"""
        context = {
            'emotions': [],
            'size_modifiers': [],
            'interactions': []
        }
        
        text_lower = dream_text.lower()
        
        # Analyze emotions
        for emotion, pattern in self.emotion_patterns.items():
            if re.search(pattern, text_lower):
                context['emotions'].append(emotion)
        
        # Analyze size and intensity
        for size, pattern in self.size_patterns.items():
            if re.search(pattern, text_lower):
                context['size_modifiers'].append(size)
        
        return context
    
    def _find_symbols(self, dream_text: str) -> List[Dict]:
        """ค้นหาสัญลักษณ์ในความฝัน - ปรับปรุงการตัดคำภาษาไทย"""
        symbols_found = []
        text_lower = dream_text.lower()
        
        # เพิ่มการจัดการคำที่มีปัญหาในการตัดคำ
        text_normalized = self._fix_thai_tokenization(text_lower)
        
        # Search in all categories
        for category, symbols in self.knowledge_base.items():
            for symbol_name, symbol_data in symbols.items():
                # ใช้การค้นหาแบบ exact match และ partial match
                if self._is_symbol_present(symbol_name, text_normalized):
                    # Calculate position for priority (earlier = higher priority)
                    position = text_normalized.find(symbol_name)
                    
                    symbols_found.append({
                        'name': symbol_name,
                        'category': category,
                        'data': symbol_data,
                        'position': position
                    })
        
        # Sort by position (earlier symbols first)
        symbols_found.sort(key=lambda x: x['position'])
        
        return symbols_found
    
    def _fix_thai_tokenization(self, text: str) -> str:
        """แก้ไขปัญหาการตัดคำภาษาไทย"""
        # แก้ไขคำที่มักจะถูกตัดผิด
        fixes = {
            'ย่าง': 'อย่าง',  # อย่าง -> ย่าง
            'ม่วยดี': 'มีความสุขดี',
            'ผ่อนคลาย': 'สบายใจ',
            'ข่มขู่': 'คุกคาม',
            'ร้ายแรง': 'อันตราย',
            'ป่วยไข้': 'เจ็บป่วย',
            'ท้องฟ้า': 'ฟ้า',
            'น้ำใส': 'น้ำ',
            'น้ำขุ่น': 'น้ำ'
        }
        
        text_fixed = text
        for wrong, correct in fixes.items():
            text_fixed = text_fixed.replace(wrong, correct)
        
        # เพิ่มการแก้ไขคำที่ถูกตัดผิดเป็น "ย่า"
        import re
        
        # แก้ไข "อย่าง" ที่ถูกตัดเป็น "ย่าง" 
        text_fixed = re.sub(r'\bย่าง\b', 'อย่าง', text_fixed)
        
        # แก้ไขรูปแบบอื่นๆ ที่คล้ายกัน
        common_fixes = [
            (r'\bม่วย\b', 'มี'),           # "มี" -> "ม่วย" 
            (r'\bค่วย\b', 'คิว'),          # "คิว" -> "ค่วย"
            (r'\bป่วย(?!ไข้)\b', 'ปี'),    # "ปี" -> "ป่วย" (ยกเว้น "ป่วยไข้")
            (r'\bส่วย\b', 'สี'),           # "สี" -> "ส่วย"
            (r'\bล่วย\b', 'ลี'),           # "ลี" -> "ล่วย"
            (r'\bห่วย\b', 'ห'),            # "ห" -> "ห่วย"
            (r'\bต่วย\b', 'ตี'),           # "ตี" -> "ต่วย"
        ]
        
        for pattern, replacement in common_fixes:
            text_fixed = re.sub(pattern, replacement, text_fixed)
        
        return text_fixed
    
    def _is_symbol_present(self, symbol: str, text: str) -> bool:
        """ตรวจสอบว่าสัญลักษณ์อยู่ในข้อความหรือไม่ - แบบฉลาด"""
        # Direct match
        if symbol in text:
            return True
        
        # Check for partial matches for compound symbols
        symbol_parts = symbol.split()
        if len(symbol_parts) > 1:
            # For multi-word symbols, check if all parts are present
            return all(part in text for part in symbol_parts)
        
        # Check for similar words (for single character differences)
        if len(symbol) > 2:
            import re
            # Create a pattern that allows for small variations
            pattern = re.escape(symbol)
            # Allow for one character difference
            if re.search(pattern, text):
                return True
        
        return False
    
    def _generate_interpretation(self, symbols_found: List[Dict], context: Dict) -> str:
        """สร้างคำทำนายภาพรวม"""
        if not symbols_found:
            return "ความฝันของคุณมีความหมายที่ลึกลับ แต่ยังไม่ชัดเจนในเรื่องสัญลักษณ์"
        
        primary_symbol = symbols_found[0]
        interpretation = f"การฝันเห็น{primary_symbol['name']}"
        
        # Add emotional context
        if 'fear' in context['emotions']:
            interpretation += "ในลักษณะที่น่ากลัว อาจบ่งบอกถึงความท้าทายที่กำลังจะเผชิญ"
        elif 'joy' in context['emotions']:
            interpretation += "อย่างมีความสุข เป็นลางดีที่บ่งบอกถึงโชคลาภ"
        elif 'peaceful' in context['emotions']:
            interpretation += "อย่างสงบ หมายถึงความสงบสุขในชีวิต"
        
        # Add primary meaning
        interpretation += f" {primary_symbol['data']['meaning']}"
        
        # Add secondary symbols if any
        if len(symbols_found) > 1:
            secondary_symbols = [s['name'] for s in symbols_found[1:3]]
            interpretation += f" ประกอบกับการมี{', '.join(secondary_symbols)} ยิ่งเสริมความหมายให้แข็งแกร่งขึ้น"
        
        # Add size modifiers
        if 'huge' in context['size_modifiers']:
            interpretation += " ขนาดที่ใหญ่โตบ่งบอกถึงความสำคัญและผลกระทบที่มากขึ้น"
        elif 'many' in context['size_modifiers']:
            interpretation += " จำนวนที่มากหลายบ่งบอกถึงความอุดมสมบูรณ์"
        
        return interpretation
    
    def _predict_numbers_with_reasoning(self, symbols_found: List[Dict], context: Dict) -> List[Dict]:
        """ทำนายเลขพร้อมเหตุผล"""
        predicted_numbers = []
        used_numbers = set()
        
        if not symbols_found:
            return self._get_default_numbers()
        
        primary_symbol = symbols_found[0]
        
        # Primary symbol numbers (highest confidence)
        main_combinations = primary_symbol['data']['combinations']
        for i, number in enumerate(main_combinations):
            if number not in used_numbers:
                confidence = 0.95 - (i * 0.05)  # Decreasing confidence
                predicted_numbers.append({
                    "number": number,
                    "score": round(confidence, 2),
                    "reason": f"มาจากสัญลักษณ์ '{primary_symbol['name']}' โดยตรงตามตำรา"
                })
                used_numbers.add(number)
        
        # Mixed numbers from multiple symbols
        if len(symbols_found) > 1:
            for secondary_symbol in symbols_found[1:3]:
                # Create mixed combinations
                primary_main = primary_symbol['data']['main']
                secondary_main = secondary_symbol['data']['main']
                
                mixed_combinations = [
                    f"{primary_main}{secondary_main}",
                    f"{secondary_main}{primary_main}",
                ]
                
                for number in mixed_combinations:
                    if number not in used_numbers and len(predicted_numbers) < 8:
                        confidence = 0.85 - (len(predicted_numbers) * 0.03)
                        predicted_numbers.append({
                            "number": number,
                            "score": round(confidence, 2),
                            "reason": f"ผสมจาก '{primary_symbol['name']}' และ '{secondary_symbol['name']}'"
                        })
                        used_numbers.add(number)
        
        # Context-modified numbers
        if 'fear' in context['emotions'] and len(predicted_numbers) < 8:
            # Add reversed numbers for fearful context
            for pred in predicted_numbers[:2]:
                reversed_num = pred['number'][::-1]
                if reversed_num not in used_numbers:
                    predicted_numbers.append({
                        "number": reversed_num,
                        "score": round(pred['score'] - 0.1, 2),
                        "reason": f"เลขกลับเนื่องจากบรรยากาศที่น่ากลัวในฝัน"
                    })
                    used_numbers.add(reversed_num)
        
        # Size modifiers
        if 'huge' in context['size_modifiers']:
            # Boost confidence for existing numbers
            for pred in predicted_numbers[:3]:
                pred['score'] = min(0.98, pred['score'] + 0.05)
                pred['reason'] += " (เสริมด้วยขนาดที่ใหญ่โต)"
        
        # Ensure we have at least 4 numbers
        while len(predicted_numbers) < 4:
            # Add secondary combinations from primary symbol
            symbol_data = symbols_found[0]['data']
            backup_numbers = [
                f"{symbol_data['main']}{symbol_data['main']}",
                f"{symbol_data['secondary']}{symbol_data['secondary']}",
                f"{symbol_data['main']}0",
                f"{symbol_data['secondary']}0"
            ]
            
            for number in backup_numbers:
                if number not in used_numbers and len(predicted_numbers) < 8:
                    predicted_numbers.append({
                        "number": number,
                        "score": round(0.70 - (len(predicted_numbers) * 0.02), 2),
                        "reason": f"เลขสำรองจากสัญลักษณ์ '{symbols_found[0]['name']}'"
                    })
                    used_numbers.add(number)
                    break
            else:
                break
        
        # Sort by confidence score
        predicted_numbers.sort(key=lambda x: x['score'], reverse=True)
        
        return predicted_numbers[:8]  # Return top 8 numbers
    
    def _handle_no_symbols_found(self, dream_text: str) -> Dict:
        """จัดการกรณีไม่พบสัญลักษณ์ในฝัน"""
        # Still analyze context and sentiment even without symbols
        fixed_text = self._fix_thai_tokenization(dream_text.lower())
        context = self._analyze_context(fixed_text)
        sentiment = self._determine_sentiment(context, [])
        
        # Try to find numbers in text
        numbers_in_text = re.findall(r'\b\d{1,2}\b', dream_text)
        
        if numbers_in_text:
            predicted_numbers = []
            for i, num in enumerate(numbers_in_text[:4]):
                predicted_numbers.append({
                    "number": f"{int(num):02d}",
                    "score": round(0.75 - (i * 0.05), 2),
                    "reason": f"เลขที่ปรากฏในความฝันโดยตรง"
                })
            
            # Generate interpretation based on sentiment
            if sentiment == "Negative":
                interpretation = "แม้ไม่พบสัญลักษณ์ที่ชัดเจน แต่บรรยากาศของฝันบ่งบอกถึงความกังวลหรือความท้าทาย พบตัวเลขที่น่าสนใจในฝัน ควรใช้ความระมัดระวังในการเสี่ยงโชค"
            elif sentiment == "Positive":
                interpretation = "แม้ไม่พบสัญลักษณ์ที่ชัดเจน แต่พลังงานบวกในฝันบ่งบอกถึงโชคลาภที่กำลังมา พบตัวเลขที่น่าสนใจ ลองนำไปเสี่ยงโชคดู"
            else:
                interpretation = "ไม่พบสัญลักษณ์ที่ชัดเจนในความฝัน แต่พบตัวเลขที่น่าสนใจ ลองนำเลขเหล่านี้ไปเสี่ยงโชคดู"
            
            return {
                "interpretation": interpretation,
                "main_symbols": [],
                "sentiment": sentiment,
                "predicted_numbers": predicted_numbers
            }
        
        return self._get_default_numbers(dream_text, context, sentiment)
    
    def _get_default_numbers(self, dream_text: str = "", context: Dict = None, sentiment: str = "Neutral") -> Dict:
        """เลขเริ่มต้นเมื่อไม่พบสัญลักษณ์"""
        if sentiment == "Negative":
            default_numbers = [
                {"number": "08", "score": 0.65, "reason": "เลขสำหรับความฝันที่มีความกังวล ช่วยป้องกันอันตราย"},
                {"number": "40", "score": 0.60, "reason": "เลขแห่งการเปลี่ยนแปลงจากสถานการณ์ยากลำบาก"},
                {"number": "26", "score": 0.55, "reason": "เลขแห่งการผ่านพ้นอุปสรรค"},
                {"number": "73", "score": 0.50, "reason": "เลขแห่งความเข้มแข็งในยามยาก"}
            ]
            interpretation = "ความฝันของคุณสะท้อนความกังวลหรือความท้าทายที่กำลังเผชิญ แม้ไม่พบสัญลักษณ์ที่ชัดเจน แต่บรรยากาศของฝันบ่งบอกถึงความจำเป็นที่ต้องระมัดระวัง"
        elif sentiment == "Positive":
            default_numbers = [
                {"number": "19", "score": 0.70, "reason": "เลขมงคลแห่งความสำเร็จและชัยชนะ"},
                {"number": "28", "score": 0.65, "reason": "เลขแห่งโชคลาภและความมั่งคั่ง"},
                {"number": "56", "score": 0.60, "reason": "เลขแห่งความเจริญรุ่งเรือง"},
                {"number": "91", "score": 0.55, "reason": "เลขแห่งเกียรติยศและความภาคภูมิใจ"}
            ]
            interpretation = "ความฝันของคุณเต็มไปด้วยพลังงานบวก แม้ไม่พบสัญลักษณ์ที่ชัดเจน แต่บรรยากาศดีงามนำมาซึ่งโชคลาภที่กำลังจะมาถึง"
        elif sentiment == "Mixed":
            default_numbers = [
                {"number": "15", "score": 0.75, "reason": "เลขแห่งการผจญภัยและความกล้าหาญ"},
                {"number": "48", "score": 0.70, "reason": "เลขแห่งการข้ามผ่านอุปสรรค"},
                {"number": "37", "score": 0.65, "reason": "เลขแห่งการเปลี่ยนแปลงและพัฒนา"},
                {"number": "92", "score": 0.60, "reason": "เลขแห่งความสมดุลระหว่างโชคและความท้าทาย"}
            ]
            interpretation = "ความฝันของคุณเป็นการผจญภัยที่ผสมผสานระหว่างความตื่นเต้นและความท้าทาย แม้มีอุปสรรค แต่จะนำไปสู่การเติบโตและความสำเร็จ"
        else:
            default_numbers = [
                {"number": "07", "score": 0.60, "reason": "เลขมงคลพื้นฐานสำหรับความฝันที่ไม่ชัดเจน"},
                {"number": "23", "score": 0.55, "reason": "เลขแห่งการเริ่มต้นใหม่"},
                {"number": "45", "score": 0.50, "reason": "เลขแห่งความเปลี่ยนแปลง"},
                {"number": "89", "score": 0.45, "reason": "เลขแห่งพระคุณและความศักดิ์สิทธิ์"}
            ]
            interpretation = "ความฝันของคุณมีความหมายที่ลึกลับ แม้ไม่พบสัญลักษณ์ที่ชัดเจน แต่ยังมีความหมายที่ควรใส่ใจ"
        
        return {
            "interpretation": interpretation,
            "main_symbols": [],
            "sentiment": sentiment,
            "predicted_numbers": default_numbers
        }
    
    def _get_fallback_response(self, dream_text: str, error_msg: str) -> Dict:
        """Response สำหรับกรณีเกิดข้อผิดพลาด"""
        return {
            "interpretation": "เกิดข้อผิดพลาดในการตีความฝัน กรุณาลองใหม่อีกครั้ง",
            "main_symbols": [],
            "predicted_numbers": [
                {"number": "07", "score": 0.50, "reason": "เลขสำรองเมื่อระบบมีปัญหา"}
            ],
            "error": error_msg
        }
    
    def _determine_sentiment(self, context: Dict, symbols_found: List[Dict]) -> str:
        """
        STEP 3: Determine emotional sentiment (Positive, Negative, Neutral)
        """
        emotions = context.get('emotions', [])
        negative_emotions = ['fear', 'sad', 'angry', 'aggressive', 'scary', 'losing']
        positive_emotions = ['joy', 'happy', 'peaceful', 'beautiful', 'giving', 'adventure', 'magical']
        
        # Check for mixed emotions - adventure/magical with fear
        if ('adventure' in emotions or 'magical' in emotions) and 'fear' in emotions:
            return "Mixed"  # Special case for adventure dreams with scary elements
            
        # Check for strong negative indicators
        if any(emo in negative_emotions for emo in emotions):
            return "Negative"
            
        # Check for positive indicators
        if any(emo in positive_emotions for emo in emotions):
            return "Positive"
            
        # Check symbols for inherent sentiment
        for symbol in symbols_found[:2]:  # Check top 2 symbols
            symbol_name = symbol['name']
            # Negative symbols
            if any(neg in symbol_name for neg in ['สีดำ', 'ไฟ', 'เลือด', 'ตาย', 'สัตว์ประหลาด', 'ปีศาจ']):
                return "Negative"
            # Positive symbols  
            if any(pos in symbol_name for pos in ['สีขาว', 'ทอง', 'พระ', 'เงิน', 'บิน', 'บินได้']):
                return "Positive"
            # Adventure symbols
            if any(adv in symbol_name for adv in ['มหาสมุทร', 'เกาะ', 'ข้าม']):
                return "Positive"
                
        return "Neutral"
    
    def _prioritize_symbols(self, symbols_found: List[Dict], context: Dict) -> List[Dict]:
        """
        STEP 4: Prioritize symbols based on narrative importance
        """
        for symbol in symbols_found:
            priority_score = symbol.get('confidence', 0.5)
            
            # Boost priority for symbols with strong emotional context
            emotions = context.get('emotions', [])
            if any(emo in ['fear', 'joy', 'aggressive'] for emo in emotions):
                if symbol['name'] in ['งู', 'เสือ', 'ไฟ']:  # Active/dangerous symbols
                    priority_score += 0.2
                    
            # Boost for size modifiers
            if any(mod in ['huge', 'big', 'many'] for mod in context.get('size_modifiers', [])):
                priority_score += 0.1
                
            symbol['priority_score'] = priority_score
            
        # Sort by priority score
        return sorted(symbols_found, key=lambda x: x.get('priority_score', 0), reverse=True)
    
    def _synthesize_numbers(self, symbols: List[Dict], context: Dict, sentiment: str) -> List[Dict]:
        """
        STEP 5: Intelligent number synthesis based on symbols, context, and emotion
        """
        predicted_numbers = []
        used_numbers = set()
        
        if not symbols:
            return [
                {"number": "07", "score": 0.60, "reason": "เลขมงคลพื้นฐานสำหรับความฝันที่ไม่ชัดเจน"},
                {"number": "23", "score": 0.55, "reason": "เลขแห่งการเริ่มต้นใหม่"}
            ]
            
        primary_symbol = symbols[0]
        
        # Start with primary symbol's base numbers
        base_combinations = primary_symbol['data']['combinations']
        
        # Modify based on sentiment
        if sentiment == "Negative":
            # For negative dreams, prioritize higher numbers or reverse combinations
            for i, num in enumerate(base_combinations):
                if num not in used_numbers:
                    score = 0.95 - (i * 0.1)
                    # Boost numbers with 8, 0 for negative energy
                    if '8' in num or '0' in num:
                        score += 0.05
                    predicted_numbers.append({
                        "number": num,
                        "score": round(score, 2),
                        "reason": f"จากสัญลักษณ์ '{primary_symbol['name']}' ในบริบทเชิงลบ ส่งผลให้เลข {num} มีพลังงานที่ต้องระวัง"
                    })
                    used_numbers.add(num)
                    
        elif sentiment == "Positive":
            # For positive dreams, prioritize auspicious combinations
            for i, num in enumerate(base_combinations):
                if num not in used_numbers:
                    score = 0.98 - (i * 0.05)  # Higher confidence for positive
                    # Boost numbers with 9, 1, 2 for positive energy
                    if any(d in num for d in ['9', '1', '2']):
                        score += 0.02
                    predicted_numbers.append({
                        "number": num,
                        "score": round(score, 2),
                        "reason": f"จากสัญลักษณ์ '{primary_symbol['name']}' ในบริบทเชิงบวก นำมาซึ่งความมงคลผ่านเลข {num}"
                    })
                    used_numbers.add(num)
        else:
            # Neutral sentiment
            for i, num in enumerate(base_combinations):
                if num not in used_numbers:
                    score = 0.85 - (i * 0.08)
                    predicted_numbers.append({
                        "number": num,
                        "score": round(score, 2),
                        "reason": f"เลข {num} มาจากสัญลักษณ์หลัก '{primary_symbol['name']}' ตามตำราโบราณ"
                    })
                    used_numbers.add(num)
        
        # Add combination numbers from multiple symbols
        if len(symbols) > 1:
            secondary_symbol = symbols[1]
            primary_main = str(primary_symbol['data']['main'])
            secondary_main = str(secondary_symbol['data']['main'])
            
            # Create combination
            combo1 = f"{primary_main}{secondary_main}"
            combo2 = f"{secondary_main}{primary_main}"
            
            for combo in [combo1, combo2]:
                if combo not in used_numbers and len(predicted_numbers) < 8:
                    score = 0.80 if sentiment == "Positive" else 0.70
                    predicted_numbers.append({
                        "number": f"{int(combo):02d}",
                        "score": round(score, 2),
                        "reason": f"ผสมเลขจาก '{primary_symbol['name']}' และ '{secondary_symbol['name']}' สะท้อนการมีสัญลักษณ์หลายตัวในฝัน"
                    })
                    used_numbers.add(combo)
        
        # Sort by score and return top results
        predicted_numbers.sort(key=lambda x: x['score'], reverse=True)
        return predicted_numbers[:8]
    
    def _generate_detailed_interpretation(self, symbols: List[Dict], context: Dict, sentiment: str) -> str:
        """
        Generate detailed narrative interpretation
        """
        if not symbols:
            return "ความฝันของคุณมีความหมายที่ลึกลับ แต่ยังไม่ชัดเจนในเรื่องสัญลักษณ์"
            
        primary_symbol = symbols[0]
        interpretation = f"การฝันเห็น{primary_symbol['name']}"
        
        # Add contextual descriptors
        emotions = context.get('emotions', [])
        size_mods = context.get('size_modifiers', [])
        
        if 'fear' in emotions or sentiment == "Negative":
            if 'big' in size_mods or 'huge' in size_mods:
                interpretation += "ขนาดใหญ่ในลักษณะที่น่ากลัว"
            else:
                interpretation += "ในลักษณะที่น่าหวาดเสียว"
            interpretation += " เป็นสัญญาณเตือนถึงอุปสรรคหรือความท้าทายที่กำลังจะเผชิญ"
            
        elif 'joy' in emotions or 'beautiful' in emotions or sentiment == "Positive":
            if 'big' in size_mods or 'huge' in size_mods:
                interpretation += "ขนาดใหญ่อย่างสง่างาม"
            else:
                interpretation += "อย่างสวยงาม"
            interpretation += " เป็นลางดีที่บ่งบอกถึงโชคลาภและความสำเร็จที่กำลังจะมาถึง"
            
        else:  # Neutral
            interpretation += " มีความหมายตามตำราโบราณว่า"
            
        # Add symbol meaning
        interpretation += f" {primary_symbol['data']['meaning']}"
        
        # Add secondary symbols context
        if len(symbols) > 1:
            secondary_names = [s['name'] for s in symbols[1:3]]
            interpretation += f" ประกอบกับการมี{', '.join(secondary_names)} ในฝันเดียวกัน ยิ่งเสริมความหมายให้แข็งแกร่งขึ้น"
            
        # Add final sentiment conclusion
        if sentiment == "Positive":
            interpretation += " โดยรวมแล้วเป็นฝันที่นำมาซึ่งความมงคลและโชคลาภ"
        elif sentiment == "Negative":
            interpretation += " ควรระมัดระวังและเตรียมพร้อมรับมือกับสิ่งท้าทายที่อาจเกิดขึ้น"
        else:
            interpretation += " เป็นฝันที่มีความหมายเป็นกลาง ควรสังเกตเหตุการณ์ที่จะเกิดขึ้น"
            
        return interpretation
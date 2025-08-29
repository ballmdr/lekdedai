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
            'fear': r'กลัว|ตกใจ|หนี|วิ่งหนี|เสียงใส|น่ากลัว|ขนหัวลุก|ย่างกลัว|ย่างน่ากลัว|เก็บตัว',
            'joy': r'ดีใจ|สุข|หัวเราะ|ยิ้ม|มีความสุข|สนุก|เพลิน|ม่วยดี|มีความ.*สุข|ร่าเริง',
            'peaceful': r'สงบ|เงียบ|สงบสุข|ชื่นใจ|สบายใจ|ผ่อนคลาย|สงบสุข|ย่างสงบ|ย่างสบาย',
            'aggressive': r'ไล่|กัด|โจมตี|ทำร้าย|ต่อสู้|รุกราน|ข่มขู่|ขู่|รุนแรง|ร้ายแรง|ย่างดุ',
            'protective': r'คุ้มครอง|ปกป้อง|ช่วย|ดูแล|เฝ้า|รักษา|ดูแลรักษา|ย่างดี|ใจดี',
            'giving': r'ให้|มอบ|แจก|ประทาน|อวยพร|ส่งมอบ|แบ่งปัน|ย่างใจดี|ย่างดี',
            'losing': r'หาย|สูญ|เสีย|หล่น|ตก|ขาด|พลัด|สูญหาย|ย่างเสียใจ'
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
        """
        try:
            # Normalize text
            if PYTHAINLP_AVAILABLE:
                dream_text = normalize(dream_text)
            
            # Extract context and emotions
            context = self._analyze_context(dream_text)
            
            # Find symbols in the dream
            symbols_found = self._find_symbols(dream_text)
            
            if not symbols_found:
                return self._handle_no_symbols_found(dream_text)
            
            # Generate interpretation
            interpretation = self._generate_interpretation(symbols_found, context)
            
            # Predict numbers with reasoning
            predicted_numbers = self._predict_numbers_with_reasoning(symbols_found, context)
            
            return {
                "interpretation": interpretation,
                "main_symbols": [symbol['name'] for symbol in symbols_found],
                "predicted_numbers": predicted_numbers,
                "context_analysis": context,
                "timestamp": datetime.now().isoformat()
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
            
            return {
                "interpretation": "ไม่พบสัญลักษณ์ที่ชัดเจนในความฝัน แต่พบตัวเลขที่น่าสนใจ ลองนำเลขเหล่านี้ไปเสี่ยงโชคดู",
                "main_symbols": [],
                "predicted_numbers": predicted_numbers
            }
        
        return self._get_default_numbers()
    
    def _get_default_numbers(self) -> Dict:
        """เลขเริ่มต้นเมื่อไม่พบสัญลักษณ์"""
        default_numbers = [
            {"number": "07", "score": 0.60, "reason": "เลขมงคลพื้นฐานสำหรับความฝันที่ไม่ชัดเจน"},
            {"number": "23", "score": 0.55, "reason": "เลขแห่งการเริ่มต้นใหม่"},
            {"number": "45", "score": 0.50, "reason": "เลขแห่งความเปลี่ยนแปลง"},
            {"number": "89", "score": 0.45, "reason": "เลขแห่งพระคุณและความศักดิ์สิทธิ์"}
        ]
        
        return {
            "interpretation": "ความฝันของคุณมีความหมายที่ลึกลับ แม้ไม่พบสัญลักษณ์ที่ชัดเจน แต่ยังมีพลังงานบวกที่ควรใส่ใจ",
            "main_symbols": [],
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
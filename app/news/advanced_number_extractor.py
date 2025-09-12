import re
from typing import Dict, List, Tuple

class AdvancedNumberExtractor:
    """ระบบวิเคราะห์เลขเชิงลึกสำหรับข่าว - Post-processing"""
    
    def __init__(self):
        # เลขสำคัญในวัฒนธรรมไทย
        self.cultural_numbers = {
            'เก้า': '9', 'เก้าห่อ': '99', 'เก้าเหลี่ยม': '9',
            'แปด': '8', 'แปดแสน': '8', 'แปดล้าน': '8',
            'เจ็ด': '7', 'เจ็ดสี': '7',
            'หก': '6', 'หกจบ': '6',
            'ห้า': '5', 'ห้าดาว': '5',
            'สี่': '4', 'สี่แยก': '4',
            'สาม': '3', 'สามก๊ก': '3',
            'สอง': '2', 'สองคู่': '22',
            'หนึ่ง': '1', 'หนึ่งเดียว': '1',
            'ศูนย์': '0', 'ห่วง': '0'
        }
        
        # คำที่บ่งบอกเลข 2 หลัก
        self.double_digit_clues = {
            'คู่': lambda x: f"{x}{x}",  # เลข 5 คู่ = 55
            'ซ้อน': lambda x: f"{x}{x}",
            'เป็นคู่': lambda x: f"{x}{x}"
        }
        
        # รูปแบบเลขที่ซ่อนอยู่
        self.hidden_patterns = {
            # นายกคนที่ 23 → 23
            'position_number': r'คนที่\s*([0-9]{1,3})',
            
            # Mercedes ทะเบียน พร 195 → พร = ป+ร = 16+23 = 39, หรือใช้ 195
            'license_advanced': r'([ก-ฮ]+)\s*([0-9]+)',
            
            # 09.09 น. → 9, 99, 909
            'time_variations': r'([0-9]{2})\.([0-9]{2})',
            
            # คดีชั้น 14 → 14, 41 (กลับหลัก)
            'reverse_numbers': r'ชั้น\s*([0-9]+)',
            
            # จำคุก 1 ปี → 1, 10, 01
            'year_variations': r'([0-9]+)\s*ปี',
            
            # 5 คัน → 5, 50, 05
            'count_variations': r'([0-9]+)\s*คัน'
        }
    
    def extract_advanced_numbers(self, title: str, content: str, basic_numbers: List[str]) -> Dict:
        """วิเคราะห์เลขเชิงลึกเพิ่มเติม"""
        
        full_text = f"{title} {content}"
        advanced_numbers = []
        explanations = []
        
        # 1. แปลงเลขภาษาไทยเป็นตัวเลข
        thai_numbers = self._extract_thai_numbers(full_text)
        if thai_numbers:
            advanced_numbers.extend(thai_numbers)
            explanations.append(f"เลขภาษาไทย: {', '.join(thai_numbers)}")
        
        # 2. หาเลขจากรูปแบบซ่อน
        hidden_numbers = self._extract_hidden_patterns(full_text)
        if hidden_numbers:
            advanced_numbers.extend(hidden_numbers)
            explanations.append(f"เลขที่ซ่อนอยู่: {', '.join(hidden_numbers)}")
        
        # 3. สร้างเลขจากการผสมผสาน
        combination_numbers = self._create_combinations(basic_numbers + advanced_numbers)
        if combination_numbers:
            advanced_numbers.extend(combination_numbers)
            explanations.append(f"เลขผสมผสาน: {', '.join(combination_numbers)}")
        
        # 4. เลขพิเศษจากบริบท
        context_numbers = self._extract_context_numbers(full_text)
        if context_numbers:
            advanced_numbers.extend(context_numbers)
            explanations.append(f"เลขจากบริบท: {', '.join(context_numbers)}")
        
        # ลบซ้ำและเรียง
        unique_numbers = list(dict.fromkeys(advanced_numbers))
        
        return {
            'advanced_numbers': unique_numbers[:15],  # จำกัด 15 เลข
            'explanations': explanations,
            'total_found': len(unique_numbers)
        }
    
    def _extract_thai_numbers(self, text: str) -> List[str]:
        """แปลงเลขภาษาไทยเป็นตัวเลข"""
        found = []
        
        for thai_word, number in self.cultural_numbers.items():
            if thai_word in text:
                found.append(number)
                
                # สร้างเลขเพิ่มเติม
                if len(number) == 1:
                    found.append(f"0{number}")  # 9 → 09
                    found.append(f"{number}0")  # 9 → 90
        
        return found
    
    def _extract_hidden_patterns(self, text: str) -> List[str]:
        """หาเลขจากรูปแบบที่ซ่อนอยู่"""
        found = []
        
        # ตำแหน่ง (คนที่ 23)
        positions = re.findall(self.hidden_patterns['position_number'], text)
        for pos in positions:
            found.append(pos)
            if len(pos) == 1:
                found.append(f"0{pos}")
        
        # ทะเบียนรถขั้นสูง
        licenses = re.findall(self.hidden_patterns['license_advanced'], text)
        for thai_chars, numbers in licenses:
            found.append(numbers[-2:])  # เอา 2 หลักท้าย
            if len(numbers) >= 3:
                found.append(numbers[-3:])  # เอา 3 หลักท้าย
        
        # เวลาแบบขั้นสูง (09.09)
        times = re.findall(self.hidden_patterns['time_variations'], text)
        for hour, minute in times:
            found.append(hour.lstrip('0') or '0')  # 09 → 9
            found.append(minute.lstrip('0') or '0')  # 09 → 9
            found.append(f"{hour.lstrip('0') or '0'}{minute.lstrip('0') or '0'}")  # 99
        
        # เลขกลับหลัก
        reverse_nums = re.findall(self.hidden_patterns['reverse_numbers'], text)
        for num in reverse_nums:
            found.append(num)
            found.append(num[::-1])  # กลับหลัก 14 → 41
        
        return found
    
    def _create_combinations(self, numbers: List[str]) -> List[str]:
        """สร้างเลขจากการผสมผสาน"""
        combinations = []
        
        # รวมเลข 2 ตัวแรก
        if len(numbers) >= 2:
            try:
                num1 = int(numbers[0]) if numbers[0].isdigit() else 0
                num2 = int(numbers[1]) if numbers[1].isdigit() else 0
                
                # บวกกัน
                sum_result = (num1 + num2) % 100
                combinations.append(f"{sum_result:02d}")
                
                # ลบกัน
                diff_result = abs(num1 - num2)
                if diff_result < 100:
                    combinations.append(f"{diff_result:02d}")
                    
            except ValueError:
                pass
        
        return combinations
    
    def _extract_context_numbers(self, text: str) -> List[str]:
        """หาเลขจากบริบทพิเศษ"""
        context_numbers = []
        
        # เลขจากชื่อคน (ทักษิณ → ท=18, ก=1, ษ=32, ิ=34, ณ=28)
        if 'ทักษิณ' in text:
            context_numbers.extend(['18', '01', '32', '28'])
        
        # เลขจากสถานที่ (ศาลฎีกา → ศ=35, า=38, ล=26)
        if 'ศาลฎีกา' in text:
            context_numbers.extend(['35', '38', '26'])
        
        # เลขมงคลจากเหตุการณ์
        if any(word in text for word in ['ชัยชนะ', 'ชนะ', 'สำเร็จ']):
            context_numbers.extend(['88', '99', '77'])
        
        if any(word in text for word in ['คุก', 'จำคุก', 'โทษ']):
            context_numbers.extend(['13', '31', '04'])
        
        return context_numbers
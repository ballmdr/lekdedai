import re
from collections import Counter

class NewsAnalyzer:
    """วิเคราะห์หาเลขจากข่าว"""
    
    def __init__(self):
        # คำสำคัญและเลขที่เกี่ยวข้อง
        self.keyword_numbers = {
            'ตาย': ['07', '70', '04', '40'],
            'เกิด': ['12', '21', '01', '10'],
            'รถ': ['18', '81', '54', '45'],
            'บ้าน': ['14', '41', '16', '61'],
            'เงิน': ['28', '82', '26', '62'],
            'ทอง': ['39', '93', '29', '92'],
            'น้ำ': ['09', '90', '19', '91'],
            'ไฟ': ['17', '71', '27', '72'],
            'ต้นไม้': ['38', '83', '48', '84'],
            'พระ': ['23', '32', '33'],
            'แม่': ['15', '51', '50'],
            'พ่อ': ['25', '52', '20'],
        }
    
    def analyze_article(self, article):
        """วิเคราะห์บทความข่าว"""
        text = f"{article.title} {article.content}".lower()
        
        found_numbers = []
        keywords_found = []
        confidence = 50  # เริ่มต้นที่ 50%
        
        # 1. หาเลขที่ปรากฏในข่าว
        direct_numbers = self.extract_direct_numbers(text)
        found_numbers.extend(direct_numbers)
        
        # 2. หาเลขจากคำสำคัญ
        keyword_numbers, keywords = self.extract_keyword_numbers(text)
        found_numbers.extend(keyword_numbers)
        keywords_found.extend(keywords)
        
        # 3. หาทะเบียนรถ
        plate_numbers = self.extract_plate_numbers(text)
        found_numbers.extend(plate_numbers)
        if plate_numbers:
            confidence += 10
        
        # 4. หาเลขบ้าน
        house_numbers = self.extract_house_numbers(text)
        found_numbers.extend(house_numbers)
        if house_numbers:
            confidence += 5
        
        # 5. ลบเลขซ้ำและจัดเรียง
        unique_numbers = self.process_numbers(found_numbers)
        
        # 6. คำนวณความน่าเชื่อถือ
        if len(unique_numbers) > 0:
            confidence = min(confidence + (len(keywords_found) * 5), 95)
        
        return {
            'numbers': unique_numbers[:15],  # จำกัดไม่เกิน 15 เลข
            'keywords': keywords_found,
            'confidence': confidence
        }
    
    def extract_direct_numbers(self, text):
        """หาเลข 2-3 หลักที่ปรากฏตรงๆ"""
        # หาเลข 2-3 หลัก
        numbers = re.findall(r'\b\d{2,3}\b', text)
        
        # กรองเลขที่น่าสนใจ (ไม่เอาปี พ.ศ. หรือ ค.ศ.)
        filtered = []
        for num in numbers:
            if len(num) == 2:
                filtered.append(num)
            elif len(num) == 3 and not (num.startswith('25') or num.startswith('20') or num.startswith('19')):
                filtered.append(num)
                # แยกเป็นเลข 2 ตัวด้วย
                filtered.append(num[:2])
                filtered.append(num[1:])
        
        return filtered
    
    def extract_keyword_numbers(self, text):
        """หาเลขจากคำสำคัญ"""
        numbers = []
        keywords = []
        
        for keyword, nums in self.keyword_numbers.items():
            if keyword in text:
                numbers.extend(nums)
                keywords.append(keyword)
        
        return numbers, keywords
    
    def extract_plate_numbers(self, text):
        """หาเลขจากทะเบียนรถ"""
        numbers = []
        
        # รูปแบบทะเบียนรถไทย
        patterns = [
            r'[0-9ก-ฮ]{2}\s*[-]?\s*(\d{2,4})',  # กข-1234
            r'(\d{1,2})\s*[ก-ฮ]{2}\s*(\d{2,4})',  # 1กข 1234
            r'ทะเบียน\s*(\d{2,4})',  # ทะเบียน 1234
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    for m in match:
                        if m and m.isdigit():
                            if len(m) <= 3:
                                numbers.append(m.zfill(2))
                            else:
                                numbers.append(m[:2])
                                numbers.append(m[-2:])
                else:
                    if len(match) <= 3:
                        numbers.append(match.zfill(2))
        
        return numbers
    
    def extract_house_numbers(self, text):
        """หาเลขบ้าน"""
        numbers = []
        
        patterns = [
            r'บ้านเลขที่\s*(\d{1,3})',
            r'เลขที่\s*(\d{1,3})',
            r'หมู่\s*(\d{1,2})',
            r'ซอย\s*(\d{1,2})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) <= 2:
                    numbers.append(match.zfill(2))
                elif len(match) == 3:
                    numbers.append(match[:2])
                    numbers.append(match[-2:])
        
        return numbers
    
    def process_numbers(self, numbers):
        """ประมวลผลและจัดเรียงเลข"""
        # นับความถี่
        counter = Counter(numbers)
        
        # เรียงตามความถี่
        sorted_numbers = sorted(counter.items(), key=lambda x: x[1], reverse=True)
        
        # คืนเฉพาะเลข (ไม่เอาความถี่)
        return [num for num, count in sorted_numbers]
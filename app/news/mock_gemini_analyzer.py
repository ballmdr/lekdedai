import re
import random
from typing import Dict, List

class MockGeminiLotteryAnalyzer:
    """Mock Gemini Analyzer สำหรับทดสอบโดยไม่ใช้ API จริง"""
    
    def __init__(self):
        # รูปแบบข่าวที่เกี่ยวข้องกับหวย
        self.relevant_keywords = [
            # อุบัติเหตุ
            'อุบัติเหตุ', 'รถชน', 'ชนกัน', 'ไฟไหม้', 'ตาย', 'เสียชีวิต', 'บาดเจ็บ',
            # คนดัง/การเมือง  
            'ดารา', 'นักร้อง', 'นักแสดง', 'นายก', 'รัฐมนตรี', 'ศาล', 'คดี',
            # เศรษฐกิจ
            'หุ้น', 'ทอง', 'ราคา', 'ล้าน', 'บาท', 'ดอลลาร์',
            # อาชญากรรม
            'ฆ่า', 'โจร', 'ข่มขืน', 'ยาเสพติด', 'จับ', 'ตำรวจ'
        ]
        
        self.irrelevant_keywords = [
            'ผลไม้', 'สุขภาพ', 'อาหาร', 'ท่องเที่ยว', 'เทคโนโลยี',
            'สปอร์ต', 'ฟุตบอล', 'กีฬา'
        ]
        
    def is_lottery_relevant(self, title: str, content: str) -> bool:
        """เช็คความเกี่ยวข้องด้วย keyword matching"""
        text = (title + ' ' + content).lower()
        
        # ถ้ามี keyword ที่ไม่เกี่ยวข้อง
        for keyword in self.irrelevant_keywords:
            if keyword in text:
                return False
                
        # ถ้ามี keyword ที่เกี่ยวข้อง
        for keyword in self.relevant_keywords:
            if keyword in text:
                return True
                
        return False
        
    def analyze_news_for_lottery(self, title: str, content: str) -> Dict:
        """Mock การวิเคราะห์เลขจากข่าว"""
        
        text = title + ' ' + content
        numbers = []
        detailed_numbers = []
        
        # หาเลขโดยตรง
        # อายุ
        age_matches = re.findall(r'อายุ\s*(\d{1,3})\s*ปี|(\d{1,3})\s*ขวบ', text)
        for match in age_matches:
            age = match[0] or match[1]
            if age:
                numbers.append(age.zfill(2))
                detailed_numbers.append({
                    'number': age.zfill(2),
                    'source': f'อายุ {age} ปี',
                    'confidence': 90
                })
        
        # ทะเบียนรถ
        plate_matches = re.findall(r'ทะเบียน\s*([ก-ฮ\s]*)\s*(\d+)', text)
        for match in plate_matches:
            plate_num = match[1]
            if len(plate_num) >= 2:
                # แยกเป็นเลข 2 หลัก
                for i in range(len(plate_num) - 1):
                    num = plate_num[i:i+2]
                    numbers.append(num)
                    detailed_numbers.append({
                        'number': num,
                        'source': f'ทะเบียน {match[0]} {plate_num}',
                        'confidence': 85
                    })
        
        # เวลา
        time_matches = re.findall(r'(\d{1,2})\.(\d{2})\s*น\.|(\d{1,2}):(\d{2})', text)
        for match in time_matches:
            hour = match[0] or match[2]
            minute = match[1] or match[3]
            if hour and minute:
                numbers.extend([hour.zfill(2), minute])
                detailed_numbers.extend([
                    {'number': hour.zfill(2), 'source': f'เวลา {hour}.{minute} น.', 'confidence': 75},
                    {'number': minute, 'source': f'เวลา {hour}.{minute} น.', 'confidence': 75}
                ])
        
        # หมายเลขคดี
        case_matches = re.findall(r'คดี.*?(\d+)|ชั้น\s*(\d+)', text)
        for match in case_matches:
            case_num = match[0] or match[1]
            if case_num:
                numbers.append(case_num.zfill(2))
                detailed_numbers.append({
                    'number': case_num.zfill(2),
                    'source': f'หมายเลขคดี/ชั้น {case_num}',
                    'confidence': 80
                })
        
        # จำนวนเงิน
        money_matches = re.findall(r'(\d+)\s*ล้าน|(\d+)\s*แสน|(\d+)\s*บาท', text)
        for match in money_matches:
            amount = match[0] or match[1] or match[2]
            if amount and len(amount) <= 3:
                if len(amount) >= 2:
                    numbers.append(amount[-2:])  # เอา 2 หลักท้าย
                    detailed_numbers.append({
                        'number': amount[-2:],
                        'source': f'จำนวนเงิน {amount}',
                        'confidence': 70
                    })
        
        # เลขทั่วไป
        general_numbers = re.findall(r'\b(\d{2,3})\b', text)
        for num in general_numbers[:5]:  # เอาแค่ 5 ตัวแรก
            if num not in [item['number'] for item in detailed_numbers]:
                # เช็คว่าไม่ใช่ปี
                if not (num.startswith('25') or num.startswith('20')):
                    numbers.append(num[-2:] if len(num) > 2 else num.zfill(2))
                    detailed_numbers.append({
                        'number': num[-2:] if len(num) > 2 else num.zfill(2),
                        'source': f'เลขที่พบในข่าว: {num}',
                        'confidence': 50
                    })
        
        # ลบเลขซ้ำ
        unique_numbers = list(dict.fromkeys(numbers))
        
        # คำนวณคะแนน
        relevance_score = 0
        category = 'other'
        
        if any(kw in text.lower() for kw in ['อุบัติเหตุ', 'รถชน', 'ไฟไหม้', 'ตาย']):
            relevance_score = 95
            category = 'accident'
        elif any(kw in text.lower() for kw in ['ดารา', 'นักร้อง', 'คนดัง']):
            relevance_score = 85
            category = 'celebrity'  
        elif any(kw in text.lower() for kw in ['นายก', 'รัฐมนตรี', 'การเมือง']):
            relevance_score = 80
            category = 'politics'
        elif any(kw in text.lower() for kw in ['หุ้น', 'ทอง', 'ราคา']):
            relevance_score = 75
            category = 'economic'
        else:
            relevance_score = 60
            
        # ปรับคะแนนตามจำนวนเลข
        if len(unique_numbers) > 5:
            relevance_score += 10
        elif len(unique_numbers) < 2:
            relevance_score -= 20
            
        return {
            'success': True,
            'is_relevant': relevance_score >= 60 and len(unique_numbers) > 0,
            'category': category,
            'relevance_score': min(relevance_score, 100),
            'numbers': unique_numbers[:15],
            'detailed_numbers': detailed_numbers,
            'reasoning': f'พบ {len(unique_numbers)} เลขจากข่าวประเภท {category}'
        }
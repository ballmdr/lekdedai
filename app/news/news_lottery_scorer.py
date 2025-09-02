import re
from typing import Dict, List, Tuple

class NewsLotteryScorer:
    """ระบบให้คะแนนข่าวสำหรับเลขเด็ดหวย"""
    
    def __init__(self):
        """กำหนดคำสำคัญและรูปแบบการให้คะแนน"""
        
        # 🔥 คำสำคัญข่าวอุบัติเหตุ (90-100 คะแนน)
        self.accident_keywords = [
            'อุบัติเหตุ', 'รถชน', 'ชนกัน', 'ชนท้าย', 'รถเสีย', 'รถพัง',
            'ไฟไหม้', 'เพลิงไหม้', 'ลุกเป็นไฟ', 'ไฟคลอก',
            'จมน้ำ', 'จมทะเล', 'จมแม่น้ำ', 'จมลง', 'ดิ่งลง',
            'ตาย', 'เสียชีวิต', 'ศพ', 'มรณกรรม', 'เหตุร้าย',
            'บาดเจ็บ', 'เจ็บสาหัส', 'รพ.', 'โรงพยาบาล',
            'เคราะห์ร้าย', 'โชคร้าย', 'ชิงชะตา'
        ]
        
        # ⭐ คำสำคัญข่าวคนดัง (80-90 คะแนน)  
        self.celebrity_keywords = [
            'ดารา', 'นักร้อง', 'นักแสดง', 'ศิลปิน', 'เซเลบ',
            'แต่งงาน', 'หย่า', 'คลอดลูก', 'เกิด', 'วันเกิด',
            'อายุ', 'ปี', 'ขวบ', 'ชันษา', 'ครบ', 'เฉลิมฉลอง',
            'รางวัล', 'ได้รับรางวัล', 'ชนะ', 'แชมป์',
            'ความรัก', 'คบกัน', 'เดท', 'มีลูก'
        ]
        
        # 📊 คำสำคัญข่าวเศรษฐกิจ (70-80 คะแนน)
        self.economic_keywords = [
            'ราคาทอง', 'ทองคำ', 'ทอง', 'บาทละ', 'บาทต่อหน่วย',
            'น้ำมัน', 'เบนซิน', 'ดีเซล', 'แก๊ส', 'แอลพีจี',
            'หุ้น', 'ดัชนี', 'SET', 'mai', 'ตลาดหุ้น',
            'ดอลลาร์', 'บาท', 'แลกเปลี่ยน', 'อัตราแลก',
            'เงินเฟ้อ', 'ดอกเบี้ย', 'เงินฝาก', 'กู้เงิน',
            'ราคา', 'ขึ้น', 'ลง', 'เพิ่ม', 'ลด', 'ปรับ'
        ]
        
        # 📰 คำสำคัญข่าวทั่วไป (40-60 คะแนน)
        self.general_keywords = [
            'การเมือง', 'รัฐบาล', 'ประชุม', 'สภา',
            'กีฬา', 'ฟุตบอล', 'สกอร์', 'แข่ง',
            'สุขภาพ', 'โควิด', 'วัคซีน', 'ป่วย',
            'ท่องเที่ยว', 'เที่ยว', 'โรงแรม', 'เทศกาล'
        ]
        
        # รูปแบบเลขที่สำคัญ
        self.number_patterns = {
            'license_plate': r'[ก-ฮ]{0,2}\s*[0-9]{2,4}|ทะเบียน\s*[0-9]{2,4}',
            'house_number': r'บ้านเลขที่\s*([0-9]{1,4})|เลขที่\s*([0-9]{1,4})',
            'age': r'อายุ\s*([0-9]{1,3})\s*ปี|([0-9]{1,3})\s*ขวบ',
            'date': r'([0-9]{1,2})\s*\/\s*([0-9]{1,2})\s*\/\s*([0-9]{2,4})',
            'time': r'([0-9]{1,2}):([0-9]{2})',
            'money': r'([0-9,]+)\s*บาท|([0-9,]+)\s*ล้าน',
            'general_numbers': r'\b([0-9]{2,3})\b'
        }
    
    def score_news_article(self, title: str, content: str) -> Dict:
        """
        ให้คะแนนข่าวตามความเหมาะสมสำหรับหวย
        
        Args:
            title: หัวข้อข่าว
            content: เนื้อหาข่าว
            
        Returns:
            Dict: {'score': int, 'category': str, 'extracted_numbers': List, 'confidence_details': Dict}
        """
        
        full_text = f"{title} {content}".lower()
        
        # วิเคราะห์หมวดหมู่และคะแนน
        category_scores = self._analyze_categories(full_text)
        
        # หาหมวดหมู่ที่ได้คะแนนสูงสุด
        best_category, base_score = max(category_scores.items(), key=lambda x: x[1])
        
        # สกัดเลขที่สำคัญ
        extracted_numbers = self._extract_important_numbers(full_text, best_category)
        
        # ปรับคะแนนตามจำนวนเลขที่ได้
        final_score = self._calculate_final_score(base_score, extracted_numbers, best_category)
        
        return {
            'score': final_score,
            'category': best_category,
            'extracted_numbers': extracted_numbers,
            'confidence_details': {
                'category_scores': category_scores,
                'base_score': base_score,
                'number_bonus': len(extracted_numbers) * 5,
                'reasoning': self._get_scoring_reason(best_category, len(extracted_numbers))
            }
        }
    
    def _analyze_categories(self, text: str) -> Dict[str, int]:
        """วิเคราะห์หมวดหมู่ข่าวและให้คะแนนพื้นฐาน"""
        
        scores = {
            'accident': 0,
            'celebrity': 0, 
            'economic': 0,
            'general': 0
        }
        
        # ตรวจสอบคำสำคัญอุบัติเหตุ
        for keyword in self.accident_keywords:
            if keyword in text:
                scores['accident'] += 10
                
        # ตรวจสอบคำสำคัญคนดัง
        for keyword in self.celebrity_keywords:
            if keyword in text:
                scores['celebrity'] += 8
                
        # ตรวจสอบคำสำคัญเศรษฐกิจ
        for keyword in self.economic_keywords:
            if keyword in text:
                scores['economic'] += 7
                
        # ตรวจสอบคำสำคัญทั่วไป
        for keyword in self.general_keywords:
            if keyword in text:
                scores['general'] += 5
        
        # แปลงเป็นคะแนนจริง
        final_scores = {}
        if scores['accident'] > 0:
            final_scores['accident'] = min(90 + scores['accident'], 100)
        if scores['celebrity'] > 0:
            final_scores['celebrity'] = min(80 + scores['celebrity'], 90)
        if scores['economic'] > 0:
            final_scores['economic'] = min(70 + scores['economic'], 80)
        if scores['general'] > 0:
            final_scores['general'] = min(40 + scores['general'], 60)
            
        # ถ้าไม่มีหมวดหมู่ใดเลย ให้คะแนนพื้นฐาน
        if not final_scores:
            final_scores['general'] = 30
            
        return final_scores
    
    def _extract_important_numbers(self, text: str, category: str) -> List[Dict]:
        """สกัดเลขที่สำคัญตามหมวดหมู่"""
        
        extracted = []
        
        # สกัดตามรูปแบบต่างๆ
        for pattern_name, pattern in self.number_patterns.items():
            matches = re.findall(pattern, text)
            
            for match in matches:
                if isinstance(match, tuple):
                    # กรณี group ในregex
                    for group in match:
                        if group and group.isdigit():
                            number_info = self._process_number(group, pattern_name, category)
                            if number_info:
                                extracted.append(number_info)
                else:
                    # กรณีเลขเดี่ยว
                    if match and match.replace(',', '').isdigit():
                        number_info = self._process_number(match.replace(',', ''), pattern_name, category)
                        if number_info:
                            extracted.append(number_info)
        
        # เรียงตามความสำคัญ
        extracted.sort(key=lambda x: x['confidence'], reverse=True)
        
        # ลบซ้ำ
        unique_numbers = []
        seen_numbers = set()
        
        for item in extracted:
            if item['number'] not in seen_numbers:
                unique_numbers.append(item)
                seen_numbers.add(item['number'])
                
        return unique_numbers[:10]  # เอาแค่ 10 เลขแรก
    
    def _process_number(self, number_str: str, pattern_type: str, category: str) -> Dict:
        """ประมวลผลเลขแต่ละตัว"""
        
        if not number_str.isdigit():
            return None
            
        num = int(number_str)
        
        # ปรับเป็นเลข 2-3 หลัก
        if len(number_str) == 1:
            formatted_number = f"0{number_str}"
        elif len(number_str) > 3:
            # เอาเฉพาะ 2-3 หลักท้าย
            formatted_number = number_str[-2:] if len(number_str) == 4 else number_str[-3:]
        else:
            formatted_number = number_str
            
        # คำนวณความเชื่อมั่น
        confidence = self._calculate_number_confidence(pattern_type, category, num)
        
        return {
            'number': formatted_number,
            'original_value': number_str,
            'source': pattern_type,
            'confidence': confidence,
            'reason': self._get_number_reason(pattern_type, category)
        }
    
    def _calculate_number_confidence(self, pattern_type: str, category: str, number: int) -> int:
        """คำนวณความเชื่อมั่นของเลข"""
        
        base_confidence = {
            'license_plate': 90,
            'house_number': 85, 
            'age': 80,
            'date': 75,
            'time': 70,
            'money': 65,
            'general_numbers': 50
        }.get(pattern_type, 50)
        
        # ปรับตามหมวดหมู่
        category_bonus = {
            'accident': 10,
            'celebrity': 8,
            'economic': 6,
            'general': 0
        }.get(category, 0)
        
        # ปรับตามช่วงเลข
        if 10 <= number <= 99:
            range_bonus = 5
        elif 100 <= number <= 999:
            range_bonus = 3
        else:
            range_bonus = 0
            
        return min(base_confidence + category_bonus + range_bonus, 100)
    
    def _calculate_final_score(self, base_score: int, extracted_numbers: List, category: str) -> int:
        """คำนวณคะแนนสุดท้าย"""
        
        # โบนัสจากจำนวนเลขที่สกัดได้
        number_bonus = min(len(extracted_numbers) * 5, 20)
        
        # โบนัสจากความเชื่อมั่นเฉลี่ยของเลข
        if extracted_numbers:
            avg_confidence = sum(item['confidence'] for item in extracted_numbers) / len(extracted_numbers)
            confidence_bonus = int(avg_confidence / 10)
        else:
            confidence_bonus = 0
            
        final = base_score + number_bonus + confidence_bonus
        
        return min(final, 100)
    
    def _get_scoring_reason(self, category: str, num_count: int) -> str:
        """ให้เหตุผลการให้คะแนน"""
        
        reasons = {
            'accident': f'ข่าวอุบัติเหตุ - เลขมักจะแม่นสูง (พบ {num_count} เลข)',
            'celebrity': f'ข่าวคนดัง - วันเกิด/อายุมักออก (พบ {num_count} เลข)',
            'economic': f'ข่าวเศรษฐกิจ - ตัวเลขสำคัญ (พบ {num_count} เลข)', 
            'general': f'ข่าวทั่วไป - ความน่าเชื่อถือปานกลาง (พบ {num_count} เลข)'
        }
        
        return reasons.get(category, f'ข่าวประเภทอื่น (พบ {num_count} เลข)')
    
    def _get_number_reason(self, pattern_type: str, category: str) -> str:
        """ให้เหตุผลของเลข"""
        
        reasons = {
            'license_plate': 'เลขทะเบียนรถ - มักออกบ่อย',
            'house_number': 'เลขบ้าน - เลขที่อยู่', 
            'age': 'อายุ - วันเกิดหรือความสำคัญ',
            'date': 'วันที่ - เหตุการณ์สำคัญ',
            'time': 'เวลา - โมงเกิดเหตุ',
            'money': 'จำนวนเงิน - มูลค่าสำคัญ',
            'general_numbers': 'เลขทั่วไป - ปรากฏในข่าว'
        }
        
        return reasons.get(pattern_type, 'เลขจากข่าว')


# ตัวอย่างการใช้งาน
def test_scorer():
    """ทดสอบระบบให้คะแนน"""
    
    scorer = NewsLotteryScorer()
    
    # ตัวอย่างข่าวอุบัติเหตุ
    accident_news = {
        'title': 'รถชนกันสนั่น 2 คนเสียชีวิต ทะเบียน กข-1234',
        'content': 'เกิดอุบัติเหตุรถชนที่บ้านเลขที่ 45 หมู่ที่ 3 เวลา 14:30 น. ผู้เสียชีวิตอายุ 35 ปี'
    }
    
    result = scorer.score_news_article(accident_news['title'], accident_news['content'])
    
    print("=== ผลการวิเคราะห์ข่าวอุบัติเหตุ ===")
    print(f"คะแนนรวม: {result['score']}")
    print(f"หมวดหมู่: {result['category']}")
    print(f"เลขที่สกัดได้: {len(result['extracted_numbers'])} เลข")
    for num_info in result['extracted_numbers']:
        print(f"  - {num_info['number']} ({num_info['source']}) ความเชื่อมั่น: {num_info['confidence']}%")
    print(f"เหตุผล: {result['confidence_details']['reasoning']}")

if __name__ == "__main__":
    test_scorer()
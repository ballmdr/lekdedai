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
        
        # 🌟 คำสำคัญข่าวแปลก/มหัศจรรย์ (95+ คะแนน)
        self.miracle_keywords = [
            'ประหลาด', 'มหัศจรรย์', 'แปลก', 'พิสดาร', 'ฮือฮา',
            'พญานาค', 'จอมปลวก', 'ต้นกล้วย', 'กล้วย', 'เห็ด',
            'เต่าสีทอง', 'เต่า', 'งู', 'ตัวเงินตัวทอง', 'สัตว์สองหัว', '5 ขา'
        ]
        
        # 🔮 คำสำคัญเลขมงคล/ความเชื่อ (92+ คะแนน)
        self.belief_keywords = [
            'ขันน้ำมนต์', 'น้ำมนต์', 'เลขหางประทัด', 'ประทัด', 'ธูป',
            'หลวงพ่อ', 'เกจิ', 'อาจารย์', 'เจ้าอาวาส', 'มรณภาพ',
            'ความฝัน', 'ฝันว่า', 'ฝันเห็น', 'นิมิต',
            'ครบรอบ', 'รำลึก', 'ปีที่'
        ]
        
        # รูปแบบเลขที่สำคัญ (ปรับปรุงใหม่)
        self.number_patterns = {
            # ทะเบียนรถ (ปรับปรุง)
            'license_plate': r'ทะเบียน\s*([ก-ฮ]{0,3})\s*([0-9]{1,4})|([ก-ฮ]{2,3})\s*([0-9]{2,4})',
            
            # อายุและจำนวนปี (ปรับปรุง)
            'age_years': r'อายุ\s*([0-9]{1,3})\s*ปี|([0-9]{1,3})\s*ขวบ|จำคุก\s*([0-9]{1,2})\s*ปี',
            
            # เวลา (ปรับปรุงให้เจอ 09.09)
            'time': r'([0-9]{1,2})\.([0-9]{2})\s*น\.|([0-9]{1,2}):([0-9]{2})',
            
            # คะแนนศาล และอัตราส่วน
            'court_score': r'คะแนน\s*([0-9]{1,2})-([0-9]{1,2})|([0-9]{1,2})-([0-9]{1,2})\s*คะแนน',
            
            # หมายเลขคดี (ใหม่)
            'case_number': r'คดี[หมายเลข]*\s*[แดงดำ]*\s*[ที่]*\s*[อม\.บค\.]*\s*([0-9]{1,3})\/([0-9]{4})|ชั้น\s*([0-9]{1,3})',
            
            # ตำแหน่งนายกฯ (ใหม่)
            'pm_position': r'นายก[รัฐมนตรี]*\s*คนที่\s*([0-9]{1,3})|อดีตนายก[รัฐมนตรี]*\s*คนที่\s*([0-9]{1,3})',
            
            # จำนวนคัน/คน/ชิ้น
            'quantity': r'([0-9]{1,3})\s*คัน|([0-9]{1,3})\s*คน|([0-9]{1,3})\s*ชิ้น',
            
            # บ้านเลขที่
            'house_number': r'บ้านเลขที่\s*([0-9]{1,4})|เลขที่\s*([0-9]{1,4})',
            
            # เงิน
            'money': r'([0-9,]+)\s*บาท|([0-9,]+)\s*ล้าน|([0-9,]+)\s*แสน',
            
            # เลขทั่วไป
            'general_numbers': r'\b([0-9]{2,3})\b'
        }
        
        # 🚫 เลขที่ต้องหลีกเลี่ยง - ไม่มีความหมายสำหรับหวย
        self.excluded_patterns = [
            r'วันที่\s*([0-9]{1,2})\s*[\/\-\.]\s*([0-9]{1,2})\s*[\/\-\.]\s*([0-9]{2,4})',  # วันที่ข่าว
            r'([0-9]{1,2})\s*[\/\-\.]\s*([0-9]{1,2})\s*[\/\-\.]\s*(25[0-9]{2})',  # ปี พ.ศ.
            r'([0-9]{1,2})\s*[\/\-\.]\s*([0-9]{1,2})\s*[\/\-\.]\s*(20[0-9]{2})',  # ปี ค.ศ.
            r'หน้า\s*([0-9]+)',  # หมายเลขหน้า
            r'ฉบับที่\s*([0-9]+)',  # เลขฉบับ
            r'รหัส\s*([0-9]+)',  # รหัสต่างๆ
            r'ID\s*([0-9]+)',  # รหัส ID
            r'เวอร์ชั่น\s*([0-9\.]+)',  # เลขเวอร์ชั่น
        ]
    
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
            'miracle': 0,
            'belief': 0,
            'accident': 0,
            'celebrity': 0, 
            'economic': 0,
            'general': 0
        }
        
        # ตรวจสอบคำสำคัญแปลก/มหัศจรรย์
        for keyword in self.miracle_keywords:
            if keyword in text:
                scores['miracle'] += 12
                
        # ตรวจสอบคำสำคัญเลขมงคล/ความเชื่อ
        for keyword in self.belief_keywords:
            if keyword in text:
                scores['belief'] += 12
                
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
        if scores['miracle'] > 0:
            final_scores['miracle'] = min(95 + scores['miracle'], 100)
        if scores['belief'] > 0:
            final_scores['belief'] = min(92 + scores['belief'], 100)
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
        
        # 🚫 เช็คว่าเลขอยู่ในรูปแบบที่ต้องหลีกเลี่ยงหรือไม่
        def should_exclude_number(number_text: str, full_text: str) -> bool:
            for excluded_pattern in self.excluded_patterns:
                if re.search(excluded_pattern, full_text):
                    # ตรวจสอบว่าเลขนี้อยู่ใน pattern ที่ต้องหลีกเลี่ยงหรือไม่
                    excluded_matches = re.findall(excluded_pattern, full_text)
                    for excluded_match in excluded_matches:
                        if isinstance(excluded_match, tuple):
                            if number_text in excluded_match:
                                return True
                        elif number_text in str(excluded_match):
                            return True
            return False
        
        # สกัดตามรูปแบบต่างๆ
        for pattern_name, pattern in self.number_patterns.items():
            matches = re.findall(pattern, text)
            
            for match in matches:
                if isinstance(match, tuple):
                    # กรณี group ในregex
                    for group in match:
                        if group and group.isdigit():
                            # เช็คว่าควรหลีกเลี่ยงหรือไม่
                            if not should_exclude_number(group, text):
                                number_info = self._process_number(group, pattern_name, category)
                                if number_info:
                                    extracted.append(number_info)
                else:
                    # กรณีเลขเดี่ยว
                    if match and match.replace(',', '').isdigit():
                        clean_number = match.replace(',', '')
                        if not should_exclude_number(clean_number, text):
                            number_info = self._process_number(clean_number, pattern_name, category)
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
            'license_plate': 95,      # ทะเบียนรถ (สูงสุด)
            'case_number': 90,        # หมายเลขคดี (ใหม่)
            'court_score': 88,        # คะแนนศาล (ใหม่)
            'pm_position': 85,        # ตำแหน่งนายกฯ (ใหม่)
            'age_years': 85,          # อายุ/ปี (ปรับปรุง)
            'house_number': 80, 
            'time': 78,               # เวลา (ปรับสูงขึ้น)
            'quantity': 75,           # จำนวน (ใหม่)
            'date': 70,
            'money': 65,
            'general_numbers': 50
        }.get(pattern_type, 50)
        
        # ปรับตามหมวดหมู่
        category_bonus = {
            'miracle': 12,
            'belief': 12,
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
            'miracle': f'ข่าวแปลก/มหัศจรรย์ - คนนิยมตีเลข (พบ {num_count} เลข)',
            'belief': f'เลขมงคล/ความเชื่อ - เลขศักดิ์สิทธิ์ (พบ {num_count} เลข)',
            'accident': f'ข่าวอุบัติเหตุ - เลขมักจะแม่นสูง (พบ {num_count} เลข)',
            'celebrity': f'ข่าวคนดัง - วันเกิด/อายุมักออก (พบ {num_count} เลข)',
            'economic': f'ข่าวเศรษฐกิจ - ตัวเลขสำคัญ (พบ {num_count} เลข)', 
            'general': f'ข่าวทั่วไป - ความน่าเชื่อถือปานกลาง (พบ {num_count} เลข)'
        }
        
        return reasons.get(category, f'ข่าวประเภทอื่น (พบ {num_count} เลข)')
    
    def _get_number_reason(self, pattern_type: str, category: str) -> str:
        """ให้เหตุผลของเลข"""
        
        reasons = {
            'license_plate': 'เลขทะเบียนรถ - เลขดีดที่คนนิยม',
            'case_number': 'หมายเลขคดี - เลขกฎหมายสำคัญ',
            'court_score': 'คะแนนศาล - เลขคำตัดสิน',
            'pm_position': 'ตำแหน่งนายกฯ - เลขอำนาจ',
            'age_years': 'อายุ/ปี - เลขสำคัญส่วนตัว',
            'house_number': 'เลขบ้าน - เลขที่อยู่', 
            'time': 'เวลา - โมงเกิดเหตุสำคัญ',
            'quantity': 'จำนวน - เลขปริมาณ',
            'date': 'วันที่ - เหตุการณ์สำคัญ',
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
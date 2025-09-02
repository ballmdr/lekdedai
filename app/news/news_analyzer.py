import re
from collections import Counter
from django.db import models
from .news_lottery_scorer import NewsLotteryScorer

class NewsAnalyzer:
    """วิเคราะห์หาเลขจากข่าว ใช้ระบบใหม่ที่เฉพาะเจาะจงสำหรับหวย"""
    
    def __init__(self):
        self.lottery_scorer = NewsLotteryScorer()
    
    def analyze_article(self, article):
        """วิเคราะห์บทความข่าว ใช้ระบบใหม่เฉพาะสำหรับหวย"""
        
        print(f"🔍 เริ่มวิเคราะห์ข่าว: {article.title[:50]}...")
        
        try:
            # ใช้ระบบให้คะแนนใหม่
            scoring_result = self.lottery_scorer.score_news_article(article.title, article.content)
            
            print(f"🎯 คะแนนข่าว: {scoring_result['score']} ({scoring_result['category']})")
            print(f"🔢 เลขที่สกัดได้: {len(scoring_result['extracted_numbers'])} เลข")
            
            # แปลงรูปแบบให้เข้ากับระบบเดิม
            extracted_numbers = [item['number'] for item in scoring_result['extracted_numbers']]
            keywords_found = [item['reason'] for item in scoring_result['extracted_numbers']]
            
            print(f"✨ เลขสุดท้าย: {extracted_numbers}")
            print(f"📊 เหตุผล: {scoring_result['confidence_details']['reasoning']}")
            
            return {
                'numbers': extracted_numbers[:15],
                'keywords': keywords_found,
                'confidence': scoring_result['score'],
                'category': scoring_result['category'],
                'detailed_analysis': scoring_result
            }
            
        except Exception as e:
            # ถ้าเกิดข้อผิดพลาด ให้ใช้ระบบเดิม
            print(f"❌ Error using new lottery scorer: {e}")
            return self.analyze_article_fallback(article)

    def _get_prioritized_numbers(self, priority_numbers):
        """จัดเรียงเลขตามความสำคัญและลบเลขซ้ำ"""
        
        high_priority = list(dict.fromkeys(priority_numbers['high']))
        medium_priority = list(dict.fromkeys(priority_numbers['medium']))
        low_priority = list(dict.fromkeys(priority_numbers['low']))
        
        # เรียงลำดับความสำคัญ: high -> medium -> low
        # ตัวเลขที่อยู่ใน priority สูงกว่า จะไม่ถูกเอามาซ้ำใน priority ที่ต่ำกว่า
        
        final_numbers = high_priority
        
        for num in medium_priority:
            if num not in final_numbers:
                final_numbers.append(num)
                
        for num in low_priority:
            if num not in final_numbers:
                final_numbers.append(num)
                
        return final_numbers

    def analyze_article_fallback(self, article):
        """ระบบวิเคราะห์แบบเดิม (fallback)"""
        text = f"{article.title} {article.content}".lower()
        
        found_numbers = []
        keywords_found = []
        confidence = 50
        
        print(f"🔄 ใช้ระบบวิเคราะห์แบบเดิม (fallback)")
        
        # ใช้ระบบเดิม
        direct_numbers = self.extract_direct_numbers(text)
        print(f"🔢 เลขที่พบตรงๆ (fallback): {direct_numbers}")
        found_numbers.extend(direct_numbers)
        
        # คำสำคัญแบบเดิม
        keyword_numbers, keywords = self.extract_keyword_numbers_fallback(text)
        print(f"🔑 เลขจากคำสำคัญ (fallback): {keyword_numbers}")
        print(f"📚 คำสำคัญที่พบ (fallback): {keywords}")
        found_numbers.extend(keyword_numbers)
        keywords_found.extend(keywords)
        
        unique_numbers = self.process_numbers(found_numbers)
        print(f"✨ เลขที่ประมวลผลแล้ว (fallback): {unique_numbers}")
        
        if len(unique_numbers) > 0:
            confidence = min(confidence + (len(keywords_found) * 5), 95)
        
        print(f"🎯 ผลลัพธ์สุดท้าย (fallback): เลข {len(unique_numbers)} ตัว, ความน่าเชื่อถือ {confidence}%")
        
        return {
            'numbers': unique_numbers[:15],
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
    
    def extract_dream_keyword_numbers(self, text):
        """หาเลขจากคำสำคัญใน DreamKeyword"""
        numbers = []
        keywords = []
        
        try:
            from dreams.models import DreamKeyword
            
            # ค้นหา keywords ที่ตรงกับในฐานข้อมูล DreamKeyword
            # เรียงลำดับตามความยาวของ keyword (ยาวที่สุดก่อน)
            all_keywords = sorted(DreamKeyword.objects.all(), key=lambda x: len(x.keyword), reverse=True)
            
            matched_positions = []  # เก็บตำแหน่งที่จับได้แล้ว
            
            for keyword_obj in all_keywords:
                keyword = keyword_obj.keyword.lower()
                
                # ค้นหาคำที่ตรงกันทั้งคำ และไม่ซ้อนทับ
                if keyword in text:
                    # หาตำแหน่งทั้งหมดที่พบคำนี้
                    start_idx = 0
                    while True:
                        idx = text.find(keyword, start_idx)
                        if idx == -1:
                            break
                        
                        start, end = idx, idx + len(keyword)
                        
                        # ตรวจสอบว่าตำแหน่งนี้ถูกจับแล้วหรือไม่
                        overlap = any(start < pos_end and end > pos_start for pos_start, pos_end in matched_positions)
                        
                        if not overlap:
                            matched_positions.append((start, end))
                            keywords.append(keyword_obj.keyword)
                            
                            # เพิ่มเลขที่มักตี
                            numbers.extend(keyword_obj.get_numbers_list())
                            break  # เจอแล้วครั้งแรกก็พอ
                        
                        start_idx = idx + 1
            
            # ลบเลขซ้ำ
            numbers = list(dict.fromkeys(numbers))
            
        except Exception as e:
            print(f"Error in extract_dream_keyword_numbers: {e}")
            # ถ้าเกิดข้อผิดพลาด ให้ใช้ระบบเดิม
            return self.extract_keyword_numbers_fallback(text)
        
        return numbers, keywords
    
    def extract_keyword_numbers_fallback(self, text):
        """หาเลขจากคำสำคัญแบบเดิม (fallback)"""
        # คำสำคัญและเลขที่เกี่ยวข้องแบบเดิม
        keyword_numbers = {
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
        
        numbers = []
        keywords = []
        
        for keyword, nums in keyword_numbers.items():
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
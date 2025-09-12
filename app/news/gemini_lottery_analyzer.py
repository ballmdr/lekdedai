import os
import logging
from typing import Dict, List, Optional
import json

# Gemini SDK
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Gemini SDK not available. Install google-genai package.")

class GeminiLotteryAnalyzer:
    """ระบบวิเคราะห์ข่าวด้วย Gemini AI เพื่อหาเลขเด็ดหวย"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise RuntimeError("Missing GEMINI_API_KEY in environment variables")
        
        if not GEMINI_AVAILABLE:
            raise RuntimeError("Gemini SDK not available. Please install google-genai package.")
            
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.0-flash-exp"  # ใช้ model ล่าสุด
        
    def analyze_news_for_lottery(self, title: str, content: str) -> Dict:
        """วิเคราะห์ข่าวด้วย Gemini เพื่อหาเลขเด็ดหวย"""
        
        prompt = f"""
คุณคือผู้เชียวชาญด้านการตีเลขหวยจากข่าว โปรดวิเคราะห์ข่าวนี้:

หัวข้อ: {title}
เนื้อหา: {content}

กรุณาตอบเป็น JSON format ดังนี้:
{{
  "is_relevant": true/false (ข่าวนี้เกี่ยวข้องกับหวยไหม: อุบัติเหตุ, คนดัง, การเมือง, อาชญากรรม, เหตุการณ์สำคัญ),
  "category": "accident/celebrity/politics/crime/economic/miracle/other",
  "relevance_score": 0-100 (คะแนนความเหมาะสม),
  "extracted_numbers": [
    {{
      "number": "XX", 
      "source": "จากอะไร เช่น อายุ 25 ปี, ทะเบียน กข-1234, เวลา 14.30 น.",
      "confidence": 0-100
    }}
  ],
  "reasoning": "อธิบายเหตุผลการตีเลข"
}}

หลักการตีเลขหวย:
1. อายุคน → เลขโดยตรง
2. ทะเบียนรถ → ตัวเลขในทะเบียน (เช่น กข-1234 → 12,34,23,14)  
3. เวลา → 14.30 → 14,30,43
4. หมายเลขคดี/ที่อยู่ → ตัวเลขที่มี
5. จำนวนเงิน/ความเสียหาย → ตัวเลขสำคัญ
6. วันที่เกิดเหตุ → ไม่ตี (เพราะเป็นแค่วันที่ข่าว)
7. ปี พ.ศ./ค.ศ. → ไม่ตี 
8. หมายเลขหน้า/ฉบับ → ไม่ตี

ตัวอย่าง:
"ทักษิณ อายุ 74 ปี ถูกศาลฎีกาส่งคืนคุก 1 ปี คดีชั้น 14 เดินทางด้วยรถทะเบียน พร 195 เวลา 09.09 น."
→ เลข: 74 (อายุ), 1 (จำคุก), 14 (คดีชั้น), 19,95 (ทะเบียน), 09 (เวลา)

กรุณาตอบเป็น JSON เท่านั้น:
"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            result_text = response.text.strip()
            
            # ลบ ```json และ ``` ที่ Gemini อาจใส่มา
            if result_text.startswith('```json'):
                result_text = result_text[7:]  # ลบ ```json
            if result_text.endswith('```'):
                result_text = result_text[:-3]  # ลบ ```
            result_text = result_text.strip()
            
            # ลองแปลง JSON
            try:
                result = json.loads(result_text)
                return {
                    'success': True,
                    'is_relevant': result.get('is_relevant', False),
                    'category': result.get('category', 'other'),
                    'relevance_score': result.get('relevance_score', 0),
                    'numbers': [item['number'] for item in result.get('extracted_numbers', [])],
                    'detailed_numbers': result.get('extracted_numbers', []),
                    'reasoning': result.get('reasoning', ''),
                    'raw_response': result_text
                }
            except json.JSONDecodeError:
                # ถ้าไม่ใช่ JSON ให้ fallback
                return {
                    'success': False,
                    'error': 'Invalid JSON response',
                    'raw_response': result_text,
                    'is_relevant': False,
                    'numbers': []
                }
                
        except Exception as e:
            logging.error(f"Gemini API error: {e}")
            return {
                'success': False,
                'error': str(e),
                'is_relevant': False,
                'numbers': []
            }
    
    def is_lottery_relevant(self, title: str, content: str) -> bool:
        """เช็คว่าข่าวนี้เกี่ยวข้องกับหวยไหม (ใช้ก่อนวิเคราะห์แบบเต็ม)"""
        
        prompt = f"""
ข่าวนี้เกี่ยวข้องกับการเล่นหวยไหม? ตอบแค่ true หรือ false

หัวข้อ: {title}
เนื้อหา: {content[:500]}...

เกี่ยวข้องถ้า:
- อุบัติเหตุ (รถชน, ไฟไหม้, ตาย, เจ็บ)
- คนดัง (ดารา, นักการเมือง, อายุ, เกิด, แต่งงาน)
- การเมือง (นายก, รัฐมนตรี, คดี, ศาล)
- อาชญากรรม (ฆ่า, โจร, ข่มขืน, ยาเสพติด)
- เศรษฐกิจ (หุ้น, ทอง, น้ำมัน, ราคา)
- เหตุการณ์แปลก/มหัศจรรย์

ไม่เกี่ยวข้องถ้า:
- ข่าวสุขภาพทั่วไป
- ข่าวสปอร์ต (นอกจากมีอุบัติเหตุ)
- ข่าวไลฟ์สไตล์
- ข่าวอาหาร/ท่องเที่ยว
- ข่าวเทคโนโลยี

ตอบ:
"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            result = response.text.strip().lower()
            return 'true' in result
        except:
            return False
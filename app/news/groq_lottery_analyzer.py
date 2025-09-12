# -*- coding: utf-8 -*-
import os
import logging
from typing import Dict, List, Optional
import json
import requests

class GroqLotteryAnalyzer:
    """ระบบวิเคราะห์ข่าวด้วย Groq Llama 3.1 8B Instant เพื่อหาเลขเด็ดหวย"""
    
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise RuntimeError("Missing GROQ_API_KEY in environment variables")
        
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-8b-instant"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
    def _make_request(self, messages: List[Dict], temperature: float = 0.4) -> str:
        """ส่ง request ไปยัง Groq API"""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
            "max_tokens": 2048
        }
        
        try:
            response = requests.post(self.api_url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            logging.error(f"Groq API request error: {e}")
            raise
        
    def analyze_news_for_lottery(self, title: str, content: str) -> Dict:
        """วิเคราะห์ข่าวด้วย Groq เพื่อหาเลขเด็ดหวย"""
        
        messages = [
            {
                "role": "system", 
                "content": "คุณคือผู้เชี่ยวชาญด้านการตีเลขหวยไทยจากข่าว ตอบเป็น JSON เท่านั้น"
            },
            {
                "role": "user", 
                "content": f"""
วิเคราะห์ข่าวนี้หาเลขเด็ดหวย โดยใช้เฉพาะข้อมูลจากข่าวนี้เท่านั้น:

หัวข้อ: {title}
เนื้อหา: {content}

กฎสำคัญ:
⚠️ ใช้เฉพาะข้อมูลที่ปรากฏในข่าวนี้เท่านั้น - ห้ามสร้างหรือเดาข้อมูล
⚠️ ถ้าไม่พบทะเบียนรถในข่าว ให้ตอบ "ไม่พบทะเบียนรถ"

หาเลขจาก:
1. ทะเบียนรถ (ที่ระบุชัดเจนในข่าว) - เช่น "รถทะเบียน กข 1234" → เลข 1234, 12, 34
2. อายุคน - เช่น "อายุ 25 ปี" → เลข 25  
3. เวลาเกิดเหตุ - เช่น "เวลา 15.30" → เลข 15, 30
4. จำนวน/ปริมาณ - เช่น "ล้ม 24 ต้น", "พัง 10 คัน" → เลข 24, 10
5. หมายเลขสถานที่/คดี - ที่ระบุชัดเจน

ห้าม:
- วันที่, ปี พ.ศ./ค.ศ.
- เลขที่ไม่มีในข่าว (ห้ามสร้างขึ้นเอง)
- ทะเบียนรถจากข่าวอื่น

ตอบเป็น JSON เท่านั้น
{{
  "is_relevant": true/false,
  "category": "accident/politics/crime/other", 
  "relevance_score": 0-100,
  "extracted_numbers": [
    {{
      "number": "เลขที่พบจริง",
      "source": "แหล่งที่มาที่ชัดเจน",
      "confidence": 0-100
    }}
  ],
  "reasoning": "อธิบายเหตุผลตามข้อมูลที่พบจริง"
}}
"""
            }
        ]
        
        try:
            result_text = self._make_request(messages)
            
            # ลบ ```json และ ``` ที่โมเดลอาจใส่มา
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            try:
                result = json.loads(result_text)
                
                # รวบเลขซ้ำกัน (ไม่สนใจ reasoning ต่างกัน)
                detailed_numbers = result.get('extracted_numbers', [])
                unique_numbers = {}
                
                for item in detailed_numbers:
                    number = item.get('number', '')
                    source = item.get('source', '') 
                    confidence = item.get('confidence', 0)
                    
                    # ถ้าเลขนี้ยังไม่มี หรือมีแต่ confidence ใหม่สูงกว่า
                    if number not in unique_numbers or confidence > unique_numbers[number]['confidence']:
                        unique_numbers[number] = {
                            'number': number,
                            'source': source,  # ใช้ source ที่มี confidence สูงสุด
                            'confidence': confidence
                        }
                    elif confidence == unique_numbers[number]['confidence'] and len(source) < len(unique_numbers[number]['source']):
                        # ถ้า confidence เท่ากัน ใช้ source ที่สั้นกว่า (กระชับกว่า)
                        unique_numbers[number]['source'] = source
                
                # แปลงกลับเป็น list และเรียงตาม confidence
                final_numbers = list(unique_numbers.values())
                final_numbers.sort(key=lambda x: x['confidence'], reverse=True)
                
                return {
                    'success': True,
                    'is_relevant': result.get('is_relevant', False),
                    'category': result.get('category', 'other'),
                    'relevance_score': result.get('relevance_score', 0),
                    'numbers': [item['number'] for item in final_numbers],
                    'detailed_numbers': final_numbers,
                    'reasoning': result.get('reasoning', ''),
                    'raw_response': result_text,
                    'analyzer_type': 'groq'  # ระบุประเภท analyzer
                }
            except json.JSONDecodeError as e:
                logging.error(f"Groq JSON Parse Error: {e}")
                return {
                    'success': False,
                    'error': 'Invalid JSON response',
                    'raw_response': result_text,
                    'is_relevant': False,
                    'numbers': [],
                    'analyzer_type': 'groq'
                }
                
        except Exception as e:
            error_msg = str(e)
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                logging.error(f"Groq API Rate Limit: {e}")
                return {
                    'success': False,
                    'error': 'RATE_LIMIT_EXCEEDED',
                    'message': 'Groq API rate limit exceeded',
                    'is_relevant': False,
                    'numbers': [],
                    'analyzer_type': 'groq'
                }
            else:
                logging.error(f"Groq API Error: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'is_relevant': False,
                    'numbers': [],
                    'analyzer_type': 'groq'
                }
    
    def is_lottery_relevant(self, title: str, content: str) -> bool:
        """เช็คว่าข่าวนี้เกี่ยวข้องกับหวยไหม (ใช้ก่อนวิเคราะห์แบบเต็ม)"""
        
        messages = [
            {
                "role": "system",
                "content": "คุณคือผู้เชี่ยวชาญตีเลขหวยไทย ตอบแค่ true หรือ false เท่านั้น"
            },
            {
                "role": "user", 
                "content": f"""
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
            }
        ]

        try:
            result = self._make_request(messages, temperature=0.2)
            result_text = result.strip().lower()
            return 'true' in result_text
        except Exception as e:
            logging.error(f"Groq relevance check error: {e}")
            return False

    def format_content(self, content: str) -> str:
        """จัดรูปแบบเนื้อหาด้วย Groq AI"""
        
        messages = [
            {
                "role": "system",
                "content": "คุณช่วยเรียบเรียงข่าวภาษาไทยให้อ่านง่าย กระชับ และเป็นระเบียบ"
            },
            {
                "role": "user",
                "content": f"""
เรียบเรียงเนื้อหาข่าวนี้ให้อ่านง่ายขึ้น:

{content}

หลักเกณฑ์:
1. ตัดขยะออก (Logo, เมนู, โฆษณา)
2. จัดย่อหน้าให้เหมาะสม
3. เก็บข้อมูลสำคัญไว้ครบ (อายุ, ทะเบียนรถ, เวลา, จำนวนเงิน)
4. ใช้ภาษาเรียบง่าย
5. ไม่เกิน 1000 คำ

เรียบเรียงแล้วตอบเฉพาะเนื้อหาที่จัดรูปแบบแล้ว:
"""
            }
        ]
        
        try:
            formatted_content = self._make_request(messages, temperature=0.3)
            return formatted_content.strip()
        except Exception as e:
            logging.error(f"Groq content formatting error: {e}")
            return content  # fallback ใช้เนื้อหาเดิม
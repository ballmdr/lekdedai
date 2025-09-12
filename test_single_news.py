# -*- coding: utf-8 -*-
import os
import sys
import django
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import json

# --- Setup Django ---
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lekdedai.settings')
django.setup()

from news.models import NewsArticle, NewsCategory
from lekdedai.utils import generate_unique_slug
from django.utils import timezone

# --- Setup Gemini ---
api_key = "AIzaSyAjivjnnUo2AL5v4HGVkC4mTIH4kxMyOPU"
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash-8b')  # ใช้ Flash Lite เพื่อประหยัด quota

def _clean_website_junk(content):
    """ลบขยะเว็บไซต์ออกจากเนื้อหาก่อนบันทึกลงฐานข้อมูล"""
    import re
    
    if not content:
        return ""
    
    # ถ้าเจอขยะในส่วนต้น ลองหาจุดเริ่มต้นเนื้อหาจริง
    if any(keyword in content[:300].lower() for keyword in ['logo', 'thairath', 'สมาชิก', 'light', 'dark', 'ฟังข่าว']):
        # หาจุดเริ่มต้นเนื้อหาจริง
        start_markers = ['อดีตนายกรัฐมนตรี', 'นายกรัฐมนตรี', 'ทักษิณ ชินวัตร', 'ทักษิณ', 'รองนายก', 'รัฐมนตรี']
        for marker in start_markers:
            if marker in content:
                start_pos = content.find(marker)
                if start_pos > 50:  # ต้องมีขยะอย่างน้อย 50 ตัวอักษรข้างหน้า
                    content = content[start_pos:]
                    break
    
    return content.strip()

def scrape_thairath_news(url):
    """Scrape ข่าวจาก Thairath URL"""
    print(f"🔍 กำลัง scrape ข่าวจาก: {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # หา title
        title_elem = soup.find('h1') or soup.find('title')
        title = title_elem.get_text(strip=True) if title_elem else 'ข่าวจาก Thairath'
        
        # หา content
        content_selectors = [
            '.entry-content', '.post-content', '.article-content',
            'article', '.content', 'main'
        ]
        
        content = ""
        for selector in content_selectors:
            elem = soup.select_one(selector)
            if elem:
                # ลบ script, style tags
                for tag in elem(['script', 'style', 'nav', 'footer', 'aside']):
                    tag.decompose()
                content = elem.get_text(separator=' ', strip=True)
                break
        
        if not content:
            # fallback ใช้ body
            body = soup.find('body')
            if body:
                for tag in body(['script', 'style', 'nav', 'footer', 'aside']):
                    tag.decompose()
                content = body.get_text(separator=' ', strip=True)
        
        print(f"✅ Scrape สำเร็จ: {len(content)} ตัวอักษร")
        
        # Clean content ก่อนบันทึก - ลบขยะเว็บไซต์ออก
        cleaned_content = _clean_website_junk(content.strip())
        
        return {
            'title': title.strip(),
            'content': cleaned_content[:2000],  # จำกัด 2000 ตัวอักษร
            'url': url
        }
        
    except Exception as e:
        print(f"❌ Error scraping: {e}")
        return None

def analyze_with_gemini(title, content):
    """วิเคราะห์ข่าวด้วย Gemini Flash Lite"""
    print("🤖 กำลังวิเคราะห์ด้วย Gemini...")
    
    prompt = f"""
คุณเป็นผู้เชี่ยวชาญตีเลขหวยไทย วิเคราะห์ข่าวนี้หาเลขเด็ด:

หัวข้อ: {title}
เนื้อหา: {content}

⚠️ สำคัญมาก: ทะเบียนรถเป็นเลขเด็ดที่สำคัญที่สุด! หาทะเบียนรถให้ได้
ค้นหา: "ทะเบียน", "รถทะเบียน", "เลขทะเบียน" หรือรูปแบบ "กข-1234", "พร-195" 

หาเลขจาก:
1. ทะเบียนรถ (สำคัญที่สุด!) - เช่น "พร 195" → เลข 195, 19, 95
2. อายุคน - เช่น "อายุ 25 ปี" → เลข 25
3. เวลาเกิดเหตุ - เช่น "เวลา 9.09" → เลข 09
4. หมายเลขคดี - เช่น "คดีชั้น 14" → เลข 14
5. จำนวนเงิน/คน - เช่น "5 ล้าน" → เลข 5

ห้าม: 
- วันที่ (เช่น 9 ก.ย., วันที่ 12), ปี พ.ศ. (เช่น 2568)
- เลขซ้ำกัน: ถ้าเลขเดียวกันมาจากเหตุผลเดียวกัน ให้ใส่แค่ครั้งเดียว

ตอบเป็น JSON เท่านั้น:
{{
  "is_relevant": true,
  "category": "politics",
  "relevance_score": 85,
  "extracted_numbers": [
    {{
      "number": "195",
      "source": "ทะเบียนรถ พร 195",
      "confidence": 95
    }},
    {{
      "number": "19",
      "source": "จากทะเบียน พร 195 (19)",
      "confidence": 90
    }},
    {{
      "number": "95",
      "source": "จากทะเบียน พร 195 (95)",
      "confidence": 90
    }}
  ],
  "reasoning": "ทะเบียนรถเป็นเลขเด็ดสำคัญในข่าวนี้"
}}
"""
    
    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        print(f"📝 Gemini Response: {result_text[:500]}...")  # เพิ่ม debug
        
        # ทำความสะอาด JSON
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
                number = item['number']
                source = item['source'] 
                confidence = item['confidence']
                
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
                'raw_response': result_text
            }
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            return {
                'success': False,
                'error': 'Invalid JSON response',
                'raw_response': result_text
            }
            
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "429" in error_msg:
            print(f"❌ API Quota หมด: {e}")
            print("⏹️ หยุดการทำงาน - ไม่ใช้ Mock Analyzer")
            return {
                'success': False,
                'error': 'QUOTA_EXCEEDED',
                'message': 'Gemini API quota exceeded'
            }
        else:
            print(f"❌ Gemini API Error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

def save_to_database(news_data, analysis):
    """บันทึกข่าวและผลวิเคราะห์ลงฐานข้อมูล"""
    print("💾 กำลังบันทึกลงฐานข้อมูล...")
    
    # หา/สร้าง category
    category_name = {
        'politics': 'การเมือง',
        'accident': 'อุบัติเหตุ', 
        'crime': 'อาชญากรรม',
        'celebrity': 'คนดัง',
        'other': 'อื่นๆ'
    }.get(analysis.get('category', 'other'), 'อื่นๆ')
    
    category, created = NewsCategory.objects.get_or_create(
        name=category_name,
        defaults={
            'slug': analysis.get('category', 'other'),
            'description': f'ข่าว{category_name}ที่วิเคราะห์ด้วย Gemini AI'
        }
    )
    
    # สร้าง slug
    slug = generate_unique_slug(NewsArticle, news_data['title'], None)
    
    # บันทึกข่าว
    article = NewsArticle.objects.create(
        title=news_data['title'],
        slug=slug,
        category=category,
        intro=news_data['content'][:300] + '...' if len(news_data['content']) > 300 else news_data['content'],
        content=news_data['content'],
        extracted_numbers=','.join(analysis['numbers'][:15]),
        confidence_score=min(analysis.get('relevance_score', 50), 100),
        lottery_relevance_score=analysis.get('relevance_score', 50),
        lottery_category=analysis.get('category', 'other'),
        status='published',
        published_date=timezone.now(),
        source_url=news_data['url'],
        
        # เก็บข้อมูล Gemini analysis
        insight_summary=analysis.get('reasoning', ''),
        insight_impact_score=analysis.get('relevance_score', 0) / 100,
        insight_entities=[
            {
                'value': item['number'],
                'entity_type': 'number',
                'reasoning': item['source'],
                'significance_score': item['confidence'] / 100
            } for item in analysis.get('detailed_numbers', [])
        ]
    )
    
    print(f"✅ บันทึกสำเร็จ: {article.title}")
    print(f"🔗 URL: http://localhost:8000{article.get_absolute_url()}")
    
    return article

def main():
    url = "https://www.thairath.co.th/news/politic/2881640"  # URL ข่าวทักษิณ
    
    print("=== ทดสอบระบบข่าวเดี่ยวด้วย Gemini Flash Lite ===")
    print()
    
    # 1. Scrape ข่าว
    news_data = scrape_thairath_news(url)
    if not news_data:
        print("❌ ไม่สามารถ scrape ข่าวได้")
        return
    
    print(f"📰 หัวข้อ: {news_data['title']}")
    print(f"📝 เนื้อหา: {len(news_data['content'])} ตัวอักษร")
    print()
    
    # 2. วิเคราะห์ด้วย Gemini
    analysis = analyze_with_gemini(news_data['title'], news_data['content'])
    
    if not analysis['success']:
        if analysis.get('error') == 'QUOTA_EXCEEDED':
            print("⏹️ หยุดการทำงานเนื่องจาก quota หมด")
            return
        else:
            print(f"❌ การวิเคราะห์ล้มเหลว: {analysis.get('error', 'Unknown error')}")
            return
    
    if not analysis.get('is_relevant') or not analysis.get('numbers'):
        print("⚠️ ข่าวไม่เกี่ยวข้องกับหวยหรือไม่พบเลขเด็ด")
        return
    
    print("✅ ผลการวิเคราะห์:")
    print(f"   🔢 เลข: {', '.join(analysis['numbers'])}")
    print(f"   📊 คะแนน: {analysis.get('relevance_score', 0)}/100")
    print(f"   📂 หมวด: {analysis.get('category', 'other')}")
    print(f"   💡 เหตุผล: {analysis.get('reasoning', '')[:100]}...")
    print()
    
    # 3. บันทึกลงฐานข้อมูล
    try:
        article = save_to_database(news_data, analysis)
        print()
        print("🎉 สำเร็จทั้งหมด!")
        print(f"📰 ข่าว: {article.title}")
        print(f"🔢 เลขเด็ด: {article.extracted_numbers}")
        print(f"🌐 ดูได้ที่: http://localhost:8000{article.get_absolute_url()}")
        
    except Exception as e:
        print(f"❌ Error saving to database: {e}")

if __name__ == "__main__":
    main()
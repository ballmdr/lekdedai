# -*- coding: utf-8 -*-
import os
import sys
import django
import google.generativeai as genai
from datetime import datetime

# --- Setup Django ---
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lekdedai.settings')
django.setup()

from news.models import NewsArticle

# --- Setup Gemini Flash Lite ---
api_key = "AIzaSyAjivjnnUo2AL5v4HGVkC4mTIH4kxMyOPU"
genai.configure(api_key=api_key)

# ใช้ model standard (Flash) แทน Lite เพื่อความแม่นยำ
model = genai.GenerativeModel('gemini-1.5-flash')

def analyze_with_gemini_lite():
    today = datetime.now()
    today_date_thai = today.strftime("%d %B %Y")
    
    print(f"=== Gemini Flash Lite Analysis - {today_date_thai} ===")
    print()
    
    # ดึงข่าวล่าสุด
    recent_news = NewsArticle.objects.order_by('-published_date')[:3]  # ลด quota ใช้แค่ 3 ข่าว
    
    if not recent_news:
        print("❌ ไม่พบข่าวในฐานข้อมูล")
        return
    
    print(f"✅ พบข่าวล่าสุด {len(recent_news)} ข่าว")
    print()
    
    all_numbers = []
    
    for i, article in enumerate(recent_news, 1):
        print(f"🔍 วิเคราะห์ข่าวที่ {i}: {article.title[:60]}...")
        
        # สร้าง prompt บังคับให้ตีเลขจากข่าว
        prompt = f"""
คุณเป็นผู้เชี่ยวชาญตีเลขหวยไทย ต้องหาเลขเด็ดจากข่าวนี้:

{article.title}

{article.content[:500]}

คำสั่ง: ข่าวทุกข่าวสามารถตีเลขได้ หาเลขจากตัวเลขใดก็ได้ในข่าว เช่น อายุ, จำนวน, เวลา, ทะเบียน, หมายเลข

ตอบเป็น JSON เท่านั้น:
{{
  "is_relevant": true,
  "category": "accident/politics/crime/celebrity",
  "numbers": ["XX", "YY", "ZZ"],
  "reasoning": "เลข XX จาก..., เลข YY จาก..."
}}

บังคับ: ต้องมีเลขอย่างน้อย 1-3 ตัว ถ้าไม่เจอให้สุ่มจากตัวเลขในข่าว
"""
        
        try:
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            print(f"   📝 Raw Response: {result_text[:100]}...")
            
            # ลองแปลง JSON
            import json
            try:
                # ลบ markdown formatting ถ้ามี
                if result_text.startswith('```json'):
                    result_text = result_text[7:]
                if result_text.endswith('```'):
                    result_text = result_text[:-3]
                result_text = result_text.strip()
                
                result = json.loads(result_text)
                
                if result.get('is_relevant') and result.get('numbers'):
                    numbers = result['numbers']
                    all_numbers.extend(numbers)
                    
                    print(f"   ✅ เลขที่ได้: {', '.join(numbers)}")
                    print(f"   📂 หมวด: {result.get('category', 'other')}")
                    print(f"   💡 เหตุผล: {result.get('reasoning', '')[:80]}...")
                else:
                    print(f"   ⚠️ ไม่เกี่ยวข้องหรือไม่พบเลข")
                    
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON Error: {e}")
                print(f"   📄 Response: {result_text}")
                
        except Exception as e:
            if "quota" in str(e).lower():
                print(f"   ❌ API Quota หมด: {e}")
                break
            else:
                print(f"   ❌ Error: {e}")
        
        print()
        
        # พักสักครู่เพื่อไม่ให้ hit rate limit
        import time
        time.sleep(1)
    
    # สรุปผลลัพธ์
    if all_numbers:
        unique_numbers = list(dict.fromkeys(all_numbers))[:10]  # เอา 10 ตัวแรก
        
        print("🎯 เลขเด็ดจาก Gemini Flash Lite:")
        print("=" * 40)
        print(f"🎲 {', '.join(unique_numbers)}")
    else:
        print("❌ ไม่พบเลขเด็ดจากการวิเคราะห์")
    
    print()
    print("✅ การวิเคราะห์ด้วย Gemini Flash Lite เสร็จสิ้น")

if __name__ == "__main__":
    analyze_with_gemini_lite()
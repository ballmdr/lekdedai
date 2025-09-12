# -*- coding: utf-8 -*-
import os
import google.generativeai as genai
from datetime import datetime, timedelta

# --- 1. Setup API Key ---
api_key = "AIzaSyAjivjnnUo2AL5v4HGVkC4mTIH4kxMyOPU"
genai.configure(api_key=api_key)
print("API Key configured successfully")

# --- 2. Setup Model (ไม่ใช้ Google Search เพื่อประหยัด quota) ---
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. สร้าง Prompt สำหรับสั่งงาน Gemini ---
# ดึงวันที่ปัจจุบันในรูปแบบภาษาไทย
# เนื่องจากเราอยู่ในประเทศไทย (+7) ให้ใช้เวลาปัจจุบันได้เลย
today = datetime.now()
today_date_thai = today.strftime("%d %B %Y") # เช่น 11 September 2025

# ดึงข่าวจากฐานข้อมูลที่มีอยู่
import sys
sys.path.append('/app')
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lekdedai.settings')
django.setup()

from news.models import NewsArticle

# ดึงข่าวล่าสุด 5 ข่าว
recent_news = NewsArticle.objects.order_by('-published_date')[:5]

news_content = ""
for i, article in enumerate(recent_news, 1):
    news_content += f"{i}. {article.title}\n{article.content[:500]}...\n\n"

# สร้าง Prompt ที่ใช้ข่าวจากฐานข้อมูล
prompt = f"""
กรุณาทำหน้าที่เป็นบรรณาธิการข่าวและนักวิเคราะห์ตัวเลข โปรดวิเคราะห์ข่าวต่อไปนี้และสรุปเป็นข่าวประจำวันที่ {today_date_thai}:

{news_content}

โปรดจัดหมวดหมู่ข่าวและทำ "แนวทางการตีเลขเด็ดจากข่าว" โดยวิเคราะห์ตัวเลขที่ปรากฏในข่าวเหล่านั้น เช่น:
- เลขทะเบียนรถ  
- อายุของบุคคล
- จำนวนผู้บาดเจ็บ/เสียชีวิต
- วันที่และเวลาที่เกิดเหตุ
- หมายเลขคดี
- ตัวเลขอื่นๆ ที่น่าสนใจ

นำเสนอในรูปแบบที่อ่านง่าย ชัดเจน และเป็นกลาง พร้อมเหตุผลการตีเลขแต่ละตัว
"""

print(f"กำลังค้นหาและวิเคราะห์ข่าวประจำวันที่ {today_date_thai}...")
print(f"พบข่าวล่าสุด {len(recent_news)} ข่าว")
print("ตัวอย่างข่าว:")
print(news_content[:500] + "...")
print("-" * 30)

# --- 4. ทดสอบการโหลดข่าวโดยไม่เรียก API ---
if len(recent_news) > 0:
    print("✅ โหลดข่าวจากฐานข้อมูลสำเร็จ")
    print("✅ สร้าง Prompt สำเร็จ")
    print("❌ API Quota หมด - ข้ามการเรียก Gemini API")
else:
    print("❌ ไม่พบข่าวในฐานข้อมูล")

print("-" * 30)
print("✅ การทดสอบเสร็จสิ้น (รอ quota reset หรือใช้ Mock Analyzer)")

# สาธิตการใช้ Mock Analyzer แทน
print("\n=== ทดสอบ Mock Analyzer แทน ===")
try:
    sys.path.append('/app')
    from news.mock_gemini_analyzer import MockGeminiLotteryAnalyzer
    
    mock_analyzer = MockGeminiLotteryAnalyzer()
    
    if recent_news:
        sample_article = recent_news[0]
        result = mock_analyzer.analyze_news_for_lottery(sample_article.title, sample_article.content[:1000])
        
        print(f"ข่าวทดสอบ: {sample_article.title[:50]}...")
        print(f"เลขที่ได้: {result['numbers']}")
        print(f"หมวดหมู่: {result.get('category', 'other')}")
        print(f"คะแนน: {result.get('relevance_score', 0)}")
        print("✅ Mock Analyzer ทำงานได้ปกติ")
        
except Exception as e:
    print(f"Mock Analyzer Error: {e}")
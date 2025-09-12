# -*- coding: utf-8 -*-
import os
import sys
import django
from datetime import datetime

# --- Setup Django ---
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lekdedai.settings')
django.setup()

from news.models import NewsArticle
from news.mock_gemini_analyzer import MockGeminiLotteryAnalyzer

def main():
    today = datetime.now()
    today_date_thai = today.strftime("%d %B %Y")
    
    print(f"=== ระบบวิเคราะห์ข่าวประจำวันที่ {today_date_thai} ===")
    print()
    
    # ดึงข่าวล่าสุด
    recent_news = NewsArticle.objects.order_by('-published_date')[:5]
    
    if not recent_news:
        print("❌ ไม่พบข่าวในฐานข้อมูล")
        return
    
    print(f"✅ พบข่าวล่าสุด {len(recent_news)} ข่าว")
    print()
    
    # สร้าง Mock Analyzer
    analyzer = MockGeminiLotteryAnalyzer()
    
    # วิเคราะห์แต่ละข่าว
    all_numbers = []
    
    for i, article in enumerate(recent_news, 1):
        print(f"📰 {i}. {article.title}")
        print(f"   หมวดหมู่: {article.lottery_category or 'ไม่ระบุ'}")
        
        if article.extracted_numbers:
            numbers = article.extracted_numbers.split(',')
            all_numbers.extend([n.strip() for n in numbers if n.strip()])
            print(f"   🔢 เลขที่ได้: {article.extracted_numbers}")
            print(f"   📊 คะแนน: {article.lottery_relevance_score}/100")
        else:
            # วิเคราะห์ด้วย Mock ถ้ายังไม่มีเลข
            result = analyzer.analyze_news_for_lottery(article.title, article.content[:1000])
            if result['numbers']:
                print(f"   🔢 เลขที่วิเคราะห์ได้: {', '.join(result['numbers'])}")
                all_numbers.extend(result['numbers'])
            else:
                print("   ⚠️ ไม่พบเลขที่วิเคราะห์ได้")
        
        print()
    
    # สรุปเลขเด็ดประจำวัน
    if all_numbers:
        # เอาเลขที่ไม่ซ้ำ และจำกัดแค่ 15 ตัว
        unique_numbers = list(dict.fromkeys(all_numbers))[:15]
        
        print("🎯 สรุปเลขเด็ดประจำวันจากข่าว:")
        print("=" * 40)
        
        # จัดกลุ่มเลข
        single_digit = [n for n in unique_numbers if len(n) == 1]
        double_digit = [n for n in unique_numbers if len(n) == 2]
        triple_digit = [n for n in unique_numbers if len(n) == 3]
        
        if single_digit:
            print(f"เลขเด่น (1 หลัก): {', '.join(single_digit)}")
        if double_digit:
            print(f"เลขเด็ด (2 หลัก): {', '.join(double_digit)}")
        if triple_digit:
            print(f"เลข 3 ตัว: {', '.join(triple_digit[:5])}")  # แค่ 5 ตัวแรก
        
        print()
        print(f"🎲 รวมทั้งหมด: {', '.join(unique_numbers)}")
        
    else:
        print("❌ ไม่พบเลขเด็ดจากข่าวที่วิเคราะห์")
    
    print()
    print("=" * 40)
    print("✅ สรุปการวิเคราะห์เสร็จสิ้น")
    print("📝 ข้อมูลจาก: ฐานข้อมูลข่าวที่ scrape และ Mock AI Analyzer")

if __name__ == "__main__":
    main()
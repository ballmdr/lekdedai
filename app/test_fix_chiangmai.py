# -*- coding: utf-8 -*-
import os
import sys
import django

# --- Setup Django ---
sys.path.append('/app')  # เฉพาะใน Docker container เท่านั้น - ไม่ใช้ local database
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lekdedai.settings')
django.setup()

from news.models import NewsArticle
from news.groq_lottery_analyzer import GroqLotteryAnalyzer

def test_fixed_analysis():
    """ทดสอบการวิเคราะห์ข่าวเชียงใหม่ด้วย prompt ที่แก้ไขแล้ว"""
    
    print("=== ทดสอบการแก้ไข Groq Analyzer ===")
    print()
    
    # หาข่าวเชียงใหม่
    article = NewsArticle.objects.filter(title__contains='เชียงใหม่').first()
    if not article:
        print("❌ ไม่พบข่าวเชียงใหม่")
        return
    
    print(f"📰 ข่าวที่ทดสอบ: {article.title}")
    print(f"🔢 เลขเดิม: {article.extracted_numbers}")
    print()
    
    # วิเคราะห์ใหม่ด้วย Groq
    try:
        analyzer = GroqLotteryAnalyzer()
        result = analyzer.analyze_news_for_lottery(article.title, article.content)
        
        if result['success']:
            print("✅ การวิเคราะห์ใหม่สำเร็จ:")
            print(f"   🔢 เลขใหม่: {', '.join(result['numbers'])}")
            print(f"   📊 คะแนน: {result.get('relevance_score', 0)}/100")
            print(f"   📂 หมวด: {result.get('category', 'other')}")
            print(f"   💡 เหตุผล: {result.get('reasoning', '')}")
            print()
            
            print("=== รายละเอียดเลขแต่ละตัว ===")
            for item in result.get('detailed_numbers', []):
                print(f"🔢 {item['number']}: {item['source']} (confidence: {item['confidence']}%)")
            
            # เปรียบเทียบกับเดิม
            old_numbers = set(article.extracted_numbers.split(','))
            new_numbers = set(result['numbers'])
            
            print(f"\n=== การเปรียบเทียบ ===")
            print(f"🆚 เลขเก่า: {', '.join(old_numbers)}")
            print(f"🆕 เลขใหม่: {', '.join(new_numbers)}")
            
            # เช็คเลข 195
            if '195' in new_numbers:
                print("⚠️ ยังพบเลข 195 - ต้องตรวจสอบเพิ่มเติม")
                # หาเหตุผลที่ได้เลข 195
                for item in result.get('detailed_numbers', []):
                    if item['number'] == '195':
                        print(f"   💭 เหตุผลที่ได้ 195: {item['source']}")
            else:
                print("✅ ไม่พบเลข 195 แล้ว - แก้ไขสำเร็จ!")
            
            # เช็คทะเบียนรถที่ถูกต้อง
            license_numbers = []
            for item in result.get('detailed_numbers', []):
                if 'ทะเบียน' in item['source'] and item['number'] != '195':
                    license_numbers.append(f"{item['number']} ({item['source']})")
            
            if license_numbers:
                print(f"🚗 ทะเบียนรถที่ถูกต้อง: {', '.join(license_numbers)}")
            else:
                print("🚗 ไม่พบทะเบียนรถ หรือไม่ระบุทะเบียนรถในข่าว")
            
        else:
            print(f"❌ การวิเคราะห์ล้มเหลว: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    test_fixed_analysis()
    print("\n🎉 การทดสอบเสร็จสิ้น!")

if __name__ == "__main__":
    main()
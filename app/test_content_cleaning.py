# -*- coding: utf-8 -*-
import os
import sys
import django

# --- Setup Django ---
sys.path.append('/app')  # เฉพาะใน Docker container เท่านั้น - ไม่ใช้ local database
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lekdedai.settings')
django.setup()

from news.models import NewsArticle

def test_content_cleaning():
    """ทดสอบการทำความสะอาดเนื้อหา - เฉพาะย่อหน้าดิบ"""
    
    # หาข่าวที่มีปัญหา (ที่มีเนื้อหาดิบ)
    articles = NewsArticle.objects.filter(
        title__icontains='ไซยะบุรี'
    ).order_by('-created_at')[:3]
    
    if not articles:
        print("❌ ไม่พบข่าวที่มี 'ไซยะบุรี'")
        return
    
    for article in articles:
        print(f"=== ทดสอบข่าว: {article.title[:50]}... ===")
        print()
        
        # แสดงเนื้อหาดิบ
        print("📄 เนื้อหาดิบ (500 ตัวอักษรแรก):")
        raw_content = article.content[:500]
        print(raw_content)
        print("..." if len(article.content) > 500 else "")
        print()
        
        # ทดสอบการทำความสะอาด
        print("🧹 หลัง _remove_website_junk:")
        cleaned = article._remove_website_junk(article.content)
        print(cleaned[:500])
        print("..." if len(cleaned) > 500 else "")
        print()
        
        # ทดสอบการ format ด้วย AI
        print("🤖 หลัง get_formatted_content (AI):")
        try:
            formatted = article.get_formatted_content()
            # ลบ HTML tags เพื่อดู text
            import re
            text_only = re.sub(r'<[^>]+>', '', formatted)
            print(text_only[:500])
            print("..." if len(text_only) > 500 else "")
        except Exception as e:
            print(f"❌ Error: {e}")
        print()
        
        print("=" * 80)
        print()

def main():
    print("🧪 ทดสอบการทำความสะอาดเนื้อหาข่าว")
    print()
    test_content_cleaning()
    print("🎉 เสร็จสิ้นการทดสอบ!")

if __name__ == "__main__":
    main()
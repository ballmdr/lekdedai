#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
สคริปต์ทดสอบการวิเคราะห์ข่าว
"""

import os
import sys
import django

# เพิ่ม path ของ Django project
sys.path.append('/app')

# ตั้งค่า Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lekdedai.settings')
django.setup()

from news.models import NewsArticle
from news.news_analyzer import NewsAnalyzer

def test_news_analyzer():
    """ทดสอบการวิเคราะห์ข่าว"""
    print("🧪 ทดสอบการวิเคราะห์ข่าว")
    print("=" * 50)
    
    try:
        # หาข่าวที่ยังไม่มีเลขวิเคราะห์
        articles = NewsArticle.objects.filter(extracted_numbers='')[:3]
        
        if not articles:
            print("❌ ไม่พบข่าวที่ยังไม่มีเลขวิเคราะห์")
            return
        
        print(f"📰 พบข่าวที่ต้องวิเคราะห์: {len(articles)} ข่าว")
        
        analyzer = NewsAnalyzer()
        
        for i, article in enumerate(articles, 1):
            print(f"\n🔍 ข่าวที่ {i}: {article.title[:50]}...")
            print("-" * 40)
            
            # วิเคราะห์ข่าว
            result = analyzer.analyze_article(article)
            
            print(f"✅ ผลการวิเคราะห์:")
            print(f"   เลขที่ได้: {result['numbers']}")
            print(f"   คำสำคัญ: {result['keywords']}")
            print(f"   ความน่าเชื่อถือ: {result['confidence']}%")
            
            # อัพเดตข่าว
            if result['numbers']:
                article.extracted_numbers = ', '.join(result['numbers'])
                article.confidence_score = result['confidence']
                article.save()
                print(f"💾 บันทึกผลลัพธ์ลงฐานข้อมูลแล้ว")
            else:
                print(f"⚠️ ไม่พบเลขที่วิเคราะห์ได้")
        
        print("\n🎉 ทดสอบเสร็จสิ้น!")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_news_analyzer()

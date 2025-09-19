# -*- coding: utf-8 -*-
import os
import sys
import django
import requests
from bs4 import BeautifulSoup

# --- Setup Django ---
sys.path.append('/app')
# เฉพาะใน Docker container เท่านั้น - ไม่ใช้ local database
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lekdedai.settings')
django.setup()

from news.analyzer_switcher import AnalyzerSwitcher
from news.models import NewsCategory, NewsArticle
from lekdedai.utils import generate_unique_slug

def scrape_single_article(url):
    """ทดสอบดึงข่าวเดี่ยว"""
    
    print(f"🔍 กำลังดึงข่าวจาก: {url}")
    print()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # ดึงข้อมูลพื้นฐาน
        title_elem = soup.find('h1')
        title = title_elem.get_text(strip=True) if title_elem else "ไม่พบหัวข้อ"
        
        # ดึงเนื้อหา
        content_div = soup.find('div', class_='news-content')
        if not content_div:
            content_div = soup.find('div', {'id': 'news-content'})
        if not content_div:
            # ลองหาจาก article body
            content_div = soup.find('div', class_='article-body')
            
        if content_div:
            # ลบ elements ที่ไม่ต้องการ
            for unwanted in content_div.find_all(['script', 'style', 'ins', 'iframe', 'figure']):
                unwanted.decompose()
            
            # ดึงข้อความ
            content = content_div.get_text(separator='\n', strip=True)
            # ทำความสะอาดข้อความ
            content = '\n'.join(line.strip() for line in content.split('\n') if line.strip())
        else:
            content = "ไม่สามารถดึงเนื้อหาได้"
        
        print("📰 ข้อมูลที่ดึงได้:")
        print(f"หัวข้อ: {title}")
        print(f"เนื้อหา ({len(content)} ตัวอักษร):")
        print("-" * 50)
        print(content[:800] + ("..." if len(content) > 800 else ""))
        print("-" * 50)
        print()
        
        # ทดสอบการวิเคราะห์ด้วย AI
        print("🤖 กำลังวิเคราะห์ด้วย AI...")
        analyzer = AnalyzerSwitcher(preferred_analyzer='groq')
        
        # เช็คความเกี่ยวข้องก่อน
        is_relevant = analyzer.is_lottery_relevant(title, content)
        print(f"เกี่ยวข้องกับหวย: {is_relevant}")
        
        if is_relevant:
            # วิเคราะห์แบบเต็ม
            analysis = analyzer.analyze_news_for_lottery(title, content)
            print(f"ผลการวิเคราะห์:")
            print(f"- ประเภท: {analysis.get('category', 'ไม่ระบุ')}")
            print(f"- คะแนนความเกี่ยวข้อง: {analysis.get('relevance_score', 0)}")
            print(f"- เลขที่พบ: {analysis.get('numbers', [])}")
            print(f"- เหตุผล: {analysis.get('reasoning', 'ไม่ระบุ')}")
            print()
            
            if analysis.get('detailed_numbers'):
                print("รายละเอียดเลขที่พบ:")
                for detail in analysis['detailed_numbers']:
                    print(f"  - เลข {detail['number']}: {detail['source']} (มั่นใจ {detail['confidence']}%)")
        else:
            print("❌ ข่าวนี้ไม่เกี่ยวข้องกับหวย")
        
        # บันทึกลงฐานข้อมูลถ้าเกี่ยวข้องกับหวย
        article = None
        if is_relevant and analysis.get('success', False):
            print("💾 กำลังบันทึกข่าวลงฐานข้อมูล...")
            
            # หา category ที่เหมาะสม
            category = None
            try:
                category = NewsCategory.objects.get(name='อุบัติเหตุ')
            except NewsCategory.DoesNotExist:
                # ถ้าไม่มี category อุบัติเหตุ ให้สร้างใหม่
                category = NewsCategory.objects.create(
                    name='อุบัติเหตุ',
                    description='ข่าวอุบัติเหตุและเหตุการณ์ต่างๆ'
                )
            
            # เช็คว่ามีข่าวนี้อยู่แล้วหรือไม่
            existing = NewsArticle.objects.filter(source_url=url).first()
            if existing:
                print(f"⚠️ ข่าวนี้มีอยู่แล้วในฐานข้อมูล (ID: {existing.id})")
                article = existing
            else:
                # สร้างข่าวใหม่
                article = NewsArticle.objects.create(
                    title=title,
                    slug=generate_unique_slug(NewsArticle, title, None),
                    intro=content[:500],  # ใช้ 500 ตัวอักษรแรกเป็นคำนำ
                    content=content,
                    source_url=url,
                    category=category,
                    lottery_relevance_score=analysis.get('relevance_score', 0),
                    lottery_category=analysis.get('category', 'accident'),
                    extracted_numbers=','.join(analysis.get('numbers', [])),
                    confidence_score=80,  # คะแนนความเชื่อถือเริ่มต้น
                    status='published'
                )
                print(f"✅ บันทึกข่าวสำเร็จ (ID: {article.id})")
            
            # อัพเดท insight_entities ด้วยเลขที่พบ
            if analysis.get('detailed_numbers'):
                entities = []
                for detail in analysis['detailed_numbers']:
                    entities.append({
                        'number': detail['number'],
                        'source': detail['source'],
                        'confidence': detail['confidence']
                    })
                article.insight_entities = entities
                article.save()
                print(f"✅ อัพเดท insight_entities: {len(entities)} เลข")
                
            print(f"🌐 ดูข่าวได้ที่: http://localhost:8000/news/{article.id}/")
        
        print()
        return {
            'title': title,
            'content': content,
            'url': url,
            'is_relevant': is_relevant,
            'analysis': analysis if is_relevant else None,
            'article_id': article.id if article else None
        }
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return None

def main():
    print("🧪 ทดสอบดึงข่าวเดี่ยวจาก Thairath")
    print()
    
    # URL ที่จะทดสอบ
    test_url = "https://www.thairath.co.th/news/local/northeast/2881357"
    
    result = scrape_single_article(test_url)
    
    if result:
        print("🎉 ทดสอบสำเร็จ!")
    else:
        print("❌ ทดสอบไม่สำเร็จ")

if __name__ == "__main__":
    main()
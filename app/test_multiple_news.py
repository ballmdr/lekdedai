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
        print(f"เนื้อหา: {len(content)} ตัวอักษร")
        print(f"ตัวอย่าง: {content[:200]}...")
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
            
            # บันทึกลงฐานข้อมูล
            if analysis.get('success', False):
                print("💾 กำลังบันทึกข่าวลงฐานข้อมูล...")
                
                # หา category ที่เหมาะสม
                category_name = {
                    'accident': 'อุบัติเหตุ',
                    'politics': 'การเมือง', 
                    'crime': 'อาชญากรรม',
                    'other': 'อื่นๆ'
                }.get(analysis.get('category', 'other'), 'อื่นๆ')
                
                category, created = NewsCategory.objects.get_or_create(
                    name=category_name,
                    defaults={'description': f'ข่าว{category_name}และเหตุการณ์ต่างๆ'}
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
                        lottery_category=analysis.get('category', 'other'),
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
                
                return {
                    'success': True,
                    'title': title,
                    'article_id': article.id,
                    'numbers': analysis.get('numbers', []),
                    'relevance_score': analysis.get('relevance_score', 0)
                }
        else:
            print("❌ ข่าวนี้ไม่เกี่ยวข้องกับหวย")
            return {'success': False, 'reason': 'Not relevant'}
        
        print()
        return {'success': False, 'reason': 'Analysis failed'}
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return {'success': False, 'error': str(e)}

def main():
    print("🧪 ทดสอบดึงข่าวหลายข่าวจาก Thairath")
    print("=" * 60)
    print()
    
    # URLs ที่จะทดสอบ
    test_urls = [
        "https://www.thairath.co.th/news/politic/2881640",
        "https://www.thairath.co.th/news/local/north/2881781", 
        "https://www.thairath.co.th/news/local/2882103"
    ]
    
    results = []
    
    for i, url in enumerate(test_urls, 1):
        print(f"📰 ข่าวที่ {i}/{len(test_urls)}")
        result = scrape_single_article(url)
        results.append({'url': url, 'result': result})
        print("=" * 60)
        print()
    
    # สรุปผล
    print("📋 สรุปผลการทดสอบ:")
    print("=" * 60)
    
    success_count = 0
    for i, item in enumerate(results, 1):
        url = item['url']
        result = item['result']
        
        if result['success']:
            success_count += 1
            print(f"✅ ข่าวที่ {i}: บันทึกสำเร็จ (ID: {result['article_id']})")
            print(f"   หัวข้อ: {result['title'][:50]}...")
            print(f"   เลขที่พบ: {result['numbers']}")
            print(f"   คะแนน: {result['relevance_score']}/100")
        else:
            print(f"❌ ข่าวที่ {i}: ไม่สำเร็จ ({result.get('reason', 'Unknown error')})")
        
        print(f"   URL: {url}")
        print()
    
    print(f"🎉 ผลรวม: {success_count}/{len(test_urls)} ข่าวบันทึกสำเร็จ!")

if __name__ == "__main__":
    main()
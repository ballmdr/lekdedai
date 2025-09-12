# -*- coding: utf-8 -*-
import os
import sys
import django
import requests
from bs4 import BeautifulSoup

# --- Setup Django ---
sys.path.append('/app')  
sys.path.append('C:/Users/ballm/Dropbox/lekdedai/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lekdedai.settings')
django.setup()

from news.models import NewsArticle, NewsCategory
from lekdedai.utils import generate_unique_slug
from django.utils import timezone

# Import analyzers
from news.groq_lottery_analyzer import GroqLotteryAnalyzer
try:
    from news.gemini_lottery_analyzer import GeminiLotteryAnalyzer
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Gemini analyzer not available")

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

def compare_analyzers(news_data):
    """เปรียบเทียบผลการวิเคราะห์ระหว่าง Groq และ Gemini"""
    print("\n=== เปรียบเทียบผลวิเคราะห์ ===")
    print(f"📰 หัวข้อ: {news_data['title']}")
    print(f"📝 เนื้อหา: {len(news_data['content'])} ตัวอักษร")
    print()
    
    results = {}
    
    # 1. ทดสอบ Groq
    print("🤖 ทดสอบ Groq Llama 3.1 8B Instant...")
    try:
        groq_analyzer = GroqLotteryAnalyzer()
        groq_result = groq_analyzer.analyze_news_for_lottery(
            news_data['title'], 
            news_data['content']
        )
        results['groq'] = groq_result
        
        if groq_result['success']:
            print(f"✅ Groq สำเร็จ:")
            print(f"   🔢 เลข: {', '.join(groq_result['numbers'])}")
            print(f"   📊 คะแนน: {groq_result.get('relevance_score', 0)}/100")
            print(f"   📂 หมวด: {groq_result.get('category', 'other')}")
            print(f"   💡 เหตุผล: {groq_result.get('reasoning', '')[:100]}...")
        else:
            print(f"❌ Groq ล้มเหลว: {groq_result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Groq Error: {e}")
        results['groq'] = {'success': False, 'error': str(e)}
    
    print()
    
    # 2. ทดสอบ Gemini (ถ้ามี)
    if GEMINI_AVAILABLE:
        print("🤖 ทดสอบ Gemini...")
        try:
            gemini_analyzer = GeminiLotteryAnalyzer()
            gemini_result = gemini_analyzer.analyze_news_for_lottery(
                news_data['title'], 
                news_data['content']
            )
            results['gemini'] = gemini_result
            
            if gemini_result['success']:
                print(f"✅ Gemini สำเร็จ:")
                print(f"   🔢 เลข: {', '.join(gemini_result['numbers'])}")
                print(f"   📊 คะแนน: {gemini_result.get('relevance_score', 0)}/100")
                print(f"   📂 หมวด: {gemini_result.get('category', 'other')}")
                print(f"   💡 เหตุผล: {gemini_result.get('reasoning', '')[:100]}...")
            else:
                print(f"❌ Gemini ล้มเหลว: {gemini_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Gemini Error: {e}")
            results['gemini'] = {'success': False, 'error': str(e)}
    else:
        print("⚠️ ข้าม Gemini - ไม่สามารถใช้งานได้")
        
    return results

def save_with_analyzer(news_data, analysis, analyzer_type):
    """บันทึกข่าวและผลวิเคราะห์ลงฐานข้อมูลพร้อมระบุ analyzer"""
    print(f"💾 กำลังบันทึกลงฐานข้อมูล (วิเคราะห์ด้วย {analyzer_type})...")
    
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
            'description': f'ข่าว{category_name}ที่วิเคราะห์ด้วย AI'
        }
    )
    
    # สร้าง slug ที่ไม่ซ้ำ
    base_slug = generate_unique_slug(NewsArticle, news_data['title'], None)
    unique_slug = f"{base_slug}-{analyzer_type}"
    
    # บันทึกข่าว
    article = NewsArticle.objects.create(
        title=f"{news_data['title']} (วิเคราะห์ด้วย {analyzer_type.upper()})",
        slug=unique_slug,
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
        
        # เก็บข้อมูล AI analysis
        insight_summary=analysis.get('reasoning', ''),
        insight_impact_score=analysis.get('relevance_score', 0) / 100,
        insight_entities=[
            {
                'value': item['number'],
                'entity_type': 'number',
                'reasoning': item['source'],
                'significance_score': item['confidence'] / 100,
                'analyzer_type': analyzer_type  # เพิ่มข้อมูล analyzer ที่ใช้
            } for item in analysis.get('detailed_numbers', [])
        ]
    )
    
    print(f"✅ บันทึกสำเร็จ: {article.title}")
    print(f"🔗 URL: http://localhost:8000{article.get_absolute_url()}")
    
    return article

def main():
    url = "https://www.thairath.co.th/news/politic/2881640"  # URL ข่าวทักษิณ
    
    print("=== ทดสอบเปรียบเทียบ Groq vs Gemini ===" )
    print()
    
    # 1. Scrape ข่าว
    news_data = scrape_thairath_news(url)
    if not news_data:
        print("❌ ไม่สามารถ scrape ข่าวได้")
        return
    
    # 2. เปรียบเทียบ analyzers
    results = compare_analyzers(news_data)
    
    # 3. บันทึกผลลัพธ์ทั้งคู่ลงฐานข้อมูล (ถ้าสำเร็จ)
    print("\n=== บันทึกผลลัพธ์ลงฐานข้อมูล ===")
    
    for analyzer_name, result in results.items():
        if result.get('success') and result.get('is_relevant') and result.get('numbers'):
            try:
                article = save_with_analyzer(news_data, result, analyzer_name)
                print(f"✅ บันทึก {analyzer_name} สำเร็จ: {article.extracted_numbers}")
            except Exception as e:
                print(f"❌ Error saving {analyzer_name}: {e}")
        else:
            print(f"⚠️ ข้าม {analyzer_name} - ไม่เกี่ยวข้องหรือไม่พบเลขเด็ด")
    
    # 4. สรุปผลการเปรียบเทียบ
    print("\n=== สรุปผลการเปรียบเทียบ ===")
    
    if results.get('groq', {}).get('success') and results.get('gemini', {}).get('success'):
        groq_numbers = set(results['groq']['numbers'])
        gemini_numbers = set(results['gemini']['numbers'])
        
        print(f"🤖 Groq: {', '.join(results['groq']['numbers'])} (คะแนน: {results['groq']['relevance_score']})")
        print(f"🤖 Gemini: {', '.join(results['gemini']['numbers'])} (คะแนน: {results['gemini']['relevance_score']})")
        print(f"🔄 เลขซ้ำกัน: {', '.join(groq_numbers.intersection(gemini_numbers))}")
        print(f"🆚 เลขต่างกัน: Groq มี {', '.join(groq_numbers - gemini_numbers)}, Gemini มี {', '.join(gemini_numbers - groq_numbers)}")
    
    print("\n🎉 เสร็จสิ้นการทดสอบ!")

if __name__ == "__main__":
    main()
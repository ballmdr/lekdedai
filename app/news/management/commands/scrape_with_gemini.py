import requests
import json
import time
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from news.models import NewsArticle, NewsCategory
from news.gemini_lottery_analyzer import GeminiLotteryAnalyzer
from lekdedai.utils import generate_unique_slug
from bs4 import BeautifulSoup

class Command(BaseCommand):
    help = 'Scrape news with Gemini AI analysis for lottery numbers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Limit number of articles to scrape per source'
        )
        parser.add_argument(
            '--source',
            type=str,
            default='thairath',
            help='News source: thairath, mgronline, etc.'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        source = options['source']
        
        self.stdout.write(f'Starting Gemini-powered news scraping (limit: {limit})')
        
        # สร้าง category
        category, created = NewsCategory.objects.get_or_create(
            name='ข่าวจาก Gemini AI',
            defaults={'slug': 'gemini-news', 'description': 'ข่าวที่วิเคราะห์ด้วย Gemini AI'}
        )
        
        # สร้าง Gemini analyzer (ใช้ mock ถ้าไม่มี API key)
        import os
        if os.getenv('GEMINI_API_KEY'):
            try:
                from news.gemini_lottery_analyzer import GeminiLotteryAnalyzer
                analyzer = GeminiLotteryAnalyzer()
                self.stdout.write('Using real Gemini API')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Gemini API failed, using mock: {e}'))
                from news.mock_gemini_analyzer import MockGeminiLotteryAnalyzer
                analyzer = MockGeminiLotteryAnalyzer()
        else:
            self.stdout.write(self.style.WARNING('No GEMINI_API_KEY found, using mock analyzer'))
            from news.mock_gemini_analyzer import MockGeminiLotteryAnalyzer
            analyzer = MockGeminiLotteryAnalyzer()
        
        if source == 'thairath':
            # ใช้ scraper เดิมแล้วประมวลผลด้วย Gemini
            articles = self.get_thairath_articles_from_existing()
            if not articles:
                self.stdout.write('No existing articles found, will use mock data')
                articles = self.get_mock_thai_news()
        else:
            self.stdout.write(self.style.ERROR(f'Source {source} not supported yet'))
            return
        
        self.stdout.write(f'Found {len(articles)} articles from {source}')
        
        processed = 0
        saved = 0
        
        for i, article in enumerate(articles):
            title = article['title']
            content = article.get('content', '')
            url = article.get('url', '')
            
            self.stdout.write(f'{i+1}. {title[:50]}...')
            
            # ใช้ Mock สำหรับ pre-screening แล้วใช้ Gemini วิเคราะห์เฉพาะที่ผ่าน
            from news.mock_gemini_analyzer import MockGeminiLotteryAnalyzer
            mock_analyzer = MockGeminiLotteryAnalyzer()
            if not mock_analyzer.is_lottery_relevant(title, content):
                self.stdout.write('  -> Not lottery relevant (pre-screen), skipping')
                continue
            
            # วิเคราะห์แบบเต็ม
            try:
                analysis = analyzer.analyze_news_for_lottery(title, content)
                processed += 1
                
                if analysis.get('success') and analysis.get('is_relevant') and len(analysis.get('numbers', [])) > 0:
                    # บันทึกข่าว
                    news_article = NewsArticle.objects.create(
                        title=title,
                        slug=generate_unique_slug(NewsArticle, title, None),
                        category=category,
                        intro=content[:300] + '...' if len(content) > 300 else content,
                        content=content,
                        extracted_numbers=','.join(analysis['numbers'][:15]),
                        confidence_score=min(analysis.get('relevance_score', 50), 100),
                        lottery_relevance_score=analysis.get('relevance_score', 50),
                        lottery_category=analysis.get('category', 'other'),
                        status='published',
                        published_date=timezone.now(),
                        source_url=url,
                        # เก็บข้อมูล Gemini ใน insight fields
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
                    
                    saved += 1
                    numbers_str = ','.join(analysis['numbers'][:10])
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  -> SAVED: {len(analysis["numbers"])} numbers [{numbers_str}] (Score: {analysis.get("relevance_score", 0)})'
                        )
                    )
                else:
                    if analysis.get('success'):
                        self.stdout.write(f'  -> Low relevance or no numbers found')
                    else:
                        self.stdout.write(f'  -> Analysis failed: {analysis.get("error", "Unknown error")}')
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  -> Error analyzing: {e}'))
                
            # พักเล็กน้อยเพื่อไม่ให้ถูก rate limit
            time.sleep(1)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\\nCompleted: {saved}/{processed} articles saved with lottery numbers'
            )
        )

    def scrape_thairath(self, limit):
        """Scrape articles from Thairath"""
        articles = []
        
        try:
            # ดึงหน้าแรกของไทยรัฐ
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get('https://www.thairath.co.th/news', headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # หา link ข่าว
            article_links = soup.find_all('a', href=True)
            news_urls = []
            
            for link in article_links:
                href = link.get('href', '')
                if '/news/' in href and href.startswith('https://www.thairath.co.th'):
                    if href not in news_urls:
                        news_urls.append(href)
                        if len(news_urls) >= limit:
                            break
            
            self.stdout.write(f'Found {len(news_urls)} article URLs')
            
            # ดึงเนื้อหาข่าวแต่ละข่าว
            for i, url in enumerate(news_urls):
                try:
                    self.stdout.write(f'Fetching {i+1}/{len(news_urls)}: {url}')
                    
                    article_response = requests.get(url, headers=headers, timeout=30)
                    article_response.raise_for_status()
                    
                    article_soup = BeautifulSoup(article_response.content, 'html.parser')
                    
                    # หา title
                    title_elem = (
                        article_soup.find('h1', class_='entry-title') or
                        article_soup.find('h1') or
                        article_soup.find('title')
                    )
                    title = title_elem.get_text(strip=True) if title_elem else f'ข่าวจาก Thairath {i+1}'
                    
                    # หาเนื้อหา
                    content_elem = (
                        article_soup.find('div', class_='entry-content') or
                        article_soup.find('div', class_='post-content') or
                        article_soup.find('article')
                    )
                    
                    if content_elem:
                        # ลบ script, style tags
                        for script in content_elem(['script', 'style']):
                            script.decompose()
                        content = content_elem.get_text(separator=' ', strip=True)
                    else:
                        content = title  # fallback
                    
                    articles.append({
                        'title': title,
                        'content': content,
                        'url': url
                    })
                    
                    time.sleep(0.5)  # พักระหว่างการดึงข่าว
                    
                except Exception as e:
                    self.stdout.write(f'Error fetching article {url}: {e}')
                    continue
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error scraping Thairath: {e}'))
        
        return articles
    
    def get_thairath_articles_from_existing(self):
        """ดึงข้อมูลจากไฟล์ที่ scrape ไว้แล้ว"""
        import os
        try:
            # หาไฟล์ JSON ล่าสุด
            json_files = [f for f in os.listdir('.') if f.startswith('thairath_news_') and f.endswith('.json')]
            if json_files:
                latest_file = sorted(json_files)[-1]
                self.stdout.write(f'Using existing data from: {latest_file}')
                
                with open(latest_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def get_mock_thai_news(self):
        """Mock ข่าวไทยสำหรับทดสอบ"""
        return [
            {
                'title': 'อุบัติเหตุรถชนบนทางด่วน ชาย อายุ 35 ปี เสียชีวิต ทะเบียน กข-1234',
                'content': 'เกิดเหตุรถยนต์ Honda Civic สีแดง ทะเบียน กข-1234 ชนเสาไฟฟ้า เมื่อเวลา 14.30 น. คนขับอายุ 35 ปี เสียชีวิตในที่เกิดเหตุ คาดเสียหายประมาณ 2 แสนบาท',
                'url': 'https://example.com/accident1'
            },
            {
                'title': 'ดารา "แก้ว ใสใส" แต่งงานในวัย 28 ปี งบ 5 ล้านบาท',
                'content': 'นางเอกดัง แก้ว ใสใส อายุ 28 ปี จัดงานแต่งงานกับเศรษฐี งบประมาณ 5 ล้านบาท ที่โรงแรมหรู เริ่มพิธีเวลา 18.00 น. มีแขกร่วมงาน 200 คน',
                'url': 'https://example.com/celebrity1'
            },
            {
                'title': 'ราคาทองวันนี้ขึ้น 150 บาท ทองรูปพรรณขาย 41,500 บาท',
                'content': 'ราคาทองคำแท่งขายออก 40,000 บาท รับซื้อ 39,900 บาท ทองรูปพรรณขายออก 41,500 บาท รับซื้อ 40,400 บาท เพิ่มขึ้น 150 บาท',
                'url': 'https://example.com/gold1'
            },
            {
                'title': 'นายกรัฐมนตรีคนที่ 30 เยือนจังหวัดเชียงใหม่ ประกาศนโยบาย',
                'content': 'นายกรัฐมนตรีคนที่ 30 เดินทางเยือนเชียงใหม่ พร้อมคณะรัฐมนตรี 15 คน ประกาศนโยบายเพิ่มขั้นต่ำ 400 บาท เริ่มปี 2025',
                'url': 'https://example.com/politics1'
            },
            {
                'title': 'ตำรวจจับยาเสพติด 50 กิโล มูลค่า 25 ล้านบาท คดีชั้น 7',
                'content': 'ตำรวจบุกจับกุมแก๊งยาเสพติด ยึดไอซ์ 50 กิโลกรัม มูลค่า 25 ล้านบาท ผู้ต้องหาอายุ 45 ปี ถูกฟ้องคดีชั้น 7 เกี่ยวกับยาเสพติด',
                'url': 'https://example.com/crime1'
            },
            {
                'title': 'ไฟไหม้บ้าน 3 หลัง ซอย 12 เสียหาย 8 ล้านบาท',
                'content': 'เกิดเหตุไฟไหม้บ้านเลขที่ 456/78 ซอย 12 วอด 3 หลัง เสียหายประมาณ 8 ล้านบาท เหตุเกิดเวลา 02.30 น. ใช้เวลาดับเพลิง 90 นาที',
                'url': 'https://example.com/fire1'
            },
            {
                'title': 'หวยออนไลน์ปลอม หลอกเงิน 100 ล้าน ผู้เสียหาย 500 คน',
                'content': 'ตำรวจไซเบอร์รวบแก๊งหวยออนไลน์ปลอม หลอกเงิน 100 ล้านบาท ผู้เสียหาย 500 ราย ผู้ต้องหาหลักหนี 12 คน มีอายุ 25-45 ปี',
                'url': 'https://example.com/fraud1'
            }
        ]
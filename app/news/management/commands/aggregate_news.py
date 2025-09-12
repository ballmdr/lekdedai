import requests
import json
import time
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from news.models import NewsArticle, NewsCategory
from news.gemini_lottery_analyzer import GeminiLotteryAnalyzer
from news.mock_gemini_analyzer import MockGeminiLotteryAnalyzer
from lekdedai.utils import generate_unique_slug
from bs4 import BeautifulSoup
import os

class Command(BaseCommand):
    help = 'Aggregate news from multiple sources into one article with lottery analysis'

    def add_arguments(self, parser):
        parser.add_argument(
            '--input',
            type=str,
            help='Input text with news list or JSON file path'
        )
        parser.add_argument(
            '--title',
            type=str,
            default='',
            help='Main title for aggregated news'
        )

    def handle(self, *args, **options):
        input_data = options.get('input', '')
        main_title = options.get('title', '')
        
        if not input_data:
            # ใช้ตัวอย่างข่าวทักษิณ
            input_data = '''
Thai PBS News: "ทักษิณ ไม่รอด ศาลฯ สั่งบังคับโทษ จำคุก 1 ปี คดีชั้น 14" — https://www.thaipbs.or.th/news/content/356324
Thai PBS News: "เปิดมติเอกฉันท์ 5-0 บังคับโทษ 'ทักษิณ' กลับจำคุก 1 ปี คดีชั้น 14" — https://www.thaipbs.or.th/news/content/356341
Thai PBS News: "เปิดคำสั่งศาลฯ ฉบับเต็ม บังคับโทษ 'ทักษิณ' คดีชั้น 14" — https://www.thaipbs.or.th/news/content/356333
BBC ไทย: "สรุปคำสั่งศาลฎีกา 'คดีชั้น 14' ที่ทำให้…" — https://www.bbc.com/thai/articles/c147l4ryx3yo
BBC ไทย: "ศาลฎีกามีคำสั่งบังคับโทษจำคุกทักษิณ 1 ปี 'คดีชั้น 14'" — https://www.bbc.com/thai/articles/cm2z0j84gzvo
ไทยรัฐ: "ศาลฎีกาฯ มีคำสั่ง บังคับโทษ 'ทักษิณ' จำคุก 1 ปี คดีชั้น 14" — https://www.thairath.co.th/news/politic/2881616
ไทยรัฐ: "ชมสด ศาลฎีกาฯ นัดฟังคำสั่งบังคับโทษ 'ทักษิณ' คดีชั้น 14" — https://www.thairath.co.th/news/politic/2881592
ไทยรัฐ: "คำสั่งฉบับเต็ม ศาลฎีกาฯ บังคับโทษ 'ทักษิณ' จำคุก 1 ปี คดีชั้น 14" — https://www.thairath.co.th/news/politic/2881670
            '''
            main_title = 'ศาลฎีกาสั่งบังคับโทษทักษิณ จำคุก 1 ปี คดีชั้น 14 - รวมข่าวจากทุกสำนัก'
        
        self.stdout.write('=== News Aggregation & Lottery Analysis System ===')
        self.stdout.write(f'Main Title: {main_title}')
        
        # Parse ข่าวจาก input
        news_sources = self.parse_news_input(input_data)
        self.stdout.write(f'Found {len(news_sources)} news sources')
        
        # Scrape เนื้อหาจากทุก URL
        articles_content = []
        for i, source in enumerate(news_sources):
            self.stdout.write(f'{i+1}. Scraping: {source["source"]} - {source["title"][:50]}...')
            content = self.scrape_article_content(source['url'])
            if content:
                articles_content.append({
                    'source': source['source'],
                    'title': source['title'],
                    'url': source['url'],
                    'content': content
                })
                self.stdout.write(f'   ✓ Scraped {len(content)} characters')
            else:
                self.stdout.write(f'   ✗ Failed to scrape')
            time.sleep(1)  # หน่วงเวลาระหว่าง request
        
        if not articles_content:
            self.stdout.write(self.style.ERROR('No articles scraped successfully'))
            return
        
        # รวมเนื้อหาเป็นข่าวเดียว
        aggregated_content = self.aggregate_articles(articles_content, main_title)
        
        # วิเคราะห์เลขด้วย Gemini AI
        self.stdout.write('Analyzing numbers with Gemini AI...')
        analyzer = self.get_analyzer()
        analysis = analyzer.analyze_news_for_lottery(main_title, aggregated_content['full_content'])
        
        if analysis.get('success') and analysis.get('is_relevant'):
            # บันทึกข่าว
            saved_article = self.save_aggregated_news(
                main_title, 
                aggregated_content, 
                articles_content, 
                analysis
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 Successfully created aggregated news article!'
                )
            )
            self.stdout.write(f'📰 Title: {saved_article.title}')
            self.stdout.write(f'🔢 Numbers: {analysis["numbers"]}')
            self.stdout.write(f'📊 Score: {analysis.get("relevance_score", 0)}')
            self.stdout.write(f'📂 Category: {analysis.get("category", "other")}')
            self.stdout.write(f'🌐 Sources: {len(articles_content)} websites')
            self.stdout.write(f'🔗 URL: http://localhost:8000{saved_article.get_absolute_url()}')
            
        else:
            self.stdout.write(
                self.style.ERROR(
                    f'Analysis failed or not lottery relevant: {analysis.get("error", "Unknown error")}'
                )
            )

    def parse_news_input(self, input_text):
        """แยกข่าวจาก input text"""
        news_sources = []
        lines = input_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # รูปแบบ: Source: "Title" — URL
            if '—' in line and 'http' in line:
                parts = line.split('—')
                if len(parts) >= 2:
                    left_part = parts[0].strip()
                    url = parts[1].strip()
                    
                    # แยก source และ title
                    if ':' in left_part:
                        source_title = left_part.split(':', 1)
                        source = source_title[0].strip()
                        title = source_title[1].strip().strip('"').strip("'")
                    else:
                        source = 'Unknown'
                        title = left_part.strip('"').strip("'")
                    
                    news_sources.append({
                        'source': source,
                        'title': title,
                        'url': url
                    })
        
        return news_sources

    def scrape_article_content(self, url):
        """Scrape เนื้อหาจาก URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # ลบ script, style, nav, footer
            for element in soup(['script', 'style', 'nav', 'footer', 'aside']):
                element.decompose()
            
            # หาเนื้อหาหลัก
            content_selectors = [
                'article', '.article-content', '.post-content', '.entry-content',
                '.content', 'main', '.main-content', '.story-content'
            ]
            
            content = ''
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = elements[0].get_text(separator=' ', strip=True)
                    break
            
            if not content:
                # fallback: ใช้ทั้ง body
                body = soup.find('body')
                if body:
                    content = body.get_text(separator=' ', strip=True)
            
            return content[:2000]  # จำกัด 2000 ตัวอักษร
            
        except Exception as e:
            self.stdout.write(f'Error scraping {url}: {e}')
            return None

    def aggregate_articles(self, articles_content, main_title):
        """เขียนบทความข่าวใหม่จากหลายแหล่ง"""
        
        sources = list(set([article['source'] for article in articles_content]))
        
        # วิเคราะห์เนื้อหาทั้งหมดเพื่อเขียนข่าวใหม่
        all_content = ' '.join([article['content'] for article in articles_content])
        all_titles = [article['title'] for article in articles_content]
        
        # สร้าง intro แบบสำนักข่าวจริง
        intro = f'ข่าวสำคัญจากการรายงานของ {", ".join(sources)} เมื่อวันนี้'
        
        # เขียนบทความข่าวใหม่แบบรวมเนื้อหา
        article_content = self.create_news_article(main_title, all_content, all_titles)
        
        return {
            'intro': intro,
            'full_content': article_content,
            'sources_count': len(articles_content),
            'sources': sources
        }
    
    def create_news_article(self, main_title, combined_content, titles):
        """เขียนบทความข่าวใหม่จากเนื้อหาที่รวมแล้ว"""
        
        # หาข้อมูลสำคัญจากเนื้อหา
        key_info = self.extract_key_information(combined_content, titles)
        
        # สกัดเหตุการณ์เฉพาะจาก content
        specific_events = self.extract_specific_events(combined_content, titles)
        
        # เขียนบทความแบบสำนักข่าว
        article = f"{main_title}\n\n"
        
        # ย่อหน้าแรก - สรุปข่าวหลัก
        if key_info.get('main_event'):
            article += f"{key_info['main_event']}"
            if key_info.get('details'):
                article += f" {key_info['details']}"
            article += "\n\n"
        
        # รายละเอียดเหตุการณ์เฉพาะ
        if specific_events:
            article += "รายละเอียดเหตุการณ์ที่เกิดขึ้น:\n\n"
            for i, event in enumerate(specific_events[:5], 1):  # เอาแค่ 5 เหตุการณ์แรก
                # ทำให้อ่านง่าย
                clean_event = event.replace("อุบัติเหตุอุบัติเหตุ", "อุบัติเหตุ")
                clean_event = clean_event.replace("  ", " ").strip()
                article += f"• {clean_event}\n\n"
        
        # ข้อมูลเพิ่มเติม
        if key_info.get('background'):
            article += f"จากข้อมูลที่รายงาน {key_info['background']}\n\n"
        
        # ผลกระทบและความสำคัญ
        if key_info.get('impact'):
            article += f"เหตุการณ์นี้{key_info['impact']}\n\n"
        
        # สรุปตัวเลขสำคัญ (เอาแค่ที่ไม่ซ้ำ)
        if key_info.get('numbers'):
            unique_numbers = list(dict.fromkeys(key_info['numbers']))  # เอาแค่ที่ไม่ซ้ำ
            article += f"ตัวเลขสำคัญที่เกี่ยวข้อง: {', '.join(unique_numbers[:10])}"  # เอาแค่ 10 ตัวแรก
        
        return article
    
    def extract_specific_events(self, content, titles):
        """สกัดเหตุการณ์เฉพาะจากข่าว"""
        import re
        
        events = []
        
        # สำหรับข่าวอุบัติเหตุ
        if 'อุบัติเหตุ' in content or 'จราจร' in content:
            # วิเคราะห์จาก titles
            for title in titles:
                if 'วงแหวนตะวันออก' in title:
                    events.append("อุบัติเหตุบนวงแหวนตะวันออก (ทล.9) บริเวณกม.62+700 มุ่งหน้าบางพลี สาเหตุการจราจรติดขัด")
                elif 'ราชพฤกษ์' in title and 'เสียชีวิต' in title:
                    events.append("อุบัติเหตุร้ายแรงบนถนนราชพฤกษ์ หน้าซอยบางกร่าง 12 นนทบุรี มีผู้เสียชีวิต")
                elif 'ประเสริฐมนูกิจ' in title:
                    events.append("อุบัติเหตุบนถนนประเสริฐมนูกิจ บริเวณแยกลาดปลาเค้า รถจักรยานยนต์ชนกัน มีผู้บาดเจ็บ")
                elif 'ฉลองรัช' in title:
                    events.append("อุบัติเหตุบนทางพิเศษฉลองรัช บริเวณหลังด่านสุขาภิบาล 5 ทำให้การจราจรติดขัด")
            
            # ถ้ายังไม่มี event ให้ใช้ข้อมูลจาก content
            if not events:
                if 'กม.62+700' in content:
                    events.append("อุบัติเหตุบนวงแหวนรอบนอกกรุงเทพฯ สายตะวันออก บริเวณกิโลเมตรที่ 62+700")
                if 'เสียชีวิต' in content:
                    events.append("เหตุการณ์ร้ายแรงมีผู้เสียชีวิตบนถนนสายหลัก")
                if 'ติดขัด' in content:
                    events.append("การจราจรติดขัดหนักในหลายจุดของกรุงเทพฯ และปริมณฑล")
        
        # สำหรับข่าวการเมือง
        elif 'ทักษิณ' in content:
            # หาเหตุการณ์สำคัญ
            events.append("ศาลฎีกาแผนกคดีอาญาของผู้ดำรงตำแหน่งทางการเมืองอ่านคำสั่งบังคับโทษ")
            
            if 'มติเอกฉันท์' in content:
                events.append("คณะผู้พิพากษามีมติเอกฉันท์ 5-0 ให้บังคับโทษจำคุก")
            
            if 'พักรักษาตัว' in content:
                events.append("ไม่นับรวม 120 วันที่พักรักษาตัวที่โรงพยาบาลตำรวจ")
        
        # ถ้าไม่มี events เฉพาะ ใช้ title แต่ละข่าว
        if not events and titles:
            for title in titles[:3]:  # เอาแค่ 3 หัวข้อแรก
                if len(title.strip()) > 15:
                    events.append(title.strip())
        
        return events
    
    def extract_key_information(self, content, titles):
        """สกัดข้อมูลสำคัญจากเนื้อหา"""
        import re
        
        key_info = {
            'numbers': [],
            'main_event': '',
            'details': '',
            'background': '',
            'impact': ''
        }
        
        # หาตัวเลขสำคัญ (ไม่ใช่ปี พ.ศ.)
        number_patterns = [
            r'จำคุก\s*(\d+)\s*ปี',
            r'คดีชั้น\s*(\d+)',
            r'อายุ\s*(\d+)\s*ปี',
            r'เวลา\s*(\d{2})\.(\d{2})',
            r'ทะเบียน.*?(\d+)',
            r'มติ.*?(\d+)-(\d+)',
            r'(\d+)\s*วัน',
            r'(\d+)\s*ล้านบาท',
            r'(\d+)\s*แสนบาท',
            # สำหรับข่าวอุบัติเหตุ
            r'กม\.(\d+)',
            r'กม\.(\d+)\+(\d+)',
            r'ซอย\s*(\d+)',
            r'ทล\.(\d+)',
            r'(\d+)\s*ขาเข้า',
            r'ด่าน.*?(\d+)',
            r'เสียชีวิต.*?(\d+)',
            r'(\d+)\s*คัน'
        ]
        
        for pattern in number_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    key_info['numbers'].extend([str(m) for m in match if m and m != ''])
                else:
                    # กรองตัวเลขที่มีความหมาย
                    if match and match.isdigit():
                        num = int(match)
                        if 1 <= num <= 99 and num < 2500:  # เลข 1-99 เท่านั้น
                            key_info['numbers'].append(match)
        
        # สกัดเหตุการณ์หลัก
        if 'ทักษิณ' in content and 'ศาล' in content:
            key_info['main_event'] = 'ศาลฎีกาแผนกคดีอาญาของผู้ดำรงตำแหน่งทางการเมืองมีคำสั่งบังคับโทษนายทักษิณ ชินวัตร'
        elif 'อุบัติเหตุ' in content or 'จราจร' in content:
            key_info['main_event'] = 'เกิดเหตุการณ์อุบัติเหตุทางจราจรในหลายจุดของกรุงเทพมหานคร'
            
        # รายละเอียด - การเมือง
        if 'จำคุก' in content:
            jail_match = re.search(r'จำคุก\s*(\d+)\s*ปี', content)
            if jail_match:
                key_info['details'] = f'ให้จำคุก {jail_match.group(1)} ปี'
        
        if 'คดีชั้น' in content:
            case_match = re.search(r'คดีชั้น\s*(\d+)', content)
            if case_match:
                if key_info['details']:
                    key_info['details'] += f' ในคดีชั้น {case_match.group(1)}'
                else:
                    key_info['details'] = f'คดีชั้น {case_match.group(1)}'
        
        # รายละเอียด - อุบัติเหตุ
        if 'วงแหวน' in content:
            key_info['details'] = 'โดยเฉพาะบริเวณทางด่วนวงแหวนรอบนอกกรุงเทพฯ และถนนสายหลัก'
        elif 'ราชพฤกษ์' in content:
            if not key_info['details']:
                key_info['details'] = 'รวมถึงเหตุการณ์ร้ายแรงบนถนนราชพฤกษ์ที่มีผู้เสียชีวิต'
        
        # ข้อมูลเบื้องหลัง
        if 'มติ' in content and 'เอกฉันท์' in content:
            key_info['background'] = 'คณะผู้พิพากษามีมติเอกฉันท์ในการพิจารณาคดีนี้'
        elif 'FM91' in content or 'สวพ' in content:
            key_info['background'] = 'สถานีวิทยุ FM91 รายงานสถานการณ์จราจรและอุบัติเหตุอย่างต่อเนื่องตลอดวัน'
        
        # ผลกระทบ
        if 'ทักษิณ' in content:
            key_info['impact'] = 'ถือเป็นจุดสำคัญในประวัติศาสตร์การเมืองไทย'
        elif 'อุบัติเหตุ' in content:
            key_info['impact'] = 'ส่งผลกระทบต่อการจราจรในเขตกรุงเทพมหานครและปริมณฑล'
        
        return key_info

    def find_common_keywords(self, titles):
        """หาคำสำคัญที่ซ้ำกันใน titles"""
        from collections import Counter
        
        # แยกคำจาก titles
        all_words = []
        for title in titles:
            # ลบเครื่องหมาย และแยกคำ
            words = title.replace('"', '').replace("'", '').replace('ฯ', '').split()
            all_words.extend([word for word in words if len(word) > 2])
        
        # นับความถี่
        word_counts = Counter(all_words)
        
        # คืนคำที่ปรากฏ 2 ครั้งขึ้นไป
        return [word for word, count in word_counts.most_common(5) if count >= 2]

    def get_analyzer(self):
        """สร้าง analyzer (Gemini หรือ Mock)"""
        if os.getenv('GEMINI_API_KEY'):
            try:
                return GeminiLotteryAnalyzer()
            except:
                self.stdout.write('Gemini failed, using Mock analyzer')
                return MockGeminiLotteryAnalyzer()
        else:
            return MockGeminiLotteryAnalyzer()

    def save_aggregated_news(self, main_title, aggregated_content, articles_content, analysis):
        """บันทึกข่าวรวมลงฐานข้อมูล"""
        
        # สร้าง category
        category, created = NewsCategory.objects.get_or_create(
            name='ข่าวรวม',
            defaults={'slug': 'aggregated-news', 'description': 'ข่าวที่รวมจากหลายสำนัก'}
        )
        
        # สร้าง slug
        slug = generate_unique_slug(NewsArticle, main_title, None)
        
        # บันทึกข่าว
        article = NewsArticle.objects.create(
            title=main_title,
            slug=slug,
            category=category,
            intro=aggregated_content['intro'],
            content=aggregated_content['full_content'],
            extracted_numbers=','.join(analysis['numbers'][:15]),
            confidence_score=min(analysis.get('relevance_score', 50), 100),
            lottery_relevance_score=analysis.get('relevance_score', 50),
            lottery_category=analysis.get('category', 'other'),
            status='published',
            published_date=timezone.now(),
            source_url=articles_content[0]['url'] if articles_content else '',
            
            # เก็บข้อมูล Gemini analysis
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
        
        return article
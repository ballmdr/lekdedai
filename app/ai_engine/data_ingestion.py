"""
Data Ingestion System
ระบบเก็บข้อมูลอัตโนมัติสำหรับ AI
"""

import re
import json
import requests
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.utils import timezone
from django.conf import settings
import logging

from .models import DataSource, DataIngestionRecord
from news.models import NewsArticle
from dreams.models import DreamInterpretation

logger = logging.getLogger(__name__)

class TextProcessor:
    """ประมวลผลข้อความและสกัดข้อมูล"""
    
    @staticmethod
    def extract_numbers_from_text(text: str) -> List[str]:
        """สกัดตัวเลขจากข้อความ"""
        if not text:
            return []
            
        # ค้นหาตัวเลข 1-6 หลัก
        patterns = [
            r'\b\d{1}\b',   # เลข 1 หลัก
            r'\b\d{2}\b',   # เลข 2 หลัก
            r'\b\d{3}\b',   # เลข 3 หลัก
            r'\b\d{4}\b',   # เลข 4 หลัก
            r'\b\d{6}\b'    # เลข 6 หลัก (หวย)
        ]
        
        numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            numbers.extend(matches)
        
        # กรองเลขที่ไม่ใช่ปี
        filtered_numbers = []
        for num in numbers:
            # ข้ามปี ค.ศ.
            if len(num) == 4 and (num.startswith('19') or num.startswith('20')):
                continue
            # ข้ามเลขที่มีค่าน้อยเกินไป
            if len(num) == 1 and int(num) < 1:
                continue
                
            filtered_numbers.append(num)
        
        return list(set(filtered_numbers))  # ไม่ซ้ำ
    
    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        """สกัดคำสำคัญ"""
        if not text:
            return []
            
        # คำสำคัญที่เกี่ยวข้องกับหวย
        lottery_keywords = [
            'หวย', 'ลอตเตอรี่', 'เลข', 'งวด', 'ออก', 'รางวัล',
            'เด็ด', 'ดัง', 'แม่น', 'ถูก', 'รวย', 'โชค',
            'ทำนาย', 'พยากรณ์', 'วิเคราะห์', 'สถิติ',
            'ความฝัน', 'ฝัน', 'เฮง', 'มงคล', 'ศาล', 'วัด'
        ]
        
        # ความฝันและสัญลักษณ์
        dream_symbols = [
            'งู', 'ช้าง', 'ปลา', 'นก', 'แมว', 'หมา', 'เสือ', 'หนู',
            'ผี', 'เทพ', 'พระ', 'แม่', 'พ่อ', 'ลิง', 'กบ', 'เต่า',
            'น้ำ', 'ไฟ', 'ฟ้า', 'ดิน', 'ต้นไม้', 'ดอกไม้', 'บ้าน', 'รถ'
        ]
        
        all_keywords = lottery_keywords + dream_symbols
        found_keywords = []
        
        text_lower = text.lower()
        for keyword in all_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    @staticmethod
    def calculate_sentiment_score(text: str) -> float:
        """คำนวณคะแนนอารมณ์ (sentiment)"""
        if not text:
            return 0.5
            
        # คำบวก
        positive_words = [
            'ดี', 'เยี่ยม', 'ยอด', 'สุดยอด', 'แม่น', 'ถูก', 'รวย', 
            'โชค', 'เฮง', 'มงคล', 'ได้', 'ชนะ', 'รางวัล', 'ดัง'
        ]
        
        # คำลบ
        negative_words = [
            'แย่', 'เสีย', 'เสี่ยง', 'อันตราย', 'ผิด', 'พลาด', 
            'เสียใจ', 'โชคร้าย', 'ล้มเหลว', 'ปัญหา', 'ลำบาก'
        ]
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.5
            
        # คำนวณคะแนน (0-1)
        score = 0.5 + (positive_count - negative_count) / (total_words * 2)
        return max(0.0, min(1.0, score))
    
    @staticmethod
    def calculate_relevance_score(title: str, content: str) -> float:
        """คำนวณคะแนนความเกี่ยวข้องกับการทำนายหวย"""
        
        if not title and not content:
            return 0.0
            
        full_text = f"{title} {content}".lower()
        
        # คำสำคัญหลัก (น้ำหนักสูง)
        main_keywords = ['หวย', 'ลอตเตอรี่', 'เลขเด็ด', 'ทำนาย', 'รางวัล']
        main_score = sum(2 for keyword in main_keywords if keyword in full_text)
        
        # คำสำคัญรอง (น้ำหนักปานกลาง)
        secondary_keywords = ['เลข', 'งวด', 'ออก', 'แม่น', 'ถูก', 'โชค', 'เฮง']
        secondary_score = sum(1 for keyword in secondary_keywords if keyword in full_text)
        
        # คำสำคัญความฝัน (น้ำหนักต่ำ)
        dream_keywords = ['ฝัน', 'ความฝัน', 'งู', 'ช้าง', 'ปลา']
        dream_score = sum(0.5 for keyword in dream_keywords if keyword in full_text)
        
        total_score = main_score + secondary_score + dream_score
        max_possible_score = len(main_keywords) * 2 + len(secondary_keywords) + len(dream_keywords) * 0.5
        
        relevance = total_score / max_possible_score if max_possible_score > 0 else 0
        return min(1.0, relevance)

class NewsIngester:
    """เก็บข้อมูลจากข่าวสาร"""
    
    def __init__(self):
        self.text_processor = TextProcessor()
    
    def ingest_from_existing_news(self, data_source: DataSource) -> List[DataIngestionRecord]:
        """เก็บข้อมูลจาก news app ในระบบ"""
        
        records = []
        
        try:
            # ดึงข่าวหวยจาก news app ที่เผยแพร่แล้ว
            from news.models import NewsArticle
            
            # หาข่าวหวยล่าสุดที่มีเลขเด็ด หรือข่าวทั้งหมด
            recent_articles = NewsArticle.objects.filter(
                status='published',
                published_date__gte=timezone.now() - timedelta(days=7)  # ข่าวใน 7 วันล่าสุด
            ).order_by('-published_date')[:15]
            
            for article in recent_articles:
                try:
                    # ตรวจสอบว่าได้ ingest ข่าวนี้แล้วหรือยัง
                    existing_record = DataIngestionRecord.objects.filter(
                        data_source=data_source,
                        title=article.title
                    ).first()
                    
                    if existing_record:
                        continue  # ข้ามถ้า ingest แล้ว
                    
                    # สร้างเนื้อหาสำหรับวิเคราะห์
                    full_content = f"{article.title}. {article.intro} {article.content}"
                    
                    # วิเคราะห์เนื้อหาด้วย TextProcessor
                    extracted_numbers_from_text = self.text_processor.extract_numbers_from_text(full_content)
                    keywords = self.text_processor.extract_keywords(full_content)
                    sentiment_score = self.text_processor.calculate_sentiment_score(full_content)
                    
                    # ถ้าบทความมีเลขเด็ดอยู่แล้ว ให้ใช้เลขนั้นรวมกับเลขที่วิเคราะห์ได้
                    if article.extracted_numbers:
                        existing_numbers = article.get_extracted_numbers_list()
                        # รวมเลขที่มีอยู่กับเลขที่วิเคราะห์ได้
                        all_numbers = list(set(existing_numbers + extracted_numbers_from_text))
                    else:
                        all_numbers = extracted_numbers_from_text
                    
                    # สร้างบันทึกข้อมูล
                    record = DataIngestionRecord.objects.create(
                        data_source=data_source,
                        raw_content=full_content[:1000],  # จำกัดความยาวเนื้อหา
                        processed_content=article.title,  # หัวข้อเป็นเนื้อหาที่ประมวลผล
                        title=article.title,
                        publish_date=article.published_date,
                        author=article.author.username if article.author else '',
                        extracted_numbers=all_numbers,
                        keywords=keywords,
                        sentiment_score=sentiment_score,
                        relevance_score=article.confidence_score / 100.0,  # แปลงเป็น 0-1
                        processing_status='completed',
                        processed_at=timezone.now()
                    )
                    
                    records.append(record)
                    logger.info(f"Ingested news article '{article.title[:50]}...' with {len(all_numbers)} numbers")
                    
                except Exception as e:
                    logger.error(f"Error ingesting news article {article.id}: {str(e)}")
                    continue
                    
        except ImportError:
            logger.error("Cannot import news.models - news app not available")
        except Exception as e:
            logger.error(f"Error in ingest_from_existing_news: {str(e)}")
        
        return records
    
    def ingest_from_external_api(self, data_source: DataSource) -> List[DataIngestionRecord]:
        """เก็บข้อมูลจาก API ภายนอก (ตัวอย่าง)"""
        
        records = []
        
        # ตัวอย่างการเรียก API (ต้องแทนที่ด้วย API จริง)
        try:
            if data_source.api_endpoint:
                headers = {}
                if data_source.api_key:
                    headers['Authorization'] = f'Bearer {data_source.api_key}'
                
                # TODO: เรียก API จริงและประมวลผลข้อมูล
                # response = requests.get(data_source.api_endpoint, headers=headers, timeout=30)
                
                # สำหรับการทดสอบ - สร้างข้อมูลจำลอง
                mock_articles = self._generate_mock_news_data()
                
                for article_data in mock_articles:
                    record = self._create_record_from_external_data(data_source, article_data)
                    records.append(record)
                    
        except Exception as e:
            logger.error(f"Error ingesting from external API {data_source.name}: {str(e)}")
        
        return records
    
    def _generate_mock_news_data(self) -> List[Dict]:
        """สร้างข้อมูลข่าวจำลองสำหรับทดสอบ"""
        
        mock_titles = [
            "เลขเด็ดงวดนี้ 15 47 89 จากการวิเคราะห์สถิติ",
            "ช่วงนี้เลข 23 ออกบ่อย ควรจับตาดู",
            "นักเล่นหวยแชร์เลข 56 78 จากความฝันเห็นงูใหญ่",
            "สถิติหวย 10 งวดล่าสุด เลข 12 34 มาแรง",
            "ผลหวยงวดที่แล้ว 923456 เลขท้าย 56 ฮิตมาก"
        ]
        
        mock_data = []
        for title in mock_titles:
            content = f"รายละเอียดข่าว {title} " + " ".join([
                f"เลข{random.randint(10,99)}", f"หวย{random.randint(100,999)}",
                "การวิเคราะห์", "สถิติ", "แนวโน้ม", "ทำนาย"
            ])
            
            mock_data.append({
                'title': title,
                'content': content,
                'published_date': timezone.now() - timedelta(hours=random.randint(1, 48)),
                'author': f'นักข่าว{random.randint(1,5)}'
            })
        
        return mock_data
    
    def _create_record_from_external_data(self, data_source: DataSource, article_data: Dict) -> DataIngestionRecord:
        """สร้างบันทึกจากข้อมูลภายนอก"""
        
        # ประมวลผลข้อความ
        full_text = f"{article_data['title']} {article_data['content']}"
        extracted_numbers = self.processor.extract_numbers_from_text(full_text)
        keywords = self.processor.extract_keywords(full_text)
        sentiment_score = self.processor.calculate_sentiment_score(article_data['content'])
        relevance_score = self.processor.calculate_relevance_score(
            article_data['title'], article_data['content']
        )
        
        record = DataIngestionRecord.objects.create(
            data_source=data_source,
            raw_content=article_data['content'],
            processed_content=article_data['content'],
            title=article_data['title'],
            publish_date=article_data.get('published_date', timezone.now()),
            author=article_data.get('author', ''),
            extracted_numbers=extracted_numbers,
            keywords=keywords,
            sentiment_score=sentiment_score,
            relevance_score=relevance_score,
            processing_status='completed',
            processed_at=timezone.now()
        )
        
        return record

class SocialMediaIngester:
    """เก็บข้อมูลจากโซเชียลมีเดีย"""
    
    def __init__(self):
        self.processor = TextProcessor()
    
    def ingest_social_mentions(self, data_source: DataSource) -> List[DataIngestionRecord]:
        """เก็บข้อมูลการพูดถึงหวยในโซเชียล"""
        
        records = []
        
        # ตัวอย่างการสร้างข้อมูลโซเชียลจำลอง
        # ในการใช้งานจริงจะต้องเชื่อมต่อกับ API ของแต่ละแพลตฟอร์ม
        
        mock_posts = self._generate_mock_social_data()
        
        for post_data in mock_posts:
            try:
                extracted_numbers = self.processor.extract_numbers_from_text(post_data['content'])
                keywords = self.processor.extract_keywords(post_data['content'])
                sentiment_score = self.processor.calculate_sentiment_score(post_data['content'])
                relevance_score = self.processor.calculate_relevance_score('', post_data['content'])
                
                record = DataIngestionRecord.objects.create(
                    data_source=data_source,
                    raw_content=post_data['content'],
                    processed_content=post_data['content'],
                    title=f"Social post from {post_data['platform']}",
                    publish_date=post_data['created_at'],
                    author=post_data['username'],
                    extracted_numbers=extracted_numbers,
                    keywords=keywords,
                    sentiment_score=sentiment_score,
                    relevance_score=relevance_score,
                    processing_status='completed',
                    processed_at=timezone.now()
                )
                
                records.append(record)
                
            except Exception as e:
                logger.error(f"Error processing social media post: {str(e)}")
                continue
        
        return records
    
    def _generate_mock_social_data(self) -> List[Dict]:
        """สร้างข้อมูลโซเชียลจำลอง"""
        
        mock_posts = [
            {
                'platform': 'Facebook',
                'username': 'user123',
                'content': 'วันนี้ฝันเห็นงูใหญ่สีเขียว คิดว่าจะได้เลข 89 หรือ 98 กันนะ',
                'created_at': timezone.now() - timedelta(hours=random.randint(1, 12))
            },
            {
                'platform': 'Twitter', 
                'username': 'lotto_lover',
                'content': 'เลข 15 47 ออกบ่อยมากช่วงนี้ ใครยังไม่ซื้อรีบไปซื้อเลย #หวย #เลขเด็ด',
                'created_at': timezone.now() - timedelta(hours=random.randint(1, 24))
            },
            {
                'platform': 'Facebook',
                'username': 'dream_predict',
                'content': 'ฝันเห็นช้างขาวมาให้เลข 23 34 56 ใครอยากลองเสี่ยงดูลอง',
                'created_at': timezone.now() - timedelta(hours=random.randint(1, 6))
            },
            {
                'platform': 'Line',
                'username': 'หวยมาแรง',
                'content': 'เซียนดูเลขแล้ว งวดนี้ 67 78 89 น่าจะออก จับตาดูกัน',
                'created_at': timezone.now() - timedelta(hours=random.randint(1, 18))
            },
            {
                'platform': 'Twitter',
                'username': 'number_guru',
                'content': 'สถิติบอกว่า 12 กับ 21 ไม่ออกนาน 5 งวดแล้ว คราวนี้น่าจะถึงตา',
                'created_at': timezone.now() - timedelta(hours=random.randint(1, 8))
            }
        ]
        
        return mock_posts

class DreamDataIngester:
    """เก็บข้อมูลความฝัน"""
    
    def __init__(self):
        self.processor = TextProcessor()
    
    def ingest_dream_interpretations(self, data_source: DataSource) -> List[DataIngestionRecord]:
        """เก็บข้อมูลการตีความฝัน"""
        
        records = []
        
        # ดึงข้อมูลความฝันจากระบบ
        recent_dreams = DreamInterpretation.objects.filter(
            interpreted_at__gte=timezone.now() - timedelta(days=7)
        )[:30]
        
        for dream in recent_dreams:
            try:
                # วิเคราะห์ความฝัน
                extracted_numbers = self._extract_numbers_from_dream(dream)
                keywords = self.processor.extract_keywords(dream.dream_text)
                
                # ความฝันมักมี sentiment เป็นกลาง
                sentiment_score = 0.6
                
                # คำนวณความเกี่ยวข้อง
                relevance_score = self._calculate_dream_relevance(dream.dream_text)
                
                record = DataIngestionRecord.objects.create(
                    data_source=data_source,
                    raw_content=dream.dream_text,
                    processed_content=dream.interpretation,
                    title=f"Dream interpretation - {dream.interpreted_at.strftime('%d/%m/%Y')}",
                    publish_date=dream.interpreted_at,
                    author=dream.user.username if dream.user else 'Anonymous',
                    extracted_numbers=extracted_numbers,
                    keywords=keywords,
                    sentiment_score=sentiment_score,
                    relevance_score=relevance_score,
                    processing_status='completed',
                    processed_at=timezone.now()
                )
                
                records.append(record)
                
            except Exception as e:
                logger.error(f"Error processing dream interpretation {dream.id}: {str(e)}")
                continue
        
        return records
    
    def _extract_numbers_from_dream(self, dream: DreamInterpretation) -> List[str]:
        """สกัดตัวเลขจากความฝัน"""
        numbers = []
        
        # เลขที่แนะนำจากการตีความ
        if dream.suggested_numbers:
            suggested = dream.suggested_numbers.split(',')
            numbers.extend([num.strip() for num in suggested if num.strip()])
        
        # เลขจากข้อความความฝัน
        text_numbers = self.processor.extract_numbers_from_text(dream.dream_text)
        numbers.extend(text_numbers)
        
        return list(set(numbers))
    
    def _calculate_dream_relevance(self, dream_text: str) -> float:
        """คำนวณความเกี่ยวข้องของความฝัน"""
        
        # ความฝันที่มีสัญลักษณ์ที่เกี่ยวข้องกับการทำนาย
        symbolic_keywords = [
            'งู', 'ช้าง', 'ปลา', 'นก', 'เสือ', 'หนู', 'มังกร',
            'ผี', 'เทพ', 'พระ', 'ศาล', 'วัด', 'น้ำ', 'ไฟ', 'ทอง',
            'เลข', 'ตัวเลข', 'นับ', 'จำนวน'
        ]
        
        text_lower = dream_text.lower()
        found_symbols = sum(1 for keyword in symbolic_keywords if keyword in text_lower)
        
        # คำนวณคะแนน
        max_symbols = len(symbolic_keywords)
        relevance = (found_symbols / max_symbols) * 0.8 + 0.2  # ขั้นต่ำ 0.2
        
        return min(1.0, relevance)

class TrendDataIngester:
    """เก็บข้อมูลเทรนด์และสถิติ"""
    
    def __init__(self):
        self.processor = TextProcessor()
    
    def ingest_google_trends(self, data_source: DataSource) -> List[DataIngestionRecord]:
        """เก็บข้อมูล Google Trends (จำลอง)"""
        
        records = []
        
        # สร้างข้อมูล Google Trends จำลอง
        mock_trends = self._generate_mock_trends_data()
        
        for trend_data in mock_trends:
            try:
                record = DataIngestionRecord.objects.create(
                    data_source=data_source,
                    raw_content=json.dumps(trend_data),
                    processed_content=trend_data['description'],
                    title=f"Google Trends: {trend_data['keyword']}",
                    publish_date=trend_data['date'],
                    author='Google Trends',
                    extracted_numbers=trend_data['related_numbers'],
                    keywords=[trend_data['keyword']],
                    sentiment_score=0.5,  # เป็นกลาง
                    relevance_score=trend_data['trend_score'],
                    processing_status='completed',
                    processed_at=timezone.now()
                )
                
                records.append(record)
                
            except Exception as e:
                logger.error(f"Error processing trends data: {str(e)}")
                continue
        
        return records
    
    def _generate_mock_trends_data(self) -> List[Dict]:
        """สร้างข้อมูลเทรนด์จำลอง"""
        
        trending_keywords = [
            'หวย', 'เลขเด็ด', 'ทำนายหวย', 'เลขดัง', 'หวยรัฐบาล'
        ]
        
        trends = []
        for keyword in trending_keywords:
            # สร้างเลขที่เกี่ยวข้องแบบสุ่ม
            related_numbers = [f"{random.randint(10, 99):02d}" for _ in range(3)]
            
            trend_data = {
                'keyword': keyword,
                'trend_score': random.uniform(0.6, 0.9),
                'related_numbers': related_numbers,
                'description': f"คำค้นหา '{keyword}' กำลังเป็นที่นิยมในช่วงนี้ เลขที่เกี่ยวข้อง: {', '.join(related_numbers)}",
                'date': timezone.now() - timedelta(hours=random.randint(1, 24))
            }
            
            trends.append(trend_data)
        
        return trends

class DataIngestionManager:
    """ตัวจัดการหลักสำหรับการเก็บข้อมูล"""
    
    def __init__(self):
        self.news_ingester = NewsIngester()
        self.social_ingester = SocialMediaIngester()
        self.dream_ingester = DreamDataIngester()
        self.trend_ingester = TrendDataIngester()
    
    def run_all_ingestors(self) -> Dict[str, int]:
        """รันการเก็บข้อมูลทั้งหมด"""
        
        results = {
            'news': 0,
            'social_media': 0, 
            'dreams': 0,
            'trends': 0,
            'total': 0
        }
        
        try:
            # เก็บข้อมูลข่าว
            news_sources = DataSource.objects.filter(source_type='news', is_active=True)
            for source in news_sources:
                records = self.news_ingester.ingest_from_existing_news(source)
                results['news'] += len(records)
                
                # อัปเดตเวลาการเก็บข้อมูล
                source.last_scraped = timezone.now()
                source.save()
            
            # เก็บข้อมูลโซเชียล
            social_sources = DataSource.objects.filter(source_type='social_media', is_active=True)
            for source in social_sources:
                records = self.social_ingester.ingest_social_mentions(source)
                results['social_media'] += len(records)
                source.last_scraped = timezone.now()
                source.save()
            
            # เก็บข้อมูลความฝัน
            dream_sources = DataSource.objects.filter(source_type='dreams', is_active=True)
            for source in dream_sources:
                records = self.dream_ingester.ingest_dream_interpretations(source)
                results['dreams'] += len(records)
                source.last_scraped = timezone.now()
                source.save()
            
            # เก็บข้อมูลเทรนด์
            trend_sources = DataSource.objects.filter(source_type='trends', is_active=True)
            for source in trend_sources:
                records = self.trend_ingester.ingest_google_trends(source)
                results['trends'] += len(records)
                source.last_scraped = timezone.now()
                source.save()
            
            results['total'] = sum([results[key] for key in results if key != 'total'])
            
            logger.info(f"Data ingestion completed. Total records: {results['total']}")
            
        except Exception as e:
            logger.error(f"Error in data ingestion: {str(e)}")
            raise
        
        return results
    
    def collect_from_source(self, data_source: DataSource) -> List[DataIngestionRecord]:
        """เก็บข้อมูลจากแหล่งเฉพาะ"""
        
        records = []
        
        try:
            if data_source.source_type == 'news':
                records = self.news_ingester.ingest_from_existing_news(data_source)
            elif data_source.source_type == 'social_media':
                records = self.social_ingester.ingest_social_mentions(data_source)
            elif data_source.source_type == 'dreams':
                records = self.dream_ingester.ingest_dream_interpretations(data_source)
            elif data_source.source_type == 'trends':
                records = self.trend_ingester.ingest_trend_data(data_source)
            
            if records:
                # อัปเดตเวลาการเก็บข้อมูล
                data_source.last_scraped = timezone.now()
                data_source.save()
                
                logger.info(f"Collected {len(records)} records from {data_source.name}")
            
        except Exception as e:
            logger.error(f"Error collecting from source {data_source.name}: {str(e)}")
        
        return records
    
    def run_ingestion_for_source(self, source_id: int) -> int:
        """รันการเก็บข้อมูลสำหรับแหล่งข้อมูลเฉพาะ"""
        
        try:
            source = DataSource.objects.get(id=source_id, is_active=True)
            records = []
            
            if source.source_type == 'news':
                records = self.news_ingester.ingest_from_existing_news(source)
            elif source.source_type == 'social_media':
                records = self.social_ingester.ingest_social_mentions(source)
            elif source.source_type == 'dreams':
                records = self.dream_ingester.ingest_dream_interpretations(source)
            elif source.source_type == 'trends':
                records = self.trend_ingester.ingest_google_trends(source)
            
            # อัปเดตเวลาการเก็บข้อมูล
            source.last_scraped = timezone.now()
            source.save()
            
            logger.info(f"Ingestion completed for {source.name}: {len(records)} records")
            return len(records)
            
        except DataSource.DoesNotExist:
            logger.error(f"Data source {source_id} not found")
            return 0
        except Exception as e:
            logger.error(f"Error in ingestion for source {source_id}: {str(e)}")
            return 0
    
    def cleanup_old_records(self, days_to_keep: int = 30) -> int:
        """ลบข้อมูลเก่าที่เกินกำหนด"""
        
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        old_records = DataIngestionRecord.objects.filter(
            ingested_at__lt=cutoff_date
        )
        
        count = old_records.count()
        old_records.delete()
        
        logger.info(f"Cleaned up {count} old ingestion records")
        return count
    
    def get_ingestion_statistics(self) -> Dict[str, Any]:
        """ดึงสถิติการเก็บข้อมูล"""
        
        from django.db.models import Count, Avg
        
        stats = {
            'total_records': DataIngestionRecord.objects.count(),
            'records_today': DataIngestionRecord.objects.filter(
                ingested_at__date=timezone.now().date()
            ).count(),
            'records_by_source_type': dict(
                DataIngestionRecord.objects.values('data_source__source_type')
                .annotate(count=Count('id'))
                .values_list('data_source__source_type', 'count')
            ),
            'avg_relevance_score': DataIngestionRecord.objects.aggregate(
                avg_relevance=Avg('relevance_score')
            )['avg_relevance'] or 0,
            'processing_status_breakdown': dict(
                DataIngestionRecord.objects.values('processing_status')
                .annotate(count=Count('id'))
                .values_list('processing_status', 'count')
            )
        }
        
        return stats
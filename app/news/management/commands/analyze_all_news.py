"""
Management command สำหรับวิเคราะห์เลขและ Insight AI ให้ข่าวทั้งหมด
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from news.models import NewsArticle
import json
import re


class Command(BaseCommand):
    help = 'วิเคราะห์เลขและสร้าง Insight AI ให้ข่าวทุกบทความที่ยังไม่มี'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='บังคับวิเคราะห์ใหม่แม้ข่าวที่มี insight แล้ว',
        )
        parser.add_argument(
            '--article-id',
            type=int,
            help='วิเคราะห์เฉพาะบทความที่ระบุ ID',
        )

    def handle(self, *args, **options):
        # เริ่มต้นการทำงาน
        self.stdout.write(
            self.style.SUCCESS('เริ่มการวิเคราะห์เลขและ Insight AI'))

        # กำหนดเงื่อนไขการคัดเลือกบทความ
        if options['article_id']:
            # วิเคราะห์บทความที่ระบุ
            articles = NewsArticle.objects.filter(id=options['article_id'])
            if not articles.exists():
                raise CommandError(f'ไม่พบบทความ ID {options["article_id"]}')
        elif options['force']:
            # วิเคราะห์ทุกบทความ
            articles = NewsArticle.objects.filter(status='published')
        else:
            # วิเคราะห์เฉพาะบทความที่ยังไม่มี insight
            articles = NewsArticle.objects.filter(
                status='published',
                insight_analyzed_at__isnull=True
            )

        total_articles = articles.count()
        
        if total_articles == 0:
            self.stdout.write(
                self.style.WARNING('ไม่มีบทความที่ต้องวิเคราะห์'))
            return

        self.stdout.write(f'พบบทความที่ต้องวิเคราะห์: {total_articles} บทความ')
        self.stdout.write('-' * 60)

        # วิเคราะห์ทีละบทความ
        success_count = 0
        error_count = 0

        for i, article in enumerate(articles, 1):
            self.stdout.write(
                f'[{i}/{total_articles}] {article.title[:50]}...')

            try:
                # วิเคราะห์เลขจากเนื้อหา
                extracted_numbers = self.extract_numbers_from_content(article)
                
                if extracted_numbers:
                    # สร้าง Insight AI data
                    insight_data = self.generate_insight_data(
                        article, extracted_numbers)
                    
                    # อัปเดตบทความ
                    self.update_article_with_insight(
                        article, extracted_numbers, insight_data)
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  SUCCESS วิเคราะห์สำเร็จ - ได้ {len(extracted_numbers)} เลข'))
                    success_count += 1
                else:
                    # ไม่พบเลข แต่ยังตั้งค่า analyzed_at
                    article.insight_analyzed_at = timezone.now()
                    article.insight_summary = 'ไม่พบเลขที่สามารถวิเคราะห์ได้จากข่าวนี้'
                    article.insight_impact_score = 0.1
                    article.save()
                    
                    self.stdout.write(
                        self.style.WARNING('  - ไม่พบเลขในข่าวนี้'))
                    success_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ERROR เกิดข้อผิดพลาด: {str(e)}'))
                error_count += 1

        # สรุปผล
        self.stdout.write('-' * 60)
        self.stdout.write(
            self.style.SUCCESS(f'วิเคราะห์เสร็จสิ้น!'))
        self.stdout.write(f'สำเร็จ: {success_count} บทความ')
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f'ข้อผิดพลาด: {error_count} บทความ'))

    def extract_numbers_from_content(self, article):
        """วิเคราะห์เลขจากเนื้อหาข่าว"""
        text = f"{article.title} {article.intro or ''} {article.content or ''}"
        
        # หาเลขทุกรูปแบบ
        number_patterns = [
            r'\b\d{1,3}\b',  # เลข 1-3 หลัก
            r'\b\d{1,2}[/\-\.]\d{1,2}\b',  # เลขแบบ 12/34, 12-34
            r'(?:เลข|หมายเลข|ทะเบียน)[\s]*[ก-ฮ]*[\s]*[\-]?[\s]*(\d+)',  # เลขที่มีคำนำหน้า
            r'(\d+)[\s]*(?:ปี|ปี|ชั้น|ล้าน|พัน|บาท|นาที|ชั่วโมง|คน)',  # เลขที่มีหน่วย
            r'อายุ[\s]*(\d+)',  # อายุ
            r'บ้านเลขที่[\s]*(\d+)',  # เลขบ้าน
        ]
        
        numbers = []
        for pattern in number_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                
                # กรองเลขที่สมเหตุสมผล (1-999)
                try:
                    num = int(match.replace('-', '').replace('/', ''))
                    if 1 <= num <= 999:
                        # แปลงให้เป็น 2 หลักถ้าเป็นเลข 1 หลัก
                        if num < 10:
                            numbers.append(f"0{num}")
                        else:
                            numbers.append(str(num))
                except ValueError:
                    continue
        
        # ลบเลขซ้ำและจำกัดจำนวน
        unique_numbers = list(dict.fromkeys(numbers))  # เก็บลำดับ
        return unique_numbers[:10]  # จำกัดสูงสุด 10 เลข

    def generate_insight_data(self, article, numbers):
        """สร้างข้อมูล Insight AI"""
        
        # วิเคราะห์ประเภทข่าวและกำหนด impact score
        title_lower = article.title.lower()
        content_lower = (article.content or '').lower()
        
        # กำหนด impact score ตามประเภทข่าว
        if any(keyword in title_lower for keyword in ['อุบัติเหตุ', 'ชน', 'เสียชีวิต', 'บาดเจ็บ']):
            impact_score = 0.85
            category = 'accident'
        elif any(keyword in title_lower for keyword in ['ไฟไหม้', 'ระเบิด', 'พัง', 'เสียหาย']):
            impact_score = 0.80
            category = 'disaster'
        elif any(keyword in title_lower for keyword in ['พบศพ', 'ฆ่า', 'ตาย']):
            impact_score = 0.90
            category = 'crime'
        elif any(keyword in title_lower for keyword in ['หุ้น', 'ตลาด', 'เศรษฐกิจ']):
            impact_score = 0.70
            category = 'economy'
        elif any(keyword in title_lower for keyword in ['ยาเสพติด', 'จับกุม', 'ตำรวจ']):
            impact_score = 0.75
            category = 'police'
        else:
            impact_score = 0.60
            category = 'general'

        # สร้าง summary
        summary = self.generate_summary(article, category)
        
        # สร้าง entities
        entities = self.generate_entities(article, numbers, category)
        
        return {
            'summary': summary,
            'impact_score': impact_score,
            'entities': entities,
            'category': category
        }

    def generate_summary(self, article, category):
        """สร้างสรุปข่าวสำหรับ Insight AI"""
        title = article.title
        
        # สกัดข้อมูลสำคัญจากหัวข้อ
        if category == 'accident':
            return f"เหตุการณ์: {title[:80]}..."
        elif category == 'disaster':
            return f"ภัยพิบัติ: {title[:80]}..."  
        elif category == 'crime':
            return f"คดีอาญา: {title[:80]}..."
        elif category == 'economy':
            return f"ข่าวเศรษฐกิจ: {title[:80]}..."
        elif category == 'police':
            return f"การปราบปราม: {title[:80]}..."
        else:
            return f"ข่าวทั่วไป: {title[:80]}..."

    def generate_entities(self, article, numbers, category):
        """สร้าง entities สำหรับแต่ละเลข"""
        text = f"{article.title} {article.content or ''}"
        entities = []
        
        for number in numbers:
            entity = self.analyze_number_context(number, text, category)
            if entity:
                entities.append(entity)
        
        return entities

    def analyze_number_context(self, number, text, category):
        """วิเคราะห์บริบทของเลขแต่ละตัว"""
        num_int = int(number)
        
        # หารูปแบบที่เลขปรากฏในข้อความ
        contexts = []
        
        # ค้นหาบริบทรอบๆ เลข
        number_patterns = [
            (fr'อายุ[\s]*{num_int}', 'age', f'อายุ {num_int} ปี'),
            (fr'บ้านเลขที่[\s]*{num_int}', 'address', f'ที่อยู่บ้านเลขที่ {num_int}'),
            (fr'ชั้น[\s]*{num_int}', 'floor', f'ชั้นที่ {num_int}'),
            (fr'{num_int}[\s]*ล้าน', 'amount', f'จำนวนเงิน {num_int} ล้านบาท'),
            (fr'{num_int}[\s]*นาที', 'duration', f'ระยะเวลา {num_int} นาที'),
            (fr'{num_int}[\s]*คน', 'quantity', f'จำนวนผู้คน {num_int} คน'),
            (fr'หมายเลข[\s]*{num_int}', 'identifier', f'หมายเลข {num_int}'),
            (fr'เลข[\s]*{num_int}', 'identifier', f'เลข {num_int}'),
            (fr'ทะเบียน.*{num_int}', 'license', f'ทะเบียนรถ {num_int}'),
        ]
        
        for pattern, entity_type, reason in number_patterns:
            if re.search(pattern, text):
                return {
                    'number': number,
                    'type': entity_type,
                    'reason': reason,
                    'significance_score': self.calculate_significance_score(
                        entity_type, category)
                }
        
        # ถ้าไม่เจอบริบทเฉพาะ ให้ประเมินจากค่าเลข
        if category == 'accident' and 10 <= num_int <= 99:
            return {
                'number': number,
                'type': 'general',
                'reason': f'เลข {number} จากเหตุการณ์อุบัติเหตุ',
                'significance_score': 0.7
            }
        elif num_int <= 31:  # อาจเป็นวันที่
            return {
                'number': number,
                'type': 'date',
                'reason': f'เลข {number} น่าจะเป็นวันที่',
                'significance_score': 0.6
            }
        elif 10 <= num_int <= 99:  # เลข 2 หลัก
            return {
                'number': number,
                'type': 'general',
                'reason': f'เลข {number} จากเนื้อหาข่าว',
                'significance_score': 0.5
            }
        
        return None

    def calculate_significance_score(self, entity_type, category):
        """คำนวณคะแนนความสำคัญ"""
        base_scores = {
            'age': 0.9,
            'address': 0.8,
            'amount': 0.9,
            'duration': 0.7,
            'quantity': 0.8,
            'identifier': 0.6,
            'license': 0.8,
            'floor': 0.7,
            'general': 0.5,
            'date': 0.6,
        }
        
        # ปรับคะแนนตามประเภทข่าว
        if category in ['accident', 'crime']:
            return min(1.0, base_scores.get(entity_type, 0.5) + 0.1)
        else:
            return base_scores.get(entity_type, 0.5)

    def update_article_with_insight(self, article, numbers, insight_data):
        """อัปเดตบทความด้วยข้อมูล Insight"""
        
        # อัปเดต extracted_numbers ถ้ายังไม่มี
        if not article.extracted_numbers:
            article.extracted_numbers = ','.join(numbers[:6])
        
        # อัปเดต Insight AI data
        article.insight_analyzed_at = timezone.now()
        article.insight_summary = insight_data['summary']
        article.insight_impact_score = insight_data['impact_score']
        article.insight_entities = insight_data['entities']
        
        # คำนวณ confidence score
        if insight_data['entities']:
            avg_score = sum(e['significance_score'] 
                          for e in insight_data['entities']) / len(insight_data['entities'])
            article.confidence_score = int(avg_score * 100)
        else:
            article.confidence_score = 50
        
        # อัปเดต lottery category ถ้ายังไม่มี
        if not article.lottery_category:
            category_mapping = {
                'accident': 'accident',
                'crime': 'accident', 
                'disaster': 'accident',
                'economy': 'economic',
                'police': 'general',
                'general': 'general'
            }
            article.lottery_category = category_mapping.get(
                insight_data['category'], 'general')
        
        # อัปเดต lottery_relevance_score ตาม insight
        if not article.lottery_relevance_score or article.lottery_relevance_score < 70:
            article.lottery_relevance_score = min(
                95, int(insight_data['impact_score'] * 100))
        
        article.save()
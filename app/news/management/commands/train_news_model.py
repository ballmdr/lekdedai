"""
Django management command สำหรับฝึกสอน NewsEntity_Model
Usage: python manage.py train_news_model --prepare-data
"""
import os
import sys
from django.core.management.base import BaseCommand
from django.conf import settings

# Add MCP directory to Python path
MCP_DIR = os.path.join(settings.BASE_DIR, '..', 'mcp_dream_analysis')
sys.path.insert(0, MCP_DIR)

import asyncio
from mcp_servers.news_entity_mcp import news_entity_api

class Command(BaseCommand):
    help = 'Train NewsEntity_Model for numerical entity recognition'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--prepare-data',
            action='store_true',
            help='Prepare training data from Django models first'
        )
        parser.add_argument(
            '--data-file',
            type=str,
            default='news_entity_training_data.json',
            help='Training data JSON file path'
        )
        parser.add_argument(
            '--test-size',
            type=float,
            default=0.2,
            help='Test size for train/test split (default: 0.2)'
        )
        parser.add_argument(
            '--save-model',
            action='store_true',
            default=True,
            help='Save the trained model after training'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 เริ่มการฝึกสอน NewsEntity_Model')
        )
        
        # Step 1: Prepare data if requested
        if options['prepare_data']:
            self.stdout.write('📊 เตรียมข้อมูลการฝึกสอนจาก Django models...')
            try:
                training_data = self.prepare_news_data()
                self.save_training_data(training_data, options['data_file'])
                self.stdout.write(
                    self.style.SUCCESS(f'✅ เตรียมข้อมูลสำเร็จ: {len(training_data)} รายการ')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ เตรียมข้อมูลไม่สำเร็จ: {str(e)}')
                )
                return
        else:
            # Load existing data
            try:
                training_data = self.load_training_data(options['data_file'])
                self.stdout.write(
                    self.style.SUCCESS(f'📂 โหลดข้อมูลสำเร็จ: {len(training_data)} รายการ')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ โหลดข้อมูลไม่สำเร็จ: {str(e)}')
                )
                return
        
        # Step 2: Train model
        self.stdout.write('🎯 เริ่มการฝึกสอนโมเดล NewsEntity_Model...')
        try:
            result = asyncio.run(self.train_model_async(training_data, options))
            
            if result.get('success'):
                self.stdout.write(
                    self.style.SUCCESS('✅ การฝึกสอนโมเดลสำเร็จ!')
                )
                self.stdout.write(f'📈 จำนวนข้อมูลฝึกสอน: {result.get("training_samples", 0)}')
                
                metrics = result.get('metrics', {})
                if metrics:
                    self.stdout.write('📊 ผลการประเมินโมเดล (F1-Score):')
                    for entity_type, entity_metrics in metrics.items():
                        f1_score = entity_metrics.get('f1', 0)
                        accuracy = entity_metrics.get('accuracy', 0)
                        self.stdout.write(f'   {entity_type}: F1={f1_score:.3f}, Accuracy={accuracy:.3f}')
                
                if result.get('model_saved'):
                    self.stdout.write('💾 บันทึกโมเดลแล้ว')
                
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ การฝึกสอนไม่สำเร็จ: {result.get("error", "Unknown error")}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ เกิดข้อผิดพลาดในการฝึกสอน: {str(e)}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('🏁 การฝึกสอน NewsEntity_Model เสร็จสิ้น')
        )
    
    def prepare_news_data(self):
        """Prepare news training data from Django models and synthetic data"""
        training_data = []
        
        # 1. From existing NewsArticle model
        try:
            from news.models import NewsArticle
            
            for article in NewsArticle.objects.all()[:200]:  # Limit for performance
                # Extract existing numbers from content
                entities = self.extract_entities_from_content(article.content)
                
                sample = {
                    'news_content': f"{article.title} {article.content}",
                    'entities': entities,
                    'source': 'existing_news'
                }
                training_data.append(sample)
                
        except ImportError:
            self.stdout.write(
                self.style.WARNING('⚠️  NewsArticle model not found, skipping existing news data')
            )
        
        # 2. Generate synthetic news data with labeled entities
        synthetic_data = self.generate_synthetic_news_data()
        training_data.extend(synthetic_data)
        
        return training_data
    
    def extract_entities_from_content(self, content):
        """Extract entities from existing news content using simple patterns"""
        import re
        
        entities = {
            'license_plate': [],
            'age': [],
            'house_number': [],
            'quantity': [],
            'date': [],
            'time': [],
            'lottery_number': [],
            'phone_number': [],
            'id_number': [],
        }
        
        # Simple pattern matching for labeling
        patterns = {
            'license_plate': r'[ก-ฮ]{1,2}\s*[\d]{1,4}|[\d]{2,4}(?=\s*(?:ทะเบียน|รถ))',
            'age': r'(?:อายุ|ปี|วัย)\s*[\d]{1,3}|[\d]{1,3}\s*(?:ขวบ|ปี|เดือน)',
            'house_number': r'(?:บ้านเลขที่|เลขที่|หมู่ที่)\s*[\d]{1,6}|[\d]{1,6}/[\d]{1,3}',
            'quantity': r'[\d,]{1,15}\s*(?:บาท|กิโลกรัม|กิโล|ตัว|คน)',
            'lottery_number': r'[\d]{6}(?!\d)',
            'phone_number': r'[\d]{3}[-\s][\d]{3}[-\s][\d]{4}|[\d]{10}',
        }
        
        for entity_type, pattern in patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            # Extract just numbers
            for match in matches:
                numbers = re.findall(r'\d+', str(match))
                entities[entity_type].extend(numbers[:3])  # Limit per entity type
        
        return entities
    
    def generate_synthetic_news_data(self):
        """Generate synthetic news data with labeled entities"""
        import random
        
        # Templates for different types of news
        news_templates = [
            # License plate news
            {
                'template': 'เกิดอุบัติเหตุรถยนต์ทะเบียน {license} ชนกับรถจักรยานยนต์ทะเบียน {license2} ที่หน้า บ้านเลขที่ {house_num}',
                'entities': {
                    'license_plate': ['{license}', '{license2}'],
                    'house_number': ['{house_num}']
                }
            },
            
            # Age and quantity news  
            {
                'template': 'คุณ{name} อายุ {age} ปี ซื้อลอตเตอรี่เลข {lottery} ในราคา {price} บาท',
                'entities': {
                    'age': ['{age}'],
                    'lottery_number': ['{lottery}'],
                    'quantity': ['{price}']
                }
            },
            
            # House and phone news
            {
                'template': 'เหตุเพลิงไหม้บ้านเลขที่ {house_num}/{sub_num} หมู่ {village} สามารถติดต่อได้ที่ {phone}',
                'entities': {
                    'house_number': ['{house_num}', '{sub_num}', '{village}'],
                    'phone_number': ['{phone}']
                }
            },
            
            # Mixed entities news
            {
                'template': 'ผู้ป่วย อายุ {age} ปี ที่อยู่บ้านเลขที่ {house_num} ได้รับเงินช่วยเหลือ {amount} บาท โทร {phone}',
                'entities': {
                    'age': ['{age}'],
                    'house_number': ['{house_num}'],
                    'quantity': ['{amount}'],
                    'phone_number': ['{phone}']
                }
            }
        ]
        
        # Sample data generators
        sample_data = {
            'license': ['กข 1234', 'นม 5678', '2345', '8901'],
            'license2': ['ฟก 2468', 'สท 1357', '9876', '5432'],
            'house_num': ['123', '456', '789', '101'],
            'sub_num': ['12', '45', '67', '89'],
            'village': ['7', '12', '3', '25'],
            'age': ['25', '45', '67', '32'],
            'lottery': ['123456', '789012', '345678', '901234'],
            'price': ['2500', '5000', '1200', '800'],
            'amount': ['10000', '25000', '50000', '15000'],
            'phone': ['081-234-5678', '082-345-6789', '083-456-7890', '084-567-8901'],
            'name': ['สมชาย', 'สมหญิง', 'สมศักดิ์', 'สมศรี']
        }
        
        synthetic_data = []
        
        for template_data in news_templates:
            template = template_data['template']
            entity_map = template_data['entities']
            
            # Generate 20 samples per template
            for i in range(20):
                # Fill template with random data
                filled_template = template
                actual_entities = {entity_type: [] for entity_type in entity_map.keys()}
                
                for placeholder in re.findall(r'\{(\w+)\}', template):
                    if placeholder in sample_data:
                        value = random.choice(sample_data[placeholder])
                        filled_template = filled_template.replace(f'{{{placeholder}}}', value, 1)
                        
                        # Map to actual entities
                        for entity_type, placeholders in entity_map.items():
                            if f'{{{placeholder}}}' in placeholders:
                                # Extract numbers only
                                numbers = re.findall(r'\d+', value)
                                actual_entities[entity_type].extend(numbers)
                
                sample = {
                    'news_content': filled_template,
                    'entities': actual_entities,
                    'source': 'synthetic_news'
                }
                synthetic_data.append(sample)
        
        return synthetic_data
    
    def save_training_data(self, data, filepath):
        """Save training data to JSON file"""
        import json
        
        full_path = os.path.join(settings.BASE_DIR, filepath)
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_training_data(self, filepath):
        """Load training data from JSON file"""
        import json
        
        full_path = os.path.join(settings.BASE_DIR, filepath)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Training data file not found: {full_path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def train_model_async(self, training_data, options):
        """Train model asynchronously"""
        try:
            result = await news_entity_api.train_model(training_data)
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
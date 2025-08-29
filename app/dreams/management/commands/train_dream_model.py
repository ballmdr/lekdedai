"""
Django management command สำหรับฝึกสอน DreamSymbol_Model
Usage: python manage.py train_dream_model --prepare-data
"""
import os
import sys
from django.core.management.base import BaseCommand
from django.conf import settings

# Add MCP directory to Python path
MCP_DIR = os.path.join(settings.BASE_DIR, '..', 'mcp_dream_analysis')
sys.path.insert(0, MCP_DIR)

import asyncio
from mcp_servers.dream_symbol_mcp import dream_symbol_api

class Command(BaseCommand):
    help = 'Train DreamSymbol_Model for symbolic interpretation'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--prepare-data',
            action='store_true',
            help='Prepare training data from Django models first'
        )
        parser.add_argument(
            '--data-file',
            type=str,
            default='dream_symbol_training_data.json',
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
            self.style.SUCCESS('🔮 เริ่มการฝึกสอน DreamSymbol_Model')
        )
        
        # Step 1: Prepare data if requested
        if options['prepare_data']:
            self.stdout.write('📊 เตรียมข้อมูลการฝึกสอนจาก Django models...')
            try:
                training_data = self.prepare_dream_data()
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
        self.stdout.write('🎯 เริ่มการฝึกสอนโมเดล DreamSymbol_Model...')
        try:
            result = asyncio.run(self.train_model_async(training_data, options))
            
            if result.get('success'):
                self.stdout.write(
                    self.style.SUCCESS('✅ การฝึกสอนโมเดลสำเร็จ!')
                )
                self.stdout.write(f'📈 จำนวนข้อมูลฝึกสอน: {result.get("training_samples", 0)}')
                
                metrics = result.get('metrics', {})
                if metrics:
                    self.stdout.write('📊 ผลการประเมินโมเดล:')
                    for metric, value in metrics.items():
                        if isinstance(value, float):
                            self.stdout.write(f'   {metric}: {value:.4f}')
                        else:
                            self.stdout.write(f'   {metric}: {value}')
                
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
            self.style.SUCCESS('🏁 การฝึกสอน DreamSymbol_Model เสร็จสิ้น')
        )
    
    def prepare_dream_data(self):
        """Prepare dream training data from Django models"""
        from dreams.models import DreamKeyword, DreamInterpretation
        import random
        
        training_data = []
        
        # 1. From DreamKeyword table
        for keyword in DreamKeyword.objects.all():
            # Basic sample
            sample = {
                'dream_text': f"ฝันเห็น{keyword.keyword}",
                'main_number': int(keyword.main_number),
                'secondary_number': int(keyword.secondary_number),
                'combinations': keyword.get_numbers_list(),
                'category': keyword.category.name,
                'source': 'keyword_db'
            }
            training_data.append(sample)
            
            # Generate variations
            variations = [
                f"ฝันว่า{keyword.keyword}ใหญ่มาก",
                f"เห็น{keyword.keyword}สีสวยในฝัน",
                f"ฝันเล่นกับ{keyword.keyword}",
                f"ฝันกลัว{keyword.keyword}มากๆ",
                f"ในฝัน{keyword.keyword}มาหาฉัน"
            ]
            
            for variation in random.sample(variations, min(2, len(variations))):
                var_sample = sample.copy()
                var_sample['dream_text'] = variation
                var_sample['source'] = 'keyword_variation'
                training_data.append(var_sample)
        
        # 2. From DreamInterpretation table
        for interp in DreamInterpretation.objects.all():
            if interp.suggested_numbers:
                numbers = [n.strip() for n in interp.suggested_numbers.split(',')]
                
                # Estimate main/secondary from first number
                if numbers and len(numbers[0]) >= 2:
                    first_num = numbers[0]
                    main_num = int(first_num[0]) if first_num[0].isdigit() else 1
                    secondary_num = int(first_num[1]) if len(first_num) > 1 and first_num[1].isdigit() else 0
                else:
                    main_num = 1
                    secondary_num = 0
                
                sample = {
                    'dream_text': interp.dream_text,
                    'main_number': main_num,
                    'secondary_number': secondary_num,
                    'combinations': numbers[:6],
                    'category': 'user_interpretation',
                    'source': 'real_interpretation'
                }
                training_data.append(sample)
        
        # 3. Generate synthetic data
        synthetic_data = self.generate_synthetic_dream_data()
        training_data.extend(synthetic_data)
        
        return training_data
    
    def generate_synthetic_dream_data(self):
        """Generate synthetic dream data"""
        import random
        
        # Dream elements with their numbers
        elements = {
            'งู': (5, 6, ['56', '89', '08', '65']),
            'ช้าง': (9, 1, ['91', '19', '01', '90']),
            'เสือ': (3, 4, ['34', '43', '03', '30']),
            'พระ': (8, 9, ['89', '98', '08', '99']),
            'เงิน': (8, 2, ['82', '28', '88', '22']),
            'ทอง': (9, 8, ['98', '89', '99', '88']),
        }
        
        # Templates
        templates = [
            "ฝันเห็น{element}ใหญ่{color}",
            "ฝันว่า{element}มา{action}ฉัน",
            "ในฝัน{element}ให้{object}ฉัน",
            "ฝัน{element}ตัวเล็กๆ",
            "เห็น{element}ในฝันเมื่อคืน"
        ]
        
        colors = ['สีทอง', 'สีขาว', 'สีดำ', 'สีแดง', 'สีเขียว']
        actions = ['กัด', 'ไล่', 'เล่นกับ', 'ตาม', 'คุ้มครอง']
        objects = ['เงิน', 'ทอง', 'ดอกไม้', 'อาหาร', 'ของขวัญ']
        
        synthetic_data = []
        
        for element, (main, secondary, combinations) in elements.items():
            for template in templates:
                for i in range(3):  # 3 samples per template per element
                    dream_text = template.format(
                        element=element,
                        color=random.choice(colors),
                        action=random.choice(actions),
                        object=random.choice(objects)
                    )
                    
                    sample = {
                        'dream_text': dream_text,
                        'main_number': main,
                        'secondary_number': secondary,
                        'combinations': combinations,
                        'category': 'synthetic',
                        'source': 'generated'
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
            result = await dream_symbol_api.train_model(training_data)
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
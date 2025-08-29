"""
Django management command สำหรับฝึกสอน Dream ML Model
"""
import os
import sys
from django.core.management.base import BaseCommand
from django.conf import settings

# Add MCP directory to Python path
MCP_DIR = os.path.join(settings.BASE_DIR, '..', 'mcp_dream_analysis')
sys.path.insert(0, MCP_DIR)

from data_preparation import prepare_and_save_data
from django_integration import train_model_from_django

class Command(BaseCommand):
    help = 'Train Dream Analysis ML Model with data from Django database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--prepare-data',
            action='store_true',
            help='Prepare training data from Django models first'
        )
        parser.add_argument(
            '--data-file',
            type=str,
            default='dream_training_data.json',
            help='Training data JSON file path'
        )
        parser.add_argument(
            '--save-model',
            action='store_true',
            default=True,
            help='Save the trained model after training'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🤖 เริ่มการฝึกสอน Dream Analysis ML Model')
        )
        
        # Step 1: Prepare data if requested
        if options['prepare_data']:
            self.stdout.write('📊 เตรียมข้อมูลการฝึกสอนจากฐานข้อมูล Django...')
            try:
                training_data = prepare_and_save_data(options['data_file'])
                self.stdout.write(
                    self.style.SUCCESS(f'✅ เตรียมข้อมูลสำเร็จ: {len(training_data)} รายการ')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ เตรียมข้อมูลไม่สำเร็จ: {str(e)}')
                )
                return
        
        # Step 2: Train model
        self.stdout.write('🎯 เริ่มการฝึกสอนโมเดล ML...')
        try:
            result = train_model_from_django()
            
            if result.get('success'):
                self.stdout.write(
                    self.style.SUCCESS('✅ การฝึกสอนโมเดลสำเร็จ!')
                )
                self.stdout.write(f'📈 จำนวนข้อมูลฝึกสอน: {result.get("training_samples", 0)}')
                
                metrics = result.get('metrics', {})
                if metrics:
                    self.stdout.write('📊 ผลการประเมินโมเดล:')
                    for metric, value in metrics.items():
                        self.stdout.write(f'   {metric}: {value:.4f}')
                
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
            self.style.SUCCESS('🏁 การฝึกสอนเสร็จสิ้น')
        )
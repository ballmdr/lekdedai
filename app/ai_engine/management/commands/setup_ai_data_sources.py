"""
Management command สำหรับตั้งค่าแหล่งข้อมูลสำหรับ AI
"""

from django.core.management.base import BaseCommand, CommandError
from ai_engine.models import DataSource, AIModelType
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'ตั้งค่าแหล่งข้อมูลและโมเดล AI เริ่มต้น'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-sources',
            action='store_true',
            help='สร้างแหล่งข้อมูลเริ่มต้น'
        )
        
        parser.add_argument(
            '--create-models',
            action='store_true',
            help='สร้างโมเดล AI เริ่มต้น'
        )
        
        parser.add_argument(
            '--reset',
            action='store_true',
            help='ลบข้อมูลเก่าแล้วสร้างใหม่ (ระวัง!)'
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(self.style.WARNING('⚠️  กำลังลบข้อมูลเก่าทั้งหมด...'))
            DataSource.objects.all().delete()
            AIModelType.objects.all().delete()
            self.stdout.write('ลบข้อมูลเก่าเสร็จแล้ว')
        
        if options['create_sources'] or not DataSource.objects.exists():
            self._create_data_sources()
        
        if options['create_models'] or not AIModelType.objects.exists():
            self._create_ai_models()
        
        self.stdout.write(self.style.SUCCESS('✅ ตั้งค่าระบบ AI เสร็จสิ้น'))
    
    def _create_data_sources(self):
        """สร้างแหล่งข้อมูลเริ่มต้น"""
        
        self.stdout.write('📊 กำลังสร้างแหล่งข้อมูล...')
        
        data_sources = [
            # แหล่งข่าว
            {
                'name': 'ข่าวหวยจาก News App',
                'source_type': 'news',
                'url': '/news/',
                'api_endpoint': '',
                'description': 'ดึงข่าวหวยจาก News App ภายในระบบ รวมบทความข่าวที่มีเลขเด็ดและการวิเคราะห์',
                'is_active': True,
                'scraping_interval': 3  # ทุก 3 ชั่วโมง (บ่อยกว่าเดิมเพราะเป็นข้อมูลภายใน)
            },
            {
                'name': 'Google News - หวย',
                'source_type': 'news', 
                'url': 'https://news.google.com/search?q=หวย',
                'api_endpoint': '',
                'is_active': False,  # ปิดไว้ก่อนเพราะต้องใช้ API Key
                'scraping_interval': 12
            },
            
            # แหล่งโซเชียลมีเดีย
            {
                'name': 'Facebook - กลุมหวย',
                'source_type': 'social_media',
                'url': 'https://facebook.com',
                'api_endpoint': '',
                'is_active': True,
                'scraping_interval': 4
            },
            {
                'name': 'Twitter - #หวย #เลขเด็ด',
                'source_type': 'social_media',
                'url': 'https://twitter.com/search?q=%23หวย',
                'api_endpoint': '',
                'is_active': True,
                'scraping_interval': 3
            },
            
            # แหล่งความฝัน
            {
                'name': 'ระบบตีความฝัน',
                'source_type': 'dreams',
                'url': '',
                'api_endpoint': '',
                'is_active': True,
                'scraping_interval': 8
            },
            
            # แหล่งสถิติและเทรนด์
            {
                'name': 'Google Trends - คำค้นหาหวย',
                'source_type': 'trends',
                'url': 'https://trends.google.com',
                'api_endpoint': '',
                'is_active': True,
                'scraping_interval': 24
            },
            
            # แหล่งโหราศาสตร์
            {
                'name': 'เว็บไซต์โหราศาสตร์',
                'source_type': 'astrology',
                'url': '',
                'api_endpoint': '',
                'is_active': False,  # ปิดไว้ก่อน
                'scraping_interval': 24
            }
        ]
        
        created_count = 0
        for source_data in data_sources:
            source, created = DataSource.objects.get_or_create(
                name=source_data['name'],
                defaults=source_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'  ✅ สร้าง: {source.name}')
            else:
                self.stdout.write(f'  ⏭️  มีอยู่แล้ว: {source.name}')
        
        self.stdout.write(f'สร้างแหล่งข้อมูลใหม่ {created_count} แหล่ง')
    
    def _create_ai_models(self):
        """สร้างโมเดล AI เริ่มต้น"""
        
        self.stdout.write('🤖 กำลังสร้างโมเดล AI...')
        
        ai_models = [
            {
                'name': 'Journalist AI',
                'role': 'journalist',
                'description': 'โมเดล AI สำหรับวิเคราะห์ข่าวสารและโซเชียลมีเดีย สกัดตัวเลขและวิเคราะห์กระแสความนิยม',
                'input_data_types': ['news', 'social_media'],
                'weight_in_ensemble': 0.4,
                'is_active': True
            },
            {
                'name': 'Dream Interpreter AI',
                'role': 'interpreter', 
                'description': 'โมเดล AI สำหรับตีความฝันและโหราศาสตร์ แปลงสัญลักษณ์เป็นตัวเลข',
                'input_data_types': ['dreams', 'astrology'],
                'weight_in_ensemble': 0.3,
                'is_active': True
            },
            {
                'name': 'Statistical Trend AI',
                'role': 'statistician',
                'description': 'โมเดล AI สำหรับวิเคราะห์สถิติและแนวโน้ม หาเลขฮิต เลขเย็น และรูปแบบ',
                'input_data_types': ['statistics', 'trends'],
                'weight_in_ensemble': 0.3,
                'is_active': True
            },
            {
                'name': 'Ensemble Master AI',
                'role': 'ensemble',
                'description': 'โมเดล AI หลักที่รวมผลจากทั้ง 3 โมเดลและตัดสินใจเลขเด็ดสุดท้าย',
                'input_data_types': ['all'],
                'weight_in_ensemble': 1.0,
                'is_active': True
            }
        ]
        
        created_count = 0
        for model_data in ai_models:
            model, created = AIModelType.objects.get_or_create(
                role=model_data['role'],
                defaults=model_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'  ✅ สร้าง: {model.name}')
            else:
                self.stdout.write(f'  ⏭️  มีอยู่แล้ว: {model.name}')
                # อัปเดตน้ำหนัก
                if model.weight_in_ensemble != model_data['weight_in_ensemble']:
                    model.weight_in_ensemble = model_data['weight_in_ensemble']
                    model.save()
                    weight = model_data["weight_in_ensemble"]
                    self.stdout.write(f'    🔄 อัปเดตน้ำหนัก: {weight}')
        
        self.stdout.write(f'สร้างโมเดล AI ใหม่ {created_count} โมเดล')
        
        # ตรวจสอบน้ำหนักรวม
        total_weight = sum([
            AIModelType.objects.get(role='journalist').weight_in_ensemble,
            AIModelType.objects.get(role='interpreter').weight_in_ensemble,
            AIModelType.objects.get(role='statistician').weight_in_ensemble
        ])
        
        if abs(total_weight - 1.0) > 0.01:
            self.stdout.write(
                self.style.WARNING(f'⚠️  น้ำหนักรวมของโมเดลไม่เท่ากับ 1.0 (ปัจจุบัน: {total_weight})')
            )
        else:
            self.stdout.write('✅ น้ำหนักของโมเดลถูกต้อง')
"""
Management command สำหรับตั้งค่าแหล่งข้อมูลสำหรับ AI
"""

from django.core.management.base import BaseCommand
from ai_engine.models import DataSource, AIModelType
from ai_engine.source_registry import (
    LEGACY_INACTIVE_NAMES,
    REGISTRY_VERSION,
    SOURCE_REGISTRY,
)
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
        """สร้าง/อัปเดตแหล่งข้อมูลจากทะเบียนที่อนุมัติ (Task 16).

        ยึด key เป็นตัวตน: รันซ้ำอัปเดตเฉพาะฟิลด์ทะเบียน ไม่ล้างเวลาสำเร็จ/ล้มเหลว.
        """

        self.stdout.write(f'📊 กำลังซิงค์ทะเบียนแหล่งข้อมูล v{REGISTRY_VERSION}...')

        for entry in SOURCE_REGISTRY:
            source, created = DataSource.objects.update_or_create(
                key=entry["key"],
                defaults={
                    "name": entry["name"],
                    "source_type": entry["source_type"],
                    "category": entry["category"],
                    "url": entry["url"],
                    "attribution": entry["attribution"],
                    "fetch_policy": entry["fetch_policy"],
                    "license_status": entry["license_status"],
                    "license_note": entry["license_note"],
                    "is_active": entry["is_active"],
                    "scraping_interval": entry["scraping_interval"],
                },
            )
            action = "สร้าง" if created else "อัปเดต"
            state = "เปิดใช้" if source.is_active else "ปิดไว้"
            self.stdout.write(f'  ✅ {action}: {source.name} ({state})')

        deactivated = (
            DataSource.objects.filter(name__in=LEGACY_INACTIVE_NAMES, is_active=True)
            .update(is_active=False)
        )
        if deactivated:
            self.stdout.write(
                f'  🔕 ปิดแหล่ง seed รุ่นเก่าที่ใช้จริงไม่ได้ {deactivated} แหล่ง'
            )

        self.stdout.write(
            f'ทะเบียนแหล่งข้อมูล: {DataSource.objects.filter(key__isnull=False).count()} แหล่ง'
        )
    
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
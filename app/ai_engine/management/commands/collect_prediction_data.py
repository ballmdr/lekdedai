"""
Management command สำหรับเก็บข้อมูลเพื่อการทำนาย
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from ai_engine.data_ingestion import DataIngestionManager
from ai_engine.models import DataSource
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'เก็บข้อมูลจากแหล่งต่างๆ เพื่อใช้ในการทำนายหวย'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source-type',
            type=str,
            choices=['news', 'social_media', 'dreams', 'trends'],
            help='ประเภทของแหล่งข้อมูลที่ต้องการเก็บ'
        )
        
        parser.add_argument(
            '--source-id',
            type=int,
            help='ID ของแหล่งข้อมูลเฉพาะที่ต้องการเก็บ'
        )
        
        parser.add_argument(
            '--cleanup-days',
            type=int,
            default=30,
            help='ลบข้อมูลเก่าที่เก็บไว้เกินกี่วัน (default: 30)'
        )
        
        parser.add_argument(
            '--cleanup-only',
            action='store_true',
            help='ลบข้อมูลเก่าอย่างเดียว ไม่เก็บข้อมูลใหม่'
        )

    def handle(self, *args, **options):
        ingestion_manager = DataIngestionManager()
        
        try:
            # ถ้าเป็น cleanup เท่านั้น
            if options['cleanup_only']:
                cleaned_count = ingestion_manager.cleanup_old_records(options['cleanup_days'])
                self.stdout.write(
                    self.style.SUCCESS(f'ลบข้อมูลเก่าแล้ว {cleaned_count} รายการ')
                )
                return
            
            # เก็บข้อมูลจากแหล่งเฉพาะ
            if options['source_id']:
                records_count = ingestion_manager.run_ingestion_for_source(options['source_id'])
                self.stdout.write(
                    self.style.SUCCESS(f'เก็บข้อมูลได้ {records_count} รายการจากแหล่งข้อมูล ID {options["source_id"]}')
                )
                return
            
            # เก็บข้อมูลจากประเภทเฉพาะ
            if options['source_type']:
                sources = DataSource.objects.filter(
                    source_type=options['source_type'],
                    is_active=True
                )
                
                if not sources.exists():
                    raise CommandError(f'ไม่พบแหล่งข้อมูลประเภท {options["source_type"]} ที่เปิดใช้งาน')
                
                total_records = 0
                for source in sources:
                    records_count = ingestion_manager.run_ingestion_for_source(source.id)
                    total_records += records_count
                    self.stdout.write(f'  - {source.name}: {records_count} รายการ')
                
                self.stdout.write(
                    self.style.SUCCESS(f'เก็บข้อมูลจาก {options["source_type"]} รวม {total_records} รายการ')
                )
                return
            
            # เก็บข้อมูลทั้งหมด
            self.stdout.write('กำลังเก็บข้อมูลจากทุกแหล่ง...')
            results = ingestion_manager.run_all_ingestors()
            
            # แสดงผลลัพธ์
            self.stdout.write('\n=== ผลลัพธ์การเก็บข้อมูล ===')
            for source_type, count in results.items():
                if source_type != 'total':
                    self.stdout.write(f'{source_type}: {count} รายการ')
            
            self.stdout.write(
                self.style.SUCCESS(f'\nเก็บข้อมูลเสร็จแล้ว รวม {results["total"]} รายการ')
            )
            
            # ลบข้อมูลเก่า
            if options['cleanup_days'] > 0:
                cleaned_count = ingestion_manager.cleanup_old_records(options['cleanup_days'])
                self.stdout.write(f'ลบข้อมูลเก่าแล้ว {cleaned_count} รายการ')
            
            # แสดงสถิติ
            stats = ingestion_manager.get_ingestion_statistics()
            self.stdout.write('\n=== สถิติการเก็บข้อมูล ===')
            self.stdout.write(f'ข้อมูลทั้งหมด: {stats["total_records"]} รายการ')
            self.stdout.write(f'ข้อมูลวันนี้: {stats["records_today"]} รายการ')
            self.stdout.write(f'คะแนนความเกี่ยวข้องเฉลี่ย: {stats["avg_relevance_score"]:.2f}')
            
        except Exception as e:
            logger.error(f'Error in data collection: {str(e)}')
            raise CommandError(f'เกิดข้อผิดพลาดในการเก็บข้อมูล: {str(e)}')
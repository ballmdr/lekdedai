"""
Management command สำหรับสร้างการทำนายด้วย AI
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime, timedelta
from ai_engine.prediction_engine import PredictionEngine
from ai_engine.models import PredictionSession, EnsemblePrediction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'สร้างการทำนายเลขเด็ดด้วย AI Ensemble Model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--draw-date',
            type=str,
            help='วันที่งวดหวย (รูปแบบ YYYY-MM-DD) ถ้าไม่ระบุจะใช้งวดถัดไป'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='บังคับสร้างการทำนายใหม่ แม้จะมีอยู่แล้ว'
        )
        
        parser.add_argument(
            '--session-id',
            type=str,
            help='ID ของเซสชันที่ต้องการรันใหม่'
        )
        
        parser.add_argument(
            '--lock-predictions',
            action='store_true',
            help='ล็อกการทำนายสำหรับวันที่ระบุ (ป้องกันการเปลี่ยนแปลง)'
        )
        
        parser.add_argument(
            '--show-stats',
            action='store_true',
            help='แสดงสถิติการทำนายล่าสุด'
        )

    def handle(self, *args, **options):
        engine = PredictionEngine()
        
        try:
            # แสดงสถิติ
            if options['show_stats']:
                self._show_prediction_stats()
                return
            
            # ล็อกการทำนาย
            if options['lock_predictions']:
                if not options['draw_date']:
                    raise CommandError('กรุณาระบุ --draw-date เมื่อใช้ --lock-predictions')
                
                draw_date = datetime.strptime(options['draw_date'], '%Y-%m-%d').date()
                engine.lock_predictions_for_draw_date(draw_date)
                self.stdout.write(
                    self.style.SUCCESS(f'ล็อกการทำนายสำหรับงวดวันที่ {draw_date} แล้ว')
                )
                return
            
            # กำหนดวันที่งวด
            if options['draw_date']:
                draw_date = datetime.strptime(options['draw_date'], '%Y-%m-%d').date()
            else:
                # หาวันที่งวดถัดไป (สมมุติหวยออกทุกวันที่ 1 และ 16 ของเดือน)
                draw_date = self._get_next_draw_date()
            
            # รันเซสชันเฉพาะ
            if options['session_id']:
                try:
                    session = PredictionSession.objects.get(session_id=options['session_id'])
                    self.stdout.write(f'กำลังรันเซสชัน {session.session_id}...')
                    ensemble_prediction = engine.run_prediction(session)
                    self._display_prediction_results(ensemble_prediction)
                    return
                except PredictionSession.DoesNotExist:
                    raise CommandError(f'ไม่พบเซสชัน {options["session_id"]}')
            
            # ตรวจสอบว่ามีการทำนายแล้วหรือไม่
            existing_prediction = EnsemblePrediction.objects.filter(
                session__for_draw_date=draw_date,
                session__status__in=['completed', 'locked']
            ).first()
            
            if existing_prediction and not options['force']:
                self.stdout.write(
                    self.style.WARNING(f'มีการทำนายสำหรับงวด {draw_date} อยู่แล้ว')
                )
                self.stdout.write('ใช้ --force เพื่อสร้างใหม่ หรือ --show-stats เพื่อดูผลลัพธ์')
                self._display_prediction_results(existing_prediction)
                return
            
            # สร้างเซสชันใหม่
            self.stdout.write(f'สร้างเซสชันการทำนายสำหรับงวด {draw_date}...')
            session = engine.create_prediction_session(draw_date)
            
            self.stdout.write(f'เซสชัน ID: {session.session_id}')
            self.stdout.write(f'ช่วงเก็บข้อมูล: {session.data_collection_period_start} ถึง {session.data_collection_period_end}')
            
            # รันการทำนาย
            self.stdout.write('กำลังรันการทำนาย AI...')
            self.stdout.write('- เริ่มต้นการวิเคราะห์ด้วย Journalist AI...')
            self.stdout.write('- เริ่มต้นการวิเคราะห์ด้วย Dream Interpreter AI...')
            self.stdout.write('- เริ่มต้นการวิเคราะห์ด้วย Statistical Trend AI...')
            self.stdout.write('- รวมผลการวิเคราะห์...')
            
            ensemble_prediction = engine.run_prediction(session)
            
            self.stdout.write(self.style.SUCCESS('การทำนาย AI เสร็จสิ้น!'))
            self._display_prediction_results(ensemble_prediction)
            
        except Exception as e:
            logger.error(f'Error in AI prediction: {str(e)}')
            raise CommandError(f'เกิดข้อผิดพลาดในการทำนาย: {str(e)}')
    
    def _get_next_draw_date(self) -> datetime.date:
        """หาวันที่งวดถัดไป"""
        today = timezone.now().date()
        
        # สมมุติหวยออกวันที่ 1 และ 16 ของทุกเดือน
        if today.day < 16:
            return today.replace(day=16)
        else:
            # เดือนถัดไป วันที่ 1
            if today.month == 12:
                return today.replace(year=today.year + 1, month=1, day=1)
            else:
                return today.replace(month=today.month + 1, day=1)
    
    def _display_prediction_results(self, prediction: EnsemblePrediction):
        """แสดงผลการทำนาย"""
        self.stdout.write('\\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('🎯 ผลการทำนาย AI Ensemble Model'))
        self.stdout.write('='*50)
        
        self.stdout.write(f'📅 งวดวันที่: {prediction.session.for_draw_date}')
        timestamp_str = prediction.prediction_timestamp.strftime("%d/%m/%Y %H:%M:%S")
        self.stdout.write(f'🕐 เวลาทำนาย: {timestamp_str}')
        self.stdout.write(f'📊 ความมั่นใจรวม: {prediction.overall_confidence:.1%}')
        self.stdout.write(f'📈 จำนวนข้อมูลที่ใช้: {prediction.total_data_points:,} รายการ')
        
        # เลข 2 ตัวแนะนำ
        if prediction.final_two_digit:
            self.stdout.write('\\n🎲 เลขท้าย 2 ตัวแนะนำ:')
            for i, item in enumerate(prediction.get_top_two_digit_numbers(), 1):
                number = item["number"]
                confidence = item["confidence"]
                reasoning = item["reasoning"][:80]
                self.stdout.write(f'  {i}. {number} (มั่นใจ {confidence:.1%})')
                self.stdout.write(f'     💡 {reasoning}...')
        
        # เลข 3 ตัวแนะนำ
        if prediction.final_three_digit:
            self.stdout.write('\\n🎯 เลขท้าย 3 ตัวแนะนำ:')
            for i, item in enumerate(prediction.get_top_three_digit_numbers(), 1):
                number = item["number"]
                confidence = item["confidence"]
                reasoning = item["reasoning"][:80]
                self.stdout.write(f'  {i}. {number} (มั่นใจ {confidence:.1%})')
                self.stdout.write(f'     💡 {reasoning}...')
        
        # สรุปการทำนาย
        self.stdout.write(f'\\n📝 สรุป: {prediction.prediction_summary}')
        
        # การมีส่วนร่วมของแต่ละโมเดล
        if prediction.model_contributions:
            self.stdout.write('\\n🤖 การมีส่วนร่วมของโมเดล AI:')
            for model_name, contribution in prediction.model_contributions.items():
                weight = contribution["weight"]
                self.stdout.write(f'  - {model_name}: น้ำหนัก {weight:.1%}')
                if contribution.get('top_numbers'):
                    two_digit = contribution['top_numbers'].get('two_digit', [])[:2]
                    if two_digit:
                        numbers_str = ", ".join(two_digit)
                        self.stdout.write(f'    เลขแนะนำ: {numbers_str}')
        
        self.stdout.write('\\n' + '='*50)
        self.stdout.write('🌟 เลขเด็ดจาก AI พร้อมแล้ว! โชคดีครับ/ค่ะ 🌟')
        self.stdout.write('='*50)
    
    def _show_prediction_stats(self):
        """แสดงสถิติการทำนาย"""
        from django.db.models import Count, Avg
        
        self.stdout.write('\\n' + '='*40)
        self.stdout.write('📊 สถิติการทำนาย AI')
        self.stdout.write('='*40)
        
        # จำนวนการทำนายทั้งหมด
        total_predictions = EnsemblePrediction.objects.count()
        self.stdout.write(f'การทำนายทั้งหมด: {total_predictions} ครั้ง')
        
        # การทำนายล่าสุด
        latest = EnsemblePrediction.objects.order_by('-prediction_timestamp').first()
        if latest:
            self.stdout.write(f'การทำนายล่าสุด: งวด {latest.session.for_draw_date}')
            self.stdout.write(f'ความมั่นใจ: {latest.overall_confidence:.1%}')
        
        # ความมั่นใจเฉลี่ย
        avg_confidence = EnsemblePrediction.objects.aggregate(
            avg_conf=Avg('overall_confidence')
        )['avg_conf']
        
        if avg_confidence:
            self.stdout.write(f'ความมั่นใจเฉลี่ย: {avg_confidence:.1%}')
        
        # สถิติเซสชัน
        sessions_by_status = dict(
            PredictionSession.objects.values('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        )
        
        self.stdout.write('\\nสถานะเซสชัน:')
        for status, count in sessions_by_status.items():
            self.stdout.write(f'  {status}: {count} เซสชัน')
        
        self.stdout.write('='*40)
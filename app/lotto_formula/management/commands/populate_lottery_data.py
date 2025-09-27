from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import random
from lotto_formula.models import LotteryFormula, LotteryResult, Prediction

class Command(BaseCommand):
    help = 'Populate lottery database with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Creating lottery formulas...')
        
        # สร้างสูตรคำนวณตัวอย่าง
        formulas_data = [
            {
                'name': 'สูตรบวกลบ',
                'description': 'สูตรคำนวณโดยการบวกลบเลขอ้างอิง เหมาะสำหรับผู้เริ่มต้น',
                'method': '''วิธีการคำนวณ:
1. เอาเลข 2 ตัวแรกจากเลขอ้างอิงมาบวกกัน
2. เอาเลข 2 ตัวแรกมาลบกัน
3. เอาเลข 2 ตัวแรกมาคูณกัน
4. นำผลลัพธ์มาจัดเรียงเป็นเลข 3 ตัว

ตัวอย่าง: เลขอ้างอิง 123456
- 1+2=3, 1-2=-1(9), 1×2=2 → 392
- 2+3=5, 2-3=-1(9), 2×3=6 → 596''',
                'accuracy_rate': 78.5,
            },
            {
                'name': 'สูตรเลขวิ่ง',
                'description': 'สูตรคำนวณเลขที่วิ่งตามลำดับ เหมาะสำหรับเลขท้าย 3 ตัว',
                'method': '''วิธีการคำนวณ:
1. เอาเลขตัวแรกจากเลขอ้างอิง
2. บวกเพิ่มทีละ 1 ไปเรื่อยๆ
3. ถ้าเกิน 9 ให้เริ่มใหม่ที่ 0

ตัวอย่าง: เลขอ้างอิง 345
- เลขฐาน 3: 345, 456, 567
- เลขฐาน 4: 456, 567, 678''',
                'accuracy_rate': 65.2,
            },
            {
                'name': 'สูตรเลขกลับ',
                'description': 'สูตรคำนวณโดยการกลับเลขและคำนวณ เหมาะสำหรับรางวัลใหญ่',
                'method': '''วิธีการคำนวณ:
1. เอาเลขอ้างอิงมากลับหลัง
2. นำเลขเดิมกับเลขกลับมาบวกกัน
3. นำเลขเดิมกับเลขกลับมาลบกัน
4. นำเลขเดิมคูณ 2

ตัวอย่าง: เลขอ้างอิง 123
- เลขกลับ 321
- 123+321=444
- 123-321=-198 → 802''',
                'accuracy_rate': 82.1,
            },
            {
                'name': 'สูตรเลขคู่คี่',
                'description': 'สูตรคำนวณโดยแยกเลขคู่และเลขคี่ เหมาะสำหรับเลขท้าย 2 ตัว',
                'method': '''วิธีการคำนวณ:
1. แยกเลขคู่และเลขคี่จากเลขอ้างอิง
2. รวมเลขคู่ทั้งหมด
3. รวมเลขคี่ทั้งหมด
4. นำผลรวมมาคำนวณต่อ

ตัวอย่าง: เลขอ้างอิง 123456
- เลขคู่: 2,4,6 รวม=12
- เลขคี่: 1,3,5 รวม=9
- ผลลัพธ์: 12+9=21 → 21''',
                'accuracy_rate': 71.8,
            },
            {
                'name': 'สูตรเลขมงคล',
                'description': 'สูตรคำนวณตามหลักโหราศาสตร์ไทย เหมาะสำหรับผู้ที่เชื่อเรื่องมงคล',
                'method': '''วิธีการคำนวณ:
1. นำเลขอ้างอิงมาคำนวณตามหลักเลขศาสตร์
2. บวกเลขทุกตัวจนได้เลขหลักเดียว
3. นำเลขมงคลมาประกอบ
4. คำนวณตามวันในสัปดาห์

ตัวอย่าง: เลขอ้างอิง 789
- 7+8+9=24 → 2+4=6
- เลขมงคล 6: 168, 269, 360''',
                'accuracy_rate': 69.4,
            }
        ]

        for formula_data in formulas_data:
            formula, created = LotteryFormula.objects.get_or_create(
                name=formula_data['name'],
                defaults=formula_data
            )
            if created:
                self.stdout.write(f'Created formula: {formula.name}')

        # สร้างผลหวยตัวอย่าง
        self.stdout.write('Creating lottery results...')
        
        # สร้างผลหวย 20 งวดย้อนหลัง
        for i in range(20):
            draw_date = timezone.now().date() - timedelta(days=i*15)  # ทุก 15 วัน
            first_prize = f"{random.randint(100000, 999999):06d}"
            
            result, created = LotteryResult.objects.get_or_create(
                draw_date=draw_date,
                defaults={
                    'first_prize': first_prize,
                    'winning_numbers': first_prize
                }
            )
            if created:
                self.stdout.write(f'Created result for {draw_date}: {first_prize}')

        # สร้างการทำนายตัวอย่าง
        self.stdout.write('Creating predictions...')
        
        formulas = LotteryFormula.objects.all()
        results = LotteryResult.objects.all()
        
        for formula in formulas:
            correct_count = 0
            total_count = 0
            
            for result in results[:15]:  # ทำนาย 15 งวดล่าสุด
                # สร้างเลขทำนายแบบสุ่ม
                predicted_numbers = f"{random.randint(100, 999):03d}"
                
                # กำหนดความถูกต้องตามอัตราความแม่นยำของสูตร
                is_correct = random.random() < (formula.accuracy_rate / 100)
                if is_correct:
                    correct_count += 1
                total_count += 1
                
                prediction, created = Prediction.objects.get_or_create(
                    formula=formula,
                    draw_date=result.draw_date,
                    defaults={
                        'predicted_numbers': predicted_numbers,
                        'is_correct': is_correct
                    }
                )
            
            # อัปเดตสถิติของสูตร
            formula.total_predictions = total_count
            formula.correct_predictions = correct_count
            formula.accuracy_rate = (correct_count / total_count * 100) if total_count > 0 else 0
            formula.save()
            
            self.stdout.write(f'Updated {formula.name}: {correct_count}/{total_count} correct')

        self.stdout.write(
            self.style.SUCCESS('Successfully populated lottery data!')
        )

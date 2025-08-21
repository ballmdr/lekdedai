from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from lottery_checker.models import LotteryDraw

class Command(BaseCommand):
    help = 'เพิ่มข้อมูลตัวอย่างหวยในฐานข้อมูล'

    def handle(self, *args, **options):
        # ลบข้อมูลเก่าทั้งหมด
        LotteryDraw.objects.all().delete()
        self.stdout.write('ลบข้อมูลเก่าทั้งหมดแล้ว')
        
        # สร้างข้อมูลตัวอย่าง 12 งวดย้อนหลัง
        today = date.today()
        
        for i in range(12):
            draw_date = today - timedelta(days=i*15)  # ประมาณ 15 วันต่องวด
            
            # สร้างเลขรางวัลตัวอย่าง
            base_number = 100000 + (i * 1000)  # เลขฐานที่เปลี่ยนไปตามงวด
            
            draw = LotteryDraw.objects.create(
                draw_date=draw_date,
                draw_number=f"งวดที่ {draw_date.strftime('%Y%m%d')}",
                first_prize=str(base_number + 12345),
                second_prize_1=str(base_number + 23456),
                second_prize_2=str(base_number + 34567),
                second_prize_3=str(base_number + 45678),
                third_prize_1=str(base_number + 56789),
                third_prize_2=str(base_number + 67890),
                third_prize_3=str(base_number + 78901),
                third_prize_4=str(base_number + 89012),
                third_prize_5=str(base_number + 90123),
                fourth_prize_1=str(base_number + 11111),
                fourth_prize_2=str(base_number + 22222),
                fourth_prize_3=str(base_number + 33333),
                fourth_prize_4=str(base_number + 44444),
                fourth_prize_5=str(base_number + 55555),
                fourth_prize_6=str(base_number + 66666),
                fourth_prize_7=str(base_number + 77777),
                fourth_prize_8=str(base_number + 88888),
                fourth_prize_9=str(base_number + 99999),
                fourth_prize_10=str(base_number + 00000),
                fifth_prize_1=str(base_number + 10101),
                fifth_prize_2=str(base_number + 20202),
                fifth_prize_3=str(base_number + 30303),
                fifth_prize_4=str(base_number + 40404),
                fifth_prize_5=str(base_number + 50505),
                fifth_prize_6=str(base_number + 60606),
                fifth_prize_7=str(base_number + 70707),
                fifth_prize_8=str(base_number + 80808),
                fifth_prize_9=str(base_number + 90909),
                fifth_prize_10=str(base_number + 12121),
                fifth_prize_11=str(base_number + 13131),
                fifth_prize_12=str(base_number + 14141),
                fifth_prize_13=str(base_number + 15151),
                fifth_prize_14=str(base_number + 16161),
                fifth_prize_15=str(base_number + 17171),
                fifth_prize_16=str(base_number + 18181),
                fifth_prize_17=str(base_number + 19191),
                fifth_prize_18=str(base_number + 21212),
                fifth_prize_19=str(base_number + 22222),
                fifth_prize_20=str(base_number + 23232),
                fifth_prize_21=str(base_number + 24242),
                fifth_prize_22=str(base_number + 25252),
                fifth_prize_23=str(base_number + 26262),
                fifth_prize_24=str(base_number + 27272),
                fifth_prize_25=str(base_number + 28282),
                fifth_prize_26=str(base_number + 29292),
                fifth_prize_27=str(base_number + 31313),
                fifth_prize_28=str(base_number + 32323),
                fifth_prize_29=str(base_number + 33333),
                fifth_prize_30=str(base_number + 34343),
                fifth_prize_31=str(base_number + 35353),
                fifth_prize_32=str(base_number + 36363),
                fifth_prize_33=str(base_number + 37373),
                fifth_prize_34=str(base_number + 38383),
                fifth_prize_35=str(base_number + 39393),
                fifth_prize_36=str(base_number + 41414),
                fifth_prize_37=str(base_number + 42424),
                fifth_prize_38=str(base_number + 43434),
                fifth_prize_39=str(base_number + 44444),
                fifth_prize_40=str(base_number + 45454),
                fifth_prize_41=str(base_number + 46464),
                fifth_prize_42=str(base_number + 47474),
                fifth_prize_43=str(base_number + 48484),
                fifth_prize_44=str(base_number + 49494),
                fifth_prize_45=str(base_number + 51515),
                fifth_prize_46=str(base_number + 52525),
                fifth_prize_47=str(base_number + 53535),
                fifth_prize_48=str(base_number + 54545),
                fifth_prize_49=str(base_number + 55555),
                fifth_prize_50=str(base_number + 56565),
                source="Sample Data"
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'สร้างข้อมูลงวดวันที่ {draw_date.strftime("%d/%m/%Y")} สำเร็จ'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'สร้างข้อมูลตัวอย่างทั้งหมด {LotteryDraw.objects.count()} งวดเรียบร้อยแล้ว'
            )
        )


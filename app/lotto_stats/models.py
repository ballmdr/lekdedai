from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta

class LotteryDraw(models.Model):
    """ข้อมูลการออกรางวัลแต่ละงวด"""
    draw_date = models.DateField("วันที่ออกรางวัล", unique=True)
    draw_round = models.CharField("งวดที่", max_length=20, blank=True)
    
    # รางวัลหลัก
    first_prize = models.CharField("รางวัลที่ 1", max_length=6)
    
    # เลข 2 ตัว
    two_digit = models.CharField("เลขท้าย 2 ตัว", max_length=2)
    
    # เลข 3 ตัว
    three_digit_front = models.CharField("เลขหน้า 3 ตัว", max_length=100, help_text="คั่นด้วยเครื่องหมายจุลภาค")
    three_digit_back = models.CharField("เลขท้าย 3 ตัว", max_length=100, help_text="คั่นด้วยเครื่องหมายจุลภาค")
    
    created_at = models.DateTimeField("บันทึกเมื่อ", auto_now_add=True)
    updated_at = models.DateTimeField("อัปเดตเมื่อ", auto_now=True)
    
    class Meta:
        verbose_name = "ผลการออกรางวัล"
        verbose_name_plural = "ผลการออกรางวัล"
        ordering = ['-draw_date']
    
    def __str__(self):
        return f"งวดวันที่ {self.draw_date.strftime('%d/%m/%Y')} - {self.first_prize}"
    
    def get_all_two_digits(self):
        """ดึงเลข 2 ตัวทั้งหมดจากรางวัลที่ 1"""
        return [self.first_prize[i:i+2] for i in range(5)]
    
    def get_all_three_digits(self):
        """ดึงเลข 3 ตัวทั้งหมด"""
        front = [x.strip() for x in self.three_digit_front.split(',') if x.strip()]
        back = [x.strip() for x in self.three_digit_back.split(',') if x.strip()]
        return front + back
    
    def get_three_digit_front_list(self, limit=2):
        """ดึงเลขหน้า 3 ตัว (3 ตัวแรก) เฉพาะจำนวนที่ระบุ"""
        full_numbers = [x.strip() for x in self.three_digit_front.split(',') if x.strip()]
        # ตัดเอาเฉพาะ 3 ตัวแรกของแต่ละเลข
        three_digit_numbers = [num[:3] for num in full_numbers if len(num) >= 3]
        return three_digit_numbers[:limit]
    
    def get_three_digit_back_list(self, limit=2):
        """ดึงเลขท้าย 3 ตัว (3 ตัวท้าย) เฉพาะจำนวนที่ระบุ"""
        full_numbers = [x.strip() for x in self.three_digit_back.split(',') if x.strip()]
        # ตัดเอาเฉพาะ 3 ตัวท้ายของแต่ละเลข
        three_digit_numbers = [num[-3:] for num in full_numbers if len(num) >= 3]
        return three_digit_numbers[:limit]

class NumberStatistics(models.Model):
    """สถิติของเลขแต่ละตัว"""
    number = models.CharField("เลข", max_length=3, unique=True)
    number_type = models.CharField("ประเภท", max_length=10, choices=[
        ('2D', 'เลข 2 ตัว'),
        ('3D', 'เลข 3 ตัว'),
    ])
    
    # สถิติการออก
    total_appearances = models.IntegerField("จำนวนครั้งที่ออก", default=0)
    last_appeared = models.DateField("ออกล่าสุดเมื่อ", null=True, blank=True)
    days_since_last = models.IntegerField("จำนวนวันที่ไม่ออก", default=0)
    
    # สถิติเพิ่มเติม
    max_consecutive = models.IntegerField("ออกติดต่อกันสูงสุด", default=0)
    average_gap = models.FloatField("ระยะห่างเฉลี่ย (วัน)", default=0)
    
    updated_at = models.DateTimeField("อัปเดตล่าสุด", auto_now=True)
    
    class Meta:
        verbose_name = "สถิติเลข"
        verbose_name_plural = "สถิติเลข"
        ordering = ['-total_appearances']
    
    def __str__(self):
        return f"{self.number} ({self.number_type})"

class HotColdNumber(models.Model):
    """เลขฮอต/เลขเย็น"""
    date = models.DateField("วันที่คำนวณ", default=timezone.now)
    
    # เลขฮอต (ออกบ่อย)
    hot_2d = models.JSONField("เลขฮอต 2 ตัว", default=list)
    hot_3d = models.JSONField("เลขฮอต 3 ตัว", default=list)
    
    # เลขเย็น (ไม่ออกนาน)
    cold_2d = models.JSONField("เลขเย็น 2 ตัว", default=list)
    cold_3d = models.JSONField("เลขเย็น 3 ตัว", default=list)
    
    # ช่วงเวลาที่ใช้คำนวณ
    calculation_days = models.IntegerField("จำนวนวันที่ใช้คำนวณ", default=90)
    
    class Meta:
        verbose_name = "เลขฮอต/เลขเย็น"
        verbose_name_plural = "เลขฮอต/เลขเย็น"
        ordering = ['-date']
        
    def __str__(self):
        return f"{self.number} ({self.number_type})"
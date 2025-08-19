from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

class AIModel(models.Model):
    """โมเดล AI สำหรับทำนายเลข"""
    name = models.CharField("ชื่อโมเดล", max_length=100)
    version = models.CharField("เวอร์ชัน", max_length=20)
    algorithm = models.CharField("อัลกอริทึม", max_length=50, choices=[
        ('random_forest', 'Random Forest'),
        ('neural_network', 'Neural Network'),
        ('pattern_analysis', 'Pattern Analysis'),
        ('statistical', 'Statistical Model'),
    ], default='pattern_analysis')
    
    accuracy = models.FloatField("ความแม่นยำ (%)", default=0.0)
    training_date = models.DateTimeField("วันที่เทรน", auto_now_add=True)
    is_active = models.BooleanField("ใช้งานอยู่", default=True)
    
    # Model parameters
    parameters = models.JSONField("พารามิเตอร์", default=dict)
    
    class Meta:
        verbose_name = "โมเดล AI"
        verbose_name_plural = "โมเดล AI"
        ordering = ['-training_date']
    
    def __str__(self):
        return f"{self.name} v{self.version}"

class PredictionFactor(models.Model):
    """ปัจจัยที่ใช้ในการทำนาย"""
    name = models.CharField("ชื่อปัจจัย", max_length=100)
    code = models.CharField("รหัส", max_length=50, unique=True)
    description = models.TextField("คำอธิบาย", blank=True)
    weight = models.FloatField("น้ำหนัก", default=1.0)
    is_active = models.BooleanField("ใช้งาน", default=True)
    
    class Meta:
        verbose_name = "ปัจจัยการทำนาย"
        verbose_name_plural = "ปัจจัยการทำนาย"
    
    def __str__(self):
        return self.name

class LuckyNumberPrediction(models.Model):
    """ผลการทำนายเลขเด็ด"""
    prediction_date = models.DateField("วันที่ทำนาย", default=timezone.now)
    for_draw_date = models.DateField("สำหรับงวดวันที่", null=True, blank=True)
    
    # โมเดลที่ใช้
    ai_model = models.ForeignKey(
        AIModel,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="โมเดลที่ใช้"
    )
    
    # เลขที่ทำนาย
    two_digit_numbers = models.CharField(
        "เลข 2 ตัว",
        max_length=200,
        help_text="คั่นด้วยเครื่องหมายจุลภาค"
    )
    three_digit_numbers = models.CharField(
        "เลข 3 ตัว",
        max_length=200,
        help_text="คั่นด้วยเครื่องหมายจุลภาค"
    )
    
    # Confidence scores
    overall_confidence = models.FloatField("ความมั่นใจรวม (%)", default=50.0)
    
    # รายละเอียดการทำนาย
    prediction_details = models.JSONField("รายละเอียดการทำนาย", default=dict)
    factors_used = models.JSONField("ปัจจัยที่ใช้", default=dict)
    
    # ผู้ใช้ที่ขอทำนาย
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ผู้ขอทำนาย"
    )
    
    created_at = models.DateTimeField("สร้างเมื่อ", auto_now_add=True)
    views = models.IntegerField("จำนวนคนดู", default=0)
    
    class Meta:
        verbose_name = "การทำนายเลขเด็ด"
        verbose_name_plural = "การทำนายเลขเด็ด"
        ordering = ['-prediction_date', '-created_at']
    
    def __str__(self):
        return f"ทำนายวันที่ {self.prediction_date.strftime('%d/%m/%Y')}"
    
    def get_two_digit_list(self):
        """แปลงเลข 2 ตัวเป็น list"""
        return [num.strip() for num in self.two_digit_numbers.split(',') if num.strip()]
    
    def get_three_digit_list(self):
        """แปลงเลข 3 ตัวเป็น list"""
        return [num.strip() for num in self.three_digit_numbers.split(',') if num.strip()]

class PredictionAccuracy(models.Model):
    """บันทึกความแม่นยำของการทำนาย"""
    prediction = models.ForeignKey(
        LuckyNumberPrediction,
        on_delete=models.CASCADE,
        related_name='accuracy_records',
        verbose_name="การทำนาย"
    )
    
    actual_result = models.CharField("ผลที่ออกจริง", max_length=6)
    actual_two_digit = models.CharField("2 ตัวที่ออก", max_length=2)
    
    # ผลการตรวจสอบ
    is_correct_first = models.BooleanField("ถูกรางวัลที่ 1", default=False)
    is_correct_two_digit = models.BooleanField("ถูก 2 ตัว", default=False)
    is_correct_three_digit = models.BooleanField("ถูก 3 ตัว", default=False)
    
    checked_date = models.DateField("วันที่ตรวจสอบ", auto_now_add=True)
    
    class Meta:
        verbose_name = "ความแม่นยำการทำนาย"
        verbose_name_plural = "ความแม่นยำการทำนาย"

class UserFeedback(models.Model):
    """ฟีดแบ็คจากผู้ใช้"""
    prediction = models.ForeignKey(
        LuckyNumberPrediction,
        on_delete=models.CASCADE,
        related_name='feedbacks',
        verbose_name="การทำนาย"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ผู้ให้ฟีดแบ็ค"
    )
    
    RATING_CHOICES = [
        (5, '⭐⭐⭐⭐⭐ ดีมาก'),
        (4, '⭐⭐⭐⭐ ดี'),
        (3, '⭐⭐⭐ ปานกลาง'),
        (2, '⭐⭐ แย่'),
        (1, '⭐ แย่มาก'),
    ]
    
    rating = models.IntegerField("คะแนน", choices=RATING_CHOICES)
    comment = models.TextField("ความคิดเห็น", blank=True)
    is_winner = models.BooleanField("ถูกรางวัล", default=False)
    
    created_at = models.DateTimeField("ให้คะแนนเมื่อ", auto_now_add=True)
    
    class Meta:
        verbose_name = "ฟีดแบ็ค"
        verbose_name_plural = "ฟีดแบ็ค"
        ordering = ['-created_at']
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
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
    
    # เชื่อมโยงกับโมเดลใหม่
    model_type = models.ForeignKey(
        'AIModelType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ประเภทโมเดลใหม่"
    )
    
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
    # สามารถเชื่อมโยงกับการทำนายแบบเก่าหรือแบบใหม่
    old_prediction = models.ForeignKey(
        LuckyNumberPrediction,
        on_delete=models.CASCADE,
        related_name='feedbacks',
        null=True,
        blank=True,
        verbose_name="การทำนายแบบเก่า"
    )
    
    ensemble_prediction = models.ForeignKey(
        'EnsemblePrediction',
        on_delete=models.CASCADE,
        related_name='feedbacks',
        null=True,
        blank=True,
        verbose_name="การทำนาย AI รวม"
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

class DataSource(models.Model):
    """แหล่งข้อมูลสำหรับ AI"""
    SOURCE_TYPES = [
        ('news', 'ข่าว'),
        ('social_media', 'โซเชียลมีเดีย'),
        ('dreams', 'ความฝัน'),
        ('statistics', 'สถิติ'),
        ('trends', 'เทรนด์'),
        ('astrology', 'โหราศาสตร์'),
    ]
    
    name = models.CharField("ชื่อแหล่งข้อมูล", max_length=100)
    source_type = models.CharField("ประเภท", max_length=20, choices=SOURCE_TYPES)
    url = models.URLField("URL", blank=True)
    api_endpoint = models.URLField("API Endpoint", blank=True)
    api_key = models.CharField("API Key", max_length=255, blank=True)
    is_active = models.BooleanField("ใช้งานอยู่", default=True)
    scraping_interval = models.IntegerField("ความถี่เก็บข้อมูล (ชั่วโมง)", default=6)
    
    last_scraped = models.DateTimeField("เก็บข้อมูลล่าสุด", null=True, blank=True)
    
    class Meta:
        verbose_name = "แหล่งข้อมูล"
        verbose_name_plural = "แหล่งข้อมูล"
    
    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"

class DataIngestionRecord(models.Model):
    """บันทึกการเก็บข้อมูล"""
    data_source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name='ingestion_records',
        verbose_name="แหล่งข้อมูล"
    )
    
    # ข้อมูลดิบที่เก็บได้
    raw_content = models.TextField("ข้อมูลดิบ")
    processed_content = models.TextField("ข้อมูลที่ประมวลผลแล้ว", blank=True)
    
    # Metadata
    title = models.CharField("หัวข้อ", max_length=500, blank=True)
    publish_date = models.DateTimeField("วันที่เผยแพร่", null=True, blank=True)
    author = models.CharField("ผู้เขียน", max_length=200, blank=True)
    
    # การประมวลผล
    extracted_numbers = models.JSONField("เลขที่สกัดได้", default=list)
    keywords = models.JSONField("คำสำคัญ", default=list)
    sentiment_score = models.FloatField("คะแนนอารมณ์", null=True, blank=True)
    relevance_score = models.FloatField("คะแนนความเกี่ยวข้อง", default=0.0)
    
    # ข้อมูลระบบ
    ingested_at = models.DateTimeField("เก็บข้อมูลเมื่อ", auto_now_add=True)
    processed_at = models.DateTimeField("ประมวลผลเมื่อ", null=True, blank=True)
    processing_status = models.CharField(
        "สถานะการประมวลผล",
        max_length=20,
        choices=[
            ('pending', 'รอประมวลผล'),
            ('processing', 'กำลังประมวลผล'),
            ('completed', 'เสร็จสิ้น'),
            ('failed', 'ล้มเหลว'),
        ],
        default='pending'
    )
    
    error_message = models.TextField("ข้อความข้อผิดพลาด", blank=True)
    
    class Meta:
        verbose_name = "บันทึกการเก็บข้อมูล"
        verbose_name_plural = "บันทึกการเก็บข้อมูล"
        ordering = ['-ingested_at']
        indexes = [
            models.Index(fields=['data_source', '-ingested_at']),
            models.Index(fields=['processing_status', '-ingested_at']),
        ]
    
    def __str__(self):
        return f"{self.data_source.name} - {self.ingested_at.strftime('%d/%m/%Y %H:%M')}"

class AIModelType(models.Model):
    """ประเภทของโมเดล AI"""
    MODEL_ROLES = [
        ('journalist', 'Journalist AI - วิเคราะห์ข่าวและโซเชียลมีเดีย'),
        ('interpreter', 'Interpreter AI - ตีความฝันและโหราศาสตร์'),
        ('statistician', 'Statistician AI - วิเคราะห์สถิติและเทรนด์'),
        ('ensemble', 'Ensemble AI - รวมผลจากโมเดลทั้งหมด'),
    ]
    
    name = models.CharField("ชื่อโมเดล", max_length=100)
    role = models.CharField("บทบาท", max_length=20, choices=MODEL_ROLES)
    description = models.TextField("คำอธิบาย")
    input_data_types = models.JSONField("ประเภทข้อมูลนำเข้า", default=list)
    weight_in_ensemble = models.FloatField("น้ำหนักในการรวม", default=1.0)
    is_active = models.BooleanField("ใช้งานอยู่", default=True)
    
    class Meta:
        verbose_name = "ประเภทโมเดล AI"
        verbose_name_plural = "ประเภทโมเดล AI"
    
    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"

class PredictionSession(models.Model):
    """เซสชันการทำนาย - รวบรวมการทำงานของ AI ทั้ง 3 โมเดล"""
    session_id = models.CharField("รหัสเซสชัน", max_length=50, unique=True)
    for_draw_date = models.DateField("สำหรับงวดวันที่")
    start_time = models.DateTimeField("เริ่มต้นเมื่อ", auto_now_add=True)
    end_time = models.DateTimeField("สิ้นสุดเมื่อ", null=True, blank=True)
    
    # ข้อมูลที่ใช้ในการทำนาย
    data_collection_period_start = models.DateTimeField("เก็บข้อมูลตั้งแต่")
    data_collection_period_end = models.DateTimeField("เก็บข้อมูลถึง")
    
    # สถานะ
    STATUS_CHOICES = [
        ('collecting_data', 'กำลังเก็บข้อมูล'),
        ('analyzing', 'กำลังวิเคราะห์'),
        ('completed', 'เสร็จสิ้น'),
        ('failed', 'ล้มเหลว'),
        ('locked', 'ล็อกแล้ว'),  # ล็อกเพื่อไม่ให้เปลี่ยนแปลงในวันหวยออก
    ]
    
    status = models.CharField("สถานะ", max_length=20, choices=STATUS_CHOICES, default='collecting_data')
    
    # ข้อมูลสถิติ
    total_data_sources = models.IntegerField("จำนวนแหล่งข้อมูล", default=0)
    total_data_points = models.IntegerField("จำนวนข้อมูล", default=0)
    processing_time_seconds = models.FloatField("เวลาประมวลผล (วินาที)", null=True, blank=True)
    
    class Meta:
        verbose_name = "เซสชันการทำนาย"
        verbose_name_plural = "เซสชันการทำนาย"
        ordering = ['-start_time']
    
    def __str__(self):
        return f"การทำนายงวด {self.for_draw_date} ({self.get_status_display()})"

class ModelPrediction(models.Model):
    """ผลการทำนายจากโมเดลแต่ละตัว"""
    session = models.ForeignKey(
        PredictionSession,
        on_delete=models.CASCADE,
        related_name='model_predictions',
        verbose_name="เซสชัน"
    )
    
    model_type = models.ForeignKey(
        AIModelType,
        on_delete=models.CASCADE,
        verbose_name="โมเดล"
    )
    
    # ผลการทำนาย
    predicted_numbers = models.JSONField("เลขที่ทำนาย")
    confidence_scores = models.JSONField("คะแนนความมั่นใจ")
    reasoning = models.JSONField("เหตุผลการทำนาย")
    
    # ข้อมูลที่ใช้
    input_data_summary = models.JSONField("สรุปข้อมูลนำเข้า")
    data_sources_used = models.JSONField("แหล่งข้อมูลที่ใช้")
    
    # Performance metrics
    processing_time = models.FloatField("เวลาประมวลผล (วินาที)")
    created_at = models.DateTimeField("สร้างเมื่อ", auto_now_add=True)
    
    class Meta:
        verbose_name = "ผลการทำนายของโมเดล"
        verbose_name_plural = "ผลการทำนายของโมเดล"
        unique_together = ['session', 'model_type']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.model_type.name} - {self.session.for_draw_date}"

class EnsemblePrediction(models.Model):
    """ผลการทำนายรวมสุดท้าย"""
    session = models.OneToOneField(
        PredictionSession,
        on_delete=models.CASCADE,
        related_name='ensemble_prediction',
        verbose_name="เซสชัน"
    )
    
    # เลขเด็ดสุดท้าย
    final_two_digit = models.JSONField("เลข 2 ตัวสุดท้าย")  # [{"number": "15", "confidence": 0.85, "reasoning": "..."}]
    final_three_digit = models.JSONField("เลข 3 ตัวสุดท้าย")
    
    # คะแนนรวม
    overall_confidence = models.FloatField("ความมั่นใจรวม")
    
    # การอธิบาย
    prediction_summary = models.TextField("สรุปการทำนาย")
    model_contributions = models.JSONField("การมีส่วนร่วมของแต่ละโมเดล")
    
    # สถิติ
    total_data_points = models.IntegerField("จำนวนข้อมูลที่ใช้")
    prediction_timestamp = models.DateTimeField("เวลาทำนาย", auto_now_add=True)
    
    # การแสดงผล
    is_featured = models.BooleanField("แสดงในหน้าหลัก", default=False)
    view_count = models.IntegerField("จำนวนผู้ดู", default=0)
    
    class Meta:
        verbose_name = "การทำนายรวมสุดท้าย"
        verbose_name_plural = "การทำนายรวมสุดท้าย"
        ordering = ['-prediction_timestamp']
    
    def __str__(self):
        return f"เลขเด็ด AI งวด {self.session.for_draw_date}"
    
    def get_top_two_digit_numbers(self, limit=3):
        """ดึงเลข 2 ตัวอันดับต้น"""
        return sorted(self.final_two_digit, key=lambda x: x['confidence'], reverse=True)[:limit]
    
    def get_top_three_digit_numbers(self, limit=2):
        """ดึงเลข 3 ตัวอันดับต้น"""
        return sorted(self.final_three_digit, key=lambda x: x['confidence'], reverse=True)[:limit]

class PredictionAccuracyTracking(models.Model):
    """ติดตามความแม่นยำของการทำนาย"""
    ensemble_prediction = models.OneToOneField(
        EnsemblePrediction,
        on_delete=models.CASCADE,
        related_name='accuracy_tracking',
        verbose_name="การทำนาย"
    )
    
    # ผลจริงที่ออก
    actual_first_prize = models.CharField("รางวัลที่ 1 ที่ออกจริง", max_length=6, blank=True)
    actual_last_two_digits = models.CharField("เลข 2 ตัวท้ายที่ออกจริง", max_length=2, blank=True)
    actual_last_three_digits = models.CharField("เลข 3 ตัวท้ายที่ออกจริง", max_length=3, blank=True)
    
    # ความแม่นยำ
    two_digit_accuracy = models.BooleanField("ทำนายเลข 2 ตัวถูก", default=False)
    three_digit_accuracy = models.BooleanField("ทำนายเลข 3 ตัวถูก", default=False)
    first_prize_accuracy = models.BooleanField("ทำนายรางวัลที่ 1 ถูก", default=False)
    
    # ความแม่นยำย่อย
    model_accuracies = models.JSONField("ความแม่นยำของแต่ละโมเดล", default=dict)
    
    # การอัปเดต
    checked_at = models.DateTimeField("ตรวจสอบเมื่อ", auto_now_add=True)
    updated_at = models.DateTimeField("อัปเดตเมื่อ", auto_now=True)
    
    class Meta:
        verbose_name = "การติดตามความแม่นยำ"
        verbose_name_plural = "การติดตามความแม่นยำ"
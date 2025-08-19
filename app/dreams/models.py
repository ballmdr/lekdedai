from django.db import models
from django.contrib.auth.models import User

class DreamCategory(models.Model):
    """หมวดหมู่ความฝัน"""
    name = models.CharField("ชื่อหมวดหมู่", max_length=100)
    description = models.TextField("คำอธิบาย", blank=True)
    
    class Meta:
        verbose_name = "หมวดหมู่ความฝัน"
        verbose_name_plural = "หมวดหมู่ความฝัน"
    
    def __str__(self):
        return self.name

class DreamKeyword(models.Model):
    """คำสำคัญในความฝันและเลขที่เกี่ยวข้อง"""
    keyword = models.CharField("คำสำคัญ", max_length=100, db_index=True)
    category = models.ForeignKey(
        DreamCategory,
        on_delete=models.CASCADE,
        related_name='keywords',
        verbose_name="หมวดหมู่"
    )
    numbers = models.CharField(
        "เลขที่เกี่ยวข้อง", 
        max_length=100,
        help_text="ใส่เลขคั่นด้วยเครื่องหมายจุลภาค เช่น 12,34,56"
    )
    
    class Meta:
        verbose_name = "คำสำคัญความฝัน"
        verbose_name_plural = "คำสำคัญความฝัน"
        ordering = ['keyword']
    
    def __str__(self):
        return f"{self.keyword} - {self.numbers}"
    
    def get_numbers_list(self):
        """แปลงเลขเป็น list"""
        return [num.strip() for num in self.numbers.split(',') if num.strip()]

class DreamInterpretation(models.Model):
    """การตีความฝันของผู้ใช้"""
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ผู้ใช้"
    )
    dream_text = models.TextField("รายละเอียดความฝัน")
    interpreted_at = models.DateTimeField("วันที่ตีความ", auto_now_add=True)
    
    # ผลการตีความ
    keywords_found = models.TextField("คำสำคัญที่พบ", blank=True)
    suggested_numbers = models.CharField("เลขที่แนะนำ", max_length=200, blank=True)
    interpretation = models.TextField("คำทำนาย", blank=True)
    
    # ข้อมูลเพิ่มเติม
    dream_date = models.DateField("วันที่ฝัน", null=True, blank=True)
    ip_address = models.GenericIPAddressField("IP Address", null=True, blank=True)
    
    class Meta:
        verbose_name = "การตีความฝัน"
        verbose_name_plural = "การตีความฝัน"
        ordering = ['-interpreted_at']
    
    def __str__(self):
        return f"ความฝันเมื่อ {self.interpreted_at.strftime('%d/%m/%Y %H:%M')}"
from django.db import models
from django.utils import timezone

class LottoResult(models.Model):
    """ข้อมูลผลรางวัลหวยจาก API"""
    
    draw_date = models.DateField("วันที่ออกรางวัล", unique=True, db_index=True)
    result_data = models.JSONField("ข้อมูลผลรางวัลจาก API")
    source = models.CharField("แหล่งข้อมูล", max_length=50, default="GLO API")
    created_at = models.DateTimeField("วันที่สร้าง", auto_now_add=True)
    updated_at = models.DateTimeField("วันที่อัปเดต", auto_now=True)
    
    class Meta:
        verbose_name = "ผลรางวัลหวย"
        verbose_name_plural = "ผลรางวัลหวย"
        ordering = ['-draw_date']
        indexes = [
            models.Index(fields=['draw_date']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"ผลรางวัลหวยวันที่ {self.draw_date.strftime('%d/%m/%Y')}"
    
    @property
    def formatted_date(self):
        """วันที่ในรูปแบบไทย"""
        return self.draw_date.strftime('%d/%m/%Y')
    
    @property
    def is_today(self):
        """ตรวจสอบว่าเป็นวันนี้หรือไม่"""
        return self.draw_date == timezone.now().date()
    
    @property
    def is_recent(self):
        """ตรวจสอบว่าเป็นข้อมูลล่าสุดหรือไม่ (7 วันล่าสุด)"""
        return self.draw_date >= (timezone.now().date() - timezone.timedelta(days=7))
    
    def get_prize_numbers(self, prize_type):
        """ดึงเลขรางวัลตามประเภท"""
        if isinstance(self.result_data, dict):
            return self.result_data.get(prize_type, [])
        return []
    
    def get_all_numbers(self):
        """ดึงเลขรางวัลทั้งหมด"""
        all_numbers = []
        if isinstance(self.result_data, dict):
            for prize_type, numbers in self.result_data.items():
                if isinstance(numbers, list):
                    all_numbers.extend(numbers)
                elif isinstance(numbers, str):
                    all_numbers.append(numbers)
        return all_numbers

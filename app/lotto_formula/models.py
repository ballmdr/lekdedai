from django.db import models
from django.urls import reverse

class LotteryFormula(models.Model):
    name = models.CharField(max_length=100, verbose_name="ชื่อสูตร")
    description = models.TextField(verbose_name="คำอธิบาย")
    method = models.TextField(verbose_name="วิธีการคำนวณ")
    accuracy_rate = models.FloatField(verbose_name="อัตราความแม่นยำ")
    total_predictions = models.IntegerField(default=0, verbose_name="จำนวนการทำนาย")
    correct_predictions = models.IntegerField(default=0, verbose_name="การทำนายที่ถูก")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "สูตรคำนวณ"
        verbose_name_plural = "สูตรคำนวณ"
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('lotto_formula:formula_detail', kwargs={'pk': self.pk})

class LotteryResult(models.Model):
    draw_date = models.DateField(verbose_name="วันที่ออกรางวัล")
    winning_numbers = models.CharField(max_length=20, verbose_name="เลขที่ออก")
    first_prize = models.CharField(max_length=6, verbose_name="รางวัลที่ 1")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "ผลการออกรางวัล"
        verbose_name_plural = "ผลการออกรางวัล"
        ordering = ['-draw_date']
    
    def __str__(self):
        return f"{self.draw_date} - {self.first_prize}"

class Prediction(models.Model):
    formula = models.ForeignKey(LotteryFormula, on_delete=models.CASCADE)
    predicted_numbers = models.CharField(max_length=20, verbose_name="เลขที่ทำนาย")
    draw_date = models.DateField(verbose_name="งวดที่ทำนาย")
    is_correct = models.BooleanField(default=False, verbose_name="ถูกต้อง")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "การทำนาย"
        verbose_name_plural = "การทำนาย"

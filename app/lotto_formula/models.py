from django.db import models
from django.urls import reverse

class LotteryFormula(models.Model):
    """สูตรคำนวณหวย — contract สำหรับ production (Task 14).

    code/version คือตัวตนของสูตร (dispatch โค้ดคำนวณด้วย code ไม่ใช่ชื่อแสดงผล),
    input_spec/output_spec อธิบาย input/output ที่รองรับ,
    is_approved คือรายชื่อสูตรที่อนุมัติให้แสดงในเครื่องคำนวณ.
    accuracy_rate/total_predictions/correct_predictions เป็นผลวัดจริงเท่านั้น
    (0/0 = ยังไม่เคยวัด ห้ามแปลว่าเป็น 0%).
    """
    code = models.SlugField("รหัสสูตร", max_length=50, unique=True, default="")
    version = models.CharField("เวอร์ชันสูตร", max_length=20, default="1.0")
    name = models.CharField(max_length=100, verbose_name="ชื่อสูตร")
    description = models.TextField(verbose_name="คำอธิบาย")
    method = models.TextField(verbose_name="วิธีการคำนวณ")
    input_spec = models.JSONField("สเปก input", default=dict)
    output_spec = models.JSONField("สเปก output", default=dict)
    is_approved = models.BooleanField("อนุมัติใช้งาน", default=True, db_index=True)
    accuracy_rate = models.FloatField(verbose_name="อัตราความแม่นยำ")
    verified_count = models.IntegerField(
        default=0, verbose_name="จำนวนที่ตรวจผลแล้วย้อนหลัง"
    )
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
    """การทำนายของสูตรต่องวด — บันทึกก่อนวันออกผลเท่านั้น (Task 15).

    is_correct = None แปลว่ายังไม่ถึงเวลาตรวจ (pending) ห้ามนับเป็นแพ้หรือชนะ.
    verified_count/accuracy บนสูตรนับเฉพาะแถวที่ตรวจแล้วเท่านั้น.
    """
    formula = models.ForeignKey(LotteryFormula, on_delete=models.CASCADE)
    predicted_numbers = models.CharField(max_length=20, verbose_name="เลขที่ทำนาย")
    input_numbers = models.CharField(
        max_length=20, verbose_name="เลขอ้างอิงที่ใช้คำนวณ", default="", blank=True
    )
    draw_date = models.DateField(verbose_name="งวดที่ทำนาย")
    is_correct = models.BooleanField(
        verbose_name="ถูกต้อง", null=True, blank=True, default=None
    )
    verified_at = models.DateTimeField(verbose_name="ตรวจเมื่อ", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "การทำนาย"
        verbose_name_plural = "การทำนาย"

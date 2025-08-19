# ระบบ Slug ภาษาไทยสำหรับ Django

## ภาพรวม
ระบบนี้ถูกออกแบบมาเพื่อรองรับการสร้าง slug จากข้อความภาษาไทยใน Django เหมือนกับ WordPress โดยสามารถบันทึก slug เป็นภาษาไทยได้โดยตรง

## ฟีเจอร์หลัก

### 1. ฟังก์ชัน `thai_slugify()`
- สร้าง slug จากข้อความภาษาไทย
- รองรับการบันทึกภาษาไทยแบบ URL-encoded
- มี fallback หลายระดับเพื่อให้แน่ใจว่าจะได้ slug ที่ถูกต้อง

### 2. ฟังก์ชัน `generate_unique_slug()`
- สร้าง slug ที่ไม่ซ้ำกัน
- เพิ่มตัวเลขต่อท้ายอัตโนมัติถ้า slug ซ้ำ

### 3. Custom Form Fields
- `ThaiSlugField` - field สำหรับ slug ที่รองรับภาษาไทย
- `NewsCategoryForm` - ฟอร์มสำหรับหมวดหมู่ข่าว
- `NewsArticleForm` - ฟอร์มสำหรับบทความข่าว

### 4. Admin Integration
- ปรับแต่ง Django admin ให้รองรับ slug ภาษาไทย
- สร้าง slug อัตโนมัติเมื่อบันทึก

## วิธีการใช้งาน

### ในโมเดล
```python
from lekdedai.utils import thai_slugify, generate_unique_slug

class MyModel(models.Model):
    title = models.CharField("หัวข้อ", max_length=200)
    slug = models.SlugField("Slug", unique=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(MyModel, self.title, self.slug)
        super().save(*args, **kwargs)
```

### ในฟอร์ม
```python
from .forms import NewsArticleForm

class MyView(View):
    def get(self, request):
        form = NewsArticleForm()
        return render(request, 'template.html', {'form': form})
```

### ใน Admin
```python
from .forms import NewsArticleForm

@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    form = NewsArticleForm
    
    def save_model(self, request, obj, form, change):
        if not obj.slug:
            from lekdedai.utils import generate_unique_slug
            obj.slug = generate_unique_slug(NewsArticle, obj.title, obj.slug)
        super().save_model(request, obj, form, change)
```

## ตัวอย่างผลลัพธ์

| ข้อความภาษาไทย | Slug ที่ได้ |
|----------------|-------------|
| ข่าวล่าสุด | ข่าวล่าสุด |
| รถชนกัน | รถชนกัน |
| เลขเด็ดวันนี้ | เลขเด็ดวันนี้ |
| When The Phone Rings เปิดมาตอนแรก | when-the-phone-rings-เปิดมาตอนแรก |

## การตั้งค่า

### 1. ติดตั้งไฟล์ utils.py
วางไฟล์ `lekdedai/utils.py` ในโปรเจค Django ของคุณ

### 2. Import ในโมเดล
```python
from lekdedai.utils import thai_slugify, generate_unique_slug
```

### 3. ใช้ในโมเดล
เพิ่มฟังก์ชัน `save()` ที่สร้าง slug อัตโนมัติ

### 4. ปรับแต่ง Admin (ถ้าต้องการ)
ใช้ custom forms และ `save_model()` method

## ข้อดี

1. **รองรับภาษาไทย**: บันทึก slug เป็นภาษาไทยได้โดยตรง
2. **เหมือน WordPress**: ทำงานเหมือนระบบ slug ของ WordPress
3. **อัตโนมัติ**: สร้าง slug อัตโนมัติเมื่อบันทึก
4. **ไม่ซ้ำกัน**: ตรวจสอบและป้องกัน slug ซ้ำ
5. **ยืดหยุ่น**: รองรับทั้งภาษาไทยและภาษาอังกฤษ

## หมายเหตุ

- ระบบจะใช้ `allow_unicode=True` ใน Django slugify
- มี fallback หลายระดับเพื่อให้แน่ใจว่าจะได้ slug ที่ถูกต้อง
- รองรับการใช้งานใน Django admin และ custom forms


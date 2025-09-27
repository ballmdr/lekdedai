"""
Forms for the news app
"""
from django import forms
from django.forms import ModelForm
from .models import NewsCategory, NewsArticle
from lekdedai.utils import thai_slugify

class ThaiSlugField(forms.CharField):
    """
    Custom field สำหรับ slug ที่รองรับภาษาไทย
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'ใส่ slug หรือปล่อยว่างเพื่อสร้างอัตโนมัติ'
        })
    
    def clean(self, value):
        if not value:
            return value
        
        # ใช้ฟังก์ชัน thai_slugify เพื่อสร้าง slug ที่ถูกต้อง
        cleaned_slug = thai_slugify(value)
        
        # ตรวจสอบว่า slug ผ่าน validation หรือไม่
        if not cleaned_slug:
            raise forms.ValidationError('ไม่สามารถสร้าง slug จากข้อความที่ให้ได้')
        
        return cleaned_slug

class NewsCategoryForm(ModelForm):
    """ฟอร์มสำหรับหมวดหมู่ข่าว"""
    slug = ThaiSlugField(
        label="Slug",
        required=False,
        help_text="ใส่ slug หรือปล่อยว่างเพื่อสร้างอัตโนมัติจากชื่อหมวดหมู่"
    )
    
    class Meta:
        model = NewsCategory
        fields = ['name', 'slug', 'description']
    
    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        name = self.cleaned_data.get('name')
        
        # ถ้าไม่มี slug ให้สร้างจากชื่อ
        if not slug and name:
            slug = thai_slugify(name)
        
        return slug

class NewsArticleForm(ModelForm):
    """ฟอร์มสำหรับบทความข่าว"""
    slug = ThaiSlugField(
        label="Slug",
        required=False,
        help_text="ใส่ slug หรือปล่อยว่างเพื่อสร้างอัตโนมัติจากหัวข้อข่าว"
    )
    
    class Meta:
        model = NewsArticle
        fields = [
            'title', 'slug', 'category', 'author', 'intro', 'content',
            'featured_image', 'numbers_with_reasons', 'status', 'published_date',
            'views', 'meta_description'
        ]
        widgets = {
            'numbers_with_reasons': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '[{"number": "24", "reason": "วันที่เกิดเหตุ"}, {"number": "08", "reason": "เวลาที่เกิดเหตุ"}]',
                'help_text': 'รูปแบบ JSON: [{"number": "เลข", "reason": "เหตุผล"}]',
                'style': 'font-size: 14px; font-family: monospace;',
                'rows': 5
            }),
            'intro': forms.Textarea(attrs={'rows': 3}),
            'content': forms.Textarea(attrs={'rows': 15}),
            'meta_description': forms.Textarea(attrs={'rows': 3}),
            'views': forms.NumberInput(attrs={'min': 0})
        }
    
    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        title = self.cleaned_data.get('title')
        
        # ถ้าไม่มี slug ให้สร้างจากหัวข้อ
        if not slug and title:
            slug = thai_slugify(title)

        return slug


    def clean_numbers_with_reasons(self):
        """ตรวจสอบ JSON format ของเลขพร้อมเหตุผล"""
        import json
        data = self.cleaned_data.get('numbers_with_reasons')

        if not data:
            return []

        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                raise forms.ValidationError('รูปแบบ JSON ไม่ถูกต้อง')

        if not isinstance(data, list):
            raise forms.ValidationError('ข้อมูลต้องเป็น Array')

        # ตรวจสอบแต่ละรายการ
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                raise forms.ValidationError(f'รายการที่ {i+1} ต้องเป็น Object')

            if 'number' not in item or 'reason' not in item:
                raise forms.ValidationError(f'รายการที่ {i+1} ต้องมี "number" และ "reason"')

            # ตรวจสอบเลข
            try:
                int(item['number'])
            except ValueError:
                raise forms.ValidationError(f'เลข "{item["number"]}" ไม่ใช่ตัวเลข')

            # ตรวจสอบความยาวเลข
            if len(str(item['number'])) < 1 or len(str(item['number'])) > 4:
                raise forms.ValidationError(f'เลข "{item["number"]}" ควรมี 1-4 หลัก')

        return data

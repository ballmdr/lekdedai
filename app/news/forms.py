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
            'featured_image', 'extracted_numbers', 'confidence_score',
            'status', 'published_date', 'meta_description'
        ]
    
    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        title = self.cleaned_data.get('title')
        
        # ถ้าไม่มี slug ให้สร้างจากหัวข้อ
        if not slug and title:
            slug = thai_slugify(title)
        
        return slug

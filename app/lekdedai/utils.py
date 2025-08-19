"""
Utility functions for the lekdedai project
"""
import re
import urllib.parse
from django.utils.text import slugify

def thai_slugify(text):
    """
    สร้าง slug จากข้อความภาษาไทย
    รองรับการบันทึกภาษาไทยแบบ URL-encoded เหมือน WordPress
    """
    if not text:
        return ""
    
    # วิธีที่ 1: ใช้ Django slugify กับ allow_unicode=True (รองรับภาษาไทย)
    slug = slugify(text, allow_unicode=True)
    
    # ถ้าได้ผลลัพธ์ที่ดี ให้ใช้เลย
    if slug and len(slug) > 0:
        return slug
    
    # วิธีที่ 2: สร้าง slug แบบง่ายโดยลบอักขระพิเศษ
    # แทนที่อักขระพิเศษด้วยเครื่องหมายขีด
    slug = re.sub(r'[^\w\s\u0E00-\u0E7F-]', '', text)  # รองรับภาษาไทย
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = slug.strip('-')
    
    # ถ้ายังว่างเปล่า ให้ใช้วิธีที่ 3
    if not slug:
        # วิธีที่ 3: URL encode ข้อความภาษาไทย
        # แทนที่ช่องว่างด้วยเครื่องหมายขีด
        slug = text.replace(' ', '-')
        # ลบอักขระพิเศษที่อาจทำให้ URL ไม่ถูกต้อง
        slug = re.sub(r'[^\w\u0E00-\u0E7F-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        slug = slug.strip('-')
    
    # ตรวจสอบว่า slug ผ่าน validation หรือไม่
    # ถ้าไม่ผ่าน ให้ใช้ slugify แบบเดิม
    if not re.match(r'^[a-zA-Z0-9\u0E00-\u0E7F_-]+$', slug):
        # ใช้ slugify แบบเดิมเป็น fallback
        slug = slugify(text, allow_unicode=True)
        if not slug:
            # ถ้ายังไม่ได้ ให้สร้าง slug แบบง่าย
            slug = re.sub(r'[^\w\s-]', '', text)
            slug = re.sub(r'[-\s]+', '-', slug)
            slug = slug.strip('-')
    
    return slug

def generate_unique_slug(model_class, text, existing_slug=None):
    """
    สร้าง slug ที่ไม่ซ้ำกัน
    """
    base_slug = thai_slugify(text)
    slug = base_slug
    counter = 1
    
    # ตรวจสอบว่า slug ซ้ำหรือไม่
    while model_class.objects.filter(slug=slug).exclude(slug=existing_slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    return slug

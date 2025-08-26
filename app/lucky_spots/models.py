from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


class Region(models.Model):
    REGION_CHOICES = [
        ('north', 'ภาคเหนือ'),
        ('central', 'ภาคกลาง'),
        ('northeast', 'ภาคอีสาน'),
        ('south', 'ภาคใต้'),
        ('east', 'ภาคตะวันออก'),
        ('west', 'ภาคตะวันตก'),
    ]
    
    name = models.CharField(max_length=20, choices=REGION_CHOICES, unique=True, verbose_name="ภาค")
    
    class Meta:
        verbose_name = "ภาค"
        verbose_name_plural = "ภาค"
    
    def __str__(self):
        return self.get_name_display()


class Province(models.Model):
    name = models.CharField(max_length=100, verbose_name="จังหวัด")
    region = models.ForeignKey(Region, on_delete=models.CASCADE, verbose_name="ภาค")
    
    class Meta:
        verbose_name = "จังหวัด"
        verbose_name_plural = "จังหวัด"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class LocationCategory(models.Model):
    CATEGORY_CHOICES = [
        ('temple', 'วัด'),
        ('shrine', 'ศาลเจ้า'),
        ('sacred_tree', 'ต้นไม้ศักดิ์สิทธิ์'),
        ('naga', 'พญานาค'),
        ('mysterious', 'สิ่งลี้ลับ'),
        ('cave', 'ถ้ำ'),
        ('mountain', 'ภูเขา'),
        ('river', 'แม่น้ำ/ลำธาร'),
        ('other', 'อื่นๆ'),
    ]
    
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True, verbose_name="ประเภทสถานที่")
    icon = models.CharField(max_length=100, blank=True, verbose_name="ไอคอน", help_text="CSS class หรือ URL ของไอคอน")
    
    class Meta:
        verbose_name = "ประเภทสถานที่"
        verbose_name_plural = "ประเภทสถานที่"
    
    def __str__(self):
        return self.get_name_display()


class LuckyLocation(models.Model):
    name = models.CharField(max_length=200, verbose_name="ชื่อสถานที่")
    description = models.TextField(verbose_name="รายละเอียด", help_text="ประวัติความเป็นมา ความเชื่อ เรื่องราวที่น่าสนใจ")
    
    # Location data
    latitude = models.DecimalField(max_digits=10, decimal_places=8, verbose_name="ละติจูด")
    longitude = models.DecimalField(max_digits=11, decimal_places=8, verbose_name="ลองจิจูด")
    address = models.TextField(blank=True, verbose_name="ที่อยู่")
    
    # Classification
    province = models.ForeignKey(Province, on_delete=models.CASCADE, verbose_name="จังหวัด")
    category = models.ForeignKey(LocationCategory, on_delete=models.CASCADE, verbose_name="ประเภท")
    
    # Lucky numbers and highlights
    lucky_numbers = models.TextField(blank=True, verbose_name="เลขเด็ดที่เคยให้โชค", 
                                   help_text="เลขเด็ดที่เคยออกจากสถานที่นี้ (แยกด้วยเครื่องหมายจุลภาค)")
    highlights = models.TextField(blank=True, verbose_name="ไฮไลท์สำคัญ", 
                                help_text="สรุปจุดเด่นของสถานที่")
    
    # Images
    main_image = models.ImageField(upload_to='lucky_spots/main/', blank=True, verbose_name="รูปภาพหลัก")
    
    # SEO and URLs
    slug = models.SlugField(max_length=250, unique=True, verbose_name="Slug")
    
    # Status and metadata
    is_active = models.BooleanField(default=True, verbose_name="เปิดใช้งาน")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่สร้าง")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="วันที่อัปเดต")
    views_count = models.PositiveIntegerField(default=0, verbose_name="จำนวนการเข้าชม")
    
    class Meta:
        verbose_name = "สถานที่เลขเด็ด"
        verbose_name_plural = "สถานที่เลขเด็ด"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['province']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
            models.Index(fields=['latitude', 'longitude']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.province.name})"
    
    def get_absolute_url(self):
        return reverse('lucky_spots:location_detail', kwargs={'slug': self.slug})
    
    def get_lucky_numbers_list(self):
        """Return lucky numbers as a list"""
        if self.lucky_numbers:
            return [num.strip() for num in self.lucky_numbers.split(',') if num.strip()]
        return []


class LocationImage(models.Model):
    location = models.ForeignKey(LuckyLocation, on_delete=models.CASCADE, 
                               related_name='gallery_images', verbose_name="สถานที่")
    image = models.ImageField(upload_to='lucky_spots/gallery/', verbose_name="รูปภาพ")
    caption = models.CharField(max_length=200, blank=True, verbose_name="คำอธิบายรูป")
    order = models.PositiveIntegerField(default=0, verbose_name="ลำดับ")
    
    class Meta:
        verbose_name = "รูปภาพสถานที่"
        verbose_name_plural = "รูปภาพสถานที่"
        ordering = ['order']
    
    def __str__(self):
        return f"รูปภาพของ {self.location.name}"


class LocationComment(models.Model):
    location = models.ForeignKey(LuckyLocation, on_delete=models.CASCADE, 
                               related_name='comments', verbose_name="สถานที่")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ผู้ใช้", null=True, blank=True)
    name = models.CharField(max_length=100, verbose_name="ชื่อ", 
                          help_text="สำหรับผู้ใช้ที่ไม่ได้ลงทะเบียน")
    email = models.EmailField(blank=True, verbose_name="อีเมล")
    comment = models.TextField(verbose_name="ความคิดเห็น")
    lucky_number_shared = models.CharField(max_length=100, blank=True, verbose_name="เลขเด็ดที่แบ่งปัน")
    
    is_approved = models.BooleanField(default=False, verbose_name="อนุมัติแล้ว")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่สร้าง")
    
    class Meta:
        verbose_name = "ความคิดเห็น"
        verbose_name_plural = "ความคิดเห็น"
        ordering = ['-created_at']
    
    def __str__(self):
        author = self.user.username if self.user else self.name
        return f"ความคิดเห็นของ {author} ใน {self.location.name}"
    
    def get_author_name(self):
        return self.user.get_full_name() or self.user.username if self.user else self.name


class LocationNewsTag(models.Model):
    """Tag สำหรับเชื่อมโยงข่าวกับสถานที่"""
    location = models.ForeignKey(LuckyLocation, on_delete=models.CASCADE, 
                               related_name='news_tags', verbose_name="สถานที่")
    news_article = models.ForeignKey('news.NewsArticle', on_delete=models.CASCADE, 
                                   verbose_name="ข่าว")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "แท็กข่าวสถานที่"
        verbose_name_plural = "แท็กข่าวสถานที่"
        unique_together = ['location', 'news_article']
    
    def __str__(self):
        return f"{self.location.name} <-> {self.news_article.title}"

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import RegexValidator
import re
from lekdedai.utils import thai_slugify, generate_unique_slug

# สร้าง validator ที่รองรับภาษาไทย
thai_slug_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9\u0E00-\u0E7F_-]+$',
    message='Slug ต้องประกอบด้วยตัวอักษร ตัวเลข ขีดล่าง ขีดกลาง หรือตัวอักษรภาษาไทยเท่านั้น'
)

class NewsCategory(models.Model):
    """หมวดหมู่ข่าว"""
    name = models.CharField("ชื่อหมวดหมู่", max_length=100)
    slug = models.SlugField("Slug", unique=True, validators=[thai_slug_validator])
    description = models.TextField("คำอธิบาย", blank=True)
    
    class Meta:
        verbose_name = "หมวดหมู่ข่าว"
        verbose_name_plural = "หมวดหมู่ข่าว"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(NewsCategory, self.name, self.slug)
        super().save(*args, **kwargs)

class NewsArticle(models.Model):
    """บทความข่าว"""
    STATUS_CHOICES = [
        ('draft', 'แบบร่าง'),
        ('published', 'เผยแพร่'),
        ('archived', 'เก็บถาวร'),
    ]
    
    title = models.CharField("หัวข้อข่าว", max_length=200)
    slug = models.SlugField("Slug", unique=True, max_length=200, validators=[thai_slug_validator])
    category = models.ForeignKey(
        NewsCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='articles',
        verbose_name="หมวดหมู่"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ผู้เขียน"
    )
    
    # เนื้อหา
    intro = models.TextField("คำนำ", max_length=500)
    content = models.TextField("เนื้อหาข่าว")
    featured_image = models.ImageField(
        "รูปภาพหลัก",
        upload_to='news/%Y/%m/',
        blank=True,
        null=True
    )
    
    # เลขที่ได้จากข่าว พร้อมเหตุผล
    numbers_with_reasons = models.JSONField(
        "เลขพร้อมเหตุผล",
        default=list,
        blank=True,
        help_text="รูปแบบ: [{'number': '24', 'reason': 'วันที่เกิดเหตุ'}, ...]"
    )

    
    # การเผยแพร่
    status = models.CharField(
        "สถานะ",
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft'
    )
    published_date = models.DateTimeField("วันที่เผยแพร่", blank=True, null=True)
    created_at = models.DateTimeField("สร้างเมื่อ", auto_now_add=True)
    updated_at = models.DateTimeField("อัปเดตล่าสุด", auto_now=True)
    
    # SEO
    meta_description = models.CharField("Meta Description", max_length=160, blank=True)
    
    # การนับ
    views = models.IntegerField("จำนวนคนดู", default=0)
    
    
    class Meta:
        verbose_name = "บทความข่าว"
        verbose_name_plural = "บทความข่าว"
        ordering = ['-published_date', '-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(NewsArticle, self.title, self.slug)
        
        # ถ้าเปลี่ยนสถานะเป็น published และยังไม่มีวันที่เผยแพร่
        if self.status == 'published' and not self.published_date:
            self.published_date = timezone.now()
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('news:article_detail', kwargs={'slug': self.slug})
    

    def get_numbers_with_reasons(self):
        """ดึงเลขพร้อมเหตุผล"""
        if self.numbers_with_reasons:
            return self.numbers_with_reasons
        return []

    def get_numbers_only(self):
        """ดึงเฉพาะเลข จาก numbers_with_reasons"""
        numbers = []
        for item in self.get_numbers_with_reasons():
            if isinstance(item, dict) and 'number' in item:
                numbers.append(item['number'])
        return numbers

    def add_number_with_reason(self, number, reason):
        """เพิ่มเลขพร้อมเหตุผล"""
        if not self.numbers_with_reasons:
            self.numbers_with_reasons = []

        # ตรวจสอบว่าเลขนี้มีอยู่แล้วหรือไม่
        for item in self.numbers_with_reasons:
            if isinstance(item, dict) and item.get('number') == str(number):
                item['reason'] = reason  # อัพเดทเหตุผล
                return

        # เพิ่มเลขใหม่
        self.numbers_with_reasons.append({
            'number': str(number),
            'reason': reason
        })
    
    def get_formatted_content(self):
        """จัดรูปแบบเนื้อหาด้วย AI (Groq/Gemini) พร้อม filter ขยะ"""
        from django.utils.safestring import mark_safe
        import json
        import re
        
        if not self.content:
            return ""
        
        # ถ้ามีเนื้อหาที่จัดรูปแบบแล้วใน formatted_content ให้ใช้เลย
        if hasattr(self, '_formatted_content_cache'):
            return mark_safe(self._formatted_content_cache)
        
        # Pre-filter: เอาขยะเว็บไซต์ออกก่อน
        cleaned_content = self._remove_website_junk(self.content)
        
        try:
            # ใช้ analyzer_switcher แทนการเรียก API โดยตรง
            from .analyzer_switcher import AnalyzerSwitcher
            
            switcher = AnalyzerSwitcher(preferred_analyzer='groq')  # ใช้ Groq เป็นหลัก
            
            # ใช้ format_content method ถ้ามี (สำหรับ Groq)
            analyzer = switcher.get_analyzer()
            if analyzer and hasattr(analyzer, 'format_content'):
                formatted_content = analyzer.format_content(cleaned_content)
                
                # แปลงเป็น HTML paragraphs
                paragraphs = formatted_content.split('\n')
                html_paragraphs = []
                for para in paragraphs:
                    para = para.strip()
                    if para and not self._is_junk_paragraph(para):
                        html_paragraphs.append(f'<p class="mb-4">{para}</p>')
                
                if html_paragraphs:
                    formatted_html = '\n'.join(html_paragraphs)
                    self._formatted_content_cache = formatted_html
                    return mark_safe(formatted_html)
                
        except Exception as e:
            # Fallback to basic formatting if AI fails
            pass
        
        # Fallback to basic formatting
        return self._get_basic_formatted_content(cleaned_content)
    
    def _get_basic_formatted_content(self, content):
        """จัดรูปแบบเนื้อหาแบบพื้นฐานเมื่อ AI ไม่ทำงาน"""
        from django.utils.safestring import mark_safe
        
        if not content:
            return ""
        
        # แยกย่อหน้าและจัดรูปแบบ
        paragraphs = content.split('\n')
        
        # Filter ย่อหน้าขยะออก
        filtered_paragraphs = []
        for para in paragraphs:
            para = para.strip()
            if para and not self._is_junk_paragraph(para):
                filtered_paragraphs.append(para)
        
        # ถ้าไม่มีย่อหน้าที่สะอาด ใช้ทั้งหมด
        if not filtered_paragraphs:
            filtered_paragraphs = [para.strip() for para in paragraphs if para.strip()]
        
        # สร้าง HTML
        html_paragraphs = []
        for para in filtered_paragraphs:
            html_paragraphs.append(f'<p class="mb-4">{para}</p>')
        
        formatted_html = '\n'.join(html_paragraphs)
        
        # Cache ผลลัพธ์
        self._formatted_content_cache = formatted_html
        
        return mark_safe(formatted_html)
    
    def _remove_website_junk(self, content):
        """ลบขยะเว็บไซต์และย่อหน้าดิบออกก่อนส่งให้ AI"""
        import re
        
        if not content:
            return ""
        
        # แยกเป็นย่อหน้า
        paragraphs = content.split('\n')
        cleaned_paragraphs = []
        
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if not para:
                continue
            
            # ตรวจสอบย่อหน้าแรกว่าเป็นข้อความดิบหรือไม่
            if i == 0 or (i == 1 and not cleaned_paragraphs):  # ย่อหน้าแรกที่มีเนื้อหา
                # เช็คว่าเป็นย่อหน้าดิบ (copy-paste จากต้นฉบับ) - เพิ่มเงื่อนไขให้ครอบคลุมมากขึ้น
                is_raw_paragraph = (
                    '**' not in para and  # ไม่มี markdown formatting
                    len(para) > 80 and   # ยาวเกินไป (ลดจาก 100 เป็น 80)
                    not para.startswith('วันที่') and  # ไม่ใช่ข้อความข่าวปกติ
                    not para.startswith('เมื่อ') and
                    not para.startswith('ที่ผ่านมา') and
                    not para.startswith('ผู้สื่อข่าว') and
                    not para.startswith('อุบัติเหตุ') and
                    not para.startswith('ต่อมา') and
                    not para.startswith('จากกรณี') and
                    # เพิ่มเงื่อนไข pattern ข้อความดิบที่พบใหม่
                    ('บริษัท' in para or 'จำกัด' in para or 'เมื่อเร็วๆ นี้' in para or 'นครหลวง' in para or
                     'เดินทางออกบ้าน' in para or 'อดีต' in para or 'เจ้าหน้าที่คาด' in para or
                     'รถพังยับกว่า' in para or 'บ้านเสียหาย' in para or 'ด้านเจ้าของพร้อม' in para or
                     # pattern ที่พบในข่าวราชบุรี
                     ('เจ้าหน้าที่คาดสาเหตุ' in para and 'รถพังยับ' in para and 'บ้านเสียหาย' in para))
                )
                
                if is_raw_paragraph:
                    # หาจุดเริ่มต้นข่าวจริงในย่อหน้าดิบ
                    formatted_start_markers = [
                        '**',  # Markdown headers
                        'วันที่', 'เมื่อวันที่', 
                        'พิธี', 'งาน', 'การประชุม', 'เหตุการณ์',
                        'นาย', 'ดร.', 'คุณ', 'ผู้', 'ท่าน'
                    ]
                    
                    found_clean_start = False
                    for marker in formatted_start_markers:
                        marker_pos = para.find(marker)
                        if marker_pos > 50:  # ต้องมีข้อความข้างหน้าพอสมควร (เป็นส่วนดิบ)
                            clean_part = para[marker_pos:].strip()
                            if len(clean_part) > 50:  # ส่วนที่สะอาดต้องยาวพอ
                                cleaned_paragraphs.append(clean_part)
                                found_clean_start = True
                                break
                    
                    if not found_clean_start:
                        # ถ้าหาจุดเริ่มต้นไม่ได้ ข้ามทั้งย่อหน้าดิบ
                        continue
                else:
                    # ย่อหน้าปกติ หรือมี formatting อยู่แล้ว
                    if not self._is_junk_paragraph(para):
                        cleaned_paragraphs.append(para)
            else:
                # ย่อหน้าอื่นๆ ตรวจสอบขยะเว็บไซต์ปกติ
                if not self._is_junk_paragraph(para):
                    cleaned_paragraphs.append(para)
        
        # รวมย่อหน้าที่สะอาดแล้ว
        if cleaned_paragraphs:
            return '\n'.join(cleaned_paragraphs)
        else:
            # ถ้าไม่มีย่อหน้าสะอาด ใช้เนื้อหาเดิม
            return content.strip()
    
    def _is_junk_paragraph(self, paragraph):
        """ตรวจสอบว่าย่อหน้านี้เป็นขยะเว็บไซต์หรือไม่"""
        if not paragraph:
            return True
        
        para_lower = paragraph.lower()
        
        # คำที่บ่งบอกว่าเป็นขยะเว็บไซต์
        junk_keywords = [
            'logo', 'thairath', 'ไทยรัฐ', 'สมาชิก', 'ค้นหา', 
            'light', 'dark', 'ฟังข่าว', 'แชร์ข่าว', 'โมง', 'นาที',
            '-ก ก ก', '+', 'น.', 'ก.ย.', 'โมงเช้า', 'เช้า',
            'menu', 'search', 'subscribe', 'follow', 'share',
            'facebook', 'twitter', 'line', 'youtube'
        ]
        
        # ถ้ามีคำขยะมากกว่า 2 คำ ในย่อหน้าสั้นๆ
        junk_count = sum(1 for keyword in junk_keywords if keyword in para_lower)
        if junk_count >= 2 and len(paragraph) < 200:
            return True
        
        # ย่อหน้าที่มีแต่เวลาและตัวเลข
        if re.match(r'^[0-9\s\.\:\-ก\+น\.ย์โมงนาที]+$', paragraph):
            return True
        
        # ย่อหน้าสั้นมากที่มีขยะ
        if len(paragraph) < 50 and any(keyword in para_lower for keyword in junk_keywords[:10]):
            return True
        
        return False
    
    def extract_numbers_from_content(self):
        """วิเคราะห์หาเลขจากเนื้อหาข่าว"""
        text = self.content + " " + self.title
        numbers = set()
        
        # หาเลข 2-3 หลัก
        numbers.update(re.findall(r'\b\d{2,3}\b', text))
        
        # หาคำสำคัญที่อาจบ่งบอกเลข
        keywords = ['อายุ', 'บ้านเลขที่', 'ทะเบียน', 'วันที่', 'งวดที่', 'เลขที่']
        for keyword in keywords:
            # หาตัวเลข (1-4 หลัก) ที่อยู่ตามหลังคำสำคัญในระยะ 10 ตัวอักษร
            for match in re.finditer(keyword, text, re.IGNORECASE):
                search_area = text[match.end():match.end() + 10]
                found = re.findall(r'\b\d{1,4}\b', search_area)
                numbers.update(num for num in found if len(num) >= 2)
        
        # หาทะเบียนรถ
        car_plates = re.findall(r'[0-9ก-ฮ]{2}\s*[-]?\s*\d{2,4}', text)
        for plate in car_plates:
            plate_numbers = re.findall(r'\d+', plate)
            numbers.update(p[-2:] for p in plate_numbers if len(p) >= 2) # สนใจ 2 ตัวท้าย
        
        # จำกัดและลบซ้ำ
        return list(numbers)[:20]

class LuckyNumberHint(models.Model):
    """เลขเด็ดจากแหล่งต่างๆ"""
    SOURCE_TYPES = [
        ('temple', 'วัด/ศาลเจ้า'),
        ('tree', 'ต้นไม้ศักดิ์สิทธิ์'),
        ('dream', 'ความฝัน'),
        ('natural', 'ปรากฏการณ์ธรรมชาติ'),
        ('accident', 'อุบัติเหตุ'),
        ('other', 'อื่นๆ'),
    ]
    
    source_type = models.CharField("ประเภทแหล่งที่มา", max_length=20, choices=SOURCE_TYPES)
    source_name = models.CharField("ชื่อแหล่งที่มา", max_length=200)
    location = models.CharField("สถานที่", max_length=200, blank=True)
    
    # เลขเด็ด
    lucky_numbers = models.CharField("เลขเด็ด", max_length=100)
    reason = models.TextField("เหตุผล/ที่มา", blank=True)
    
    # ความน่าเชื่อถือ
    reliability_score = models.IntegerField("ความน่าเชื่อถือ (%)", default=50)
    
    # เชื่อมกับข่าว
    related_article = models.ForeignKey(
        NewsArticle,
        on_delete=models.CASCADE,
        related_name='lucky_hints',
        verbose_name="ข่าวที่เกี่ยวข้อง",
        null=True,
        blank=True
    )
    
    # วันที่
    hint_date = models.DateField("วันที่ได้เลข", default=timezone.now)
    for_draw_date = models.DateField("สำหรับงวดวันที่", null=True, blank=True)
    
    created_at = models.DateTimeField("บันทึกเมื่อ", auto_now_add=True)
    
    class Meta:
        verbose_name = "เลขเด็ด"
        verbose_name_plural = "เลขเด็ด"
        ordering = ['-hint_date']
    
    def __str__(self):
        return f"{self.source_name} - {self.lucky_numbers}"
    
    def get_numbers_list(self):
        """แปลงเลขเป็น list"""
        return [num.strip() for num in self.lucky_numbers.split(',') if num.strip()]

class NewsComment(models.Model):
    """ความคิดเห็นในข่าว"""
    article = models.ForeignKey(
        NewsArticle,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="บทความ"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ผู้แสดงความเห็น"
    )
    name = models.CharField("ชื่อ", max_length=100, blank=True)
    email = models.EmailField("อีเมล", blank=True)
    
    content = models.TextField("ความคิดเห็น")
    
    # เลขที่ผู้อ่านแนะนำ
    suggested_numbers = models.CharField(
        "เลขที่แนะนำ",
        max_length=100,
        blank=True,
        help_text="เลขที่คิดว่าจะออก"
    )
    
    is_approved = models.BooleanField("อนุมัติแล้ว", default=False)
    created_at = models.DateTimeField("แสดงความเห็นเมื่อ", auto_now_add=True)
    
    class Meta:
        verbose_name = "ความคิดเห็น"
        verbose_name_plural = "ความคิดเห็น"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"ความเห็นโดย {self.name or self.user} - {self.article.title[:30]}"
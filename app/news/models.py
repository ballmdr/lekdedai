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
    
    # เลขที่ได้จากข่าว
    extracted_numbers = models.CharField(
        "เลขที่ได้จากข่าว",
        max_length=200,
        blank=True,
        help_text="เลขที่วิเคราะห์ได้จากข่าว คั่นด้วยเครื่องหมายจุลภาค"
    )
    confidence_score = models.IntegerField(
        "ความน่าเชื่อถือ (%)",
        default=50,
        help_text="0-100"
    )
    
    # คะแนนความเหมาะสมสำหรับหวย (ระบบใหม่)
    lottery_relevance_score = models.IntegerField(
        "คะแนนความเหมาะสมหวย",
        default=0,
        help_text="0-100 คะแนนจากระบบวิเคราะห์ใหม่"
    )
    lottery_category = models.CharField(
        "หมวดหมู่สำหรับหวย",
        max_length=20,
        choices=[
            ('accident', 'อุบัติเหตุ'),
            ('celebrity', 'คนดัง'),
            ('economic', 'เศรษฐกิจ'),
            ('general', 'ทั่วไป')
        ],
        blank=True,
        help_text="หมวดหมู่ที่วิเคราะห์โดยระบบใหม่"
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
    
    # URL แหล่งที่มา
    source_url = models.URLField("URL แหล่งที่มา", blank=True, null=True)
    
    # Insight-AI Analysis Results
    insight_summary = models.TextField("สรุปเหตุการณ์ (Insight-AI)", blank=True)
    insight_impact_score = models.FloatField("คะแนนผลกระทบ (Insight-AI)", default=0.0, help_text="0.0-1.0")
    insight_entities = models.JSONField("เลขจาก Insight-AI", default=list, blank=True)
    insight_analyzed_at = models.DateTimeField("วิเคราะห์ Insight-AI เมื่อ", blank=True, null=True)
    
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
    
    def get_extracted_numbers_list(self):
        """แปลงเลขเป็น list"""
        if self.extracted_numbers:
            return [num.strip() for num in self.extracted_numbers.split(',') if num.strip()]
        return []
    
    def get_formatted_content(self):
        """จัดรูปแบบเนื้อหาด้วย Gemini AI พร้อม filter ขยะ"""
        from django.utils.safestring import mark_safe
        import google.generativeai as genai
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
            # Setup Gemini
            api_key = "AIzaSyAjivjnnUo2AL5v4HGVkC4mTIH4kxMyOPU"
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash-8b')
            
            prompt = f"""
จัดรูปแบบเนื้อหาข่าวนี้ให้อ่านง่าย เรียบเรียงเป็นย่อหน้าที่เหมาะสม:

{cleaned_content}

กฎการจัดรูปแบบ:
1. แยกย่อหน้าตามหัวข้อย่อยหรือเหตุการณ์
2. แต่ละย่อหน้า 150-300 คำ
3. เรียงลำดับเหตุการณ์ให้เป็นเหตุเป็นผล
4. ใช้ภาษาไทยที่เป็นทางการแต่อ่านง่าย
5. ลบข้อความซ้ำซ้อนออก
6. ลบย่อหน้าแรกที่เป็นขยะเว็บไซต์ออก

ตอบเป็น JSON:
{{
  "formatted_paragraphs": [
    "ย่อหน้าที่ 1...",
    "ย่อหน้าที่ 2...",
    "ย่อหน้าที่ 3..."
  ]
}}
"""
            
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            # ทำความสะอาด JSON
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            try:
                result = json.loads(result_text)
                paragraphs = result.get('formatted_paragraphs', [])
                
                # Post-filter: เอาย่อหน้าที่มีขยะออกอีกรอบ
                filtered_paragraphs = []
                for para in paragraphs:
                    if para.strip() and not self._is_junk_paragraph(para):
                        filtered_paragraphs.append(para.strip())
                
                # สร้าง HTML
                html_paragraphs = []
                for para in filtered_paragraphs:
                    html_paragraphs.append(f'<p class="mb-4">{para}</p>')
                
                formatted_content = '\n'.join(html_paragraphs)
                
                # Cache ผลลัพธ์
                self._formatted_content_cache = formatted_content
                
                return mark_safe(formatted_content)
                
            except json.JSONDecodeError:
                # Fallback to basic formatting
                return self._get_basic_formatted_content(cleaned_content)
                
        except Exception as e:
            # Fallback to basic formatting
            return self._get_basic_formatted_content(cleaned_content)
    
    def _remove_website_junk(self, content):
        """ลบขยะเว็บไซต์ออกก่อนส่งให้ Gemini"""
        import re
        
        if not content:
            return ""
        
        # ถ้าเจอขยะในส่วนต้น ลองหาจุดเริ่มต้นเนื้อหาจริง
        if any(keyword in content[:300].lower() for keyword in ['logo', 'thairath', 'สมาชิก', 'light', 'dark', 'ฟังข่าว']):
            # หาจุดเริ่มต้นเนื้อหาจริง
            start_markers = ['อดีตนายกรัฐมนตรี', 'นายกรัฐมนตรี', 'ทักษิณ ชินวัตร', 'ทักษิณ', 'รองนายก', 'รัฐมนตรี']
            for marker in start_markers:
                if marker in content:
                    start_pos = content.find(marker)
                    if start_pos > 50:  # ต้องมีขยะอย่างน้อย 50 ตัวอักษรข้างหน้า
                        content = content[start_pos:]
                        break
        
        # ลบย่อหน้าขยะออกเพิ่มเติม
        paragraphs = content.split('\n')
        cleaned_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # ข้ามย่อหน้าที่มีขยะเว็บไซต์
            if self._is_junk_paragraph(para):
                continue
            
            cleaned_paragraphs.append(para)
        
        
        return content.strip() if len(cleaned_paragraphs) <= 1 else '\n'.join(cleaned_paragraphs)
    
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
    
    def _get_basic_formatted_content(self, content=None):
        """Fallback formatting method"""
        from django.utils.safestring import mark_safe
        
        if content is None:
            content = self.content
        
        if not content:
            return ""
        
        # ใช้เนื้อหาที่ผ่าน filter แล้ว
        if not hasattr(self, '_cleaned_content'):
            content = self._remove_website_junk(content)
        
        # แยกเนื้อหาทุก 300 ตัวอักษร
        content = content.strip()
        paragraphs = []
        
        while content:
            if len(content) <= 300:
                paragraphs.append(content)
                break
            
            # หาจุดตัดที่เหมาะสม (หลังจุด หรือช่องว่าง)
            cut_point = 300
            for i in range(280, min(320, len(content))):
                if content[i] in '.!? ' and i < len(content) - 1:
                    cut_point = i + 1
                    break
            
            paragraphs.append(content[:cut_point].strip())
            content = content[cut_point:].strip()
        
        # Filter ย่อหน้าขยะออก
        filtered_paragraphs = []
        for para in paragraphs:
            if para.strip() and not self._is_junk_paragraph(para):
                filtered_paragraphs.append(para.strip())
        
        # สร้าง HTML
        html_paragraphs = []
        for para in filtered_paragraphs:
            html_paragraphs.append(f'<p class="mb-4">{para}</p>')
        
        return mark_safe('\n'.join(html_paragraphs))
    
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
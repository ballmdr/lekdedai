from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter
def smart_paragraphs(value):
    """
    แปลงเนื้อหาข่าวให้มีการจัดย่อหน้าที่เหมาะสม
    """
    if not value:
        return ""
    
    # แยกประโยคยาวๆ เป็นย่อหน้า
    # แยกที่จุด ตามด้วยช่องว่าง และตัวอักษรตัวใหญ่ หรือเลข
    paragraphs = re.split(r'\.(\s+)(?=[A-Z\u0E01-\u0E5B0-9])', value)
    
    # รวมประโยคที่แยกแล้วกลับเป็นย่อหน้า
    result = []
    current_paragraph = ""
    
    for i, part in enumerate(paragraphs):
        if i % 2 == 0:  # ส่วนเนื้อหา
            current_paragraph += part
        else:  # ส่วน whitespace
            current_paragraph += "."
            if len(current_paragraph.strip()) > 100:  # ย่อหน้าใหม่เมื่อยาวพอ
                result.append(current_paragraph.strip())
                current_paragraph = ""
    
    # เพิ่มส่วนสุดท้าย
    if current_paragraph.strip():
        result.append(current_paragraph.strip())
    
    # ถ้าไม่สามารถแยกได้ ใช้วิธีพื้นฐาน
    if len(result) <= 1:
        # แยกด้วยการหาจุดที่มีประโยคยาว
        sentences = value.split('.')
        paragraphs = []
        current_para = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            current_para += sentence + ". "
            
            # สร้างย่อหน้าใหม่เมื่อมีความยาวเหมาะสม
            if len(current_para) > 200:
                paragraphs.append(current_para.strip())
                current_para = ""
        
        if current_para.strip():
            paragraphs.append(current_para.strip())
        
        result = paragraphs
    
    # สร้าง HTML
    html_paragraphs = []
    for para in result:
        if para.strip():
            html_paragraphs.append(f'<p class="mb-4">{para.strip()}</p>')
    
    return mark_safe('\n'.join(html_paragraphs))
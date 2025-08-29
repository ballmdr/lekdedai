"""
Django template tags และ filters สำหรับ Dream Analysis
"""
from django import template
from django.utils.safestring import mark_safe
import os
import sys

register = template.Library()

# Import MCP integrations
MCP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'mcp_dream_analysis')
if os.path.exists(MCP_DIR):
    sys.path.insert(0, MCP_DIR)
    try:
        from news_integration import get_dream_numbers_from_article, get_dream_summary_from_article
        from django_integration import analyze_dream_for_django
        MCP_AVAILABLE = True
    except ImportError:
        MCP_AVAILABLE = False
else:
    MCP_AVAILABLE = False

@register.filter
def extract_dream_numbers(article):
    """
    Template filter เพื่อดึงเลขเด็ดจากข่าว
    Usage: {{ article|extract_dream_numbers }}
    """
    if not MCP_AVAILABLE or not hasattr(article, 'title') or not hasattr(article, 'content'):
        return []
    
    try:
        numbers = get_dream_numbers_from_article(article.title, article.content)
        return numbers[:6]  # จำกัดแค่ 6 เลข
    except:
        return []

@register.filter
def dream_summary(article):
    """
    Template filter เพื่อสร้างสรุปการวิเคราะห์ความฝันจากข่าว
    Usage: {{ article|dream_summary }}
    """
    if not MCP_AVAILABLE or not hasattr(article, 'title') or not hasattr(article, 'content'):
        return ""
    
    try:
        summary = get_dream_summary_from_article(article.title, article.content)
        return mark_safe(summary) if summary else ""
    except:
        return ""

@register.simple_tag
def analyze_dream_text(dream_text):
    """
    Template tag เพื่อวิเคราะห์ความฝันโดยตรง
    Usage: {% analyze_dream_text "ฝันเห็นงู" %}
    """
    if not MCP_AVAILABLE or not dream_text:
        return {
            'success': False,
            'numbers': [],
            'interpretation': 'ระบบวิเคราะห์ความฝันไม่พร้อมใช้งาน'
        }
    
    try:
        result = analyze_dream_for_django(dream_text.strip())
        return {
            'success': True,
            'numbers': result.get('numbers', [])[:6],
            'interpretation': result.get('interpretation', ''),
            'confidence': result.get('confidence', 0),
            'method': result.get('analysis_method', 'unknown')
        }
    except Exception as e:
        return {
            'success': False,
            'numbers': [],
            'interpretation': f'เกิดข้อผิดพลาด: {str(e)}',
            'error': str(e)
        }

@register.inclusion_tag('dreams/dream_numbers_widget.html')
def dream_numbers_widget(numbers, title="เลขเด็ด"):
    """
    Inclusion tag สำหรับแสดงเลขเด็ดในรูปแบบ widget
    Usage: {% dream_numbers_widget article|extract_dream_numbers %}
    """
    return {
        'numbers': numbers[:8],  # จำกัดแค่ 8 เลข
        'title': title,
        'has_numbers': bool(numbers)
    }

@register.inclusion_tag('dreams/dream_analysis_card.html')
def dream_analysis_card(article, show_details=True):
    """
    Inclusion tag สำหรับแสดงการ์ดวิเคราะห์ความฝันจากข่าว
    Usage: {% dream_analysis_card article %}
    """
    if not MCP_AVAILABLE:
        return {
            'available': False,
            'message': 'ระบบวิเคราะห์ความฝันไม่พร้อมใช้งาน'
        }
    
    try:
        numbers = get_dream_numbers_from_article(article.title, article.content)
        summary = get_dream_summary_from_article(article.title, article.content)
        
        return {
            'available': True,
            'article': article,
            'numbers': numbers[:6],
            'summary': summary,
            'has_content': bool(numbers or summary),
            'show_details': show_details
        }
    except Exception as e:
        return {
            'available': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        }

@register.filter
def has_dream_content(article):
    """
    Template filter เพื่อตรวจสอบว่าข่าวมีเนื้อหาเกี่ยวกับความฝันหรือไม่
    Usage: {% if article|has_dream_content %}
    """
    if not MCP_AVAILABLE:
        return False
    
    try:
        numbers = get_dream_numbers_from_article(article.title, article.content)
        return len(numbers) > 0
    except:
        return False

@register.simple_tag
def mcp_status():
    """
    Template tag เพื่อตรวจสอบสถานะของ MCP Service
    Usage: {% mcp_status %}
    """
    return {
        'available': MCP_AVAILABLE,
        'status': 'ready' if MCP_AVAILABLE else 'unavailable',
        'message': 'MCP Dream Analysis Service พร้อมใช้งาน' if MCP_AVAILABLE else 'MCP Service ไม่พร้อมใช้งาน'
    }
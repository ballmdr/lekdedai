"""
Django template tags และ filters สำหรับ Specialized AI Models
- DreamSymbol_Model: ตีความสัญลักษณ์ความฝัน
- NewsEntity_Model: สกัด Entity ตัวเลขจากข่าว
"""
from django import template
from django.utils.safestring import mark_safe
import os
import sys

register = template.Library()

# Import specialized AI integrations
MCP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'mcp_dream_analysis')
if os.path.exists(MCP_DIR):
    sys.path.insert(0, MCP_DIR)
    try:
        from specialized_django_integration import (
            interpret_dream_for_django,
            extract_news_numbers_for_django,
            get_ai_services_status
        )
        AI_SERVICES_AVAILABLE = True
    except ImportError:
        AI_SERVICES_AVAILABLE = False
else:
    AI_SERVICES_AVAILABLE = False

# ========== DREAM SYMBOL FILTERS & TAGS ==========

@register.filter
def interpret_dream(dream_text):
    """
    Template filter เพื่อตีความสัญลักษณ์ความฝัน
    Usage: {{ "ฝันเห็นงู"|interpret_dream }}
    """
    if not AI_SERVICES_AVAILABLE or not dream_text:
        return {
            'success': False,
            'numbers': [],
            'interpretation': 'ระบบตีความฝันไม่พร้อมใช้งาน',
            'method': 'unavailable'
        }
    
    try:
        result = interpret_dream_for_django(str(dream_text).strip())
        return result
    except Exception as e:
        return {
            'success': False,
            'numbers': [],
            'interpretation': f'เกิดข้อผิดพลาด: {str(e)}',
            'error': str(e)
        }

@register.simple_tag
def dream_interpretation(dream_text, top_k=6):
    """
    Template tag เพื่อตีความความฝันโดยละเอียด
    Usage: {% dream_interpretation "ฝันเห็นช้าง" 8 %}
    """
    if not AI_SERVICES_AVAILABLE or not dream_text:
        return {
            'success': False,
            'predictions': [],
            'interpretation': 'ระบบไม่พร้อมใช้งาน'
        }
    
    try:
        result = interpret_dream_for_django(dream_text, top_k)
        return {
            'success': True,
            'predictions': result.get('predictions', []),
            'numbers': result.get('numbers', [])[:top_k],
            'interpretation': result.get('interpretation', ''),
            'confidence': result.get('confidence', 0),
            'method': result.get('analysis_method', 'unknown'),
            'latency_ms': result.get('latency_ms', 0)
        }
    except Exception as e:
        return {
            'success': False,
            'predictions': [],
            'interpretation': f'เกิดข้อผิดพลาด: {str(e)}',
            'error': str(e)
        }

@register.inclusion_tag('dreams/dream_prediction_widget.html')
def dream_prediction_widget(dream_text, title="🔮 เลขจากความฝัน", max_numbers=6):
    """
    Inclusion tag สำหรับแสดง widget ทำนายความฝัน
    Usage: {% dream_prediction_widget "ฝันเห็นงู" %}
    """
    if not AI_SERVICES_AVAILABLE:
        return {
            'available': False,
            'title': title,
            'message': 'ระบบตีความฝันไม่พร้อมใช้งาน'
        }
    
    try:
        result = interpret_dream_for_django(dream_text)
        predictions = result.get('predictions', [])
        
        return {
            'available': True,
            'title': title,
            'dream_text': dream_text,
            'predictions': predictions[:max_numbers],
            'numbers': result.get('numbers', [])[:max_numbers],
            'confidence': result.get('confidence', 0),
            'method': result.get('analysis_method', 'unknown'),
            'has_predictions': len(predictions) > 0
        }
    except Exception as e:
        return {
            'available': False,
            'title': title,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        }

# ========== NEWS ENTITY FILTERS & TAGS ==========

@register.filter
def extract_news_numbers(article):
    """
    Template filter เพื่อสกัดเลขจากข่าว
    Usage: {{ article|extract_news_numbers }}
    """
    if not AI_SERVICES_AVAILABLE:
        return []
    
    if not hasattr(article, 'content'):
        return []
    
    try:
        # Combine title and content
        news_content = f"{getattr(article, 'title', '')} {article.content}"
        result = extract_news_numbers_for_django(news_content)
        return result.get('numbers', [])[:8]  # จำกัด 8 เลข
    except Exception:
        return []

@register.filter 
def has_news_entities(article):
    """
    Template filter เพื่อตรวจสอบว่าข่าวมี Entity ตัวเลขหรือไม่
    Usage: {% if article|has_news_entities %}
    """
    if not AI_SERVICES_AVAILABLE:
        return False
    
    try:
        numbers = extract_news_numbers(article)
        return len(numbers) > 0
    except Exception:
        return False

@register.simple_tag
def analyze_news_entities(news_content, entity_types=None):
    """
    Template tag เพื่อวิเคราะห์ Entity จากข่าวโดยละเอียด
    Usage: {% analyze_news_entities article.content %}
    """
    if not AI_SERVICES_AVAILABLE or not news_content:
        return {
            'success': False,
            'entities': {},
            'summary': 'ระบบไม่พร้อมใช้งาน'
        }
    
    try:
        result = extract_news_numbers_for_django(news_content, entity_types)
        return {
            'success': result.get('success', False),
            'entities': result.get('entities', {}),
            'numbers': result.get('numbers', []),
            'summary': result.get('summary', ''),
            'total_found': result.get('total_found', 0),
            'method': result.get('analysis_method', 'unknown'),
            'latency_ms': result.get('latency_ms', 0)
        }
    except Exception as e:
        return {
            'success': False,
            'entities': {},
            'summary': f'เกิดข้อผิดพลาด: {str(e)}',
            'error': str(e)
        }

@register.inclusion_tag('dreams/news_entity_widget.html')
def news_entity_widget(article, title="📰 เลขจากข่าว"):
    """
    Inclusion tag สำหรับแสดงเลข Entity จากข่าว
    Usage: {% news_entity_widget article %}
    """
    if not AI_SERVICES_AVAILABLE:
        return {
            'available': False,
            'title': title,
            'message': 'ระบบสกัดเลขจากข่าวไม่พร้อมใช้งาน'
        }
    
    try:
        news_content = f"{getattr(article, 'title', '')} {getattr(article, 'content', '')}"
        result = extract_news_numbers_for_django(news_content)
        
        return {
            'available': True,
            'title': title,
            'article': article,
            'entities': result.get('entities', {}),
            'numbers': result.get('numbers', [])[:8],
            'summary': result.get('summary', ''),
            'total_found': result.get('total_found', 0),
            'has_entities': result.get('total_found', 0) > 0,
            'method': result.get('analysis_method', 'unknown')
        }
    except Exception as e:
        return {
            'available': False,
            'title': title,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        }

# ========== COMBINED & UTILITY TAGS ==========

@register.inclusion_tag('dreams/ai_numbers_combined.html')
def ai_numbers_combined(dream_text=None, news_article=None, title="🤖 เลขจาก AI"):
    """
    Inclusion tag สำหรับแสดงเลขจากทั้งความฝันและข่าว
    Usage: {% ai_numbers_combined dream_text="ฝันเห็นงู" news_article=article %}
    """
    if not AI_SERVICES_AVAILABLE:
        return {
            'available': False,
            'title': title,
            'message': 'ระบบ AI ไม่พร้อมใช้งาน'
        }
    
    try:
        all_numbers = []
        sources = []
        
        # Dream numbers
        if dream_text:
            dream_result = interpret_dream_for_django(dream_text)
            dream_numbers = dream_result.get('numbers', [])[:4]
            all_numbers.extend(dream_numbers)
            if dream_numbers:
                sources.append({'type': 'dream', 'numbers': dream_numbers, 'source_text': dream_text[:50]})
        
        # News numbers
        if news_article and hasattr(news_article, 'content'):
            news_content = f"{getattr(news_article, 'title', '')} {news_article.content}"
            news_result = extract_news_numbers_for_django(news_content)
            news_numbers = news_result.get('numbers', [])[:4]
            all_numbers.extend(news_numbers)
            if news_numbers:
                sources.append({'type': 'news', 'numbers': news_numbers, 'source_text': getattr(news_article, 'title', '')})
        
        # Remove duplicates while preserving order
        unique_numbers = list(dict.fromkeys(all_numbers))
        
        return {
            'available': True,
            'title': title,
            'numbers': unique_numbers[:10],  # Max 10 numbers
            'sources': sources,
            'total_numbers': len(unique_numbers),
            'has_numbers': len(unique_numbers) > 0
        }
    except Exception as e:
        return {
            'available': False,
            'title': title,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        }

@register.simple_tag
def ai_services_status():
    """
    Template tag เพื่อตรวจสอบสถานะของ AI Services
    Usage: {% ai_services_status %}
    """
    if not AI_SERVICES_AVAILABLE:
        return {
            'available': False,
            'dream_service': False,
            'news_service': False,
            'message': 'AI Services ไม่พร้อมใช้งาน'
        }
    
    try:
        status = get_ai_services_status()
        return {
            'available': True,
            'dream_service': status.get('dream_symbol_service', {}).get('available', False),
            'news_service': status.get('news_entity_service', {}).get('available', False),
            'both_available': status.get('both_available', False),
            'status_details': status
        }
    except Exception as e:
        return {
            'available': False,
            'dream_service': False,
            'news_service': False,
            'message': f'ตรวจสอบสถานะไม่ได้: {str(e)}'
        }

@register.filter
def format_confidence(confidence):
    """
    Format confidence score for display
    Usage: {{ confidence|format_confidence }}
    """
    try:
        conf_float = float(confidence)
        if conf_float >= 80:
            return mark_safe(f'<span class="text-green-600 font-bold">{conf_float:.1f}%</span>')
        elif conf_float >= 60:
            return mark_safe(f'<span class="text-yellow-600 font-bold">{conf_float:.1f}%</span>')
        else:
            return mark_safe(f'<span class="text-red-600 font-bold">{conf_float:.1f}%</span>')
    except (ValueError, TypeError):
        return mark_safe('<span class="text-gray-500">N/A</span>')

@register.filter
def ai_method_display(method):
    """
    Display AI method in Thai
    Usage: {{ method|ai_method_display }}
    """
    method_map = {
        'dream_symbol_model': '🔮 ตีความสัญลักษณ์',
        'news_entity_model': '📰 สกัดเลขข่าว', 
        'ml_prediction': '🤖 Machine Learning',
        'pattern_based': '🔍 Pattern Matching',
        'fallback': '⚠️ ระบบสำรอง',
        'unavailable': '❌ ไม่พร้อม'
    }
    return method_map.get(str(method), str(method))
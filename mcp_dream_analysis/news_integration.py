"""
Integration สำหรับการใช้งาน Dream Analysis ในส่วนข่าว
News Integration for Dream Analysis MCP Service
"""
import os
import sys
import re
from typing import List, Dict, Any, Optional

# Add Django path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app'))

try:
    from django_integration import dream_service
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

class NewsContentAnalyzer:
    """วิเคราะห์เนื้อหาข่าวเพื่อหาเลขเด็ด"""
    
    def __init__(self):
        self.dream_keywords = {
            # คำที่บ่งบอกถึงความฝันในข่าว
            'dream_indicators': ['ฝัน', 'ความฝัน', 'ฝันเห็น', 'ฝันว่า', 'นิมิต', 'ลางฝัน'],
            
            # คำที่เกี่ยวข้องกับการทำนาย
            'prediction_words': ['ทำนาย', 'พยากรณ์', 'บอกเลข', 'เลขเด็ด', 'เลขมงคล', 'ดวงดี'],
            
            # สถานที่ที่มักจะมีการให้เลขเด็ด
            'sacred_places': ['วัด', 'ศาล', 'เจ้าที่', 'เจ้าพ่อ', 'เจ้าแม่', 'พระ', 'รูปปั้น']
        }
    
    def extract_dream_content_from_news(self, news_content: str) -> List[str]:
        """สกัดเนื้อหาที่เกี่ยวข้องกับความฝันจากข่าว"""
        dream_segments = []
        
        # แยกข่าวเป็นประโยค
        sentences = re.split(r'[.!?]', news_content)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:  # ข้ามประโยคสั้นๆ
                continue
            
            # ตรวจสอบว่าประโยคมีคำเกี่ยวกับความฝันหรือไม่
            has_dream_keyword = any(keyword in sentence for keyword in self.dream_keywords['dream_indicators'])
            has_prediction = any(keyword in sentence for keyword in self.dream_keywords['prediction_words'])
            has_sacred = any(keyword in sentence for keyword in self.dream_keywords['sacred_places'])
            
            if has_dream_keyword or (has_prediction and has_sacred):
                dream_segments.append(sentence)
        
        return dream_segments
    
    def analyze_news_for_dreams(self, news_title: str, news_content: str) -> Dict[str, Any]:
        """วิเคราะห์ข่าวเพื่อหาเนื้อหาที่เกี่ยวข้องกับความฝัน"""
        if not MCP_AVAILABLE:
            return {
                'success': False,
                'error': 'MCP Dream Analysis service not available',
                'method': 'unavailable'
            }
        
        # รวมหัวข้อและเนื้อหา
        full_text = f"{news_title} {news_content}"
        
        # สกัดส่วนที่เกี่ยวกับความฝัน
        dream_segments = self.extract_dream_content_from_news(full_text)
        
        if not dream_segments:
            return {
                'success': True,
                'has_dream_content': False,
                'message': 'ไม่พบเนื้อหาเกี่ยวกับความฝันในข่าวนี้',
                'method': 'no_content'
            }
        
        # วิเคราะห์ความฝันที่พบ
        all_numbers = []
        all_interpretations = []
        combined_confidence = 0
        
        for segment in dream_segments:
            try:
                result = dream_service.analyze_dream_sync(segment)
                
                if result.get('numbers'):
                    all_numbers.extend(result['numbers'])
                
                if result.get('interpretation'):
                    all_interpretations.append({
                        'segment': segment[:100] + '...' if len(segment) > 100 else segment,
                        'interpretation': result['interpretation'][:200] + '...' if len(result['interpretation']) > 200 else result['interpretation'],
                        'numbers': result['numbers'][:5],
                        'confidence': result.get('confidence', 0)
                    })
                
                combined_confidence += result.get('confidence', 0)
                
            except Exception as e:
                continue
        
        # รวมและกรองเลข
        unique_numbers = list(dict.fromkeys(all_numbers))[:12]  # เอาเลขไม่ซ้ำกัน 12 ตัว
        
        return {
            'success': True,
            'has_dream_content': True,
            'dream_segments': dream_segments,
            'dream_analyses': all_interpretations,
            'suggested_numbers': unique_numbers,
            'average_confidence': combined_confidence / max(len(all_interpretations), 1),
            'segments_analyzed': len(all_interpretations),
            'method': 'mcp_analysis'
        }
    
    def get_dream_numbers_from_news(self, news_title: str, news_content: str) -> List[str]:
        """ดึงเลขเด็ดจากข่าวแบบเร็ว (สำหรับใช้ใน template)"""
        result = self.analyze_news_for_dreams(news_title, news_content)
        
        if result.get('success') and result.get('suggested_numbers'):
            return result['suggested_numbers'][:6]  # ส่งกลับแค่ 6 เลขแรก
        
        return []
    
    def generate_dream_summary_for_news(self, news_title: str, news_content: str) -> str:
        """สร้างสรุปการวิเคราะห์ความฝันจากข่าว"""
        result = self.analyze_news_for_dreams(news_title, news_content)
        
        if not result.get('success'):
            return ""
        
        if not result.get('has_dream_content'):
            return ""
        
        numbers = result.get('suggested_numbers', [])[:6]
        confidence = result.get('average_confidence', 0)
        
        if numbers:
            summary = f"📰 **เลขเด็ดจากข่าว:** {', '.join(numbers)}"
            if confidence > 0:
                summary += f" (ความมั่นใจ {confidence:.0f}%)"
            return summary
        
        return ""

# Global analyzer instance
news_analyzer = NewsContentAnalyzer()

# Utility functions สำหรับใช้ใน Django
def analyze_news_article_for_dreams(news_title: str, news_content: str) -> Dict[str, Any]:
    """Main function สำหรับเรียกใช้ใน Django views หรือ models"""
    return news_analyzer.analyze_news_for_dreams(news_title, news_content)

def get_dream_numbers_from_article(news_title: str, news_content: str) -> List[str]:
    """ได้เลขเด็ดจากข่าว สำหรับใช้ใน template"""
    return news_analyzer.get_dream_numbers_from_news(news_title, news_content)

def get_dream_summary_from_article(news_title: str, news_content: str) -> str:
    """ได้สรุปการวิเคราะห์ความฝัน สำหรับแสดงใน template"""
    return news_analyzer.generate_dream_summary_for_news(news_title, news_content)
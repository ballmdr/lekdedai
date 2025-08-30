"""
Specialized Django Integration for both AI models
Updated integration layer using separate specialized models
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from django.conf import settings
import os
import sys

# Add MCP directory to path
MCP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, MCP_DIR)

try:
    from mcp_servers.dream_symbol_mcp import dream_symbol_api
    from mcp_servers.news_entity_mcp import news_entity_api
    DREAM_MCP_AVAILABLE = True
    NEWS_MCP_AVAILABLE = True
except ImportError as e:
    print(f"Warning: MCP services not available: {e}")
    DREAM_MCP_AVAILABLE = False
    NEWS_MCP_AVAILABLE = False

class SpecializedAIService:
    """Django service wrapper for both specialized AI models"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.logger = logging.getLogger(__name__)
            self._initialized = True
    
    # ========== DREAM SYMBOL METHODS ==========
    
    def interpret_dream_sync(self, dream_text: str, top_k: int = 6) -> Dict[str, Any]:
        """
        Synchronous dream interpretation using Expert AI first, then MCP fallback
        ใช้สำหรับเรียกจาก Django views - ความฝัน
        """
        try:
            # Try Expert AI first
            try:
                from models.expert_dream_interpreter import ExpertDreamInterpreter
                expert = ExpertDreamInterpreter()
                expert_result = expert.interpret_dream(dream_text)
                
                # If Expert AI succeeded, return its result directly
                if expert_result and expert_result.get('interpretation'):
                    return {
                        'interpretation': expert_result.get('interpretation', ''),
                        'main_symbols': expert_result.get('main_symbols', []),
                        'sentiment': expert_result.get('sentiment', 'Neutral'),
                        'predicted_numbers': expert_result.get('predicted_numbers', []),
                        'keywords': expert_result.get('main_symbols', []),  # For backward compatibility
                        'numbers': [pred['number'] for pred in expert_result.get('predicted_numbers', [])],  # For backward compatibility
                        'is_expert_ai': True,
                        'method': 'Expert_AI'
                    }
            except Exception as expert_error:
                self.logger.warning(f"Expert AI failed, falling back to MCP: {str(expert_error)}")
            
            # Fallback to MCP if Expert AI fails
            if not DREAM_MCP_AVAILABLE:
                return self._get_dream_fallback_response(dream_text, "MCP Dream service not available")
            
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    dream_symbol_api.interpret_dream(dream_text, top_k)
                )
                return self._format_dream_response(result, dream_text)
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Dream interpretation error: {str(e)}")
            return self._get_dream_fallback_response(dream_text, str(e))
    
    def _format_dream_response(self, mcp_result: Dict[str, Any], dream_text: str) -> Dict[str, Any]:
        """Format dream MCP response for Django compatibility"""
        
        predictions = mcp_result.get('predictions', [])
        method = mcp_result.get('method', 'unknown')
        
        # Convert to Django format
        numbers = [pred['number'] for pred in predictions]
        keywords = self._extract_keywords_from_dream(dream_text)
        
        # Check if Expert AI was used
        expert_interpretation = mcp_result.get('expert_interpretation', '')
        main_symbols = mcp_result.get('main_symbols', [])
        sentiment = mcp_result.get('sentiment')
        predicted_numbers = mcp_result.get('predicted_numbers', [])
        
        # Expert AI results - return in new format
        if expert_interpretation and sentiment and predicted_numbers:
            return {
                'interpretation': expert_interpretation,
                'main_symbols': main_symbols,
                'sentiment': sentiment,
                'predicted_numbers': predicted_numbers,
                'keywords': main_symbols,  # For backward compatibility
                'numbers': [pred['number'] for pred in predicted_numbers],  # For backward compatibility
                'is_expert_ai': True,
                'method': 'Expert_AI'
            }
        
        # Traditional format for fallback
        if expert_interpretation:
            interpretation = f"""🔮 **อาจารย์ AI ตีความฝัน**

{expert_interpretation}

**สัญลักษณ์หลักที่พบ:** {', '.join(main_symbols) if main_symbols else 'ไม่พบสัญลักษณ์เฉพาะ'}

**เลขมงคลที่แนะนำ:**

"""
        else:
            interpretation = f"""🔮 **การตีความฝันด้วย AI เฉพาะทาง**

**เลขมงคลจากการวิเคราะห์สัญลักษณ์:**

"""
        
        # Group numbers by confidence
        high_confidence = [pred for pred in predictions if pred['score'] > 0.8]
        medium_confidence = [pred for pred in predictions if 0.5 < pred['score'] <= 0.8]
        low_confidence = [pred for pred in predictions if pred['score'] <= 0.5]
        
        if high_confidence:
            interpretation += f"**เลขแนะนำสูง** (ความมั่นใจ >80%): "
            for pred in high_confidence:
                reason = pred.get('reason', 'ไม่ระบุเหตุผล')
                interpretation += f"{pred['number']} ({reason}), "
            interpretation = interpretation.rstrip(', ') + "\n\n"
        
        if medium_confidence:
            interpretation += f"**เลขแนะนำปานกลาง** (ความมั่นใจ 50-80%): "
            for pred in medium_confidence:
                reason = pred.get('reason', 'ไม่ระบุเหตุผล')
                interpretation += f"{pred['number']} ({reason}), "
            interpretation = interpretation.rstrip(', ') + "\n\n"
        
        if low_confidence:
            interpretation += f"**เลขสำรอง**: "
            for pred in low_confidence[:3]:
                interpretation += f"{pred['number']}, "
            interpretation = interpretation.rstrip(', ') + "\n\n"
        
        interpretation += f"""**🧠 วิธีการวิเคราะห์:** {method}
**⚡ เวลาประมวลผล:** {mcp_result.get('latency_ms', 0):.1f} มิลลิวินาที

**💡 คำแนะนำ:**
• เลขที่มีความมั่นใจสูงควรให้ความสำคัญมากกว่า
• สังเกตเลขที่ปรากฏซ้ำในชีวิตประจำวัน
• ใช้เป็นแนวทางในการเสี่ยงโชค

⚠️ *การทำนายด้วย AI เป็นเพียงแนวทางเท่านั้น*"""
        
        return {
            'keywords': keywords,
            'numbers': numbers,
            'interpretation': interpretation,
            'confidence': max((pred['score'] * 100 for pred in predictions), default=50),
            'analysis_method': 'dream_symbol_model',
            'predictions': predictions,
            'latency_ms': mcp_result.get('latency_ms', 0),
            'mcp_result': mcp_result,
            'is_expert_ai': False,
            'sentiment': 'Neutral'
        }
    
    def _extract_keywords_from_dream(self, dream_text: str) -> List[str]:
        """Extract keywords from dream text for compatibility"""
        common_symbols = ['งู', 'ช้าง', 'เสือ', 'พระ', 'เงิน', 'ทอง', 'น้ำ', 'ไฟ', 'แม่', 'พ่อ']
        found_keywords = [symbol for symbol in common_symbols if symbol in dream_text]
        return found_keywords
    
    def _get_dream_fallback_response(self, dream_text: str, error_msg: str) -> Dict[str, Any]:
        """Fallback response for dream interpretation"""
        fallback_numbers = ['12', '34', '56', '78', '90', '13']
        keywords = self._extract_keywords_from_dream(dream_text)
        
        interpretation = f"""⚠️ **ระบบ AI ชั่วคราวไม่พร้อมใช้งาน**

ใช้การวิเคราะห์พื้นฐาน: {', '.join(fallback_numbers)}

*ข้อผิดพลาด: {error_msg}*"""
        
        return {
            'keywords': keywords,
            'numbers': fallback_numbers,
            'interpretation': interpretation,
            'confidence': 30.0,
            'analysis_method': 'fallback',
            'error': error_msg
        }
    
    # ========== NEWS ENTITY METHODS ==========
    
    def extract_news_entities_sync(self, news_content: str, entity_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Synchronous wrapper for news entity extraction  
        ใช้สำหรับเรียกจาก Django views - ข่าว
        """
        try:
            if not NEWS_MCP_AVAILABLE:
                return self._get_news_fallback_response(news_content, "MCP News service not available")
            
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    news_entity_api.extract_entities(news_content, entity_types)
                )
                return self._format_news_response(result, news_content)
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"News entity extraction error: {str(e)}")
            return self._get_news_fallback_response(news_content, str(e))
    
    def _format_news_response(self, mcp_result: Dict[str, Any], news_content: str) -> Dict[str, Any]:
        """Format news MCP response for Django compatibility"""
        
        entities = mcp_result.get('found_entities', {})
        total_found = mcp_result.get('total_found', 0)
        method = mcp_result.get('method', 'unknown')
        
        # Convert entities to simple number list for compatibility
        all_numbers = []
        entity_summary = []
        
        for entity_type, values in entities.items():
            if values:
                all_numbers.extend(values[:3])  # Max 3 per type
                entity_summary.append(f"{entity_type}: {', '.join(values[:3])}")
        
        # Remove duplicates
        unique_numbers = list(dict.fromkeys(all_numbers))
        
        # Generate summary
        if entity_summary:
            summary = f"📰 **เลขจากข่าว:** {', '.join(unique_numbers[:8])}\n\n"
            summary += "**รายละเอียดที่พบ:**\n"
            for item in entity_summary[:5]:
                summary += f"• {item}\n"
            summary += f"\n⚡ วิธีการ: {method} ({mcp_result.get('latency_ms', 0):.1f}ms)"
        else:
            summary = "ไม่พบตัวเลขที่สำคัญในข่าวนี้"
        
        return {
            'success': True,
            'numbers': unique_numbers[:12],
            'entities': entities,
            'entity_summary': entity_summary,
            'total_found': total_found,
            'analysis_method': 'news_entity_model',
            'summary': summary,
            'latency_ms': mcp_result.get('latency_ms', 0),
            'mcp_result': mcp_result
        }
    
    def _get_news_fallback_response(self, news_content: str, error_msg: str) -> Dict[str, Any]:
        """Fallback response for news entity extraction"""
        import re
        
        # Simple pattern matching as fallback
        numbers = re.findall(r'\b\d{2,4}\b', news_content)
        unique_numbers = list(dict.fromkeys(numbers))[:6]
        
        return {
            'success': False,
            'numbers': unique_numbers,
            'entities': {},
            'entity_summary': [],
            'total_found': len(unique_numbers),
            'analysis_method': 'fallback',
            'summary': f"ระบบใช้การค้นหาพื้นฐาน: {', '.join(unique_numbers) if unique_numbers else 'ไม่พบตัวเลข'}",
            'error': error_msg
        }
    
    # ========== TRAINING METHODS ==========
    
    def train_dream_model_sync(self, training_data: List[Dict]) -> Dict[str, Any]:
        """Train dream symbol model"""
        if not DREAM_MCP_AVAILABLE:
            return {'success': False, 'error': 'Dream MCP service not available'}
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    dream_symbol_api.train_model(training_data)
                )
                return result
            finally:
                loop.close()
        except Exception as e:
            self.logger.error(f"Dream model training error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def train_news_model_sync(self, training_data: List[Dict]) -> Dict[str, Any]:
        """Train news entity model"""
        if not NEWS_MCP_AVAILABLE:
            return {'success': False, 'error': 'News MCP service not available'}
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    news_entity_api.train_model(training_data)
                )
                return result
            finally:
                loop.close()
        except Exception as e:
            self.logger.error(f"News model training error: {str(e)}")
            return {'success': False, 'error': str(e)}


# Global service instance
specialized_ai_service = SpecializedAIService()

# Utility functions for Django views
def interpret_dream_for_django(dream_text: str, top_k: int = 6) -> Dict[str, Any]:
    """
    Main function to call from Django views for dream interpretation
    ใช้แทน analyze_dream_text() เดิมใน dreams/views.py
    """
    return specialized_ai_service.interpret_dream_sync(dream_text, top_k)

def extract_news_numbers_for_django(news_content: str, entity_types: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Main function to call from Django views for news entity extraction
    ใช้สำหรับสกัดเลขจากข่าว
    """
    try:
        # Use Insight-AI for advanced news analysis
        from models.insight_ai_news_analyzer import analyze_news_for_django
        return analyze_news_for_django(news_content)
    except Exception as e:
        # Fallback to traditional method
        return specialized_ai_service.extract_news_entities_sync(news_content, entity_types)

def train_dream_model_from_django(training_data: List[Dict] = None) -> Dict[str, Any]:
    """Train dream model from Django management command"""
    if training_data is None:
        # This would typically be handled by the management command
        return {'success': False, 'error': 'No training data provided'}
    
    return specialized_ai_service.train_dream_model_sync(training_data)

def train_news_model_from_django(training_data: List[Dict] = None) -> Dict[str, Any]:
    """Train news model from Django management command"""
    if training_data is None:
        # This would typically be handled by the management command
        return {'success': False, 'error': 'No training data provided'}
    
    return specialized_ai_service.train_news_model_sync(training_data)

# Service status check
def get_ai_services_status() -> Dict[str, Any]:
    """Get status of both AI services"""
    return {
        'dream_symbol_service': {
            'available': DREAM_MCP_AVAILABLE,
            'name': 'DreamSymbol_Model',
            'description': 'Symbolic interpretation from dreams'
        },
        'news_entity_service': {
            'available': NEWS_MCP_AVAILABLE,
            'name': 'NewsEntity_Model', 
            'description': 'Numerical entity extraction from news'
        },
        'both_available': DREAM_MCP_AVAILABLE and NEWS_MCP_AVAILABLE
    }
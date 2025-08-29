"""
Integration layer between Django and MCP Dream Analysis Service
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from django.conf import settings
import os
import sys

# Add MCP directory to path
MCP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, MCP_DIR)

from mcp_server import dream_analysis_api

class DreamAnalysisService:
    """Django service wrapper for MCP Dream Analysis"""
    
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
    
    def analyze_dream_sync(self, dream_text: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for dream analysis
        ใช้สำหรับเรียกจาก Django views
        """
        try:
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    dream_analysis_api.analyze_dream(dream_text)
                )
                return self._format_django_response(result)
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Dream analysis error: {str(e)}")
            return self._get_fallback_response(dream_text, str(e))
    
    def predict_numbers_sync(self, dream_text: str, num_predictions: int = 6) -> Dict[str, Any]:
        """
        Synchronous wrapper for ML number prediction only
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    dream_analysis_api.predict_numbers_only(dream_text, num_predictions)
                )
                return result
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"ML prediction error: {str(e)}")
            return {'error': str(e), 'success': False}
    
    def train_model_sync(self, training_data: list) -> Dict[str, Any]:
        """
        Synchronous wrapper for model training
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    dream_analysis_api.train_model_with_data(training_data)
                )
                return result
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Model training error: {str(e)}")
            return {'error': str(e), 'success': False}
    
    def _format_django_response(self, mcp_result: Dict[str, Any]) -> Dict[str, Any]:
        """แปลง MCP response ให้เข้ากับ Django format เดิม"""
        
        # Extract information from MCP result
        keywords = []
        numbers = mcp_result.get('combined_numbers', [])
        confidence = mcp_result.get('confidence', 50.0)
        analysis_method = mcp_result.get('analysis_method', 'unknown')
        
        # Generate interpretation text
        if mcp_result.get('ml_prediction'):
            ml_pred = mcp_result['ml_prediction']
            main_num = ml_pred.get('main_number', 1)
            secondary_num = ml_pred.get('secondary_number', 0)
            
            interpretation = f"""🤖 **การวิเคราะห์ด้วย AI และ Machine Learning**

**เลขเด่นที่ AI แนะนำ:** {main_num} และ {secondary_num}

**การวิเคราะห์:**
• AI วิเคราะห์ความฝันของคุณด้วยเทคนิค Machine Learning
• ระบบเรียนรู้จากข้อมูลความฝันและเลขที่ออกจริง
• ความมั่นใจในการทำนาย: {confidence:.1f}%

**🎯 เลขมงคลที่แนะนำ:**
{', '.join(numbers[:8])}

**💡 คำแนะนำจาก AI:**
• เลขเด่น {main_num} และเลขรอง {secondary_num} มีความสำคัญสูง
• ลองสังเกตเลขที่ปรากฏซ้ำในชีวิตประจำวัน
• ใช้เลขเหล่านี้เป็นแนวทางในการเสี่ยงโชค

⚠️ *การทำนายด้วย AI เป็นเพียงแนวทางเท่านั้น ขอให้ใช้วิจารณญาณในการตัดสินใจ*"""
        
        else:
            # Traditional analysis
            traditional = mcp_result.get('traditional_analysis', {})
            keywords = traditional.get('keywords', [])
            
            interpretation = f"""🔮 **การตีความฝันแบบดั้งเดิม**

**สัญลักษณ์ที่พบ:** {', '.join(keywords) if keywords else 'ไม่พบสัญลักษณ์เฉพาะ'}

**เลขมงคลที่แนะนำ:**
{', '.join(numbers[:8])}

**การวิเคราะห์:**
ระบบวิเคราะห์ความฝันของคุณตามหลักการตีความแบบดั้งเดิม
ความมั่นใจ: {confidence:.1f}%

**💡 คำแนะนำ:**
• ใช้เลขเหล่านี้เป็นแนวทางในการเสี่ยงโชค
• สังเกตสัญลักษณ์ในความฝันที่ปรากฏซ้ำ
• เชื่อมโยงกับเหตุการณ์ในชีวิตจริง

⚠️ *ความฝันเป็นเพียงแนวทางเท่านั้น ขอให้ใช้วิจารณญาณในการตัดสินใจ*"""
        
        return {
            'keywords': keywords,
            'numbers': numbers[:12],  # จำกัด 12 เลข
            'interpretation': interpretation,
            'confidence': confidence,
            'analysis_method': analysis_method,
            'mcp_result': mcp_result  # เก็บผลเต็มไว้ด้วย
        }
    
    def _get_fallback_response(self, dream_text: str, error_msg: str) -> Dict[str, Any]:
        """สร้าง fallback response เมื่อเกิดข้อผิดพลาด"""
        
        # Simple keyword matching as fallback
        fallback_numbers = []
        keywords = []
        
        dream_lower = dream_text.lower()
        
        # Basic keyword matching
        keyword_map = {
            'งู': ['56', '89', '08'],
            'ช้าง': ['91', '19', '01'], 
            'เสือ': ['34', '43', '03'],
            'เงิน': ['82', '28', '88'],
            'ทอง': ['98', '89', '99'],
            'น้ำ': ['26', '62', '06'],
            'ไฟ': ['37', '73', '07'],
            'พระ': ['89', '98', '08']
        }
        
        for keyword, numbers in keyword_map.items():
            if keyword in dream_lower:
                keywords.append(keyword)
                fallback_numbers.extend(numbers)
        
        # Default numbers if nothing found
        if not fallback_numbers:
            fallback_numbers = ['07', '23', '45', '12', '34', '56']
        
        interpretation = f"""⚠️ **ระบบ AI ชั่วคราวไม่พร้อมใช้งาน**

ใช้การวิเคราะห์แบบพื้นฐานแทน:

**สัญลักษณ์ที่พบ:** {', '.join(keywords) if keywords else 'วิเคราะห์พื้นฐาน'}

**เลขที่แนะนำ:**
{', '.join(fallback_numbers[:8])}

**หมายเหตุ:** ระบบกำลังอัพเดท กรุณาลองใหม่ในภายหลัง

*ข้อผิดพลาด: {error_msg}*"""
        
        return {
            'keywords': keywords,
            'numbers': fallback_numbers[:12],
            'interpretation': interpretation,
            'confidence': 30.0,
            'analysis_method': 'fallback',
            'error': error_msg
        }

# Global service instance
dream_service = DreamAnalysisService()

# Utility functions for Django views
def analyze_dream_for_django(dream_text: str) -> Dict[str, Any]:
    """
    Main function to call from Django views
    ใช้แทน analyze_dream_text() เดิมใน views.py
    """
    return dream_service.analyze_dream_sync(dream_text)

def train_model_from_django(training_data: list = None) -> Dict[str, Any]:
    """
    Train ML model from Django management command
    """
    if training_data is None:
        # Load data from Django models
        from data_preparation import DreamDataPreparator
        preparator = DreamDataPreparator()
        training_data = preparator.prepare_training_data()
    
    return dream_service.train_model_sync(training_data)
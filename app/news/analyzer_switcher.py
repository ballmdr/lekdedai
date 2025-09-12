# -*- coding: utf-8 -*-
"""
ตัวสลับ AI Analyzer ระหว่าง Gemini และ Groq
"""
import os
import logging
from typing import Dict, Optional, Union
from .groq_lottery_analyzer import GroqLotteryAnalyzer

# ตรวจสอบ Gemini availability
try:
    from .gemini_lottery_analyzer import GeminiLotteryAnalyzer
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Gemini analyzer not available")

class AnalyzerSwitcher:
    """ตัวจัดการ AI Analyzer หลายตัว เลือกใช้ได้ตามต้องการ"""
    
    def __init__(self, preferred_analyzer: str = 'auto'):
        """
        สร้าง AnalyzerSwitcher
        
        Args:
            preferred_analyzer: 'gemini', 'groq', หรือ 'auto' (เลือกอัตโนมัติ)
        """
        self.preferred_analyzer = preferred_analyzer.lower()
        self._gemini_analyzer = None
        self._groq_analyzer = None
        
        # ตรวจสอบ API Keys
        self.gemini_available = GEMINI_AVAILABLE and bool(os.getenv('GEMINI_API_KEY'))
        self.groq_available = bool(os.getenv('GROQ_API_KEY'))
        
        logging.info(f"Analyzer availability: Gemini={self.gemini_available}, Groq={self.groq_available}")
    
    def _get_gemini_analyzer(self) -> Optional[GeminiLotteryAnalyzer]:
        """สร้าง Gemini analyzer (lazy loading)"""
        if not self.gemini_available:
            return None
            
        if self._gemini_analyzer is None:
            try:
                self._gemini_analyzer = GeminiLotteryAnalyzer()
                logging.info("Gemini analyzer initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize Gemini analyzer: {e}")
                self.gemini_available = False
                return None
                
        return self._gemini_analyzer
    
    def _get_groq_analyzer(self) -> Optional[GroqLotteryAnalyzer]:
        """สร้าง Groq analyzer (lazy loading)"""
        if not self.groq_available:
            return None
            
        if self._groq_analyzer is None:
            try:
                self._groq_analyzer = GroqLotteryAnalyzer()
                logging.info("Groq analyzer initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize Groq analyzer: {e}")
                self.groq_available = False
                return None
                
        return self._groq_analyzer
    
    def get_analyzer(self, force_type: Optional[str] = None) -> Optional[Union[GeminiLotteryAnalyzer, GroqLotteryAnalyzer]]:
        """
        เลือก analyzer ที่เหมาะสม
        
        Args:
            force_type: บังคับใช้ analyzer ประเภทใด ('gemini' หรือ 'groq')
            
        Returns:
            Analyzer instance หรือ None ถ้าไม่มีตัวไหนใช้ได้
        """
        analyzer_type = force_type or self.preferred_analyzer
        
        # ลองตามลำดับที่กำหนด
        if analyzer_type == 'gemini' and self.gemini_available:
            return self._get_gemini_analyzer()
        elif analyzer_type == 'groq' and self.groq_available:
            return self._get_groq_analyzer()
        elif analyzer_type == 'auto':
            # ลำดับความสำคัญ: Groq > Gemini (เพราะ Groq เร็วกว่าและฟรี)
            if self.groq_available:
                return self._get_groq_analyzer()
            elif self.gemini_available:
                return self._get_gemini_analyzer()
        
        # Fallback: ลองทุกตัวที่มี
        if self.groq_available:
            return self._get_groq_analyzer()
        elif self.gemini_available:
            return self._get_gemini_analyzer()
            
        return None
    
    def analyze_news_for_lottery(self, title: str, content: str, force_analyzer: Optional[str] = None) -> Dict:
        """
        วิเคราะห์ข่าวด้วย analyzer ที่เหมาะสม
        
        Args:
            title: หัวข้อข่าว
            content: เนื้อหาข่าว  
            force_analyzer: บังคับใช้ analyzer ประเภทใด
            
        Returns:
            ผลการวิเคราะห์ในรูปแบบ dict
        """
        analyzer = self.get_analyzer(force_analyzer)
        
        if analyzer is None:
            return {
                'success': False,
                'error': 'NO_ANALYZER_AVAILABLE',
                'message': 'ไม่พบ AI analyzer ที่ใช้งานได้',
                'is_relevant': False,
                'numbers': [],
                'analyzer_type': 'none'
            }
        
        try:
            result = analyzer.analyze_news_for_lottery(title, content)
            
            # เพิ่มข้อมูลประเภท analyzer
            if isinstance(analyzer, GroqLotteryAnalyzer):
                result['analyzer_type'] = 'groq'
            else:
                result['analyzer_type'] = 'gemini'
                
            return result
            
        except Exception as e:
            # ถ้า analyzer หลักล้มเหลว ลอง fallback อื่น
            logging.error(f"Primary analyzer failed: {e}")
            
            fallback_type = 'groq' if force_analyzer == 'gemini' else 'gemini'
            fallback_analyzer = self.get_analyzer(fallback_type)
            
            if fallback_analyzer and fallback_analyzer != analyzer:
                try:
                    logging.info(f"Trying fallback analyzer: {fallback_type}")
                    result = fallback_analyzer.analyze_news_for_lottery(title, content)
                    result['analyzer_type'] = fallback_type
                    result['used_fallback'] = True
                    return result
                except Exception as fallback_error:
                    logging.error(f"Fallback analyzer also failed: {fallback_error}")
            
            return {
                'success': False,
                'error': str(e),
                'is_relevant': False,
                'numbers': [],
                'analyzer_type': result.get('analyzer_type', 'unknown')
            }
    
    def is_lottery_relevant(self, title: str, content: str, force_analyzer: Optional[str] = None) -> bool:
        """
        เช็คว่าข่าวเกี่ยวข้องกับหวยไหม
        
        Args:
            title: หัวข้อข่าว
            content: เนื้อหาข่าว
            force_analyzer: บังคับใช้ analyzer ประเภทใด
            
        Returns:
            True ถ้าเกี่ยวข้องกับหวย
        """
        analyzer = self.get_analyzer(force_analyzer)
        
        if analyzer is None:
            logging.warning("No analyzer available for relevance check")
            return False
        
        try:
            return analyzer.is_lottery_relevant(title, content)
        except Exception as e:
            logging.error(f"Relevance check failed: {e}")
            return False
    
    def get_available_analyzers(self) -> Dict[str, bool]:
        """ส่งคืนรายการ analyzer ที่ใช้งานได้"""
        return {
            'gemini': self.gemini_available,
            'groq': self.groq_available
        }

# สร้าง instance สำหรับใช้งานทั่วไป
default_switcher = AnalyzerSwitcher(preferred_analyzer='auto')
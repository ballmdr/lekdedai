#!/usr/bin/env python3
"""
Insight-AI News Analyzer
A sharp investigative journalist and data analyst for finding significant numerical data 
within Thai news articles for lottery prediction purposes.
"""

import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

class InsightAINewsAnalyzer:
    """
    Insight-AI: Sharp investigative journalist and data analyst
    Specializes in finding significant numerical data within Thai news articles
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Entity patterns and keywords
        self.entity_patterns = {
            'license_plate': {
                'keywords': ['ทะเบียน', 'ป้ายทะเบียน', 'เลขรถ'],
                'patterns': [
                    r'ทะเบียน\s*([0-9A-Za-z\u0E00-\u0E7F\s\-]+)',
                    r'ป้ายทะเบียน\s*([0-9A-Za-z\u0E00-\u0E7F\s\-]+)',
                    r'เลขรถ\s*([0-9A-Za-z\u0E00-\u0E7F\s\-]+)'
                ],
                'priority': 0.9
            },
            'age': {
                'keywords': ['อายุ', 'ปี', 'วัย'],
                'patterns': [
                    r'อายุ\s*(\d{1,3})\s*ปี',
                    r'วัย\s*(\d{1,3})\s*ปี',
                    r'(\d{1,3})\s*ปี'
                ],
                'priority': 0.8
            },
            'house_number': {
                'keywords': ['บ้านเลขที่', 'เลขที่บ้าน', 'เลขที่'],
                'patterns': [
                    r'บ้านเลขที่\s*(\d+/?[\d]*)',
                    r'เลขที่บ้าน\s*(\d+/?[\d]*)',
                    r'เลขที่\s*(\d+/?[\d]*)'
                ],
                'priority': 0.6
            },
            'quantity': {
                'keywords': ['จำนวน', 'ตัว', 'ต้น', 'ใบ', 'หัว', 'ฟอง', 'คน', 'คัน'],
                'patterns': [
                    r'จำนวน\s*(\d+)',
                    r'(\d+)\s*ตัว',
                    r'(\d+)\s*ต้น',
                    r'(\d+)\s*ใบ',
                    r'(\d+)\s*หัว',
                    r'(\d+)\s*ฟอง',
                    r'(\d+)\s*คน',
                    r'(\d+)\s*คัน'
                ],
                'priority': 0.5
            },
            'date': {
                'keywords': ['วันที่', 'ว/ด/ป'],
                'patterns': [
                    r'วันที่\s*(\d{1,2})',
                    r'(\d{1,2})\s*มกราคม',
                    r'(\d{1,2})\s*กุมภาพันธ์',
                    r'(\d{1,2})\s*มีนาคม',
                    r'(\d{1,2})\s*เมษายน',
                    r'(\d{1,2})\s*พฤษภาคม',
                    r'(\d{1,2})\s*มิถุนายน',
                    r'(\d{1,2})\s*กรกฎาคม',
                    r'(\d{1,2})\s*สิงหาคม',
                    r'(\d{1,2})\s*กันยายน',
                    r'(\d{1,2})\s*ตุลาคม',
                    r'(\d{1,2})\s*พฤศจิกายน',
                    r'(\d{1,2})\s*ธันวาคม',
                    r'(\d{1,2})\s*มิ\.ย\.',
                    r'(\d{1,2})\s*ม\.ค\.',
                    r'(\d{1,2})\s*ก\.พ\.',
                    r'(\d{1,2})\s*มี\.ค\.',
                    r'(\d{1,2})\s*เม\.ย\.',
                    r'(\d{1,2})\s*พ\.ค\.',
                    r'(\d{1,2})\s*ก\.ค\.',
                    r'(\d{1,2})\s*ส\.ค\.',
                    r'(\d{1,2})\s*ก\.ย\.',
                    r'(\d{1,2})\s*ต\.ค\.',
                    r'(\d{1,2})\s*พ\.ย\.',
                    r'(\d{1,2})\s*ธ\.ค\.'
                ],
                'priority': 0.4
            },
            'time': {
                'keywords': ['เวลา', 'น.', 'นาฬิกา'],
                'patterns': [
                    r'เวลา\s*(\d{1,2}[:.]\d{2})',
                    r'(\d{1,2}[:.]\d{2})\s*น\.',
                    r'(\d{1,2})\s*น\.',
                    r'(\d{1,2}[:.]\d{2})\s*นาฬิกา'
                ],
                'priority': 0.4
            },
            'money_amount': {
                'keywords': ['บาท', 'เงิน'],
                'patterns': [
                    r'(\d+(?:,\d{3})*)\s*บาท',
                    r'เงิน\s*(\d+(?:,\d{3})*)',
                    r'(\d+(?:,\d{3})*)\s*หมื่น',
                    r'(\d+(?:,\d{3})*)\s*แสน',
                    r'(\d+(?:,\d{3})*)\s*ล้าน'
                ],
                'priority': 0.3
            },
            'coffin_number': {
                'keywords': ['เลขฝาโลง'],
                'patterns': [
                    r'เลขฝาโลง\s*(\d+)'
                ],
                'priority': 1.0
            }
        }
        
        # High-impact indicators
        self.high_impact_indicators = [
            'เสียชีวิต', 'ตาย', 'อุบัติเหตุ', 'เกิดเหตุ', 'สลด', 'น่าสลด',
            'ชาวบ้านแห่ดู', 'ฮือฮา', 'คอหวยไม่พลาด', 'เลขเด็ด', 'สาธุ',
            'ไฟไหม้', 'ระเบิด', 'ฆ่า', 'ฆาตกรรม', 'ลักทรพย์', 'ปล้น',
            'แปลก', 'ประหลาด', 'มหัศจรรย์', 'ปาฏิหาริย์', 'ลี้ลาบ',
            'ดัง', 'เซียน', 'หลวงปู่', 'หลวงพ่อ', 'พระเครื่อง'
        ]
        
        # Virality signals
        self.virality_signals = [
            'แห่ดู', 'แห่ขอ', 'แห่เก็บ', 'แห่ซื้อ', 'แห่กราบ',
            'ฮือฮา', 'กิน่าข่าว', 'ฉาว', 'ดัง', 'เป็นข่าว',
            'คอหวยไม่พลาด', 'เลขเด็ด', 'เลขมงคล', 'เลขแห่',
            'สาธุ', 'บูชา', 'กราบไหว้', 'ขอพร'
        ]
    
    def analyze_news(self, news_content: str) -> Dict[str, Any]:
        """
        Main function to analyze news content using 3-step cognitive workflow
        
        Args:
            news_content: Thai news article text
            
        Returns:
            Dict containing story_summary, story_impact_score, and extracted_entities
        """
        try:
            # Step 1: Entity Extraction (NER)
            extracted_entities = self._extract_entities(news_content)
            
            # Step 2: Story Impact Analysis
            story_impact_score = self._analyze_story_impact(news_content)
            
            # Step 3: Scoring & Prioritization
            scored_entities = self._score_and_prioritize(extracted_entities, story_impact_score, news_content)
            
            # Generate story summary
            story_summary = self._generate_story_summary(news_content)
            
            return {
                "story_summary": story_summary,
                "story_impact_score": story_impact_score,
                "extracted_entities": scored_entities
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing news: {str(e)}")
            return {
                "story_summary": "ไม่สามารถสรุปข่าวได้",
                "story_impact_score": 0.0,
                "extracted_entities": []
            }
    
    def _extract_entities(self, news_content: str) -> List[Dict[str, Any]]:
        """Step 1: Extract all numerical entities using NER patterns"""
        entities = []
        
        for entity_type, config in self.entity_patterns.items():
            for pattern in config['patterns']:
                matches = re.finditer(pattern, news_content, re.IGNORECASE)
                for match in matches:
                    # Extract number from match
                    number_str = match.group(1).strip()
                    
                    # Clean up the number
                    clean_number = self._clean_number(number_str, entity_type)
                    
                    if clean_number:
                        entities.append({
                            'entity_type': entity_type,
                            'value': clean_number,
                            'raw_match': match.group(0),
                            'position': match.start(),
                            'priority': config['priority']
                        })
        
        # Remove duplicates
        unique_entities = []
        seen = set()
        for entity in entities:
            key = (entity['entity_type'], entity['value'])
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def _clean_number(self, number_str: str, entity_type: str = '') -> Optional[str]:
        """Clean and validate extracted numbers"""
        if not number_str:
            return None
        
        # Remove common Thai characters and spaces
        cleaned = re.sub(r'[^\d/:]', '', number_str)
        
        if not cleaned or len(cleaned) > 10:  # Skip very long numbers
            return None
        
        # Extract just digits for simple cases
        if '/' not in cleaned and ':' not in cleaned:
            digits = re.findall(r'\d+', cleaned)
            if digits:
                main_number = digits[0]
                # Skip single digit numbers in most cases unless high priority
                if len(main_number) == 1:
                    return None
                return main_number
        
        return cleaned
    
    def _analyze_story_impact(self, news_content: str) -> float:
        """Step 2: Analyze story's overall impact and assign impact score"""
        score = 0.0
        content_lower = news_content.lower()
        
        # Check for high-impact indicators
        high_impact_count = 0
        for indicator in self.high_impact_indicators:
            if indicator in content_lower:
                high_impact_count += 1
        
        # Base score from high-impact indicators
        score += min(high_impact_count * 0.2, 0.6)
        
        # Check for virality signals
        virality_count = 0
        for signal in self.virality_signals:
            if signal in content_lower:
                virality_count += 1
        
        # Add virality bonus
        score += min(virality_count * 0.15, 0.3)
        
        # Event type analysis
        if any(word in content_lower for word in ['เสียชีวิต', 'ตาย', 'อุบัติเหตุ']):
            score += 0.3
        elif any(word in content_lower for word in ['ไฟไหม้', 'ระเบิด', 'ฆ่า']):
            score += 0.25
        elif any(word in content_lower for word in ['แปลก', 'ประหลาด', 'มหัศจรรย์']):
            score += 0.2
        elif any(word in content_lower for word in ['หลวงปู่', 'หลวงพ่อ', 'พระเครื่อง']):
            score += 0.2
        else:
            score += 0.1  # Basic news value
        
        return min(score, 1.0)
    
    def _score_and_prioritize(self, entities: List[Dict[str, Any]], story_impact: float, news_content: str) -> List[Dict[str, Any]]:
        """Step 3: Assign significance scores to each extracted number"""
        scored_entities = []
        
        for entity in entities:
            # Base score from entity type priority
            base_score = entity['priority']
            
            # Story impact boost
            impact_boost = story_impact * 0.3
            
            # Narrative focus analysis
            focus_score = self._analyze_narrative_focus(entity, news_content)
            
            # Calculate final significance score
            significance_score = min(base_score + impact_boost + focus_score, 1.0)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(entity, story_impact, focus_score, news_content)
            
            scored_entities.append({
                'entity_type': entity['entity_type'],
                'value': entity['value'],
                'significance_score': round(significance_score, 2),
                'reasoning': reasoning
            })
        
        # Sort by significance score
        scored_entities.sort(key=lambda x: x['significance_score'], reverse=True)
        
        return scored_entities
    
    def _analyze_narrative_focus(self, entity: Dict[str, Any], news_content: str) -> float:
        """Analyze how central the number is to the story narrative"""
        content_lower = news_content.lower()
        entity_context = entity['raw_match'].lower()
        
        # Check if mentioned in first 100 characters (likely headline/lead)
        if entity['position'] < 100:
            return 0.2
        
        # Check if mentioned multiple times
        occurrence_count = content_lower.count(entity['value'])
        if occurrence_count > 1:
            return 0.15
        
        # Check context for importance indicators
        context_indicators = [
            'หลัก', 'สำคัญ', 'เด่น', 'โดดเด่น', 'น่าสนใจ',
            'พิเศษ', 'ประจำ', 'เฉพาะ', 'เจาะจง'
        ]
        
        for indicator in context_indicators:
            if indicator in entity_context:
                return 0.1
        
        return 0.0
    
    def _generate_reasoning(self, entity: Dict[str, Any], story_impact: float, focus_score: float, news_content: str) -> str:
        """Generate reasoning for significance score"""
        content_lower = news_content.lower()
        
        # Entity type specific reasoning
        entity_reasons = {
            'license_plate': 'เป็นเลขทะเบียนรถ',
            'age': 'เป็นอายุของบุคคลที่เกี่ยวข้อง',
            'house_number': 'เป็นเลขที่อยู่สำคัญ',
            'quantity': 'เป็นจำนวนที่เกี่ยวข้องกับเหตุการณ์',
            'date': 'เป็นวันที่ที่เกิดเหตุการณ์',
            'time': 'เป็นเวลาที่เกิดเหตุการณ์',
            'money_amount': 'เป็นจำนวนเงินที่เกี่ยวข้อง',
            'coffin_number': 'เป็นเลขฝาโลงที่มีความศักดิ์สิทธิ์สูง'
        }
        
        base_reason = entity_reasons.get(entity['entity_type'], 'เป็นตัวเลขที่พบในข่าว')
        
        # Add story impact context
        if story_impact > 0.7:
            impact_text = " ในเหตุการณ์ที่สร้างความสนใจสูง"
        elif story_impact > 0.4:
            impact_text = " ในเหตุการณ์ที่มีความสำคัญปานกลาง"
        else:
            impact_text = " ในเหตุการณ์ทั่วไป"
        
        # Add focus context
        if focus_score > 0.1:
            focus_text = " และเป็นจุดสนใจหลักของข่าว"
        else:
            focus_text = ""
        
        # Add death/accident context for higher scores
        if any(word in content_lower for word in ['เสียชีวิต', 'ตาย']) and entity['entity_type'] in ['license_plate', 'age']:
            focus_text += " ซึ่งเกี่ยวข้องกับผู้เสียชีวิต"
        elif any(word in content_lower for word in ['อุบัติเหตุ', 'เกิดเหตุ']) and entity['entity_type'] == 'license_plate':
            focus_text += " ที่เกิดอุบัติเหตุ"
        
        return base_reason + impact_text + focus_text
    
    def _generate_story_summary(self, news_content: str) -> str:
        """Generate a brief story summary"""
        # Simple extractive summary - take first meaningful sentence
        sentences = re.split(r'[.!?]', news_content)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 150:
                return sentence
        
        # Fallback: take first 100 characters
        return news_content[:100] + "..." if len(news_content) > 100 else news_content

# Django integration functions
def analyze_news_for_django(news_content: str) -> Dict[str, Any]:
    """
    Main function for Django integration
    Analyze news content and return lottery numbers with significance scores
    """
    analyzer = InsightAINewsAnalyzer()
    return analyzer.analyze_news(news_content)
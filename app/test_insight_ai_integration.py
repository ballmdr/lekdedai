#!/usr/bin/env python3
"""
Test Insight-AI Integration
"""
import sys
import os
import django
from pathlib import Path

# Add MCP path
sys.path.insert(0, "/app/mcp_dream_analysis")

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lekdedai.settings')
django.setup()

from specialized_django_integration import extract_news_numbers_for_django

def test_insight_ai():
    """Test Insight-AI with sample news"""
    
    sample_news = """
    เหตุอุบัติเหตุสลดที่ถนนรัชดาภิเษก นายสมชาย วัย 45 ปี
    ขับรถทะเบียน กข 1234 กรุงเทพฯ ชนเสาไฟฟ้า เสียชีวิตที่เกิดเหตุ
    เวลา 14:30 น. ที่บ้านเลขที่ 567 ผู้เห็นเหตุการณ์จำนวน 12 คน
    แห่ดูเหตุการณ์ ตำรวจระบุมูลค่าความเสียหาย 50,000 บาท
    ชาวบ้านแห่เก็บเลขทะเบียนไปซื้อหวย
    """
    
    print("🔍 Testing Insight-AI Integration...")
    print("=" * 60)
    print("Sample News Content:")
    print(sample_news.strip())
    print("\n" + "=" * 60)
    
    try:
        result = extract_news_numbers_for_django(sample_news)
        
        if result:
            print("✅ Insight-AI Analysis Results:")
            print("-" * 40)
            
            # Story summary
            story_summary = result.get('story_summary', '')
            print(f"📄 Story Summary: {story_summary}")
            
            # Story impact score
            story_impact = result.get('story_impact_score', 0)
            print(f"📊 Story Impact Score: {story_impact:.2f} ({story_impact*100:.1f}%)")
            
            # Extracted entities
            entities = result.get('extracted_entities', [])
            print(f"\n🔢 Extracted Numbers ({len(entities)} found):")
            print("-" * 40)
            
            for i, entity in enumerate(entities[:10], 1):
                print(f"{i:2d}. {entity['value']:>6s} ({entity['entity_type']:>15s}) - Score: {entity['significance_score']*100:5.1f}%")
                print(f"     Reason: {entity['reasoning']}")
                print()
            
            # Top numbers for quick reference
            top_numbers = [entity['value'] for entity in entities[:6]]
            print(f"🎯 Top Numbers: {', '.join(top_numbers)}")
            
        else:
            print("❌ No results returned")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_insight_ai()
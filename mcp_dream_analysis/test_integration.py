#!/usr/bin/env python
"""
Test script สำหรับทดสอบการทำงานของ MCP Dream Analysis System
"""
import os
import sys
import asyncio
import json
from datetime import datetime

# Setup paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DJANGO_DIR = os.path.join(CURRENT_DIR, '..', 'app')
sys.path.insert(0, CURRENT_DIR)
sys.path.insert(0, DJANGO_DIR)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lekdedai.settings')
try:
    import django
    django.setup()
    DJANGO_AVAILABLE = True
except Exception as e:
    print(f"⚠️  Django not available: {e}")
    DJANGO_AVAILABLE = False

def test_ml_model_basic():
    """ทดสอบ ML Model พื้นฐาน"""
    print("\n🔬 ทดสอบ ML Model พื้นฐาน...")
    
    try:
        from dream_ml_model import DreamNumberMLModel
        
        model = DreamNumberMLModel()
        
        # Test feature extraction
        features = model.extract_thai_features("ฝันเห็นงูใหญ่สีเขียว")
        print(f"✅ Feature extraction: {len(features)} features")
        print(f"   ตัวอย่าง: {dict(list(features.items())[:3])}")
        
        # Test traditional analysis (should work without training)
        traditional_result = model._traditional_analysis("ฝันเห็นงูใหญ่กัดฉัน")
        print(f"✅ Traditional analysis: {traditional_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ ML Model test failed: {e}")
        return False

async def test_mcp_server():
    """ทดสอบ MCP Server"""
    print("\n🌐 ทดสอบ MCP Server...")
    
    try:
        from mcp_server import DreamAnalysisMCPServer, MCPRequest
        
        server = DreamAnalysisMCPServer()
        await server.initialize()
        
        # Test health check
        health_request = MCPRequest(
            method='health_check',
            params={},
            id='test-health'
        )
        
        response = await server.handle_request(health_request)
        print(f"✅ Health check: {response.result['status']}")
        
        # Test dream analysis
        dream_request = MCPRequest(
            method='analyze_dream',
            params={'dream_text': 'ฝันเห็นงูใหญ่สีเขียวกัดฉัน'},
            id='test-dream'
        )
        
        response = await server.handle_request(dream_request)
        if response.result:
            print(f"✅ Dream analysis successful")
            print(f"   Method: {response.result.get('analysis_method')}")
            print(f"   Numbers: {response.result.get('combined_numbers', [])[:5]}")
            print(f"   Confidence: {response.result.get('confidence', 0):.1f}%")
        else:
            print(f"❌ Dream analysis failed: {response.error}")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP Server test failed: {e}")
        return False

def test_django_integration():
    """ทดสอบ Django Integration"""
    print("\n🔗 ทดสอบ Django Integration...")
    
    if not DJANGO_AVAILABLE:
        print("⚠️  Django not available, skipping Django tests")
        return False
    
    try:
        from django_integration import analyze_dream_for_django
        
        # Test dream analysis
        result = analyze_dream_for_django("ฝันเห็นช้างขาว")
        
        print(f"✅ Django integration successful")
        print(f"   Keywords: {result.get('keywords', [])}")
        print(f"   Numbers: {result.get('numbers', [])[:5]}")
        print(f"   Method: {result.get('analysis_method')}")
        print(f"   Confidence: {result.get('confidence', 0):.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Django integration test failed: {e}")
        return False

def test_news_integration():
    """ทดสอบ News Integration"""
    print("\n📰 ทดสอบ News Integration...")
    
    try:
        from news_integration import analyze_news_article_for_dreams
        
        # Test news with dream content
        test_title = "คนฝันเห็นงูทอง บอกเลขเด็ด"
        test_content = """
        เมื่อวันที่ผ่านมา นางสมศรี อายุ 45 ปี เล่าว่าฝันเห็นงูทองใหญ่มาหาตัว
        ในความฝัน งูทองนั้นมีความยาวหลายเมตร และมีเกล็ดเป็นประกาย
        หลังตื่นนอน นางสมศรีรู้สึกว่าเป็นลางดี จึงไปขอเลขที่วัดใกล้บ้าน
        พระอาจารย์บอกว่า งูทอง หมายถึงโชคลาภ แนะนำเลข 89, 98, 08
        """
        
        result = analyze_news_article_for_dreams(test_title, test_content)
        
        if result.get('success'):
            print(f"✅ News integration successful")
            print(f"   Has dream content: {result.get('has_dream_content')}")
            if result.get('suggested_numbers'):
                print(f"   Suggested numbers: {result['suggested_numbers'][:6]}")
                print(f"   Confidence: {result.get('average_confidence', 0):.1f}%")
        else:
            print(f"❌ News analysis failed: {result.get('error', 'Unknown error')}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ News integration test failed: {e}")
        return False

def test_template_tags():
    """ทดสอบ Template Tags"""
    print("\n🏷️  ทดสอบ Template Tags...")
    
    if not DJANGO_AVAILABLE:
        print("⚠️  Django not available, skipping template tag tests")
        return False
    
    try:
        # Mock article object
        class MockArticle:
            def __init__(self, title, content):
                self.title = title
                self.content = content
        
        from dreams.templatetags.dream_analysis import extract_dream_numbers, dream_summary, has_dream_content
        
        # Test article with dream content
        test_article = MockArticle(
            "ฝันเห็นช้างขาว", 
            "ฝันว่าช้างขาวใหญ่มาหาฉัน แล้วให้เลข 91 กับฉัน"
        )
        
        # Test filters
        numbers = extract_dream_numbers(test_article)
        summary = dream_summary(test_article)
        has_content = has_dream_content(test_article)
        
        print(f"✅ Template tags working")
        print(f"   Extracted numbers: {numbers}")
        print(f"   Has dream content: {has_content}")
        if summary:
            print(f"   Summary preview: {str(summary)[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Template tags test failed: {e}")
        return False

def test_data_preparation():
    """ทดสอบ Data Preparation"""
    print("\n📊 ทดสอบ Data Preparation...")
    
    if not DJANGO_AVAILABLE:
        print("⚠️  Django not available, skipping data preparation tests")
        return False
    
    try:
        from data_preparation import DreamDataPreparator
        
        preparator = DreamDataPreparator()
        
        # Test synthetic data generation (doesn't need DB)
        synthetic_data = preparator._generate_synthetic_data()
        print(f"✅ Synthetic data generation: {len(synthetic_data)} samples")
        
        if synthetic_data:
            sample = synthetic_data[0]
            print(f"   Sample: {sample['dream_text']}")
            print(f"   Numbers: {sample['main_number']}, {sample['secondary_number']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data preparation test failed: {e}")
        return False

async def run_all_tests():
    """รันการทดสอบทั้งหมด"""
    print("🧪 เริ่มการทดสอบ MCP Dream Analysis System")
    print("=" * 60)
    
    test_results = {}
    
    # Basic tests (don't require Django)
    test_results['ml_model'] = test_ml_model_basic()
    test_results['mcp_server'] = await test_mcp_server()
    
    # Django-dependent tests
    if DJANGO_AVAILABLE:
        test_results['django_integration'] = test_django_integration()
        test_results['news_integration'] = test_news_integration()
        test_results['template_tags'] = test_template_tags()
        test_results['data_preparation'] = test_data_preparation()
    else:
        print("\n⚠️  Django tests skipped - Django not available")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 สรุปผลการทดสอบ:")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\nผลรวม: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 การทดสอบทั้งหมดผ่าน! ระบบพร้อมใช้งาน")
    else:
        print("⚠️  มีการทดสอบที่ไม่ผ่าน กรุณาตรวจสอบ")
    
    return test_results

if __name__ == "__main__":
    # Run async tests
    test_results = asyncio.run(run_all_tests())
    
    # Exit with appropriate code
    if all(test_results.values()):
        sys.exit(0)
    else:
        sys.exit(1)
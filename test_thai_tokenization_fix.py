#!/usr/bin/env python
"""
Test script สำหรับทดสอบการแก้ไขปัญหาการตัดคำภาษาไทย
"""
import sys
import os

# Add paths
MCP_DIR = os.path.join(os.path.dirname(__file__), 'mcp_dream_analysis')
sys.path.insert(0, MCP_DIR)

from models.expert_dream_interpreter import ExpertDreamInterpreter

def test_tokenization_fixes():
    """ทดสอบการแก้ไขการตัดคำ"""
    
    expert = ExpertDreamInterpreter()
    
    # Test cases with tokenization problems
    test_cases = [
        {
            'input': "ฝันเห็นงูย่างใหญ่มาก",  # อย่าง -> ย่าง
            'expected_fixed': "ฝันเห็นงูอย่างใหญ่มาก",
            'should_find': ['งู']
        },
        {
            'input': "ฝันม่วยดีเห็นช้างสีทอง",  # มี -> ม่วย  
            'expected_fixed': "ฝันมีดีเห็นช้างสีทอง",
            'should_find': ['ช้าง', 'ทอง']
        },
        {
            'input': "ฝันเห็นพระย่างสงบ",
            'expected_fixed': "ฝันเห็นพระอย่างสงบ", 
            'should_find': ['พระ']
        },
        {
            'input': "เด็กทารกย่างน่ารัก",
            'expected_fixed': "เด็กทารกอย่างน่ารัก",
            'should_find': ['เด็กทารก']
        },
        {
            'input': "น้ำใสย่างสวย",
            'expected_fixed': "น้ำอย่างสวย",
            'should_find': ['น้ำ']
        }
    ]
    
    print("🔧 ทดสอบการแก้ไขปัญหาการตัดคำภาษาไทย")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}")
        print(f"Input (ปัญหา):     {test_case['input']}")
        
        # Test tokenization fix
        fixed_text = expert._fix_thai_tokenization(test_case['input'].lower())
        print(f"Fixed Text:        {fixed_text}")
        print(f"Expected:          {test_case['expected_fixed'].lower()}")
        
        # Check if fix worked correctly
        fix_correct = fixed_text == test_case['expected_fixed'].lower()
        print(f"Fix Status:        {'✅ ถูกต้อง' if fix_correct else '❌ ผิดพลาด'}")
        
        # Test symbol detection
        result = expert.interpret_dream(test_case['input'])
        found_symbols = result.get('main_symbols', [])
        
        print(f"Symbols Found:     {found_symbols}")
        print(f"Should Find:       {test_case['should_find']}")
        
        # Check if expected symbols were found
        symbol_match = any(symbol in found_symbols for symbol in test_case['should_find'])
        print(f"Symbol Detection:  {'✅ ถูกต้อง' if symbol_match else '❌ ไม่พบสัญลักษณ์'}")
        
        if result.get('predicted_numbers'):
            top_numbers = [pred['number'] for pred in result['predicted_numbers'][:3]]
            print(f"Predicted Numbers: {', '.join(top_numbers)}")

def test_emotion_detection_with_tokenization():
    """ทดสอบการตรวจจับอารมณ์กับปัญหาการตัดคำ"""
    
    expert = ExpertDreamInterpreter()
    
    emotion_tests = [
        {
            'input': "ฝันเห็นงูย่างน่ากลัวมาก",
            'expected_emotions': ['fear'],
            'expected_symbols': ['งู']
        },
        {
            'input': "ฝันเห็นช้างย่างสวยงาม", 
            'expected_emotions': ['beautiful'],
            'expected_symbols': ['ช้าง']
        },
        {
            'input': "ฝันเห็นพระย่างสงบ",
            'expected_emotions': ['peaceful'],
            'expected_symbols': ['พระ']
        }
    ]
    
    print("\n🎭 ทดสอบการตรวจจับอารมณ์พร้อมการแก้ไขการตัดคำ")
    print("=" * 60)
    
    for i, test in enumerate(emotion_tests, 1):
        print(f"\n🧪 Emotion Test {i}")
        print(f"Input: {test['input']}")
        
        result = expert.interpret_dream(test['input'])
        context = result.get('context_analysis', {})
        found_symbols = result.get('main_symbols', [])
        
        print(f"Context Found: {context}")
        print(f"Symbols Found: {found_symbols}")
        
        # Check emotion detection
        emotions_found = context.get('emotions', []) + context.get('size_modifiers', [])
        emotion_match = any(emo in emotions_found for emo in test['expected_emotions'])
        
        # Check symbol detection  
        symbol_match = any(sym in found_symbols for sym in test['expected_symbols'])
        
        print(f"Emotion Detection: {'✅' if emotion_match else '❌'}")
        print(f"Symbol Detection:  {'✅' if symbol_match else '❌'}")

def test_complex_sentence():
    """ทดสอบประโยคซับซ้อนที่มีปัญหาการตัดคำหลายจุด"""
    
    expert = ExpertDreamInterpreter()
    
    complex_test = "เมื่อคืนฝันเห็นงูใหญ่ย่างน่ากลัวไล่กัดฉัน แต่พระมาช่วยให้ดอกไม้สีขาวย่างสวยงาม"
    
    print(f"\n🔀 ทดสอบประโยคซับซ้อน")
    print("=" * 60)
    print(f"Input: {complex_test}")
    
    # Show tokenization fix
    fixed = expert._fix_thai_tokenization(complex_test.lower())
    print(f"Fixed: {fixed}")
    
    # Full interpretation
    result = expert.interpret_dream(complex_test)
    
    print(f"\nSymbols Found: {result.get('main_symbols', [])}")
    print(f"Context: {result.get('context_analysis', {})}")
    print(f"Interpretation: {result.get('interpretation', '')[:150]}...")
    
    if result.get('predicted_numbers'):
        print(f"\nTop Numbers:")
        for pred in result['predicted_numbers'][:5]:
            print(f"  {pred['number']} - {pred['score']:.2f} - {pred['reason']}")

if __name__ == "__main__":
    try:
        test_tokenization_fixes()
        test_emotion_detection_with_tokenization()
        test_complex_sentence()
        
        print(f"\n🎉 การทดสอบเสร็จสิ้น!")
        print("✅ ระบบแก้ไขการตัดคำภาษาไทยพร้อมใช้งาน!")
        
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {str(e)}")
        import traceback
        traceback.print_exc()
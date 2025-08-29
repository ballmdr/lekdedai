#!/usr/bin/env python
"""
Test script สำหรับทดสอบ Expert Dream AI (อาจารย์ AI)
"""
import sys
import os
import json

# Add paths
MCP_DIR = os.path.join(os.path.dirname(__file__), 'mcp_dream_analysis')
sys.path.insert(0, MCP_DIR)

from models.expert_dream_interpreter import ExpertDreamInterpreter

def test_expert_dream_interpretation():
    """ทดสอบการตีความฝันแบบผู้เชี่ยวชาญ"""
    
    expert = ExpertDreamInterpreter()
    
    # Test cases based on the examples provided
    test_cases = [
        {
            'input': "เมื่อคืนฝันเห็นงูตัวใหญ่มากค่ะ",
            'expected_symbols': ['งู'],
            'expected_numbers': ['56', '65', '59']
        },
        {
            'input': "ฝันว่าเจอเด็กทารกผิวขาวนอนอยู่ในกองเงินกองทอง", 
            'expected_symbols': ['เด็กทารก', 'ขาว', 'เงิน', 'ทอง'],
            'expected_numbers': ['18', '19', '28', '13']
        },
        {
            'input': "ฝันเห็นช้างสีทองเดินในน้ำใส",
            'expected_symbols': ['ช้าง', 'ทอง', 'น้ำ'],
            'expected_numbers': ['91', '19']
        },
        {
            'input': "ฝันว่าพระให้ดอกไม้สีขาวแก่ฉัน",
            'expected_symbols': ['พระ', 'ดอกไม้', 'ขาว'],
            'expected_numbers': ['89', '98']
        },
        {
            'input': "ฝันเห็นไฟไหม้บ้านใหญ่ ฉันกลัวมาก",
            'expected_symbols': ['ไฟ', 'บ้าน'],
            'expected_numbers': ['37', '73', '68', '86']
        }
    ]
    
    print("🔮 ทดสอบอาจารย์ AI ตีความฝัน")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}")
        print(f"Input: {test_case['input']}")
        print("-" * 40)
        
        # Run interpretation
        result = expert.interpret_dream(test_case['input'])
        
        # Display results
        print(f"✅ Success: {result.get('main_symbols', [])}")
        print(f"📖 Interpretation: {result.get('interpretation', '')[:100]}...")
        
        predicted_numbers = result.get('predicted_numbers', [])
        print(f"🔢 Predicted Numbers:")
        
        for pred in predicted_numbers[:5]:  # Show top 5
            print(f"   {pred['number']} - {pred['score']:.2f} - {pred['reason']}")
        
        # Check if expected symbols were found
        found_symbols = result.get('main_symbols', [])
        expected_symbols = test_case['expected_symbols']
        
        symbol_match = any(sym in found_symbols for sym in expected_symbols)
        print(f"🎯 Symbol Match: {'✅' if symbol_match else '❌'} (Found: {found_symbols})")
        
        # Check if expected numbers are in predictions
        predicted_nums = [pred['number'] for pred in predicted_numbers]
        expected_nums = test_case['expected_numbers']
        
        number_match = any(num in predicted_nums for num in expected_nums)
        print(f"🔢 Number Match: {'✅' if number_match else '❌'}")
        
        print()

def test_context_analysis():
    """ทดสอบการวิเคราะห์บริบท"""
    expert = ExpertDreamInterpreter()
    
    context_tests = [
        {
            'input': "ฝันเห็นงูใหญ่ไล่กัดฉัน ฉันกลัวมาก",
            'expected_emotions': ['fear', 'aggressive'],
            'expected_modifiers': ['big']
        },
        {
            'input': "ฝันเห็นช้างขาวขนาดมหึมาเดินมาให้ดอกไม้",
            'expected_emotions': ['giving'],
            'expected_modifiers': ['huge']
        }
    ]
    
    print("\n🎭 ทดสอบการวิเคราะห์บริบทและอารมณ์")
    print("=" * 60)
    
    for i, test in enumerate(context_tests, 1):
        print(f"\n🧪 Context Test {i}")
        print(f"Input: {test['input']}")
        
        result = expert.interpret_dream(test['input'])
        context = result.get('context_analysis', {})
        
        print(f"😊 Emotions Found: {context.get('emotions', [])}")
        print(f"📏 Size Modifiers: {context.get('size_modifiers', [])}")
        
        # Check matches
        emotion_match = any(emo in context.get('emotions', []) for emo in test['expected_emotions'])
        modifier_match = any(mod in context.get('size_modifiers', []) for mod in test['expected_modifiers'])
        
        print(f"🎯 Emotion Detection: {'✅' if emotion_match else '❌'}")
        print(f"📏 Modifier Detection: {'✅' if modifier_match else '❌'}")

def test_json_output():
    """ทดสอบ JSON output format"""
    expert = ExpertDreamInterpreter()
    
    print("\n📋 ทดสอบ JSON Output Format")
    print("=" * 60)
    
    test_input = "ฝันเห็นพญานาคสีทองใหญ่มาก"
    result = expert.interpret_dream(test_input)
    
    print("📤 JSON Output:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # Validate structure
    required_keys = ['interpretation', 'main_symbols', 'predicted_numbers']
    structure_valid = all(key in result for key in required_keys)
    
    print(f"\n🏗️ Structure Valid: {'✅' if structure_valid else '❌'}")
    
    # Validate predicted_numbers format
    if 'predicted_numbers' in result:
        predictions = result['predicted_numbers']
        if predictions:
            first_pred = predictions[0]
            pred_format_valid = all(key in first_pred for key in ['number', 'score', 'reason'])
            print(f"🔢 Prediction Format Valid: {'✅' if pred_format_valid else '❌'}")
        else:
            print(f"🔢 Prediction Format Valid: ❌ (No predictions)")

if __name__ == "__main__":
    try:
        # Run all tests
        test_expert_dream_interpretation()
        test_context_analysis() 
        test_json_output()
        
        print("\n🎉 การทดสอบเสร็จสิ้น!")
        print("✨ อาจารย์ AI พร้อมตีความฝันแบบมืออาชีพ!")
        
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {str(e)}")
        import traceback
        traceback.print_exc()
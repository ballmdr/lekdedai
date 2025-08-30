#!/usr/bin/env python
"""
Test script สำหรับทดสอบการทำงานของ dreams page กับ Expert AI
"""
import requests
import json
import sys

def test_dreams_api():
    """ทดสอบ dreams API"""
    
    # URL สำหรับทดสอบ (localhost Docker)
    base_url = "http://localhost:8000"
    analyze_url = f"{base_url}/dreams/analyze/"
    
    # Test cases
    test_cases = [
        {
            "name": "Positive Dream",
            "dream_text": "ฝันเห็นช้างสีขาวกำลังเล่นน้ำอย่างมีความสุข",
            "expected_sentiment": "Positive"
        },
        {
            "name": "Negative Dream", 
            "dream_text": "ฝันเห็นงูสีดำตัวใหญ่ไล่กัด น่ากลัวมากๆ",
            "expected_sentiment": "Negative"
        },
        {
            "name": "Neutral Dream",
            "dream_text": "ฝันเห็นบ้านหลังเก่า",
            "expected_sentiment": "Neutral"
        }
    ]
    
    print("🧪 ทดสอบการทำงานของ Dreams API กับ Expert AI")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['name']}")
        print(f"Input: {test_case['dream_text']}")
        print("-" * 40)
        
        try:
            # ส่งคำขอไป analyze
            response = requests.post(
                analyze_url,
                json={"dream_text": test_case['dream_text']},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    result = data.get('result', {})
                    
                    print(f"✅ Success!")
                    print(f"🔮 Sentiment: {result.get('sentiment', 'N/A')}")
                    print(f"🤖 Expert AI: {'Yes' if result.get('is_expert_ai') else 'No'}")
                    print(f"🔢 Numbers: {', '.join(result.get('numbers', [])[:5])}")
                    
                    if result.get('predicted_numbers'):
                        print(f"🧠 Top Predictions:")
                        for pred in result['predicted_numbers'][:3]:
                            print(f"   {pred['number']} - {pred['score']:.2f} - {pred['reason'][:50]}...")
                    
                    # Check sentiment
                    expected = test_case['expected_sentiment']
                    actual = result.get('sentiment')
                    if actual == expected:
                        print(f"✅ Sentiment correct: {actual}")
                    else:
                        print(f"⚠️ Sentiment mismatch. Expected: {expected}, Got: {actual}")
                        
                else:
                    print(f"❌ API Error: {data.get('error', 'Unknown error')}")
                    
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้")
            print("💡 กรุณาตรวจสอบว่า Docker container ทำงานอยู่")
            break
            
        except requests.exceptions.Timeout:
            print("❌ Timeout: การเชื่อมต่อใช้เวลานานเกินไป")
            
        except Exception as e:
            print(f"❌ Unexpected Error: {str(e)}")

def test_dreams_page():
    """ทดสอบการโหลดหน้า dreams"""
    
    base_url = "http://localhost:8000"
    dreams_url = f"{base_url}/dreams/"
    
    print(f"\n🌐 ทดสอบการโหลดหน้า Dreams")
    print("=" * 60)
    
    try:
        response = requests.get(dreams_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ หน้า Dreams โหลดได้สำเร็จ")
            
            # ตรวจสอบว่ามี elements ที่ต้องการหรือไม่
            content = response.text
            
            checks = [
                ("sentimentBadge", "Sentiment Badge element"),
                ("expertNumbers", "Expert Numbers section"),
                ("aiModelBadge", "AI Model Badge"),
                ("predicted_numbers", "Predicted numbers handling")
            ]
            
            for element_id, description in checks:
                if element_id in content:
                    print(f"✅ {description} - Found")
                else:
                    print(f"❌ {description} - Missing")
                    
        else:
            print(f"❌ หน้า Dreams โหลดไม่ได้: HTTP {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    try:
        test_dreams_page()
        test_dreams_api()
        
        print(f"\n🎉 การทดสอบเสร็จสิ้น!")
        print("📝 หากการทดสอบผ่าน หมายความว่า Expert AI ทำงานได้ถูกต้อง")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ การทดสอบถูกยกเลิก")
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาดในการทดสอบ: {str(e)}")
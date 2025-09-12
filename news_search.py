import os
import google.generativeai as genai
from datetime import datetime, timedelta
from dotenv import load_dotenv

# --- 1. การตั้งค่า API Key ---
# โหลดค่าจากไฟล์ .env
load_dotenv()

# อ่าน API Key จาก Environment Variable
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("ไม่พบ GEMINI_API_KEY ใน Environment Variables หรือไฟล์ .env")
    print("โปรดตั้งค่า API Key ก่อนรันโปรแกรม")
    exit()

genai.configure(api_key=api_key)


# --- 2. การกำหนดค่า Model และเปิดใช้งาน Google Search ---
# เราจะใช้ grounding tool เพื่อให้ Gemini ค้นหาข้อมูลจาก Google ได้
grounding_tool = genai.protos.Tool({
    "google_search": genai.protos.GoogleSearchRetrieval()
})


model = genai.GenerativeModel(
    model_name='gemini-2.0-flash-lite',
    tools=[grounding_tool],
)

# --- 3. สร้าง Prompt สำหรับสั่งงาน Gemini ---
# ดึงวันที่ปัจจุบันในรูปแบบภาษาไทย
# เนื่องจากเราอยู่ในประเทศไทย (+7) ให้ใช้เวลาปัจจุบันได้เลย
today = datetime.now()
today_date_thai = today.strftime("%d %B %Y") # เช่น 11 September 2025

# สร้าง Prompt ที่ชัดเจนและครอบคลุมทุกความต้องการ
prompt = f"""
กรุณาทำหน้าที่เป็นบรรณาธิการข่าวและนักวิเคราะห์ตัวเลข โปรดสรุปข่าวดังในประเทศไทยที่เกิดขึ้นหรือเป็นประเด็นสำคัญในวันนี้ ({today_date_thai}) โดยเน้นหัวข้อต่อไปนี้:

1.  **คดีทักษิณ ชินวัตร:** ความคืบหน้าล่าสุด, คำตัดสิน, หรือเหตุการณ์ที่เกี่ยวข้อง
2.  **ความเคลื่อนไหวทางการเมือง:** การชุมนุม, การอภิปรายในสภา, หรือนโยบายสำคัญของรัฐบาล
3.  **เหตุรุนแรงชายแดนภาคใต้:** สรุปเหตุการณ์ที่น่าสนใจ
4.  **ข่าวอุบัติเหตุใหญ่ๆ:** อุบัติเหตุที่มีผู้บาดเจ็บหรือเสียชีวิตจำนวนมาก หรืออุบัติเหตุที่แปลกและเป็นที่สนใจ

หลังจากสรุปข่าวแต่ละหัวข้อแล้ว ให้ทำส่วนที่สองคือ "แนวทางการตีเลขเด็ดจากข่าว" โดยวิเคราะห์ตัวเลขที่ปรากฏในข่าวเหล่านั้น เช่น
- เลขทะเบียนรถ
- อายุของบุคคลที่เกี่ยวข้อง
- บ้านเลขที่, หมายเลขเที่ยวบิน
- จำนวนผู้บาดเจ็บ/เสียชีวิต
- วันที่และเวลาที่เกิดเหตุ
- ตัวเลขอื่นๆ ที่น่าสนใจในข่าว

นำเสนอในรูปแบบที่อ่านง่าย ชัดเจน และเป็นกลาง
"""

print(f"🔍 กำลังค้นหาและวิเคราะห์ข่าวประจำวันที่ {today_date_thai}...")
print("-" * 30)

# --- 4. ส่ง Prompt ไปให้ Gemini ประมวลผล ---
try:
    response = model.generate_content(prompt)
    
    # --- 5. แสดงผลลัพธ์ ---
    print(response.text)

except Exception as e:
    print(f"เกิดข้อผิดพลาดในการเรียก API: {e}")

print("-" * 30)
print("✅ การวิเคราะห์เสร็จสิ้น")
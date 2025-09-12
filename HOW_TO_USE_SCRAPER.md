# 🚀 วิธีใช้งาน Thairath Local News Scraper

## 📋 คำสั่งพื้นฐาน

### 1. ดึงข่าวแบบปกติ (20 ข่าว):
```bash
docker-compose exec web python manage.py scrape_thairath_local
```

### 2. ดึงข่าวแบบกำหนดจำนวน:
```bash
# ดึง 10 ข่าว
docker-compose exec web python manage.py scrape_thairath_local --limit 10

# ดึง 5 ข่าว
docker-compose exec web python manage.py scrape_thairath_local --limit 5
```

### 3. ปรับคะแนนขั้นต่ำ:
```bash
# คะแนนขั้นต่ำ 50 (ง่ายผ่าน)
docker-compose exec web python manage.py scrape_thairath_local --min-score 50

# คะแนนขั้นต่ำ 80 (ยากผ่าน)
docker-compose exec web python manage.py scrape_thairath_local --min-score 80
```

### 4. เพิ่มเวลาหน่วง (ปลอดภัยกว่า):
```bash
# หน่วง 3 วินาทีต่อข่าว
docker-compose exec web python manage.py scrape_thairath_local --delay 3.0
```

### 5. รวมทุกออปชั่น:
```bash
# ดึง 15 ข่าว, คะแนนขั้นต่ำ 60, หน่วง 2.5 วินาที
docker-compose exec web python manage.py scrape_thairath_local --limit 15 --min-score 60 --delay 2.5
```

---

## 🎯 แนะนำสำหรับการใช้งานจริง

### สำหรับผู้เริ่มต้น:
```bash
docker-compose exec web python manage.py scrape_thairath_local --limit 5 --min-score 50
```

### สำหรับการใช้งานปกติ:
```bash
docker-compose exec web python manage.py scrape_thairath_local --limit 10 --min-score 60 --delay 2.0
```

### สำหรับการใช้งานเร็ว (ระวัง block):
```bash
docker-compose exec web python manage.py scrape_thairath_local --limit 20 --min-score 70 --delay 1.0
```

---

## 📊 พารามิเตอร์ทั้งหมด

| พารามิเตอร์ | ค่าเริ่มต้น | ความหมาย | ตัวอย่าง |
|------------|-------------|-----------|----------|
| `--limit` | 20 | จำนวนข่าวที่ดึง | `--limit 10` |
| `--min-score` | 70 | คะแนนขั้นต่ำ (0-100) | `--min-score 50` |
| `--delay` | 2.0 | หน่วงเวลา (วินาที) | `--delay 3.0` |

---

## 🔍 การอ่านผลลัพธ์

### ความหมายของแต่ละบรรทัด:
```
🔍 [2/5] แม่ทัพภาค 2 ยันยังไม่เปิดด่าน...  ← กำลังประมวลข่าวที่ 2 จาก 5
   🤖 วิเคราะห์ด้วย Groq AI...              ← ส่งให้ AI วิเคราะห์
   📊 คะแนน: 80/100                        ← คะแนนความเหมาะสมกับหวย
   🔢 เลข: 12, 10, 4, 2568, 2              ← เลขที่ AI หาได้
   ✅ บันทึกสำเร็จ: 5 เลข                   ← บันทึกลง database แล้ว
```

### สถานะต่างๆ:
- **✅ บันทึกสำเร็จ** = ข่าวผ่านเกณฑ์ บันทึกแล้ว
- **⚠️ ไม่ผ่านเกณฑ์** = คะแนนต่ำ หรือไม่มีเลข
- **⏭️ มีข่าวนี้แล้ว** = ข่าวซ้ำ ข้ามไป
- **❌ ไม่สามารถดึง** = ข้อผิดพลาด

### สรุปท้าย:
```
📰 ดึงข่าว: 10 ข่าว      ← ดึงเนื้อหาได้ 10 ข่าว
🤖 วิเคราะห์: 10 ข่าว    ← ส่งให้ AI ได้ 10 ข่าว  
💾 บันทึก: 6 ข่าว       ← บันทึกได้ 6 ข่าว (4 ข่าวไม่ผ่านเกณฑ์)
```

---

## ⚠️ ข้อควรระวัง

### 1. อย่าใช้ delay ต่ำเกินไป:
```bash
# ❌ อันตราย - อาจถูก block
--delay 0.5

# ✅ ปลอดภัย  
--delay 2.0
```

### 2. อย่าดึงข่าวมากเกินไป:
```bash
# ❌ มากเกินไป
--limit 100

# ✅ พอเหมาะ
--limit 20
```

### 3. ตั้งคะแนนให้เหมาะสม:
- **คะแนน 40-50** = ได้ข่าวเยอะ แต่อาจไม่เกี่ยวข้องกับหวย
- **คะแนน 60-70** = สมดุล (แนะนำ)
- **คะแนน 80+** = ได้น้อย แต่เกี่ยวข้องกับหวยแน่นอน

---

## 🔧 เมื่อเกิดปัญหา

### 1. ไม่พบข่าว:
```bash
# ลองเพิ่มจำนวน
docker-compose exec web python manage.py scrape_thairath_local --limit 30
```

### 2. Groq API Error:
```bash
# ลดจำนวนและเพิ่มหน่วงเวลา
docker-compose exec web python manage.py scrape_thairath_local --limit 5 --delay 5.0
```

### 3. คะแนนต่ำทุกข่าว:
```bash
# ลดคะแนนขั้นต่ำ
docker-compose exec web python manage.py scrape_thairath_local --min-score 40
```

---

## 📱 ดูผลลัพธ์

หลังจากรันสำเร็จ ดูข่าวที่บันทึกได้ที่:
- **เว็บ**: http://localhost:8000/news/
- **Admin**: http://localhost:8000/admin/news/newsarticle/

---

## 💡 เทคนิคการใช้งาน

### ดึงข่าวประจำวัน:
```bash
# รันทุกเช้า
docker-compose exec web python manage.py scrape_thairath_local --limit 15 --min-score 60
```

### ทดสอบระบบ:
```bash  
# รันแค่ 3 ข่าว เพื่อทดสอบ
docker-compose exec web python manage.py scrape_thairath_local --limit 3 --min-score 50
```

### หาเลขเด็ดด่วน:
```bash
# คะแนนต่ำ ได้เลขเยอะ
docker-compose exec web python manage.py scrape_thairath_local --limit 20 --min-score 40
```

---

**📝 บันทึก:** ไฟล์นี้อัปเดตล่าสุด - Scraper ใช้งานได้แล้ว ✅
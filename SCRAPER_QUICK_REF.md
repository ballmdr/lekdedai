# ⚡ Quick Reference - Thairath Scraper

## 🚀 คำสั่งใช้บ่อย

```bash
# ดึง 10 ข่าว คะแนนต่ำ (ได้เยอะ)
docker-compose exec web python manage.py scrape_thairath_local --limit 10 --min-score 50

# ดึง 20 ข่าว คะแนนปกติ (สมดุล) 
docker-compose exec web python manage.py scrape_thairath_local --limit 20 --min-score 60

# ดึง 5 ข่าว คะแนนสูง (คุณภาพ)
docker-compose exec web python manage.py scrape_thairath_local --limit 5 --min-score 80

# ปลอดภัย (หน่วงเวลา 3 วินาที)
docker-compose exec web python manage.py scrape_thairath_local --limit 10 --delay 3.0
```

## 🎯 พารามิเตอร์

| คำสั่ง | ค่าเริ่มต้น | ใช้เมื่อไร |
|--------|-------------|-----------|
| `--limit 10` | 20 | ดึงน้อย ทดสอบ |
| `--min-score 50` | 70 | ต้องการเลขเยอะ |
| `--delay 3.0` | 2.0 | เน็ตช้า หรือระวัง block |

## 📊 อ่านผลลัพธ์

```
📰 ดึงข่าว: 10        (จำนวนที่ scrape ได้)
🤖 วิเคราะห์: 10      (ส่ง AI ได้กี่ข่าว)  
💾 บันทึก: 6          (ผ่านเกณฑ์กี่ข่าว)
```

## ⚠️ เมื่อเกิดปัญหา

- **ไม่พบข่าว** → เพิ่ม `--limit 30`
- **API Error** → เพิ่ม `--delay 5.0`  
- **คะแนนต่ำ** → ลด `--min-score 40`

## 📱 ดูผลลัพธ์

http://localhost:8000/news/

---
**💡 Pro Tip:** รันทุกเช้า `--limit 15 --min-score 60` สำหรับเลขประจำวัน!
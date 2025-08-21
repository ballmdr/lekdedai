# 🎯 Lottery Checker - ระบบตรวจสอบหวยใหม่

ระบบตรวจสอบหวยที่ดึงข้อมูลจาก GLO API และบันทึกลงฐานข้อมูล Django

## ✨ คุณสมบัติใหม่

- 🔄 **ระบบอัจฉริยะ**: ตรวจสอบวันที่ก่อน ถ้ายังไม่มีข้อมูลในฐานข้อมูลก็ดึงจาก API แล้วบันทึก
- 💾 **เก็บข้อมูลอัตโนมัติ**: บันทึกข้อมูลหวยลงฐานข้อมูลโดยอัตโนมัติ
- 🚀 **ประสิทธิภาพสูง**: ใช้ข้อมูลจากฐานข้อมูลถ้ามีแล้ว ไม่ต้องเรียก API ซ้ำ
- 🎲 **ตรวจสอบเลขหวย**: ระบบตรวจสอบเลขหวยว่าถูกรางวัลหรือไม่
- 🗑️ **ล้างข้อมูล**: สามารถล้างข้อมูลทั้งหมดและดึงข้อมูลใหม่ได้
- 📊 **สถิติข้อมูล**: แสดงสถิติข้อมูลหวยในระบบ

## 🚀 การติดตั้ง

### 1. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

### 2. รัน Migrations

```bash
python manage.py makemigrations lottery_checker
python manage.py migrate
```

## 📖 การใช้งาน

### Django Management Commands

#### ล้างข้อมูลทั้งหมดและดึงข้อมูลใหม่
```bash
# ล้างข้อมูลและดึงข้อมูล 30 วันล่าสุด (ถามยืนยัน)
python manage.py clear_and_fetch_lotto

# ล้างข้อมูลและดึงข้อมูล 60 วันล่าสุด (ไม่ถามยืนยัน)
python manage.py clear_and_fetch_lotto --days-back 60 --force
```

### API Endpoints

#### ดึงข้อมูลหวย
```http
POST /lottery_checker/api/lotto/result/
Content-Type: application/json

{
    "date": 15,
    "month": 1,
    "year": 2025
}
```

#### ดึงข้อมูลล่าสุด
```http
GET /lottery_checker/api/lotto/latest/?days=7
```

#### ดึงข้อมูลวันที่เฉพาะ
```http
GET /lottery_checker/api/lotto/date/2025/1/15/
```

#### ตรวจสอบเลขหวย
```http
POST /lottery_checker/api/lotto/check/
Content-Type: application/json

{
    "date": 15,
    "month": 1,
    "year": 2025,
    "number": "123456"
}
```

#### ล้างข้อมูลทั้งหมด
```http
POST /lottery_checker/api/lotto/clear/
```

#### ดึงสถิติข้อมูล
```http
GET /lottery_checker/api/lotto/statistics/
```

## 🏗️ โครงสร้างระบบ

### โมเดลใหม่ (LottoResult)

- `draw_date`: วันที่ออกรางวัล (unique)
- `result_data`: ข้อมูลผลรางวัลจาก API (JSON)
- `source`: แหล่งข้อมูล
- `created_at`: วันที่สร้าง
- `updated_at`: วันที่อัปเดต

### LottoService

- `fetch_from_api()`: ดึงข้อมูลจาก GLO API
- `get_or_fetch_result()`: ดึงข้อมูลจากฐานข้อมูล หรือดึงจาก API ถ้ายังไม่มี
- `save_to_database()`: บันทึกลงฐานข้อมูล
- `clear_all_data()`: ล้างข้อมูลทั้งหมด
- `get_statistics()`: ดึงสถิติข้อมูล

## 🔄 วิธีการทำงาน

1. **ตรวจสอบวันที่**: ระบบจะตรวจสอบว่าวันที่ที่ต้องการมีข้อมูลในฐานข้อมูลหรือไม่
2. **ดึงจากฐานข้อมูล**: ถ้ามีข้อมูลแล้ว จะดึงจากฐานข้อมูลทันที
3. **ดึงจาก API**: ถ้าไม่มีข้อมูล จะดึงจาก GLO API
4. **บันทึกลงฐานข้อมูล**: บันทึกข้อมูลที่ได้จาก API ลงฐานข้อมูล
5. **ส่งข้อมูลกลับ**: ส่งข้อมูลกลับให้ผู้ใช้

## 🎨 Web Interface

- **ฟอร์มค้นหาข้อมูลหวย**: ค้นหาข้อมูลหวยตามวันที่
- **ฟอร์มตรวจสอบเลขหวย**: ตรวจสอบเลขหวยว่าถูกรางวัลหรือไม่
- **ตารางข้อมูลล่าสุด**: แสดงข้อมูลหวยล่าสุดในระบบ
- **ปุ่มรีเฟรช**: รีเฟรชข้อมูลล่าสุด
- **ปุ่มล้างข้อมูล**: ล้างข้อมูลทั้งหมดในระบบ

## 🧪 การทดสอบ

### ทดสอบการทำงานของ Service

```python
from lottery_checker.lotto_service import LottoService

service = LottoService()

# ดึงข้อมูลหวยวันนี้
result = service.get_or_fetch_result(
    date=15,
    month=1,
    year=2025
)

print(result)
```

### ทดสอบ API

```bash
# ทดสอบดึงข้อมูลหวย
curl -X POST http://localhost:8000/lottery_checker/api/lotto/result/ \
  -H "Content-Type: application/json" \
  -d '{"date": 15, "month": 1, "year": 2025}'

# ทดสอบตรวจสอบเลขหวย
curl -X POST http://localhost:8000/lottery_checker/api/lotto/check/ \
  -H "Content-Type: application/json" \
  -d '{"date": 15, "month": 1, "year": 2025, "number": "123456"}'
```

## 🔧 การตั้งค่า

### Environment Variables

```bash
# GLO API settings (ถ้าต้องการเปลี่ยน)
GLO_API_URL=https://www.glo.or.th/api/checking/getLotteryResult
```

### Django Settings

ตรวจสอบว่า `lottery_checker` อยู่ใน `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... apps อื่นๆ
    'lottery_checker',
]
```

## 📝 การพัฒนา

### เพิ่มฟีเจอร์ใหม่

1. แก้ไข `models.py` สำหรับโครงสร้างข้อมูลใหม่
2. อัปเดต `lotto_service.py` สำหรับฟังก์ชันใหม่
3. เพิ่ม API endpoints ใน `views.py`
4. อัปเดต `urls.py` สำหรับ routing ใหม่
5. เพิ่ม UI elements ใน template

### การแก้ไขบั๊ก

1. ตรวจสอบ logs ใน Django console
2. ใช้ Django debug toolbar สำหรับการ debug
3. ทดสอบ API endpoints ด้วย Postman หรือ curl

## 🚨 หมายเหตุสำคัญ

- **การล้างข้อมูล**: การล้างข้อมูลทั้งหมดจะลบข้อมูลหวยทั้งหมดในระบบ
- **API Rate Limiting**: GLO API อาจมีข้อจำกัดในการเรียกใช้
- **ข้อมูลออฟไลน์**: ระบบจะทำงานได้แม้ไม่มีอินเทอร์เน็ต (ใช้ข้อมูลในฐานข้อมูล)

## 📞 การสนับสนุน

หากมีคำถามหรือปัญหา:

1. ตรวจสอบ logs ใน Django console
2. ทดสอบ API endpoints ด้วย Postman
3. ตรวจสอบการเชื่อมต่อฐานข้อมูล
4. สร้าง issue ใน repository

# LekdeDai - Django AI Project

โปรเจค Django ที่รวม AI engine, ระบบจัดการความฝัน, สถิติหวย และระบบข่าวสาร

## คุณสมบัติหลัก

### 🤖 AI Engine
- ระบบ Machine Learning สำหรับการวิเคราะห์และทำนาย
- API สำหรับการประมวลผลข้อมูล
- ระบบจัดการโมเดล AI

### 💭 Dreams Management
- ระบบบันทึกและจัดการความฝัน
- การวิเคราะห์รูปแบบความฝัน
- การเชื่อมโยงกับข้อมูลอื่นๆ

### 🎯 Lotto Statistics
- การคำนวณสถิติหวย
- การวิเคราะห์ข้อมูลย้อนหลัง
- การแสดงผลสถิติแบบกราฟ

### 📰 News System
- ระบบจัดการข่าวสาร
- การวิเคราะห์ข่าวด้วย AI
- การให้คำแนะนำโชคดี

## การติดตั้ง

### Prerequisites
- Python 3.8+
- Docker และ Docker Compose
- PostgreSQL

### การติดตั้งด้วย Docker
```bash
# Clone repository
git clone <your-repo-url>
cd lekdedai

# สร้างและรัน containers
docker-compose up -d

# สร้างฐานข้อมูลใหม่ (ถ้าต้องการ)
docker-compose exec web ./setup_new_db.sh
```

### การติดตั้งแบบ Local
```bash
# สร้าง virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# หรือ
venv\Scripts\activate  # Windows

# ติดตั้ง dependencies
pip install -r requirements.txt

# รัน migrations
python manage.py migrate

# สร้าง superuser
python manage.py createsuperuser

# รัน server
python manage.py runserver
```

## โครงสร้างโปรเจค

```
lekdedai/
├── app/                    # Django application
│   ├── ai_engine/         # AI และ Machine Learning
│   ├── dreams/            # ระบบจัดการความฝัน
│   ├── home/              # หน้าหลัก
│   ├── lekdedai/          # ตั้งค่าหลัก
│   ├── lotto_stats/       # สถิติหวย
│   ├── news/              # ระบบข่าวสาร
│   └── static/            # ไฟล์ static
├── docker-compose.yml     # Docker configuration
├── Dockerfile            # Docker image
└── requirements.txt      # Python dependencies
```

## การใช้งาน

1. เข้าสู่ระบบผ่าน `/admin/`
2. ใช้ AI Engine ที่ `/ai-engine/`
3. จัดการความฝันที่ `/dreams/`
4. ดูสถิติหวยที่ `/lotto-stats/`
5. อ่านข่าวสารที่ `/news/`

## การพัฒนา

### การรัน Tests
```bash
python manage.py test
```

### การสร้าง Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### การรัน Management Commands
```bash
# เพิ่มข้อมูลหวย
python manage.py add_lotto_data

# คำนวณสถิติ
python manage.py add_calculate_stats

# เพิ่มข้อมูลข่าว
python manage.py add_news_data

# เพิ่มข้อมูลความฝัน
python manage.py add_dream_data
```

## การปรับแต่ง

### Environment Variables
สร้างไฟล์ `.env` ในโฟลเดอร์หลัก:
```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

### การปรับแต่ง AI Models
แก้ไขไฟล์ใน `app/ai_engine/ml_engine.py` เพื่อปรับแต่งโมเดล AI

## การ Deploy

### Production
```bash
# รวบรวม static files
python manage.py collectstatic

# รันด้วย Gunicorn
gunicorn lekdedai.wsgi:application
```

### Docker Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## การสนับสนุน

หากมีปัญหาหรือคำถาม กรุณาสร้าง Issue ใน GitHub repository

## License

MIT License - ดูรายละเอียดในไฟล์ LICENSE

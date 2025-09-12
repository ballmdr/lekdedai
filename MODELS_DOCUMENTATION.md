# LekdeDai Django Models Documentation

## Overview
โมเดลหลักของระบบ LekdeDai ประกอบด้วย 4 ส่วนหลัก:

1. **ตรวจหวย (lottery_checker)** - จัดเก็บผลรางวัลหวยจาก API
2. **สถิติหวย (lotto_stats)** - วิเคราะห์สถิติจากข้อมูลในฐานข้อมูล
3. **ข่าวหวย (news)** - ดึงข่าวและวิเคราะห์เลขเด็ดจากข่าว
4. **วิเคราะห์ฝัน (dreams)** - วิเคราะห์ความฝันและแปลงเป็นเลขเด็ด

---

## 1. ตรวจหวย (lottery_checker)

### LottoResult
เก็บผลรางวัลหวยจาก API

**ฟิลด์หลัก:**
- `draw_date` - วันที่ออกรางวัล (unique)
- `result_data` - ข้อมูลผลรางวัลแบบ JSON
- `source` - แหล่งข้อมูล (default: "GLO API")
- `is_valid` - สถานะความถูกต้องของข้อมูล
- `raw_api_response` - ข้อมูลดิบจาก API

**เมธอดสำคัญ:**
- `get_prize_numbers(prize_type)` - ดึงเลขรางวัลตามประเภท
- `get_all_numbers()` - ดึงเลขรางวัลทั้งหมด
- `is_today` - ตรวจสอบว่าเป็นวันนี้
- `is_recent` - ตรวจสอบว่าเป็นข้อมูลล่าสุด (7 วัน)

**การใช้งาน:**
```python
# ดึงผลรางวัลล่าสุด
latest_result = LottoResult.objects.filter(is_valid=True).first()

# ดึงเลขรางวัลที่ 1
first_prize = latest_result.get_prize_numbers('first_prize')

# ดึงเลขทั้งหมด
all_numbers = latest_result.get_all_numbers()
```

---

## 2. สถิติหวย (lotto_stats)

### LotteryDraw
เก็บข้อมูลการออกรางวัลแต่ละงวด

**ฟิลด์หลัก:**
- `draw_date` - วันที่ออกรางวัล (unique)
- `first_prize` - รางวัลที่ 1 (6 หลัก)
- `two_digit` - เลขท้าย 2 ตัว
- `three_digit_front` - เลขหน้า 3 ตัว (คั่นด้วยจุลภาค)
- `three_digit_back` - เลขท้าย 3 ตัว (คั่นด้วยจุลภาค)

**เมธอดสำคัญ:**
- `get_all_two_digits()` - ดึงเลข 2 ตัวทั้งหมดจากรางวัลที่ 1
- `get_all_three_digits()` - ดึงเลข 3 ตัวทั้งหมด
- `get_three_digit_front_list(limit)` - ดึงเลขหน้า 3 ตัว
- `get_three_digit_back_list(limit)` - ดึงเลขท้าย 3 ตัว

### NumberStatistics
สถิติของเลขแต่ละตัว

**ฟิลด์หลัก:**
- `number` - เลข (unique)
- `number_type` - ประเภท (2D/3D)
- `total_appearances` - จำนวนครั้งที่ออก
- `last_appeared` - ออกล่าสุดเมื่อ
- `days_since_last` - จำนวนวันที่ไม่ออก
- `max_consecutive` - ออกติดต่อกันสูงสุด
- `average_gap` - ระยะห่างเฉลี่ย (วัน)

### HotColdNumber
เลขฮอต/เลขเย็น

**ฟิลด์หลัก:**
- `hot_2d` - เลขฮอต 2 ตัว (JSON)
- `hot_3d` - เลขฮอต 3 ตัว (JSON)
- `cold_2d` - เลขเย็น 2 ตัว (JSON)
- `cold_3d` - เลขเย็น 3 ตัว (JSON)
- `calculation_days` - จำนวนวันที่ใช้คำนวณ (default: 90)

**การใช้งาน:**
```python
# สร้างสถิติเลข
from lotto_stats.models import LotteryDraw, NumberStatistics

# ดึงข้อมูลการออกรางวัล
draws = LotteryDraw.objects.all()

# วิเคราะห์สถิติเลข 2 ตัว
for draw in draws:
    two_digits = draw.get_all_two_digits()
    for num in two_digits:
        stat, created = NumberStatistics.objects.get_or_create(
            number=num, number_type='2D'
        )
        if not created:
            stat.total_appearances += 1
            stat.save()
```

---

## 3. ข่าวหวย (news)

### NewsCategory
หมวดหมู่ข่าว

**ฟิลด์หลัก:**
- `name` - ชื่อหมวดหมู่
- `slug` - Slug (รองรับภาษาไทย)
- `description` - คำอธิบาย

### NewsArticle
บทความข่าว

**ฟิลด์หลัก:**
- `title` - หัวข้อข่าว
- `content` - เนื้อหาข่าว
- `extracted_numbers` - เลขที่ได้จากข่าว (คั่นด้วยจุลภาค)
- `confidence_score` - ความน่าเชื่อถือ (0-100)
- `lottery_relevance_score` - คะแนนความเหมาะสมหวย (0-100)
- `lottery_category` - หมวดหมู่: accident, celebrity, economic, general
- `source_url` - URL แหล่งที่มา

**ฟิลด์ Insight-AI:**
- `insight_summary` - สรุปเหตุการณ์จาก AI
- `insight_impact_score` - คะแนนผลกระทบ (0.0-1.0)
- `insight_entities` - เลขจาก AI (JSON)
- `insight_analyzed_at` - วันที่วิเคราะห์

**เมธอดสำคัญ:**
- `get_extracted_numbers_list()` - แปลงเลขเป็น list
- `get_formatted_content()` - จัดรูปแบบเนื้อหาเป็นย่อหน้า HTML
- `extract_numbers_from_content()` - วิเคราะห์หาเลขจากเนื้อหา

### LuckyNumberHint
เลขเด็ดจากแหล่งต่างๆ

**ฟิลด์หลัก:**
- `source_type` - ประเภทแหล่งที่มา (temple, tree, dream, natural, accident, other)
- `source_name` - ชื่อแหล่งที่มา
- `lucky_numbers` - เลขเด็ด
- `reliability_score` - ความน่าเชื่อถือ (%)
- `related_article` - ข่าวที่เกี่ยวข้อง (FK)

### NewsComment
ความคิดเห็นในข่าว

**ฟิลด์หลัก:**
- `article` - บทความที่แสดงความเห็น (FK)
- `user` - ผู้แสดงความเห็น (FK)
- `content` - ความคิดเห็น
- `suggested_numbers` - เลขที่แนะนำ
- `is_approved` - สถานะอนุมัติ

**การใช้งาน:**
```python
# สร้างบทความข่าวและวิเคราะห์เลข
from news.models import NewsArticle

article = NewsArticle.objects.create(
    title="อุบัติเหตุรถชนที่แยกห้าแพร่ง",
    content="เกิดอุบัติเหตุรถชน ทะเบียน กข-1234 อายุผู้ขับ 45 ปี",
    status='published'
)

# วิเคราะห์เลขอัตโนมัติ
numbers = article.extract_numbers_from_content()
# ได้เลข: ['34', '45', '12']

article.extracted_numbers = ','.join(numbers)
article.lottery_category = 'accident'
article.lottery_relevance_score = 85
article.save()
```

---

## 4. วิเคราะห์ฝัน (dreams)

### DreamCategory
หมวดหมู่ความฝัน

**ฟิลด์หลัก:**
- `name` - ชื่อหมวดหมู่
- `description` - คำอธิบาย

### DreamKeyword
คำสำคัญในความฝันและเลขที่เกี่ยวข้อง

**ฟิลด์หลัก:**
- `keyword` - คำสำคัญ (indexed)
- `category` - หมวดหมู่ความฝัน (FK)
- `main_number` - เลขเด่น (0-9)
- `secondary_number` - เลขรอง (0-9)
- `common_numbers` - เลขที่มักตี (คั่นด้วยจุลภาค)

**เมธอดสำคัญ:**
- `get_numbers_list()` - แปลงเลขเป็น list
- `get_main_combinations()` - สร้างเลขจากเลขเด่นและเลขรอง

### DreamInterpretation
การตีความฝันของผู้ใช้

**ฟิลด์หลัก:**
- `user` - ผู้ใช้ (FK, nullable)
- `dream_text` - รายละเอียดความฝัน

**ฟิลด์ Seer-AI (ใหม่):**
- `sentiment` - อารมณ์ของความฝัน (Positive/Negative/Neutral)
- `predicted_numbers_json` - ผลลัพธ์การทำนาย (JSON)
- `main_symbols` - สัญลักษณ์หลัก

**ฟิลด์ Legacy (เก่า):**
- `keywords_found` - คำสำคัญที่พบ
- `suggested_numbers` - เลขที่แนะนำ
- `interpretation` - คำทำนาย

**การใช้งาน:**
```python
# สร้างคำสำคัญความฝัน
from dreams.models import DreamCategory, DreamKeyword

category = DreamCategory.objects.create(name="สัตว์")

keyword = DreamKeyword.objects.create(
    keyword="งู",
    category=category,
    main_number="7",
    secondary_number="2",
    common_numbers="72,27,77,22,07,70"
)

# ได้เลขจาก combinations
combinations = keyword.get_main_combinations()
# ['72', '27', '77']

# วิเคราะห์ความฝัน
from dreams.models import DreamInterpretation

dream = DreamInterpretation.objects.create(
    dream_text="ฝันเห็นงูตัวใหญ่สีเขียว",
    sentiment="Neutral",
    predicted_numbers_json={
        "predicted_numbers": [
            {"number": "72", "confidence": 0.8, "reason": "งูในความฝัน"},
            {"number": "27", "confidence": 0.6, "reason": "สีเขียวของงู"}
        ],
        "main_symbols": ["งู", "สีเขียว"]
    },
    main_symbols="งู, สีเขียว"
)
```

---

## Model Relationships

### ความสัมพันธ์หลัก:

1. **NewsArticle ↔ LuckyNumberHint** (One-to-Many)
   - ข่าวหนึ่งข่าวสามารถมีเลขเด็ดหลายชุด

2. **NewsArticle ↔ NewsComment** (One-to-Many)
   - ข่าวหนึ่งข่าวมีความคิดเห็นได้หลายรายการ

3. **DreamCategory ↔ DreamKeyword** (One-to-Many)
   - หมวดหมู่หนึ่งมีคำสำคัญได้หลายคำ

4. **User ↔ DreamInterpretation** (One-to-Many, Nullable)
   - ผู้ใช้สามารถมีการตีความฝันหลายครั้ง

---

## Database Indexes

**Performance Optimization:**

1. **lottery_checker.LottoResult**
   - Index on `draw_date`
   - Index on `created_at`

2. **dreams.DreamKeyword**
   - Index on `keyword` (สำหรับการค้นหา)

3. **news.NewsArticle**
   - Ordering by `-published_date, -created_at`

---

## Status และการใช้งาน

✅ **Model Status**: ทุก model ผ่านการตรวจสอบ Django system check แล้ว

✅ **ความสมบูรณ์**: Models มีครบทั้ง:
- Meta classes สำหรับ verbose names ภาษาไทย
- Custom methods สำหรับการประมวลผลข้อมูล
- Proper field validations และ choices
- JSON fields สำหรับข้อมูลที่ซับซ้อน

✅ **Backward Compatibility**: Dreams model รองรับทั้งระบบเก่าและใหม่

⚠️ **Dependencies**: ต้องการ packages:
- Django 4.2+
- Pillow (สำหรับ ImageField)
- dj-database-url (สำหรับ database configuration)

## วิธีการใช้งานทั่วไป

### 1. การดึงข้อมูลล่าสุด
```python
# ผลหวยล่าสุด
latest_lotto = LottoResult.objects.filter(is_valid=True).first()

# ข่าวล่าสุด
latest_news = NewsArticle.objects.filter(status='published').first()

# ความฝันล่าสุด
latest_dreams = DreamInterpretation.objects.all()[:5]
```

### 2. การวิเคราะห์เลขเด็ด
```python
# รวบรวมเลขเด็ดจากหลายแหล่ง
from news.models import NewsArticle
from dreams.models import DreamKeyword

# จากข่าว
news_numbers = []
for article in NewsArticle.objects.filter(lottery_relevance_score__gte=70):
    news_numbers.extend(article.get_extracted_numbers_list())

# จากความฝัน
dream_numbers = []
for keyword in DreamKeyword.objects.all():
    dream_numbers.extend(keyword.get_numbers_list())

# รวมและจัดอันดับ
all_numbers = news_numbers + dream_numbers
```

### 3. การสร้างรายงานสถิติ
```python
from lotto_stats.models import NumberStatistics

# เลขฮอต (ออกบ่อย)
hot_numbers = NumberStatistics.objects.filter(
    number_type='2D'
).order_by('-total_appearances')[:10]

# เลขเย็น (ไม่ออกนาน)
cold_numbers = NumberStatistics.objects.filter(
    number_type='2D'
).order_by('days_since_last')[:10]
```

---

*เอกสารนี้อัปเดตล่าสุด: 10 กันยายน 2568*
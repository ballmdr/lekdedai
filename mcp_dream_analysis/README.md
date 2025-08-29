# MCP Dream Analysis Service

## ภาพรวม
ระบบ Machine Learning สำหรับการวิเคราะห์ความฝันและทำนายเลข พร้อม Model Context Protocol (MCP) สำหรับการใช้งานในส่วนต่างๆ ของระบบ

## คุณสมบัติหลัก
- 🤖 **Machine Learning Model** สำหรับวิเคราะห์ความฝันภาษาไทย
- 🔗 **MCP Protocol** สำหรับการเชื่อมต่อกับส่วนอื่นๆ
- 📰 **News Integration** วิเคราะห์ข่าวเพื่อหาเลขเด็ด
- 🎯 **Django Integration** ใช้งานง่ายใน Django views และ templates
- 📊 **Hybrid Analysis** รวมระบบ ML และแบบดั้งเดิม

## โครงสร้างไฟล์
```
mcp_dream_analysis/
├── dream_ml_model.py       # ML Model หลัก
├── mcp_server.py          # MCP Protocol Server
├── django_integration.py  # Django Integration Layer  
├── news_integration.py    # News Analysis Integration
├── data_preparation.py    # เตรียมข้อมูลสำหรับ ML
├── management/
│   └── commands/
│       └── train_dream_ml.py  # Django command สำหรับฝึกสอนโมเดล
└── requirements.txt
```

## การติดตั้ง

### 1. ติดตั้ง Python packages
```bash
pip install -r mcp_dream_analysis/requirements.txt
```

### 2. เพิ่ม template tags ใน Django
เพิ่มใน `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    # ... apps อื่นๆ
    'dreams',  # ต้องมีอยู่แล้ว
]
```

### 3. ฝึกสอนโมเดล ML (ครั้งแรก)
```bash
cd app
python manage.py train_dream_ml --prepare-data
```

## การใช้งาน

### 1. ใน Django Views
```python
from mcp_dream_analysis.django_integration import analyze_dream_for_django

def my_view(request):
    result = analyze_dream_for_django("ฝันเห็นงูใหญ่")
    return JsonResponse(result)
```

### 2. ใน Django Templates
```html
{% load dream_analysis %}

<!-- ตรวจสอบว่าข่าวมีเนื้อหาเกี่ยวกับความฝันหรือไม่ -->
{% if article|has_dream_content %}
    <!-- แสดงการ์ดวิเคราะห์ความฝัน -->
    {% dream_analysis_card article %}
    
    <!-- แสดงแค่เลขเด็ด -->
    {% dream_numbers_widget article|extract_dream_numbers "เลขจากข่าว" %}
{% endif %}

<!-- วิเคราะห์ความฝันโดยตรง -->
{% analyze_dream_text "ฝันเห็นช้าง" as dream_result %}
{% if dream_result.success %}
    <p>เลขแนะนำ: {{ dream_result.numbers|join:", " }}</p>
{% endif %}
```

### 3. การวิเคราะห์ข่าว
```python
from mcp_dream_analysis.news_integration import analyze_news_article_for_dreams

# วิเคราะห์ข่าวเพื่อหาเลขเด็ด
result = analyze_news_article_for_dreams(
    news_title="ฝันเห็นงูทอง", 
    news_content="เนื้อหาข่าว..."
)

if result['success'] and result['suggested_numbers']:
    print(f"เลขเด็ด: {result['suggested_numbers']}")
```

## การฝึกสอนโมเดล

### ใช้ Django Management Command
```bash
# เตรียมข้อมูลและฝึกสอน
python manage.py train_dream_ml --prepare-data

# ฝึกสอนจากไฟล์ข้อมูลที่มีอยู่
python manage.py train_dream_ml --data-file custom_data.json
```

### ใช้ Python Script โดยตรง
```python
from mcp_dream_analysis.data_preparation import prepare_and_save_data
from mcp_dream_analysis.dream_ml_model import DreamNumberMLModel

# เตรียมข้อมูล
training_data = prepare_and_save_data()

# ฝึกสอนโมเดล
model = DreamNumberMLModel()
model.train(training_data)
model.save_model()
```

## MCP Protocol API

### Analyze Dream
```json
{
  "method": "analyze_dream",
  "params": {
    "dream_text": "ฝันเห็นงูใหญ่สีเขียว"
  }
}
```

### Predict Numbers (ML Only)
```json
{
  "method": "predict_numbers", 
  "params": {
    "dream_text": "ฝันเห็นช้าง",
    "num_predictions": 6
  }
}
```

### Train Model
```json
{
  "method": "train_model",
  "params": {
    "training_data": [...],
    "test_size": 0.2,
    "save_model": true
  }
}
```

## ข้อมูลที่ใช้ในการฝึกสอน

โมเดลใช้ข้อมูลจาก 3 แหล่ง:

1. **DreamKeyword** - คำสำคัญและเลขจากฐานข้อมูล
2. **DreamInterpretation** - การตีความจริงจากผู้ใช้
3. **Synthetic Data** - ข้อมูลสังเคราะห์ที่สร้างขึ้น

## การทำงานแบบ Hybrid

ระบบจะใช้วิธีการผสม:

1. **ML Prediction** - ถ้าโมเดลถูกฝึกแล้ว
2. **Traditional Analysis** - วิธีแบบดั้งเดิม (fallback)
3. **Combined Results** - รวมผลจากทั้งสองวิธี

## การ Debug และ Monitoring

### ตรวจสอบสถานะ MCP
```html
{% load dream_analysis %}
{% mcp_status as status %}
{% if status.available %}
    <div class="alert alert-success">{{ status.message }}</div>
{% else %}
    <div class="alert alert-warning">{{ status.message }}</div>
{% endif %}
```

### Log Files
ระบบจะ log ข้อมูลไปยัง Django logging system:
```python
# ใน settings.py
LOGGING = {
    'loggers': {
        'mcp_dream_analysis': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
        },
    }
}
```

## ข้อกำหนดระบบ

- Python 3.8+
- Django 3.2+
- Memory: อย่างน้อย 512MB สำหรับ ML model
- Storage: 50MB สำหรับ model files

## การแก้ไขปัญหา

### MCP Service ไม่พร้อมใช้งาน
- ตรวจสอบการติดตั้ง requirements
- ตรวจสอบ path ของ mcp_dream_analysis directory
- ดู Django error logs

### โมเดล ML ไม่ทำงาน
- รัน `python manage.py train_dream_ml --prepare-data`
- ตรวจสอบไฟล์ `dream_ml_model.pkl`
- ระบบจะ fallback เป็นแบบดั้งเดิมอัตโนมัติ

### ประสิทธิภาพช้า
- ใช้ async ใน production environment
- Cache ผลการวิเคราะห์ที่ใช้บ่อย
- ปรับ batch_size ในการประมวลผล

## การพัฒนาต่อ

### เพิ่ม Model ใหม่
```python
class NewDreamModel(DreamNumberMLModel):
    def __init__(self):
        super().__init__()
        # เพิ่มโมเดลใหม่
```

### เพิ่ม MCP Method ใหม่
```python
async def _handle_new_method(self, params: Dict[str, Any]) -> Dict[str, Any]:
    # Implementation
    pass
```

## License
MIT License - ใช้งานได้ฟรีสำหรับ LekDedAI project
from django.core.management.base import BaseCommand
from dreams.models import DreamCategory, DreamKeyword

class Command(BaseCommand):
    help = 'Add sample dream keywords'
    
    def handle(self, *args, **options):
        # สร้าง Categories
        animals = DreamCategory.objects.get_or_create(name="สัตว์", description="สัตว์ต่างๆ ในความฝัน")[0]
        objects = DreamCategory.objects.get_or_create(name="สิ่งของ", description="วัตถุและสิ่งของ")[0]
        nature = DreamCategory.objects.get_or_create(name="ธรรมชาติ", description="ธรรมชาติและสิ่งแวดล้อม")[0]
        
        # เพิ่ม Keywords
        keywords_data = [
            # สัตว์
            (animals, "ช้าง", "89,98,08"),
            (animals, "งู", "01,10,23,32"),
            (animals, "เสือ", "37,73,29"),
            (animals, "หมา", "18,81,06"),
            (animals, "แมว", "36,63,03"),
            (animals, "นก", "19,91,16"),
            (animals, "ปลา", "24,42,58"),
            
            # สิ่งของ
            (objects, "เงิน", "28,82,00"),
            (objects, "ทอง", "39,93,62"),
            (objects, "รถ", "54,45,18"),
            (objects, "บ้าน", "14,41,21"),
            (objects, "แหวน", "16,61,94"),
            
            # ธรรมชาติ
            (nature, "น้ำ", "09,90,12"),
            (nature, "ไฟ", "17,71,25"),
            (nature, "ฝน", "26,62,09"),
            (nature, "ต้นไม้", "38,83,47"),
        ]
        
        for category, keyword, numbers in keywords_data:
            DreamKeyword.objects.get_or_create(
                keyword=keyword,
                category=category,
                defaults={'numbers': numbers}
            )
        
        self.stdout.write(self.style.SUCCESS('Successfully added dream keywords'))
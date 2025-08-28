from django.core.management.base import BaseCommand
from dreams.models import DreamCategory, DreamKeyword

class Command(BaseCommand):
    help = 'Add real dream interpretations with lottery numbers'
    
    def handle(self, *args, **options):
        # ลบข้อมูลเก่าก่อน
        DreamKeyword.objects.all().delete()
        DreamCategory.objects.all().delete()
        
        # สร้างหมวดหมู่ใหม่
        animals = DreamCategory.objects.create(
            name="🐘 หมวดสัตว์", 
            description="สัตว์ต่างๆ ในความฝัน"
        )
        people = DreamCategory.objects.create(
            name="👑 หมวดบุคคล", 
            description="บุคคลต่างๆ ในความฝัน"
        )
        objects = DreamCategory.objects.create(
            name="🏠 หมวดสิ่งของ / สถานที่", 
            description="วัตถุ สิ่งของ และสถานที่ต่างๆ"
        )
        body_parts = DreamCategory.objects.create(
            name="💪 หมวดอวัยวะและร่างกาย", 
            description="อวัยวะและส่วนต่างๆ ของร่างกาย"
        )
        colors = DreamCategory.objects.create(
            name="🎨 หมวดสี", 
            description="สีต่างๆ ในความฝัน"
        )
        nature = DreamCategory.objects.create(
            name="🌿 หมวดธรรมชาติ",
            description="ธรรมชาติต่างๆ ในความฝัน"
        )
        tools = DreamCategory.objects.create(
            name="🛠 หมวดเครื่องมือ / อุปกรณ์",
            description="เครื่องมือและอุปกรณ์ต่างๆ"
        )
        vehicles = DreamCategory.objects.create(
            name="⚙ หมวดยานพาหนะอื่น ๆ",
            description="ยานพาหนะต่างๆ"
        )
        mystical = DreamCategory.objects.create(
            name="🔮 หมวดสิ่งลี้ลับ / ความเชื่อ",
            description="สิ่งลี้ลับและความเชื่อ"
        )
        activities = DreamCategory.objects.create(
            name="🎉 หมวดกิจกรรม / งานบุญ",
            description="กิจกรรมและงานบุญต่างๆ"
        )
        
        # เพิ่ม Keywords ตามข้อมูลจริง (category, keyword, main_number, secondary_number, common_numbers)
        keywords_data = [
            # หมวดสัตว์ (Animals)
            (animals, "งูเล็ก", "5", "6", "56,65,59"),
            (animals, "พญานาค", "5", "6", "56,65,59"),
            (animals, "งู", "5", "6", "56,65,59"),
            (animals, "ปลา", "8", "7", "78,87,88"),
            (animals, "ช้าง", "9", "1", "19,99"),
            (animals, "ม้า", "1", "2", "12,42,72"),
            (animals, "วัว", "4", "2", "42,82"),
            (animals, "ควาย", "4", "2", "42,82"),
            (animals, "หมู", "0", "7", "07,47,73"),
            (animals, "หมา", "1", "4", "14,41,44"),
            (animals, "ไก่", "0", "9", "09,19"),
            (animals, "นก", "1", "6", "16,26,66"),
            (animals, "เต่า", "4", "3", "43,45,13"),
            (animals, "กบ", "8", "9", "89,59"),
            (animals, "คางคก", "8", "9", "89,59"),
            (animals, "เสือ", "3", "4", "34,43,30"),

            # หมวดบุคคล (People)
            (people, "พระ", "8", "9", "88,89,289"),
            (people, "เณร", "8", "9", "88,89,289"),
            (people, "แม่ชี", "8", "9", "88,89,289"),
            (people, "เด็กทารก", "1", "3", "11,13,33"),
            (people, "ทารก", "1", "3", "11,13,33"),
            (people, "เด็ก", "1", "3", "11,13,33"),
            (people, "คนตาย", "0", "4", "04,40,07"),
            (people, "ศพ", "0", "4", "04,40,07"),
            (people, "ผี", "0", "4", "04,40,07"),
            (people, "ผู้หญิง", "5", "6", "55,56"),
            (people, "ผู้ชาย", "1", "9", "19,91"),
            (people, "คนแก่", "8", "9", "89,90,509"),
            (people, "ปู่", "8", "9", "89,90,509"),
            (people, "ย่า", "8", "9", "89,90,509"),
            (people, "ตา", "8", "9", "89,90,509"),
            (people, "ยาย", "8", "9", "89,90,509"),
            (people, "กษัตริย์", "9", "5", "59,95,19"),
            (people, "ราชินี", "9", "5", "59,95,19"),
            (people, "พระราชา", "9", "5", "59,95,19"),

            # หมวดสิ่งของ / สถานที่ (Objects / Places)
            (objects, "บ้าน", "1", "4", "14,41,47"),
            (objects, "ที่อยู่อาศัย", "1", "4", "14,41,47"),
            (objects, "รถยนต์", "5", "4", "54,45"),
            (objects, "รถ", "5", "4", "54,45"),
            (objects, "เงิน", "8", "2", "28,82,68"),
            (objects, "ทอง", "8", "2", "28,82,68"),
            (objects, "แหวน", "0", "9", "09,60,10"),
            (objects, "เครื่องประดับ", "0", "9", "09,60,10"),
            (objects, "สร้อย", "0", "9", "09,60,10"),
            (objects, "วัด", "8", "9", "89,98,80"),
            (objects, "โบสถ์", "8", "9", "89,98,80"),
            (objects, "ศาลา", "8", "9", "89,98,80"),
            (objects, "น้ำ", "0", "2", "02,29,32"),
            (objects, "ไฟ", "7", "1", "17,77,47"),
            (objects, "เปลวไฟ", "7", "1", "17,77,47"),
            (objects, "อาวุธ", "3", "8", "38,83,03"),
            (objects, "มีด", "3", "8", "38,83,03"),
            (objects, "ปืน", "3", "8", "38,83,03"),
            (objects, "ดาบ", "3", "8", "38,83,03"),

            # หมวดอวัยวะและร่างกาย (Body Parts)
            (body_parts, "มือ", "1", "5", "15,50,52"),
            (body_parts, "แขน", "1", "5", "15,50,52"),
            (body_parts, "เท้า", "1", "2", "12,14"),
            (body_parts, "ขา", "1", "2", "12,14"),
            (body_parts, "ฟัน", "7", "8", "78,87,07"),
            (body_parts, "เลือด", "0", "2", "02,22"),

            # หมวดสีและธรรมชาติ (Colors & Nature)
            (colors, "สีขาว", "9", "0", "09,90,19"),
            (colors, "ขาว", "9", "0", "09,90,19"),
            (colors, "สีดำ", "0", "8", "08,80,18"),
            (colors, "ดำ", "0", "8", "08,80,18"),
            (colors, "สีแดง", "5", "2", "52,25,02"),
            (colors, "แดง", "5", "2", "52,25,02"),
            (colors, "สีเขียว", "7", "3", "73,37,03"),
            (colors, "เขียว", "7", "3", "73,37,03"),
            (colors, "สีเหลือง", "8", "1", "81,18,88"),
            (colors, "เหลือง", "8", "1", "81,18,88"),
            (colors, "สีน้ำเงิน", "6", "4", "64,46,06"),
            (colors, "น้ำเงิน", "6", "4", "64,46,06"),
            
            # หมวดธรรมชาติ (Nature)
            (nature, "ต้นไม้", "2", "5", "25,52"),
            (nature, "ดอกไม้", "3", "7", "37,73"),
            (nature, "ฝน", "0", "6", "06,60"),
            (nature, "ฟ้า", "1", "4", "14,41"),
            (nature, "ท้องฟ้า", "1", "4", "14,41"),
            (nature, "หิน", "4", "8", "48,84"),
            
            # หมวดเครื่องมือ / อุปกรณ์ (Tools)
            (tools, "มีด", "3", "8", "38,83"),
            (tools, "กรรไกร", "3", "8", "38,83"),
            (tools, "เชือก", "2", "5", "25,52"),
            (tools, "โทรศัพท์", "6", "7", "67,76"),
            (tools, "กระเป๋า", "5", "9", "59,95"),
            
            # หมวดยานพาหนะอื่น ๆ (Other Vehicles)
            (vehicles, "เรือ", "4", "9", "49,94"),
            (vehicles, "รถจักรยานยนต์", "7", "8", "78,87"),
            (vehicles, "เครื่องบิน", "1", "5", "15,51"),
            
            # หมวดสิ่งลี้ลับ / ความเชื่อ (Mystical)
            (mystical, "ผี", "0", "4", "04,40"),
            (mystical, "วิญญาณ", "0", "4", "04,40"),
            (mystical, "โชคลาภ", "8", "2", "82,28"),
            (mystical, "เงินทอง", "8", "2", "82,28"),
            (mystical, "พระเครื่อง", "8", "9", "89,98"),
            
            # หมวดกิจกรรม / งานบุญ (Activities)
            (activities, "งานแต่งงาน", "7", "1", "71,17"),
            (activities, "งานศพ", "0", "4", "04,40"),
            (activities, "งานบวช", "8", "9", "89,98"),
        ]
        
        # เพิ่มข้อมูลใหม่
        for category, keyword, main_num, sec_num, common_nums in keywords_data:
            DreamKeyword.objects.create(
                keyword=keyword,
                category=category,
                main_number=main_num,
                secondary_number=sec_num,
                common_numbers=common_nums
            )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated dream database with {len(keywords_data)} keywords in 11 categories'))
"""
เตรียมข้อมูลสำหรับการฝึกสอนโมเดล ML
Data Preparation for ML Model Training
"""
import os
import sys
import django
from typing import List, Dict, Any
import json

# Setup Django
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lekdedai.settings')
django.setup()

from dreams.models import DreamKeyword, DreamInterpretation, DreamCategory

class DreamDataPreparator:
    """คลาสสำหรับเตรียมข้อมูลความฝัน"""
    
    def __init__(self):
        self.data_sources = {
            'keywords': self._load_keyword_data,
            'interpretations': self._load_interpretation_data,
            'synthetic': self._generate_synthetic_data
        }
    
    def _load_keyword_data(self) -> List[Dict]:
        """โหลดข้อมูลจากตาราง DreamKeyword"""
        data = []
        
        for keyword in DreamKeyword.objects.all():
            # Create training samples from keywords
            sample = {
                'dream_text': f"ฝันเห็น{keyword.keyword}",
                'main_number': int(keyword.main_number),
                'secondary_number': int(keyword.secondary_number),
                'combinations': keyword.get_numbers_list(),
                'category': keyword.category.name,
                'source': 'keyword_db'
            }
            data.append(sample)
            
            # Generate variations
            variations = [
                f"ฝันว่า{keyword.keyword}มาหาฉัน",
                f"เห็น{keyword.keyword}ใหญ่มาก",
                f"ฝันเล่นกับ{keyword.keyword}",
                f"ฝันกลัว{keyword.keyword}",
                f"ฝัน{keyword.keyword}สีสวย"
            ]
            
            for variation in variations[:2]:  # จำกัดแค่ 2 รูปแบบ
                var_sample = sample.copy()
                var_sample['dream_text'] = variation
                var_sample['source'] = 'keyword_variation'
                data.append(var_sample)
        
        return data
    
    def _load_interpretation_data(self) -> List[Dict]:
        """โหลดข้อมูลจากการตีความจริง"""
        data = []
        
        for interp in DreamInterpretation.objects.all():
            if interp.suggested_numbers:
                # Parse suggested numbers
                numbers = [n.strip() for n in interp.suggested_numbers.split(',')]
                
                # Estimate main/secondary from first number
                if numbers and len(numbers[0]) >= 2:
                    first_num = numbers[0]
                    main_num = int(first_num[0]) if first_num[0].isdigit() else 1
                    secondary_num = int(first_num[1]) if len(first_num) > 1 and first_num[1].isdigit() else 0
                else:
                    main_num = 1
                    secondary_num = 0
                
                sample = {
                    'dream_text': interp.dream_text,
                    'main_number': main_num,
                    'secondary_number': secondary_num,
                    'combinations': numbers[:6],  # เอาแค่ 6 เลขแรก
                    'category': 'user_interpretation',
                    'source': 'real_interpretation'
                }
                data.append(sample)
        
        return data
    
    def _generate_synthetic_data(self) -> List[Dict]:
        """สร้างข้อมูลสังเคราะห์"""
        synthetic_templates = [
            # Animals
            ("ฝันเห็น{animal}ใหญ่สี{color}", {'animals': ['งู', 'ช้าง', 'เสือ', 'หมู', 'ไก่'], 'colors': ['แดง', 'เขียว', 'ขาว', 'ดำ']}),
            ("ฝันว่า{animal}มา{action}ฉัน", {'animals': ['งู', 'ช้าง', 'หมา', 'แมว'], 'actions': ['กัด', 'ไล่', 'เล่นกับ', 'ตาม']}),
            
            # People  
            ("ฝันเห็น{person}ให้{object}", {'people': ['พระ', 'เณร', 'แม่', 'พ่อ'], 'objects': ['เงิน', 'ทอง', 'ขนม', 'ดอกไม้']}),
            ("ฝันว่า{person}{emotion}มาก", {'people': ['เด็ก', 'คนแก่', 'ผู้หญิง'], 'emotions': ['ดีใจ', 'เศร้า', 'โกรธ']}),
            
            # Objects/Places
            ("ฝันไปที่{place}เห็น{object}", {'places': ['วัด', 'โบสถ์', 'ป่า', 'ทะเล'], 'objects': ['ทอง', 'เงิน', 'รถ', 'บ้าน']}),
            ("ฝันว่า{object}หาย", {'objects': ['เงิน', 'รถ', 'ทอง', 'แหวน']}),
            
            # Actions
            ("ฝันว่าฉัน{action}ใน{place}", {'actions': ['บิน', 'วิ่ง', 'ว่าย', 'เดิน'], 'places': ['น้ำ', 'ฟ้า', 'ป่า', 'วัด']})
        ]
        
        # Number mappings for synthetic data
        element_numbers = {
            # Animals
            'งู': (5, 6, ['56', '89', '08']),
            'ช้าง': (9, 1, ['91', '19', '01']),
            'เสือ': (3, 4, ['34', '43', '03']),
            'หมู': (2, 7, ['27', '72', '02']),
            'ไก่': (1, 8, ['18', '81', '01']),
            'หมา': (4, 5, ['45', '54', '04']),
            'แมว': (6, 7, ['67', '76', '06']),
            
            # People
            'พระ': (8, 9, ['89', '98', '08']),
            'เณร': (9, 0, ['90', '09', '99']),
            'แม่': (2, 8, ['28', '82', '22']),
            'พ่อ': (1, 9, ['19', '91', '11']),
            'เด็ก': (1, 3, ['13', '31', '11']),
            
            # Objects
            'เงิน': (8, 2, ['82', '28', '88']),
            'ทอง': (9, 8, ['98', '89', '99']),
            'รถ': (4, 0, ['40', '04', '44']),
            'บ้าน': (6, 8, ['68', '86', '66']),
            
            # Colors
            'แดง': (3, 0, ['30', '03', '33']),
            'เขียว': (5, 0, ['50', '05', '55']),
            'ขาว': (0, 8, ['08', '80', '00']),
            'ดำ': (0, 0, ['00', '90', '99'])
        }
        
        data = []
        
        for template, variables in synthetic_templates:
            # Generate combinations
            for i in range(10):  # สร้าง 10 ตัวอย่างต่อ template
                dream_text = template
                main_nums = []
                secondary_nums = []
                all_combinations = []
                
                # Fill template with random elements
                for var_type, options in variables.items():
                    import random
                    chosen = random.choice(options)
                    dream_text = dream_text.replace(f'{{{var_type[:-1]}}}', chosen)  # Remove 's' for singular
                    
                    # Get numbers for this element
                    if chosen in element_numbers:
                        main, secondary, combinations = element_numbers[chosen]
                        main_nums.append(main)
                        secondary_nums.append(secondary)
                        all_combinations.extend(combinations)
                
                # Calculate final numbers
                if main_nums:
                    final_main = max(set(main_nums), key=main_nums.count)  # Most frequent
                    final_secondary = max(set(secondary_nums), key=secondary_nums.count)
                    final_combinations = list(dict.fromkeys(all_combinations))[:6]  # Remove duplicates
                else:
                    final_main = 1
                    final_secondary = 0
                    final_combinations = ['10', '01', '11']
                
                sample = {
                    'dream_text': dream_text,
                    'main_number': final_main,
                    'secondary_number': final_secondary,
                    'combinations': final_combinations,
                    'category': 'synthetic',
                    'source': 'generated'
                }
                data.append(sample)
        
        return data
    
    def prepare_training_data(self, include_sources: List[str] = None) -> List[Dict]:
        """เตรียมข้อมูลสำหรับการฝึกสอน"""
        if include_sources is None:
            include_sources = ['keywords', 'interpretations', 'synthetic']
        
        all_data = []
        
        for source in include_sources:
            if source in self.data_sources:
                print(f"📥 กำลังโหลดข้อมูลจาก {source}...")
                source_data = self.data_sources[source]()
                all_data.extend(source_data)
                print(f"✅ โหลดแล้ว {len(source_data)} รายการ")
        
        print(f"📊 รวมข้อมูลทั้งหมด: {len(all_data)} รายการ")
        return all_data
    
    def save_training_data(self, data: List[Dict], filepath: str):
        """บันทึกข้อมูลการฝึกสอน"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 บันทึกข้อมูลแล้ว: {filepath}")
    
    def load_training_data(self, filepath: str) -> List[Dict]:
        """โหลดข้อมูลการฝึกสอน"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"📂 โหลดข้อมูล {len(data)} รายการจาก {filepath}")
        return data

# ฟังก์ชันสำหรับใช้งานเร็ว
def prepare_and_save_data(output_file: str = 'dream_training_data.json'):
    """เตรียมและบันทึกข้อมูล"""
    preparator = DreamDataPreparator()
    
    # เตรียมข้อมูลจากทุกแหล่ง
    training_data = preparator.prepare_training_data()
    
    # บันทึกข้อมูล
    preparator.save_training_data(training_data, output_file)
    
    return training_data

if __name__ == "__main__":
    # เรียกใช้งานโดยตรง
    data = prepare_and_save_data()
    print(f"\n🎯 เสร็จสิ้น! เตรียมข้อมูล {len(data)} รายการแล้ว")
    
    # แสดงตัวอย่างข้อมูล
    if data:
        print("\n📋 ตัวอย่างข้อมูล:")
        for i, sample in enumerate(data[:3]):
            print(f"\n{i+1}. {sample['dream_text']}")
            print(f"   เลขเด่น: {sample['main_number']}, เลขรอง: {sample['secondary_number']}")
            print(f"   เลขผสม: {', '.join(sample['combinations'][:3])}")
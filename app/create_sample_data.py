#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, date

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lekdedai.settings')
django.setup()

from lottery_checker.models import LottoResult
from dreams.models import DreamInterpretation, DreamKeyword, DreamCategory
from django.contrib.auth.models import User

def create_sample_lotto_data():
    """สร้างข้อมูลตัวอย่างสำหรับ lottery_checker"""
    print("Creating sample lottery data...")
    
    # สร้างข้อมูลผลหวยย้อนหลัง
    lotto_data = [
        {
            'draw_date': date(2025, 8, 16),
            'draw_period': '16/08/2025',
            'first_prize': '123456',
            'second_prize': ['234567', '345678'],
            'third_prize': ['456789', '567890', '678901'],
            'fourth_prize': ['789012', '890123', '901234', '012345'],
            'fifth_prize': ['123450', '234561', '345672', '456783', '567894', '678905', '789016', '890127', '901238', '012349'],
            'api_url': 'https://api.example.com/lotto/16-08-2025'
        },
        {
            'draw_date': date(2025, 8, 1),
            'draw_period': '01/08/2025',
            'first_prize': '987654',
            'second_prize': ['876543', '765432'],
            'third_prize': ['654321', '543210', '432109'],
            'fourth_prize': ['321098', '210987', '109876', '098765'],
            'fifth_prize': ['987650', '876541', '765432', '654323', '543214', '432105', '321096', '210987', '109878', '098769'],
            'api_url': 'https://api.example.com/lotto/01-08-2025'
        }
    ]
    
    for data in lotto_data:
        if not LottoResult.objects.filter(draw_date=data['draw_date']).exists():
            LottoResult.objects.create(**data)
            print(f"Created lotto result for {data['draw_date']}")
        else:
            print(f"Lotto result for {data['draw_date']} already exists")

def create_sample_dream_data():
    """สร้างข้อมูลตัวอย่างสำหรับ dreams"""
    print("Creating sample dream data...")
    
    # สร้างหมวดหมู่ความฝัน
    category, created = DreamCategory.objects.get_or_create(
        name='ความฝันทั่วไป',
        defaults={'description': 'ความฝันทั่วไปที่พบได้บ่อย'}
    )
    
    # สร้างคำสำคัญความฝัน
    dream_keywords = [
        {
            'keyword': 'งู',
            'main_number': '3',
            'secondary_number': '7',
            'common_numbers': '37,73,33,77,30,70'
        },
        {
            'keyword': 'น้ำ',
            'main_number': '2',
            'secondary_number': '8',
            'common_numbers': '28,82,22,88,20,80'
        },
        {
            'keyword': 'ต้นไม้',
            'main_number': '5',
            'secondary_number': '9',
            'common_numbers': '59,95,55,99,50,90'
        },
        {
            'keyword': 'รถ',
            'main_number': '1',
            'secondary_number': '6',
            'common_numbers': '16,61,11,66,10,60'
        },
        {
            'keyword': 'บ้าน',
            'main_number': '4',
            'secondary_number': '0',
            'common_numbers': '40,04,44,00,41,42'
        }
    ]
    
    for keyword_data in dream_keywords:
        if not DreamKeyword.objects.filter(keyword=keyword_data['keyword']).exists():
            DreamKeyword.objects.create(category=category, **keyword_data)
            print(f"Created dream keyword: {keyword_data['keyword']}")
        else:
            print(f"Dream keyword '{keyword_data['keyword']}' already exists")
    
    # สร้างข้อมูลการตีความความฝัน
    dream_data = [
        {
            'dream_text': 'ฝันเห็นงู',
            'interpretation': 'งูในความฝันหมายถึงการเปลี่ยนแปลงในชีวิต อาจเป็นเรื่องดีหรือไม่ดีขึ้นอยู่กับบริบท',
            'keywords_found': 'งู',
            'suggested_numbers': '37,73,33,77'
        },
        {
            'dream_text': 'ฝันเห็นน้ำ',
            'interpretation': 'น้ำในความฝันหมายถึงอารมณ์และความรู้สึก อาจเป็นสัญญาณของความสงบหรือความวุ่นวาย',
            'keywords_found': 'น้ำ',
            'suggested_numbers': '28,82,22,88'
        },
        {
            'dream_text': 'ฝันเห็นต้นไม้',
            'interpretation': 'ต้นไม้ในความฝันหมายถึงการเติบโตและความแข็งแกร่ง อาจเป็นสัญญาณของความสำเร็จ',
            'keywords_found': 'ต้นไม้',
            'suggested_numbers': '59,95,55,99'
        },
        {
            'dream_text': 'ฝันเห็นรถ',
            'interpretation': 'รถในความฝันหมายถึงการเดินทางในชีวิต อาจเป็นสัญญาณของการเปลี่ยนแปลงหรือการก้าวหน้า',
            'keywords_found': 'รถ',
            'suggested_numbers': '16,61,11,66'
        },
        {
            'dream_text': 'ฝันเห็นบ้าน',
            'interpretation': 'บ้านในความฝันหมายถึงความปลอดภัยและความมั่นคง อาจเป็นสัญญาณของความสุขในครอบครัว',
            'keywords_found': 'บ้าน',
            'suggested_numbers': '40,04,44,00'
        }
    ]
    
    for data in dream_data:
        if not DreamInterpretation.objects.filter(dream_text=data['dream_text']).exists():
            DreamInterpretation.objects.create(**data)
            print(f"Created dream interpretation: {data['dream_text']}")
        else:
            print(f"Dream interpretation for '{data['dream_text']}' already exists")

if __name__ == '__main__':
    create_sample_lotto_data()
    create_sample_dream_data()
    print("\nSample data creation completed!")

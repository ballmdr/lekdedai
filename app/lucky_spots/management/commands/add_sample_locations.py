from django.core.management.base import BaseCommand
from django.utils.text import slugify
from lucky_spots.models import Region, Province, LocationCategory, LuckyLocation


class Command(BaseCommand):
    help = 'Add sample lucky locations data'

    def handle(self, *args, **options):
        self.stdout.write('Adding sample lucky spots data...')
        
        # Create regions
        regions_data = [
            ('north', 'ภาคเหนือ'),
            ('central', 'ภาคกลาง'),
            ('northeast', 'ภาคอีสาน'),
            ('south', 'ภาคใต้'),
            ('east', 'ภาคตะวันออก'),
            ('west', 'ภาคตะวันตก'),
        ]
        
        for region_code, region_name in regions_data:
            region, created = Region.objects.get_or_create(name=region_code)
            if created:
                self.stdout.write(f'Created region: {region_name}')
        
        # Create provinces
        provinces_data = [
            # ภาคกลาง
            ('กรุงเทพมหานคร', 'central'),
            ('พระนครศรีอยุธยา', 'central'),
            ('ลพบุรี', 'central'),
            ('สิงห์บุรี', 'central'),
            ('อ่างทอง', 'central'),
            ('สุพรรณบุรี', 'central'),
            ('นครปฐม', 'central'),
            ('กาญจนบุรี', 'central'),
            ('ราชบุรี', 'central'),
            ('เพชรบุรี', 'central'),
            ('ประจวบคีรีขันธ์', 'central'),
            
            # ภาคเหนือ
            ('เชียงใหม่', 'north'),
            ('เชียงราย', 'north'),
            ('ลำปาง', 'north'),
            ('ลำพูน', 'north'),
            ('แม่ฮ่องสอน', 'north'),
            ('น่าน', 'north'),
            ('พะเยา', 'north'),
            ('แพร่', 'north'),
            ('สุโขทัย', 'north'),
            ('ตาก', 'north'),
            ('อุตรดิตถ์', 'north'),
            ('พิษณุโลก', 'north'),
            ('พิจิตร', 'north'),
            ('เพชรบูรณ์', 'north'),
            ('กำแพงเพชร', 'north'),
            ('นครสวรรค์', 'north'),
            ('อุทัยธานี', 'north'),
            
            # ภาคอีสาน
            ('นครราชสีมา', 'northeast'),
            ('บุรีรัมย์', 'northeast'),
            ('สุรินทร์', 'northeast'),
            ('ศีสะเกษ', 'northeast'),
            ('อุบลราชธานี', 'northeast'),
            ('ยโสธร', 'northeast'),
            ('ชัยภูมิ', 'northeast'),
            ('อำนาจเจริญ', 'northeast'),
            ('หนองบัวลำภู', 'northeast'),
            ('ขอนแก่น', 'northeast'),
            ('อุดรธานี', 'northeast'),
            ('เลย', 'northeast'),
            ('หนองคาย', 'northeast'),
            ('มหาสารคาม', 'northeast'),
            ('ร้อยเอ็ด', 'northeast'),
            ('กาฬสินธุ์', 'northeast'),
            ('สกลนคร', 'northeast'),
            ('นครพนม', 'northeast'),
            ('มุกดาหาร', 'northeast'),
            ('บึงกาฬ', 'northeast'),
            
            # ภาคใต้
            ('นครศรีธรรมราช', 'south'),
            ('กระบี่', 'south'),
            ('พังงา', 'south'),
            ('ภูเก็ต', 'south'),
            ('สุราษฎร์ธานี', 'south'),
            ('ระนอง', 'south'),
            ('ชุมพร', 'south'),
            ('สงขลา', 'south'),
            ('สตูล', 'south'),
            ('ตรัง', 'south'),
            ('พัทลุง', 'south'),
            ('ปัตตานี', 'south'),
            ('ยะลา', 'south'),
            ('นราธิวาส', 'south'),
        ]
        
        for province_name, region_code in provinces_data:
            region = Region.objects.get(name=region_code)
            province, created = Province.objects.get_or_create(
                name=province_name, 
                defaults={'region': region}
            )
            if created:
                self.stdout.write(f'Created province: {province_name}')
        
        # Create categories
        categories_data = [
            ('temple', 'วัด', '🏛️'),
            ('shrine', 'ศาลเจ้า', '⛩️'),
            ('sacred_tree', 'ต้นไม้ศักดิ์สิทธิ์', '🌳'),
            ('naga', 'พญานาค', '🐍'),
            ('mysterious', 'สิ่งลี้ลับ', '✨'),
            ('cave', 'ถ้ำ', '🕳️'),
            ('mountain', 'ภูเขา', '⛰️'),
            ('river', 'แม่น้ำ/ลำธาร', '🏞️'),
            ('other', 'อื่นๆ', '📍'),
        ]
        
        for category_code, category_name, icon in categories_data:
            category, created = LocationCategory.objects.get_or_create(
                name=category_code,
                defaults={'icon': icon}
            )
            if created:
                self.stdout.write(f'Created category: {category_name}')
        
        # Create sample locations
        sample_locations = [
            {
                'name': 'วัดพระแก้ว',
                'description': 'วัดพระแก้วหรือวัดพระศรีรัตนศาสดาราม เป็นพระอารามหลวงชั้นเอกที่ตั้งอยู่ในพระบรมมหาราชวัง เป็นที่ประดิษฐานพระพุทธมหามณีรัตนปฏิมากร หรือ พระแก้วมรกต ซึ่งเป็นพระพุทธรูปคู่บ้านคู่เมืองของไทย มีประวัติความเป็นมาอันยาวนาน และเป็นสถานที่ศักดิ์สิทธิ์ที่ผู้คนนิยมมาขอพรและเลขเด็ด',
                'latitude': 13.7540,
                'longitude': 100.4925,
                'address': 'พระนคร กรุงเทพมหานคร',
                'province': 'กรุงเทพมหานคร',
                'category': 'temple',
                'lucky_numbers': '007, 123, 456',
                'highlights': 'พระแก้วมรกต, พระอารามหลวงชั้นเอก, สถานที่ศักดิ์สิทธิ์ระดับชาติ',
            },
            {
                'name': 'ศาลเจ้าพ่อเสือ',
                'description': 'ศาลเจ้าพ่อเสือ เป็นศาลเจ้าที่มีชื่อเสียงในเรื่องการให้เลขเด็ด ตั้งอยู่ในจังหวัดกรุงเทพมหานคร ผู้คนเชื่อว่าเจ้าพ่อเสือมีความศักดิ์สิทธิ์ในการช่วยเหลือเรื่องโชคลาภและการเงิน หลายคนมาขอเลขเด็ดและได้ผลจริง',
                'latitude': 13.7307,
                'longitude': 100.5418,
                'address': 'วัฒนา กรุงเทพมหานคร',
                'province': 'กรุงเทพมหานคร',
                'category': 'shrine',
                'lucky_numbers': '168, 888, 999',
                'highlights': 'เลขเด็ดแม่น, เจ้าพ่อเสือ, โชคลาภการเงิน',
            },
            {
                'name': 'วัดไร่ขิง',
                'description': 'วัดไร่ขิง เป็นพระอารามหลวงที่มีประวัติศาสตร์ยาวนาน ตั้งอยู่ในจังหวัดนครปฐม เป็นที่ประดิษฐานองค์พระปฐมเจดีย์ ซึ่งเป็นพระเจดีย์ที่เก่าแก่ที่สุดในประเทศไทย นักท่องเที่ยวและผู้มีศรัทธามักมากราบไหว้ขอพรและเลขเด็ด',
                'latitude': 13.8199,
                'longitude': 100.0607,
                'address': 'เมืองนครปฐม นครปฐม',
                'province': 'นครปฐม',
                'category': 'temple',
                'lucky_numbers': '028, 108, 555',
                'highlights': 'พระปฐมเจดีย์, พระอารามหลวง, พระเจดีย์เก่าแก่ที่สุด',
            },
            {
                'name': 'ต้นโพธิ์ศักดิ์สิทธิ์ วัดมหาธาตุ',
                'description': 'ต้นโพธิ์ศักดิ์สิทธิ์ในวัดมหาธาตุ จังหวัดพระนครศรีอยุธยา เป็นต้นโพธิ์ที่มีอายุหลายร้อยปี มีเรื่องเล่าว่าเป็นต้นไม้ที่มีความศักดิ์สิทธิ์ ผู้คนเชื่อว่าการมากราบไหว้และขอพรจะได้รับความเป็นสิริมงคล',
                'latitude': 14.3587,
                'longitude': 100.5677,
                'address': 'พระนครศรีอยุธยา พระนครศรีอยุธยา',
                'province': 'พระนครศรีอยุธยา',
                'category': 'sacred_tree',
                'lucky_numbers': '789, 012, 345',
                'highlights': 'ต้นโพธิ์เก่าแก่, ความศักดิ์สิทธิ์, วัดมหาธาตุ',
            },
            {
                'name': 'ถ้ำพญานาค',
                'description': 'ถ้ำพญานาคที่มีตำนานและความเชื่อเรื่องพญานาค เป็นสถานที่ศักดิ์สิทธิ์ที่ผู้คนเชื่อว่ามีพญานาคคอยปกปักรักษา หลายคนมาขอพรและเลขเด็ด โดยเฉพาะในวันสำคัญทางพุทธศาสนา',
                'latitude': 17.4138,
                'longitude': 102.7877,
                'address': 'หนองคาย หนองคาย',
                'province': 'หนองคาย',
                'category': 'cave',
                'lucky_numbers': '369, 147, 258',
                'highlights': 'ถ้ำศักดิ์สิทธิ์, พญานาค, ตำนานท้องถิ่น',
            },
            {
                'name': 'ดอิสุเทพ',
                'description': 'วัดพระธาตุดอยสุเทพ เป็นพระอารามหลวงที่ตั้งอยู่บนดอยสุเทพ จังหวัดเชียงใหม่ เป็นสถานที่ศักดิ์สิทธิ์ที่สำคัญของภาคเหนือ ผู้มีศรัทธามักมากราบไหว้พระธาตุและขอพรเลขเด็ด',
                'latitude': 18.8048,
                'longitude': 98.9217,
                'address': 'สุเทพ เมืองเชียงใหม่ เชียงใหม่',
                'province': 'เชียงใหม่',
                'category': 'mountain',
                'lucky_numbers': '181, 518, 899',
                'highlights': 'พระธาตุดอยสุเทพ, ภูเขาศักดิ์สิทธิ์, วิวทิวทัศน์สวยงาม',
            },
        ]
        
        for location_data in sample_locations:
            province = Province.objects.get(name=location_data['province'])
            category = LocationCategory.objects.get(name=location_data['category'])
            
            # Generate unique slug
            base_slug = slugify(location_data['name'])
            slug = base_slug
            counter = 1
            while LuckyLocation.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            location, created = LuckyLocation.objects.get_or_create(
                name=location_data['name'],
                defaults={
                    'description': location_data['description'],
                    'latitude': location_data['latitude'],
                    'longitude': location_data['longitude'],
                    'address': location_data['address'],
                    'province': province,
                    'category': category,
                    'lucky_numbers': location_data['lucky_numbers'],
                    'highlights': location_data['highlights'],
                    'slug': slug,
                    'is_active': True,
                }
            )
            
            if created:
                self.stdout.write(f'Created location: {location_data["name"]}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully added sample lucky spots data!')
        )
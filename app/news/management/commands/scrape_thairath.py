from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from news.models import NewsArticle, NewsCategory, LuckyNumberHint
from dreams.models import DreamKeyword, DreamCategory
import requests
from bs4 import BeautifulSoup
import re
import json
import os
from urllib.parse import urljoin, urlparse
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from collections import Counter

class Command(BaseCommand):
    help = 'ดึงข่าวจากไทยรัฐและบันทึกลงฐานข้อมูล'
    
    def __init__(self):
        super().__init__()
        self.temp_files = []  # เก็บ temporary files เพื่อลบภายหลัง

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default='https://www.thairath.co.th/news/local/all-latest',
            help='URL ของหน้าเว็บไทยรัฐที่ต้องการดึงข่าว'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='จำนวนข่าวสูงสุดที่ต้องการดึง'
        )
        parser.add_argument(
            '--save',
            action='store_true',
            help='บันทึกข่าวลงฐานข้อมูล'
        )
        parser.add_argument(
            '--category',
            type=str,
            default='ข่าวทั่วไป',
            help='หมวดหมู่ข่าวที่จะบันทึก'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('เริ่มต้นดึงข่าวจากไทยรัฐ...')
        )
        
        url = options['url']
        limit = options['limit']
        save_to_db = options['save']
        category_name = options['category']
        
        # ดึงข่าว
        news_items = self.scrape_thairath(url, limit)
        
        if not news_items:
            self.stdout.write(
                self.style.ERROR('ไม่สามารถดึงข่าวได้')
            )
            return
        
        # แสดงผลลัพธ์
        self.stdout.write(
            self.style.SUCCESS(f'พบข่าวทั้งหมด: {len(news_items)} ข่าว')
        )
        
        for i, news in enumerate(news_items, 1):
            self.stdout.write(f"{i:2d}. {news['title']}")
            if news['numbers']:
                self.stdout.write(f"    เลขที่ได้: {', '.join(news['numbers'])}")
            if news.get('image_url'):
                self.stdout.write(f"    รูปภาพ: {news['image_url']}")
            self.stdout.write(f"    URL: {news['url']}")
            self.stdout.write("")
        
        # แสดงสรุปเลขที่พบ
        all_numbers = []
        for news in news_items:
            if news.get('numbers'):
                all_numbers.extend(news['numbers'])
        
        if all_numbers:
            number_counts = Counter(all_numbers)
            self.stdout.write("=" * 60)
            self.stdout.write("สรุปเลขที่พบในข่าว:")
            for number, count in number_counts.most_common():
                self.stdout.write(f"    เลข {number}: {count} ครั้ง")
            self.stdout.write("=" * 60)
        
        # บันทึกลงฐานข้อมูล
        if save_to_db:
            saved_count = self.save_news_to_db(news_items, category_name)
            self.stdout.write(
                self.style.SUCCESS(f'บันทึกลงฐานข้อมูลแล้ว: {saved_count} ข่าว')
            )
        
        # วิเคราะห์เลขเด็ด
        self.analyze_lucky_numbers(news_items)
        
        # บันทึกเป็น JSON
        output_file = f"thairath_news_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(news_items, f, ensure_ascii=False, indent=2)
        
        self.stdout.write(
            self.style.SUCCESS(f'บันทึกผลลัพธ์ลงไฟล์: {output_file}')
        )
        
        # ลบ temporary files
        self.cleanup_temp_files()
    
    def cleanup_temp_files(self):
        """ลบ temporary files ที่สร้างขึ้น"""
        for temp_file_path in self.temp_files:
            try:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    self.stdout.write(f'ลบ temporary file: {temp_file_path}')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'ไม่สามารถลบ temporary file ได้: {e}')
                )

    def scrape_thairath(self, url, limit):
        """ดึงข่าวจากไทยรัฐ"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = []
            
            # ลองหา headline ข่าวหลัก
            headline_selectors = [
                'h3.css-1xyd7f1',
                'h3',
                '.css-1xyd7f1',
                'a[href*="/news/"]'
            ]
            
            for selector in headline_selectors:
                elements = soup.select(selector)
                
                if elements:
                    for elem in elements:
                        if len(news_items) >= limit:
                            break
                            
                        try:
                            # หา link และ title
                            if elem.name == 'a':
                                link_elem = elem
                            else:
                                link_elem = elem.find('a')
                            
                            if link_elem:
                                title = link_elem.get_text(strip=True)
                                href = link_elem.get('href')
                                
                                if title and href and len(title) > 10:
                                    # สร้าง URL เต็ม
                                    if href.startswith('/'):
                                        full_url = f"https://www.thairath.co.th{href}"
                                    elif href.startswith('http'):
                                        full_url = href
                                    else:
                                        full_url = f"https://www.thairath.co.th/{href}"
                                    
                                    # หาเลขจากหัวข้อ
                                    numbers = re.findall(r'\b\d{2,3}\b', title)
                                    
                                    # หารูปภาพจาก element นี้
                                    image_url = self.extract_image_url(elem)
                                    
                                    # ถ้าไม่พบรูปภาพ ให้ลองดึงจากรายละเอียดข่าว
                                    if not image_url:
                                        image_url = self.get_image_from_news_detail(full_url)
                                    
                                    news_item = {
                                        'title': title,
                                        'url': full_url,
                                        'numbers': numbers,
                                        'image_url': image_url,
                                        'source': 'thairath',
                                        'scraped_at': timezone.now().isoformat()
                                    }
                                    
                                    # ตรวจสอบว่าไม่ซ้ำ
                                    if not any(item['url'] == full_url for item in news_items):
                                        news_items.append(news_item)
                        
                        except Exception as e:
                            continue
                    
                    if news_items:
                        break
            
            return news_items
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'เกิดข้อผิดพลาด: {e}')
            )
            return []
    
    def extract_image_url(self, element):
        """ดึง URL รูปภาพจาก element"""
        try:
            # ลองหารูปภาพในหลายรูปแบบ
            image_selectors = [
                'img',
                '.css-1xyd7f1 img',
                '.news-image img',
                '.article-image img',
                'picture img'
            ]
            
            for selector in image_selectors:
                img_elem = element.select_one(selector)
                if img_elem:
                    src = img_elem.get('src') or img_elem.get('data-src')
                    if src:
                        # สร้าง URL เต็ม
                        if src.startswith('//'):
                            return 'https:' + src
                        elif src.startswith('/'):
                            return 'https://www.thairath.co.th' + src
                        elif src.startswith('http'):
                            return src
                        else:
                            return 'https://www.thairath.co.th/' + src
            
            # ลองหาจาก parent elements
            parent = element.parent
            if parent:
                for selector in image_selectors:
                    img_elem = parent.select_one(selector)
                    if img_elem:
                        src = img_elem.get('src') or img_elem.get('data-src')
                        if src:
                            if src.startswith('//'):
                                return 'https:' + src
                            elif src.startswith('/'):
                                return 'https://www.thairath.co.th' + src
                            elif src.startswith('http'):
                                return src
                            else:
                                return 'https://www.thairath.co.th/' + src
            
            return None
            
        except Exception as e:
            return None
    
    def download_image(self, image_url, title):
        """ดาวน์โหลดรูปภาพและบันทึกลง Django"""
        try:
            if not image_url:
                return None
                
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # ดาวน์โหลดรูปภาพ
            response = requests.get(image_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # สร้างชื่อไฟล์
            parsed_url = urlparse(image_url)
            file_extension = os.path.splitext(parsed_url.path)[1]
            if not file_extension:
                file_extension = '.jpg'  # default extension
            
            # สร้างชื่อไฟล์จากหัวข้อข่าว
            safe_title = re.sub(r'[^\w\s-]', '', title.lower())
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            safe_title = safe_title[:50]  # จำกัดความยาว
            
            filename = f"{safe_title}{file_extension}"
            
            # สร้าง temporary file และเก็บไว้ในตัวแปร
            temp_file = NamedTemporaryFile(delete=False, suffix=file_extension)
            temp_file.write(response.content)
            temp_file.flush()
            temp_file.seek(0)  # ย้าย pointer ไปที่จุดเริ่มต้น
            
            # เก็บ temporary file ไว้เพื่อลบภายหลัง
            self.temp_files.append(temp_file.name)
            
            # สร้าง Django File object
            django_file = File(temp_file, name=filename)
            
            return django_file
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'ไม่สามารถดาวน์โหลดรูปภาพได้: {e}')
            )
            return None
    
    def get_image_from_news_detail(self, news_url):
        """ดึงรูปภาพจากรายละเอียดข่าว"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(news_url, headers=headers, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # ลองหารูปภาพในหลายรูปแบบ
            image_selectors = [
                '.css-1shj5k7 img',
                '.article-content img',
                '.content img',
                '.news-content img',
                'img[data-src]',
                'img[src*="thairath"]'
            ]
            
            for selector in image_selectors:
                img_elem = soup.select_one(selector)
                if img_elem:
                    src = img_elem.get('src') or img_elem.get('data-src')
                    if src:
                        # สร้าง URL เต็ม
                        if src.startswith('//'):
                            return 'https:' + src
                        elif src.startswith('/'):
                            return 'https://www.thairath.co.th' + src
                        elif src.startswith('http'):
                            return src
                        else:
                            return 'https://www.thairath.co.th/' + src
            
            return None
            
        except Exception as e:
            return None
    
    def save_news_to_db(self, news_items, category_name):
        """บันทึกข่าวลงฐานข้อมูล"""
        # หาหรือสร้างหมวดหมู่
        category, created = NewsCategory.objects.get_or_create(
            name=category_name,
            defaults={
                'slug': self.generate_slug(category_name),
                'description': f'ข่าวที่ดึงจากไทยรัฐ - {timezone.now().strftime("%Y-%m-%d")}'
            }
        )
        
        if created:
            self.stdout.write(f'สร้างหมวดหมู่ใหม่: {category_name}')
        
        # หา user admin
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.first()
        
        saved_count = 0
        
        for news_item in news_items:
            try:
                # ตรวจสอบว่าไม่ซ้ำ
                if not NewsArticle.objects.filter(source_url=news_item['url']).exists():
                    # สร้าง slug จากหัวข้อ
                    slug = self.generate_slug(news_item['title'])
                    
                    # ดาวน์โหลดรูปภาพ
                    featured_image = None
                    if news_item.get('image_url'):
                        self.stdout.write(f'กำลังดาวน์โหลดรูปภาพ: {news_item["image_url"]}')
                        featured_image = self.download_image(news_item['image_url'], news_item['title'])
                    
                    # สร้างข่าวใหม่
                    article = NewsArticle.objects.create(
                        title=news_item['title'],
                        slug=slug,
                        category=category,
                        author=admin_user,
                        intro=news_item['title'][:200] + "...",
                        content=f"ข่าวจาก: {news_item['url']}\n\n{news_item['title']}",
                        extracted_numbers=','.join(news_item['numbers']) if news_item['numbers'] else '',
                        source_url=news_item['url'],
                        featured_image=featured_image,
                        status='published',
                        published_date=timezone.now(),
                        meta_description=news_item['title'][:160]
                    )
                    
                    saved_count += 1
                    self.stdout.write(f'บันทึกข่าว: {article.title[:50]}...')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'เกิดข้อผิดพลาดในการบันทึกข่าว: {e}')
                )
                continue
        
        return saved_count
    
    def analyze_lucky_numbers(self, news_items):
        """วิเคราะห์เลขเด็ดจากข่าวที่ดึงมา ใช้ระบบเดียวกับความฝัน"""
        self.stdout.write(
            self.style.SUCCESS('เริ่มวิเคราะห์เลขเด็ดจากข่าว...')
        )
        
        all_numbers = []
        all_keywords_info = []
        
        # วิเคราะห์จากหัวข้อข่าว
        for news in news_items:
            # เลขจากหัวข้อ
            if news.get('numbers'):
                all_numbers.extend(news['numbers'])
            
            # วิเคราะห์จากคำสำคัญในหัวข้อ
            title_numbers = self.analyze_title_for_numbers(news['title'])
            if title_numbers:
                all_numbers.extend(title_numbers)
            
            # เก็บข้อมูล keywords ที่พบ
            if hasattr(self, 'news_keywords_info'):
                all_keywords_info.extend(self.news_keywords_info)
        
        # รวมเลขทั้งหมด
        if not all_numbers:
            self.stdout.write(
                self.style.WARNING('ไม่พบเลขที่สามารถวิเคราะห์ได้')
            )
            return
        
        # ลบเลขซ้ำและเรียงลำดับ
        all_numbers = list(dict.fromkeys(all_numbers))
        
        # แสดงผลการวิเคราะห์แบบละเอียด
        self.display_enhanced_analysis(all_keywords_info, all_numbers, news_items)
        
        # สร้างเลขเด็ดจากความถี่
        lucky_numbers = self.create_lucky_numbers_from_frequency(all_numbers)
        
        # บันทึกเลขเด็ดลงฐานข้อมูล
        self.save_lucky_numbers(lucky_numbers, news_items)
        
        return lucky_numbers
    
    def display_enhanced_analysis(self, keywords_info, numbers, news_items):
        """แสดงผลการวิเคราะห์แบบละเอียด"""
        self.stdout.write("=" * 60)
        self.stdout.write("การวิเคราะห์เลขเด็ดจากข่าว")
        self.stdout.write("=" * 60)
        
        if keywords_info:
            self.stdout.write(f"พบคำสำคัญ: {len(keywords_info)} คำ")
            
            # จัดกลุ่มตาม category
            categories = {}
            for info in keywords_info:
                cat = info['category']
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(info)
            
            for category, items in categories.items():
                self.stdout.write(f"\n{category}:")
                for item in items[:3]:  # แสดงไม่เกิน 3 รายการต่อหมวด
                    self.stdout.write(f"  • {item['keyword']} - เลขเด่น: {item['main_number']}, เลขรอง: {item['secondary_number']}")
                    self.stdout.write(f"    มักตีเป็น: {', '.join(item['common_numbers'][:3])}")
        
        if numbers:
            self.stdout.write(f"\nเลขที่วิเคราะห์ได้: {len(numbers)} เลข")
            # แบ่งเลขเป็นกลุ่มๆ
            numbers_groups = [numbers[i:i+4] for i in range(0, len(numbers), 4)]
            for i, group in enumerate(numbers_groups[:3], 1):
                self.stdout.write(f"ชุดที่ {i}: {', '.join(group)}")
        
        self.stdout.write("=" * 60)
    
    def create_lucky_numbers_from_frequency(self, numbers):
        """สร้างเลขเด็ดจากความถี่"""
        # นับความถี่ของเลข
        number_counts = Counter(numbers)
        
        # เรียงลำดับตามความถี่
        sorted_numbers = sorted(number_counts.items(), key=lambda x: x[1], reverse=True)
        
        # เลือกเลขเด็ด (เลขที่ปรากฏบ่อย)
        lucky_numbers = []
        for number, count in sorted_numbers[:10]:  # เอา 10 เลขแรก
            if count >= 1:  # เลขที่ปรากฏอย่างน้อย 1 ครั้ง
                lucky_numbers.append({
                    'number': number,
                    'frequency': count,
                    'confidence': min(50 + (count * 10), 95)  # ความน่าเชื่อถือ
                })
        
        # แสดงผลการวิเคราะห์
        self.stdout.write(
            self.style.SUCCESS(f'พบเลขเด็ดทั้งหมด: {len(lucky_numbers)} เลข')
        )
        
        for i, lucky in enumerate(lucky_numbers, 1):
            self.stdout.write(
                f"{i:2d}. เลข {lucky['number']} (ความถี่: {lucky['frequency']}, "
                f"ความน่าเชื่อถือ: {lucky['confidence']}%)"
            )
        
        return lucky_numbers
    
    def analyze_title_for_numbers(self, title):
        """วิเคราะห์เลขจากคำสำคัญในหัวข้อข่าว ใช้ระบบเดียวกับความฝัน"""
        numbers = []
        found_keywords = []
        matched_keywords_info = []
        
        title_lower = title.lower()
        
        # ค้นหา keywords ที่ตรงกับในฐานข้อมูล DreamKeyword
        # เรียงลำดับตามความยาวของ keyword (ยาวที่สุดก่อน) เพื่อจับคำที่เฉพาะเจาะจงมากกว่า
        all_keywords = sorted(DreamKeyword.objects.all(), key=lambda x: len(x.keyword), reverse=True)
        
        matched_positions = []  # เก็บตำแหน่งที่จับได้แล้ว เพื่อไม่ให้ซ้ำ
        
        for keyword_obj in all_keywords:
            keyword = keyword_obj.keyword.lower()
            
            # ค้นหาคำที่ตรงกันทั้งคำ และไม่ซ้อนทับกับคำที่จับแล้ว
            if keyword in title_lower:
                # หาตำแหน่งทั้งหมดที่พบคำนี้
                start_idx = 0
                while True:
                    idx = title_lower.find(keyword, start_idx)
                    if idx == -1:
                        break
                    
                    start, end = idx, idx + len(keyword)
                    
                    # ตรวจสอบว่าเป็นคำสมบูรณ์
                    is_valid_match = True
                    
                    # ตรวจสอบว่าตำแหน่งนี้ถูกจับแล้วหรือไม่
                    overlap = any(start < pos_end and end > pos_start for pos_start, pos_end in matched_positions)
                    
                    if not overlap and is_valid_match:
                        matched_positions.append((start, end))
                        found_keywords.append(keyword_obj.keyword)
                        
                        # เก็บข้อมูลเลขเด่น/เลขรอง เฉพาะคำที่พบ
                        matched_keywords_info.append({
                            'keyword': keyword_obj.keyword,
                            'category': keyword_obj.category.name,
                            'main_number': keyword_obj.main_number,
                            'secondary_number': keyword_obj.secondary_number,
                            'common_numbers': keyword_obj.get_numbers_list()
                        })
                        
                        # เพิ่มเลขที่มักตี
                        numbers.extend(keyword_obj.get_numbers_list())
                        break  # เจอแล้วครั้งแรกก็พอ
                    
                    start_idx = idx + 1
        
        # ลบเลขซ้ำและเรียงลำดับ
        numbers = list(dict.fromkeys(numbers))
        
        # เก็บข้อมูลสำหรับการวิเคราะห์เพิ่มเติม
        self.news_keywords_info = matched_keywords_info
        
        return numbers
    
    def save_lucky_numbers(self, lucky_numbers, news_items):
        """บันทึกเลขเด็ดลงฐานข้อมูล"""
        if not lucky_numbers:
            return
        
        try:
            # สร้างหมวดหมู่เลขเด็ด
            category_name = "เลขเด็ดจากข่าวไทยรัฐ"
            category, created = NewsCategory.objects.get_or_create(
                name=category_name,
                defaults={
                    'slug': self.generate_slug(category_name),
                    'description': f'เลขเด็ดที่วิเคราะห์ได้จากข่าวไทยรัฐ - {timezone.now().strftime("%Y-%m-%d")}'
                }
            )
            
            # หา user admin
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.first()
            
            saved_count = 0
            
            for lucky in lucky_numbers:
                # สร้างชื่อแหล่งที่มา
                source_name = f"ข่าวไทยรัฐ - เลข {lucky['number']}"
                
                # ตรวจสอบว่าไม่ซ้ำ
                if not LuckyNumberHint.objects.filter(
                    source_name=source_name,
                    hint_date=timezone.now().date()
                ).exists():
                    
                    # สร้างเลขเด็ดใหม่
                    lucky_hint = LuckyNumberHint.objects.create(
                        source_type='other',
                        source_name=source_name,
                        location='ไทยรัฐ',
                        lucky_numbers=lucky['number'],
                        reason=f"เลขที่วิเคราะห์ได้จากข่าวไทยรัฐ (ความถี่: {lucky['frequency']})",
                        reliability_score=lucky['confidence'],
                        hint_date=timezone.now().date(),
                        for_draw_date=timezone.now().date() + timezone.timedelta(days=1)
                    )
                    
                    saved_count += 1
                    self.stdout.write(
                        f'บันทึกเลขเด็ด: {lucky["number"]} (ความน่าเชื่อถือ: {lucky["confidence"]}%)'
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'บันทึกเลขเด็ดลงฐานข้อมูลแล้ว: {saved_count} เลข')
            )
            
            # แสดงสรุปการวิเคราะห์
            self.display_analysis_summary(lucky_numbers, news_items)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'เกิดข้อผิดพลาดในการบันทึกเลขเด็ด: {e}')
            )
    
    def display_analysis_summary(self, lucky_numbers, news_items):
        """แสดงสรุปการวิเคราะห์"""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("สรุปการวิเคราะห์เลขเด็ดจากข่าว")
        self.stdout.write("=" * 60)
        
        if lucky_numbers:
            best_number = lucky_numbers[0]
            self.stdout.write(
                self.style.SUCCESS(f"🎯 เลขเด็ดที่แนะนำ: {best_number['number']}")
            )
            self.stdout.write(f"   ความถี่: {best_number['frequency']} ครั้ง")
            self.stdout.write(f"   ความน่าเชื่อถือ: {best_number['confidence']}%")
            
            if len(lucky_numbers) > 1:
                self.stdout.write(f"\n🔢 เลขเด็ดรอง:")
                for lucky in lucky_numbers[1:4]:  # แสดง 3 เลขรอง
                    self.stdout.write(f"   เลข {lucky['number']} (ความถี่: {lucky['frequency']})")
        
        self.stdout.write(f"\n📰 จำนวนข่าวที่วิเคราะห์: {len(news_items)} ข่าว")
        self.stdout.write("=" * 60)

    def generate_slug(self, text):
        """สร้าง slug จากข้อความ"""
        # ลบอักขระพิเศษและแปลงเป็นตัวพิมพ์เล็ก
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        slug = slug.strip('-')
        
        # จำกัดความยาว
        if len(slug) > 50:
            slug = slug[:50]
        
        return slug

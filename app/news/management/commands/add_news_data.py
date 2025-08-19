from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from news.models import NewsCategory, NewsArticle, LuckyNumberHint
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Add sample news data'
    
    def handle(self, *args, **options):
        # สร้าง Categories
        categories = {
            'general': NewsCategory.objects.get_or_create(
                name='ข่าวทั่วไป',
                slug='general',
                description='ข่าวทั่วไปที่อาจมีเลขเด็ด'
            )[0],
            'temple': NewsCategory.objects.get_or_create(
                name='ข่าววัด/ศาลเจ้า',
                slug='temple',
                description='ข่าวจากวัดและศาลเจ้าต่างๆ'
            )[0],
            'accident': NewsCategory.objects.get_or_create(
                name='ข่าวอุบัติเหตุ',
                slug='accident',
                description='ข่าวอุบัติเหตุที่มีเลขน่าสนใจ'
            )[0],
            'natural': NewsCategory.objects.get_or_create(
                name='ปรากฏการณ์ธรรมชาติ',
                slug='natural',
                description='ข่าวปรากฏการณ์ธรรมชาติ'
            )[0],
        }
        
        self.stdout.write('Created categories')
        
        # ดึงหรือสร้าง user สำหรับทดสอบโดยใช้ get_or_create
        self.stdout.write('Finding or creating author user "newsadmin"...')
        admin_user, created = User.objects.get_or_create(
            username='newsadmin',
            defaults={
                'email': 'news@lekdedai.com',
                'is_staff': True,
                'is_superuser': False, # ตั้งเป็น False หรือ True ตามต้องการ
            }
        )

        if created:
            admin_user.set_password('newspass123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Successfully created new user "newsadmin"'))
        else:
            self.stdout.write('Using existing user "newsadmin"')
        # --- จบส่วนที่แก้ไข ---
        
        # สร้างข่าวตัวอย่าง
        sample_news = [
            {
                'title': 'พบเลขเด็ดที่ต้นโพธิ์ใหญ่ วัดดังกลางกรุง',
                'category': categories['temple'],
                'intro': 'ชาวบ้านแห่ไปดูต้นโพธิ์ใหญ่หลังพบเลขประหลาดปรากฏบนลำต้น',
                'content': '''ที่วัดดังแห่งหนึ่งกลางกรุงเทพฯ เกิดปรากฏการณ์ประหลาดเมื่อชาวบ้านพบตัวเลข 23 และ 89 
                ปรากฏบนลำต้นโพธิ์ใหญ่อายุกว่า 100 ปี ทำให้มีผู้คนแห่ไปดูและขอเลขเด็ดกันเป็นจำนวนมาก
                
                พระอาจารย์ของวัดเล่าว่า ต้นโพธิ์ต้นนี้มีความศักดิ์สิทธิ์มาช้านาน มักจะมีสิ่งมหัศจรรย์เกิดขึ้นบ่อยครั้ง 
                โดยเฉพาะในช่วงใกล้วันหวยออก จะมีรอยแตกบนลำต้นที่มีลักษณะคล้ายตัวเลข
                
                นอกจากเลข 23 และ 89 แล้ว ยังมีผู้พบเห็นเลข 45, 67 และ 12 ปรากฏในบริเวณใกล้เคียง
                ซึ่งหลายคนเชื่อว่าเป็นเลขมงคลที่ควรนำไปเสี่ยงโชค
                
                ทางวัดได้จัดเจ้าหน้าที่ดูแลความเรียบร้อย เนื่องจากมีผู้คนมาขอเลขเป็นจำนวนมาก
                และขอให้ทุกคนมีสติในการเสี่ยงโชค ไม่ควรใช้เงินเกินตัว''',
                'extracted_numbers': '23, 89, 45, 67, 12',
                'confidence_score': 85,
                'status': 'published',
                'published_date': timezone.now() - timedelta(days=1),
            },
            {
                'title': 'รถทะเบียน กข-2345 พุ่งชนต้นไม้ริมทาง คนขับรอดปาฏิหาริย์',
                'category': categories['accident'],
                'intro': 'อุบัติเหตุรถเก๋งพุ่งชนต้นไม้ใหญ่ คนขับรอดชีวิตอย่างน่าอัศจรรย์',
                'content': '''เมื่อเวลา 13.45 น. วันนี้ เกิดอุบัติเหตุรถเก๋งสีขาว ทะเบียน กข-2345 
                เสียหลักพุ่งชนต้นไม้ใหญ่ริมถนนสาย 304 บริเวณกม.ที่ 78 
                
                นายสมชาย (นามสมมติ) อายุ 45 ปี คนขับรถ เล่าว่า ขณะขับรถมาด้วยความเร็ว 
                ประมาณ 80 กิโลเมตรต่อชั่วโมง จู่ๆ มีสุนัขวิ่งตัดหน้า จึงหักหลบ ทำให้รถเสียหลักพุ่งชนต้นไม้
                
                สิ่งมหัศจรรย์คือ แม้รถจะพังยับเยิน แต่ตัวเขากลับไม่ได้รับบาดเจ็บแม้แต่น้อย 
                มีเพียงรอยขีดข่วนเล็กน้อย ทำให้ผู้พบเห็นต่างพากันทึ่ง
                
                ที่น่าสนใจคือ เลขทะเบียนรถ 2345 และเลขกิโลเมตรที่เกิดเหตุ 78 
                รวมถึงเวลาที่เกิดเหตุ 13.45 น. ทำให้หลายคนคิดว่าอาจเป็นเลขนำโชค
                
                ตำรวจได้ตรวจสอบที่เกิดเหตุและพบว่าไม่มีสิ่งผิดปกติ คาดว่าเป็นอุบัติเหตุจริง''',
                'extracted_numbers': '23, 45, 78, 13, 80, 04',
                'confidence_score': 75,
                'status': 'published',
                'published_date': timezone.now() - timedelta(days=2),
            },
            {
                'title': 'ฝนดาวตกปรากฏทั่วภาคเหนือ ชาวบ้านเห็นเลขในท้องฟ้า',
                'category': categories['natural'],
                'intro': 'ปรากฏการณ์ฝนดาวตกครั้งใหญ่ ชาวบ้านอ้างเห็นเลขลอยบนฟ้า',
                'content': '''เมื่อคืนที่ผ่านมา เกิดปรากฏการณ์ฝนดาวตกขนาดใหญ่ปรากฏให้เห็นทั่วภาคเหนือ 
                โดยเฉพาะในพื้นที่จังหวัดเชียงใหม่ เชียงราย และลำปาง
                
                นักดาราศาสตร์อธิบายว่า เป็นฝนดาวตกจากกลุ่มดาวหมีใหญ่ ที่เกิดขึ้นเป็นประจำทุกปี 
                แต่ปีนี้มีความหนาแน่นมากเป็นพิเศษ สามารถมองเห็นได้ด้วยตาเปล่านับร้อยดวง
                
                สิ่งที่น่าสนใจคือ มีชาวบ้านหลายคนรายงานว่า เห็นแสงดาวตกเรียงตัวเป็นรูปเลข 
                โดยเลขที่มีคนเห็นมากที่สุดคือ 17, 71, 28 และ 82
                
                นางสาวมาลี ชาวเชียงใหม่ กล่าวว่า "ดิฉันเห็นชัดเจนมาก แสงดาวตกเรียงเป็นเลข 17 
                อยู่บนฟ้านานหลายวินาที ถ่ายรูปไว้ด้วย แต่ในรูปไม่ชัดเท่าที่เห็นด้วยตา"
                
                แม้นักวิทยาศาสตร์จะอธิบายว่าเป็นเพียงความบังเอิญ แต่ชาวบ้านหลายคนเชื่อว่า
                เป็นลางบอกเหตุ และได้นำเลขดังกล่าวไปเสี่ยงโชค''',
                'extracted_numbers': '17, 71, 28, 82',
                'confidence_score': 60,
                'status': 'published',
                'published_date': timezone.now() - timedelta(days=3),
            },
            {
                'title': 'เจ้าของบ้านเลขที่ 999 ถูกหวยรางวัลที่ 1 สองงวดติด',
                'category': categories['general'],
                'intro': 'ความมหัศจรรย์ของเลขบ้าน เจ้าของถูกรางวัลใหญ่ 2 งวดซ้อน',
                'content': '''นายวิชัย (นามสมมติ) เจ้าของบ้านเลขที่ 999 หมู่ 7 ต.ในเมือง 
                สร้างความฮือฮาให้กับชาวบ้านในละแวกนั้น หลังถูกหวยรางวัลที่ 1 สองงวดติดต่อกัน
                
                เจ้าตัวเล่าว่า เขาซื้อหวยมาตลอด 20 ปี แต่ไม่เคยถูกเลย จนมาเดือนที่แล้ว 
                ฝันเห็นเลข 99 ชัดเจน จึงซื้อตามและถูกรางวัลที่ 1 ได้เงิน 6 ล้านบาท
                
                งวดต่อมา เขาฝันเห็นบ้านของตัวเองมีแสงสว่างรอบบ้าน พอตื่นมาจึงนึกถึงเลขบ้าน 999 
                และหมู่ที่ 7 จึงซื้อเลข 99, 97, 79 และถูกรางวัลที่ 1 อีกครั้ง
                
                ปัจจุบันมีคนแห่มาขอเลขที่หน้าบ้านกันเป็นจำนวนมาก บางคนถึงกับขอซื้อบ้านหลังนี้
                ในราคาที่สูงกว่าราคาตลาดหลายเท่า แต่เจ้าของไม่ขาย
                
                เลขที่น่าสนใจจากเรื่องนี้ ได้แก่ 99, 97, 79, 07 และ 20 (จากระยะเวลา 20 ปี)''',
                'extracted_numbers': '99, 97, 79, 07, 20',
                'confidence_score': 90,
                'status': 'published',
                'published_date': timezone.now() - timedelta(days=4),
            },
            {
                'title': 'พระเครื่องศักดิ์สิทธิ์ราคา 50 บาท ช่วยให้รอดจากอุบัติเหตุ',
                'category': categories['temple'],
                'intro': 'หนุ่มรอดชีวิตจากอุบัติเหตุรถชนรถ อ้างพระเครื่องช่วยไว้',
                'content': '''นายอนุชา อายุ 32 ปี รอดชีวิตอย่างปาฏิหาริย์จากอุบัติเหตุรถชนกันอย่างรุนแรง
                บนถนนมิตรภาพ กม.150 เมื่อวันที่ 15 ของเดือน
                
                เจ้าตัวเล่าว่า ขณะขับรถกลับบ้าน มีรถบรรทุกเสียหลักพุ่งข้ามเลนมาชนอย่างจัง 
                รถพังยับ แต่ตัวเขากลับมีแค่รอยถลอกเล็กน้อย
                
                "ผมเชื่อว่าพระเครื่องที่ซื้อมาเมื่อสัปดาห์ก่อนช่วยไว้ ตอนนั้นไปทำบุญที่วัด 
                เห็นพระรูปหนึ่งขายพระเครื่องราคา 50 บาท บอกว่าได้มาจากกรุเก่า เลขที่ 32"
                
                ที่น่าแปลกคือ เลขทะเบียนรถที่ชน คือ 1150 พอดีกับเลข กม. 150 
                และเกิดเหตุวันที่ 15 ทำให้หลายคนคิดว่าเลข 15, 50, 32 อาจเป็นเลขนำโชค
                
                ปัจจุบันนายอนุชายังคงเก็บพระเครื่ององค์นั้นไว้เป็นขวัญใจ''',
                'extracted_numbers': '50, 32, 15, 11',
                'confidence_score': 70,
                'status': 'published',
                'published_date': timezone.now() - timedelta(days=5),
            },
        ]
        
        # สร้างบทความข่าว
        for data in sample_news:
            article = NewsArticle.objects.create(
                title=data['title'],
                slug=None,  # ให้ auto-generate
                category=data['category'],
                author=admin_user,
                intro=data['intro'],
                content=data['content'],
                extracted_numbers=data['extracted_numbers'],
                confidence_score=data['confidence_score'],
                status=data['status'],
                published_date=data['published_date'],
                views=random.randint(100, 1000)
            )
            self.stdout.write(f'Created article: {article.title}')
        
        # สร้าง Lucky Number Hints
        lucky_hints_data = [
            {
                'source_type': 'temple',
                'source_name': 'วัดพระแก้ว',
                'location': 'กรุงเทพมหานคร',
                'lucky_numbers': '13, 31, 68, 86',
                'reason': 'เลขจากใบเซียมซีที่วัด ได้ใบที่ 13 มีเลขมงคลตามนี้',
                'reliability_score': 75,
                'for_draw_date': timezone.now().date() + timedelta(days=1),
            },
            {
                'source_type': 'tree',
                'source_name': 'ต้นตะเคียนยักษ์ อายุ 200 ปี',
                'location': 'จ.นครราชสีมา',
                'lucky_numbers': '47, 74, 29, 92',
                'reason': 'ชาวบ้านฝันเห็นเลขหลังไปกราบไหว้ต้นตะเคียน',
                'reliability_score': 65,
                'for_draw_date': timezone.now().date() + timedelta(days=1),
            },
            {
                'source_type': 'natural',
                'source_name': 'รุ้งกินน้ำ 2 ชั้น',
                'location': 'จ.เชียงใหม่',
                'lucky_numbers': '22, 77, 88',
                'reason': 'ปรากฏรุ้งกินน้ำ 2 ชั้นเป็นเวลา 22 นาที',
                'reliability_score': 55,
                'for_draw_date': timezone.now().date() + timedelta(days=1),
            },
            {
                'source_type': 'accident',
                'source_name': 'รถไฟชนรถบัสไม่มีผู้เสียชีวิต',
                'location': 'จ.ลพบุรี',
                'lucky_numbers': '00, 18, 81',
                'reason': 'รถไฟขบวนที่ 181 ชนรถบัส ไม่มีผู้เสียชีวิต (00)',
                'reliability_score': 60,
                'for_draw_date': timezone.now().date() + timedelta(days=1),
            },
            {
                'source_type': 'dream',
                'source_name': 'คุณยายวัย 88 ปี',
                'location': 'จ.สุพรรณบุรี',
                'lucky_numbers': '88, 38, 83',
                'reason': 'คุณยายอายุ 88 ฝันเห็นพญานาคทองคำ มี 38 เกล็ด',
                'reliability_score': 80,
                'for_draw_date': timezone.now().date() + timedelta(days=1),
            },
        ]
        
        # สร้าง Lucky Hints
        for hint_data in lucky_hints_data:
            hint = LuckyNumberHint.objects.create(**hint_data)
            self.stdout.write(f'Created lucky hint: {hint.source_name}')
        
        # เชื่อม Lucky Hints กับบทความข่าว
        articles = NewsArticle.objects.all()
        hints = LuckyNumberHint.objects.all()
        
        for i, hint in enumerate(hints):
            if i < len(articles):
                hint.related_article = articles[i]
                hint.save()
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully created {len(sample_news)} articles and {len(lucky_hints_data)} lucky hints'
        ))
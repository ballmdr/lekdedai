# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from news.analyzer_switcher import AnalyzerSwitcher

class Command(BaseCommand):
    help = 'ทดสอบ AI analyzers ทั้งหมดที่มี (Groq และ Gemini)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--analyzer',
            type=str,
            choices=['auto', 'groq', 'gemini'],
            default='auto',
            help='เลือกใช้ analyzer ใด (default: auto)'
        )

    def handle(self, *args, **options):
        analyzer_type = options['analyzer']
        
        self.stdout.write(
            self.style.SUCCESS(f'🧪 ทดสอบ AI Analyzers (โหมด: {analyzer_type})')
        )
        
        # สร้าง switcher
        switcher = AnalyzerSwitcher(preferred_analyzer=analyzer_type)
        
        # แสดงสถานะ analyzers ที่มี
        available = switcher.get_available_analyzers()
        self.stdout.write('\n📋 สถานะ AI Analyzers:')
        for name, status in available.items():
            status_icon = '✅' if status else '❌'
            self.stdout.write(f'  {status_icon} {name.upper()}: {"ใช้งานได้" if status else "ไม่ใช้งานได้"}')
        
        # ข้อมูลทดสอบ
        test_cases = [
            {
                'title': 'ทักษิณ ชินวัตร อายุ 74 ปี เดินทางด้วยรถทะเบียน พร 195',
                'content': 'อดีตนายกรัฐมนตรี ทักษิณ ชินวัตร อายุ 74 ปี เดินทางด้วยรถทะเบียน พร 195 เวลา 09.09 น. มาถึงศาลฎีกา คดีชั้น 14'
            },
            {
                'title': 'รถชนเสาไฟฟ้า ดับ 3 ศพ บาดเจ็บ 5 คน',
                'content': 'เหตุเกิดเมื่อเวลา 23.30 น. รถยนต์ทะเบียน กท-8524 ชนเสาไฟฟ้า ผู้ขับขี่อายุ 28 ปี ดับคาที่'
            },
            {
                'title': 'หุ้นปิดวันนี้ลบ 15.22 จุด',
                'content': 'ตลาดหุ้นไทยวันนี้ปิดการซื้อขายที่ระดับ 1,385.46 จุด ลดลง 15.22 จุด คิดเป็น -1.09%'
            }
        ]
        
        # ทดสอบแต่ละกรณี
        for i, test_case in enumerate(test_cases, 1):
            self.stdout.write(f'\n🔍 [{i}] ทดสอบ: {test_case["title"][:50]}...')
            
            try:
                # ทดสอบความเกี่ยวข้อง
                is_relevant = switcher.is_lottery_relevant(
                    test_case['title'], 
                    test_case['content']
                )
                
                self.stdout.write(f'   📊 เกี่ยวข้องกับหวย: {"✅ ใช่" if is_relevant else "❌ ไม่"}')
                
                if is_relevant:
                    # วิเคราะห์หาเลขเด็ด
                    result = switcher.analyze_news_for_lottery(
                        test_case['title'],
                        test_case['content']
                    )
                    
                    if result['success']:
                        analyzer_used = result.get('analyzer_type', 'unknown').upper()
                        fallback_used = ' (fallback)' if result.get('used_fallback') else ''
                        
                        self.stdout.write(
                            self.style.SUCCESS(f'   🤖 วิเคราะห์ด้วย: {analyzer_used}{fallback_used}')
                        )
                        self.stdout.write(f'   🔢 เลขเด็ด: {", ".join(result["numbers"])}')
                        self.stdout.write(f'   📈 คะแนน: {result.get("relevance_score", 0)}/100')
                        self.stdout.write(f'   📂 หมวด: {result.get("category", "other")}')
                        self.stdout.write(f'   💡 เหตุผล: {result.get("reasoning", "")[:60]}...')
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        self.stdout.write(
                            self.style.ERROR(f'   ❌ วิเคราะห์ล้มเหลว: {error_msg}')
                        )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Error: {e}')
                )
        
        # สรุปผล
        self.stdout.write('\n=== สรุป ===')
        active_analyzer = switcher.get_analyzer()
        if active_analyzer:
            analyzer_name = 'Groq' if hasattr(active_analyzer, '_make_request') else 'Gemini'
            self.stdout.write(
                self.style.SUCCESS(f'✅ ระบบพร้อมใช้งานด้วย {analyzer_name} analyzer')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ ไม่พบ analyzer ที่ใช้งานได้')
            )
        
        self.stdout.write(
            self.style.SUCCESS('🎉 การทดสอบเสร็จสิ้น!')
        )
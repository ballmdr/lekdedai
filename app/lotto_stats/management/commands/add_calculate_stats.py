

from django.core.management.base import BaseCommand
from lotto_stats.stats_calculator import StatsCalculator
from lotto_stats.models import HotColdNumber
from django.utils import timezone

class Command(BaseCommand):
    help = 'Calculate lottery statistics'
    
    def handle(self, *args, **options):
        calculator = StatsCalculator()
        
        # คำนวณเลขฮอต/เย็น
        hot_2d = calculator.get_hot_numbers(limit=20, days=90, number_type='2D')
        hot_3d = calculator.get_hot_numbers(limit=20, days=90, number_type='3D')
        cold_2d = calculator.get_cold_numbers(limit=20, number_type='2D')
        cold_3d = calculator.get_cold_numbers(limit=20, number_type='3D')
        
        # บันทึกผล
        HotColdNumber.objects.create(
            date=timezone.now().date(),
            hot_2d=[item['number'] for item in hot_2d],
            hot_3d=[item['number'] for item in hot_3d],
            cold_2d=[item['number'] for item in cold_2d],
            cold_3d=[item['number'] for item in cold_3d],
            calculation_days=90
        )
        
        self.stdout.write(self.style.SUCCESS('Successfully calculated statistics'))
from django.db.models import Count, Q
from datetime import datetime, timedelta
from collections import Counter
from .models import LotteryDraw, NumberStatistics

class StatsCalculator:
    def __init__(self):
        self.all_draws = LotteryDraw.objects.all().order_by('-draw_date')
    
    def get_hot_numbers(self, limit=10, days=90, number_type='2D'):
        """คำนวณเลขที่ออกบ่อย (เลขฮอต)"""
        cutoff_date = datetime.now().date() - timedelta(days=days)
        recent_draws = self.all_draws.filter(draw_date__gte=cutoff_date)
        
        number_counter = Counter()
        
        for draw in recent_draws:
            if number_type == '2D':
                # นับเลข 2 ตัวจากทุกตำแหน่ง
                number_counter[draw.two_digit] += 1
                # เลข 2 ตัวจากรางวัลที่ 1
                for num in draw.get_all_two_digits():
                    number_counter[num] += 1
            elif number_type == '3D':
                # นับเลข 3 ตัว
                for num in draw.get_all_three_digits():
                    number_counter[num] += 1
        
        hot_numbers = []
        for number, count in number_counter.most_common(limit):
            hot_numbers.append({
                'number': number,
                'count': count,
                'percentage': round((count / len(recent_draws)) * 100, 2)
            })
        
        return hot_numbers
    
    def get_cold_numbers(self, limit=10, number_type='2D'):
        """คำนวณเลขที่ไม่ออกนาน (เลขเย็น)"""
        # สร้าง set ของเลขทั้งหมด
        if number_type == '2D':
            all_numbers = set(str(i).zfill(2) for i in range(100))
        else:
            all_numbers = set(str(i).zfill(3) for i in range(1000))
        
        last_appearance = {}
        
        for number in all_numbers:
            for draw in self.all_draws:
                found = False
                
                if number_type == '2D':
                    if number == draw.two_digit or number in draw.get_all_two_digits():
                        found = True
                else:
                    if number in draw.get_all_three_digits():
                        found = True
                
                if found:
                    last_appearance[number] = draw.draw_date
                    break
        
        # คำนวณจำนวนวันที่ไม่ออก
        today = datetime.now().date()
        cold_numbers = []
        
        for number, last_date in last_appearance.items():
            days_since = (today - last_date).days
            cold_numbers.append({
                'number': number,
                'days': days_since,
                'last_date': last_date.strftime('%d/%m/%Y')
            })
        
        # เรียงตามจำนวนวันที่ไม่ออก
        cold_numbers.sort(key=lambda x: x['days'], reverse=True)
        
        return cold_numbers[:limit]
    
    def get_monthly_statistics(self):
        """สถิติรายเดือน"""
        monthly_stats = {}
        
        for draw in self.all_draws[:365]:  # ข้อมูล 1 ปี
            month_key = draw.draw_date.strftime('%Y-%m')
            
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {
                    'draws': 0,
                    'numbers_2d': [],
                    'numbers_3d': []
                }
            
            monthly_stats[month_key]['draws'] += 1
            monthly_stats[month_key]['numbers_2d'].append(draw.two_digit)
            monthly_stats[month_key]['numbers_2d'].extend(draw.get_all_two_digits())
            monthly_stats[month_key]['numbers_3d'].extend(draw.get_all_three_digits())
        
        # หาเลขที่ออกบ่อยที่สุดในแต่ละเดือน
        result = {}
        for month, data in monthly_stats.items():
            counter_2d = Counter(data['numbers_2d'])
            counter_3d = Counter(data['numbers_3d'])
            
            most_common_2d = counter_2d.most_common(1)
            most_common_3d = counter_3d.most_common(1)
            
            result[month] = {
                'total_draws': data['draws'],
                'most_common_2d': {
                    'number': most_common_2d[0][0] if most_common_2d else None,
                    'count': most_common_2d[0][1] if most_common_2d else 0
                },
                'most_common_3d': {
                    'number': most_common_3d[0][0] if most_common_3d else None,
                    'count': most_common_3d[0][1] if most_common_3d else 0
                }
            }
        
        return result
    
    def get_number_statistics(self, number):
        """สถิติของเลขที่เจาะจง"""
        stats = {
            'total_appearances': 0,
            'last_appeared': None,
            'days_since_last': 0,
            'appearance_dates': [],
            'average_gap': 0,
            'max_gap': 0,
            'min_gap': 999
        }
        
        appearances = []
        
        for draw in self.all_draws:
            found = False
            
            if len(number) == 2:
                if number == draw.two_digit or number in draw.get_all_two_digits():
                    found = True
            else:
                if number in draw.get_all_three_digits():
                    found = True
            
            if found:
                appearances.append(draw.draw_date)
        
        if appearances:
            stats['total_appearances'] = len(appearances)
            stats['last_appeared'] = appearances[0]
            stats['days_since_last'] = (datetime.now().date() - appearances[0]).days
            stats['appearance_dates'] = [d.strftime('%d/%m/%Y') for d in appearances[:10]]
            
            # คำนวณระยะห่าง
            if len(appearances) > 1:
                gaps = []
                for i in range(len(appearances) - 1):
                    gap = (appearances[i] - appearances[i + 1]).days
                    gaps.append(gap)
                
                stats['average_gap'] = round(sum(gaps) / len(gaps), 2)
                stats['max_gap'] = max(gaps)
                stats['min_gap'] = min(gaps)
        
        return stats
    
    def get_statistics_summary(self):
        """สรุปสถิติทั้งหมด"""
        total_draws = self.all_draws.count()
        
        if total_draws == 0:
            return None
        
        # หาเลขที่ออกบ่อยที่สุดตลอดกาล
        all_2d_counter = Counter()
        all_3d_counter = Counter()
        
        for draw in self.all_draws:
            all_2d_counter[draw.two_digit] += 1
            for num in draw.get_all_two_digits():
                all_2d_counter[num] += 1
            for num in draw.get_all_three_digits():
                all_3d_counter[num] += 1
        
        most_common_2d = all_2d_counter.most_common(1)[0] if all_2d_counter else (None, 0)
        most_common_3d = all_3d_counter.most_common(1)[0] if all_3d_counter else (None, 0)
        
        return {
            'total_draws': total_draws,
            'date_range': {
                'from': self.all_draws.last().draw_date.strftime('%d/%m/%Y') if self.all_draws.last() else None,
                'to': self.all_draws.first().draw_date.strftime('%d/%m/%Y') if self.all_draws.first() else None
            },
            'most_common_all_time': {
                '2d': {'number': most_common_2d[0], 'count': most_common_2d[1]},
                '3d': {'number': most_common_3d[0], 'count': most_common_3d[1]}
            }
        }
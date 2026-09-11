from datetime import datetime, timedelta
from collections import Counter
from .models import LotteryDraw
from lottery_checker.models import LottoResult

class StatsCalculator:
    def __init__(self):
        # Task 27: โหลดครั้งเดียวเป็น list — ทุก method กรองใน memory
        # (เลี่ยงสแกนตารางซ้ำหลายรอบต่อ request เดียว)
        self.all_draws = list(LotteryDraw.objects.all().order_by('-draw_date'))
        self.lotto_results = LottoResult.objects.all().order_by('-draw_date')
    
    def get_hot_numbers_from_lotto_result(self, limit=10, days=90, number_type='2D'):
        """คำนวณเลขที่ออกบ่อย (เลขฮอต) จาก LottoResult โดยตรง"""
        cutoff_date = datetime.now().date() - timedelta(days=days)
        recent_results = self.lotto_results.filter(draw_date__gte=cutoff_date)
        
        number_counter = Counter()
        
        for result in recent_results:
            # ดึงข้อมูลจาก result_data (ข้อมูลจาก API กองสลาก)
            if hasattr(result, 'result_data') and result.result_data:
                # ข้อมูลจาก GLO API จะมี statusMessage="getLotteryResult - Success" 
                # แต่ไม่มีข้อมูลรางวัล ให้ข้ามไป
                continue
        
        # ถ้าไม่มีข้อมูลจาก LottoResult ที่มีรางวัล ให้ใช้ LotteryDraw แทน
        return self.get_hot_numbers(limit, days, number_type)
    
    def get_hot_numbers(self, limit=10, days=90, number_type='2D'):
        """เลขที่ออกบ่อย (เลขฮอต) — 2D นับเฉพาะรางวัลเลขท้าย 2 ตัว (`two_digit` งวดละ 1 ค่า).

        นิยาม: ตำแหน่ง = รางวัลเลขท้าย 2 ตัวเท่านั้น (ไม่รวมเลข 2 หลักในรางวัลที่ 1),
        ช่วงเวลา = days วันล่าสุด, ตัวอย่าง = จำนวนงวดในช่วงนั้น.
        เลขคู่ในรางวัลที่ 1 ดูที่ get_hot_first_prize_pairs แยกต่างหาก.
        """
        cutoff_date = datetime.now().date() - timedelta(days=days)
        recent_draws = [d for d in self.all_draws if d.draw_date >= cutoff_date]

        if not recent_draws:
            return []

        number_counter = Counter()

        for draw in recent_draws:
            if number_type == '2D':
                # นับเฉพาะเลขท้าย 2 ตัว งวดละ 1 ครั้ง
                number_counter[draw.two_digit] += 1
            elif number_type == '3D':
                # นับเลข 3 ตัว (รางวัลเลขหน้า/ท้าย 3 ตัว เป็นรางวัลจริงอยู่แล้ว)
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

    def get_hot_first_prize_pairs(self, limit=10, days=90):
        """เลขคู่ 2 หลักที่พบบ่อยในรางวัลที่ 1 (นับทุกตำแหน่ง 5 ช่องต่องวด).

        นิยาม: ตำแหน่ง = หน้าต่างเลื่อน 2 หลัก 5 ตำแหน่งในเลขรางวัลที่ 1
        (ตำแหน่ง 1-2 ถึง 5-6), ช่วงเวลา = days วันล่าสุด.
        count = จำนวนครั้งที่พบรวมทุกตำแหน่ง, draws = จำนวนงวดที่พบอย่างน้อย 1 ครั้ง,
        percentage = draws / จำนวนงวดในช่วง (ไม่เกิน 100).
        """
        cutoff_date = datetime.now().date() - timedelta(days=days)
        recent_draws = [d for d in self.all_draws if d.draw_date >= cutoff_date]

        if not recent_draws:
            return []

        window_counter = Counter()
        draw_counter = Counter()

        for draw in recent_draws:
            seen = set()
            for num in draw.get_all_two_digits():
                window_counter[num] += 1
                seen.add(num)
            for num in seen:
                draw_counter[num] += 1

        total_draws = len(recent_draws)
        pairs = []
        for number, count in window_counter.most_common(limit):
            draws = draw_counter[number]
            pairs.append({
                'number': number,
                'count': count,
                'draws': draws,
                'percentage': round((draws / total_draws) * 100, 2),
            })

        return pairs
    
    def get_cold_numbers(self, limit=10, number_type='2D'):
        """เลขที่ไม่ออกนาน (เลขเย็น) — 2D นับเฉพาะรางวัลเลขท้าย 2 ตัว (`two_digit`).

        นิยาม: "ออก" = ปรากฏในรางวัลเลขท้าย 2 ตัวของงวดนั้น (ไม่รวมรางวัลที่ 1),
        days = จำนวนวันนับจากงวดล่าสุดที่ออกถึงวันนี้.
        เลขคู่ในรางวัลที่ 1 ดูที่ get_cold_first_prize_pairs แยกต่างหาก.
        """
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
                    if number == draw.two_digit:
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

    def get_cold_first_prize_pairs(self, limit=10):
        """เลขคู่ 2 หลักที่หายไปนานจากรางวัลที่ 1 (นับทุกตำแหน่ง 5 ช่องต่องวด).

        นิยาม: "ออก" = ปรากฏในหน้าต่างเลื่อน 2 หลักตำแหน่งใดก็ได้ของรางวัลที่ 1,
        days = จำนวนวันนับจากงวดล่าสุดที่พบถึงวันนี้.
        """
        all_numbers = set(str(i).zfill(2) for i in range(100))

        last_appearance = {}

        for number in all_numbers:
            for draw in self.all_draws:
                if number in draw.get_all_two_digits():
                    last_appearance[number] = draw.draw_date
                    break

        today = datetime.now().date()
        cold_numbers = []

        for number, last_date in last_appearance.items():
            days_since = (today - last_date).days
            cold_numbers.append({
                'number': number,
                'days': days_since,
                'last_date': last_date.strftime('%d/%m/%Y')
            })

        cold_numbers.sort(key=lambda x: x['days'], reverse=True)

        return cold_numbers[:limit]
    
    def get_monthly_statistics(self):
        """สถิติรายเดือน - จัดกลุ่มตามเดือน (ไม่แยกปี).

        นิยาม: `two_digit` = รางวัลเลขท้าย 2 ตัวของแต่ละงวด (งวดละ 1 ค่า),
        `first_pairs` = เลขคู่ 2 หลักทุกตำแหน่งในรางวัลที่ 1 (งวดละ 5 ค่า).
        แยกนับชัดเจน ไม่ปนกัน.
        """
        # Thai month names
        thai_months = {
            1: 'มกราคม', 2: 'กุมภาพันธ์', 3: 'มีนาคม', 4: 'เมษายน',
            5: 'พฤษภาคม', 6: 'มิถุนายน', 7: 'กรกฎาคม', 8: 'สิงหาคม',
            9: 'กันยายน', 10: 'ตุลาคม', 11: 'พฤศจิกายน', 12: 'ธันวาคม'
        }
        
        monthly_stats = {}
        
        for draw in self.all_draws:
            month_num = draw.draw_date.month
            month_name = thai_months[month_num]
            
            if month_name not in monthly_stats:
                monthly_stats[month_name] = {
                    'draws': [],  # เก็บข้อมูลการจับสลากแต่ละงวด
                    'two_digit': [],  # รางวัลเลขท้าย 2 ตัว (งวดละ 1 ค่า)
                    'first_pairs': [],  # เลขคู่ 2 หลักในรางวัลที่ 1 (งวดละ 5 ค่า)
                    'numbers_3d': [],
                    'month_number': month_num  # เก็บหมายเลขเดือนสำหรับเรียงลำดับ
                }
            
            # เก็บข้อมูลการจับสลาก
            monthly_stats[month_name]['draws'].append({
                'date': draw.draw_date,
                'date_str': draw.draw_date.strftime('%d/%m/%Y')
            })
            
            # เก็บเลขที่ออก (แยกตำแหน่งชัด)
            monthly_stats[month_name]['two_digit'].append(draw.two_digit)
            monthly_stats[month_name]['first_pairs'].extend(draw.get_all_two_digits())
            monthly_stats[month_name]['numbers_3d'].extend(draw.get_all_three_digits())
        
        # หาเลขที่ออกบ่อยที่สุดในแต่ละเดือน (แยกตำแหน่ง)
        result = {}
        for month, data in monthly_stats.items():
            counter_two = Counter(data['two_digit'])
            counter_pairs = Counter(data['first_pairs'])
            counter_3d = Counter(data['numbers_3d'])

            most_common_two = counter_two.most_common(1)
            most_common_pairs = counter_pairs.most_common(1)
            most_common_3d = counter_3d.most_common(1)

            # เรียงลำดับงวดตามวันที่ (ใหม่สุดก่อน)
            sorted_draws = sorted(data['draws'], key=lambda x: x['date'], reverse=True)

            result[month] = {
                'month_number': data['month_number'],  # สำหรับเรียงลำดับ
                'total_draws': len(data['draws']),
                'draw_dates': [d['date_str'] for d in sorted_draws[:5]],  # แสดง 5 งวดล่าสุด
                'most_common_two_digit': {
                    'number': most_common_two[0][0] if most_common_two else None,
                    'count': most_common_two[0][1] if most_common_two else 0
                },
                'most_common_first_pair': {
                    'number': most_common_pairs[0][0] if most_common_pairs else None,
                    'count': most_common_pairs[0][1] if most_common_pairs else 0
                },
                'most_common_3d': {
                    'number': most_common_3d[0][0] if most_common_3d else None,
                    'count': most_common_3d[0][1] if most_common_3d else 0
                }
            }
        
        # เรียงลำดับตามเดือน (มกราคม, กุมภาพันธ์, ...)
        sorted_result = {}
        for month in sorted(result.keys(), key=lambda x: result[x]['month_number']):
            sorted_result[month] = result[month]
        
        return sorted_result
    
    def get_number_statistics(self, number):
        """สถิติของเลขที่เจาะจง.

        นิยามสำหรับเลข 2 หลัก: ค่าหลัก (total_appearances/last_appeared/days_since_last/
        average_gap/...) นับเฉพาะรางวัลเลขท้าย 2 ตัว (`two_digit` งวดละ 1 ค่า) เท่านั้น.
        การพบในรางวัลที่ 1 รายงานแยกในคีย์ `first_prize` (นับทุกตำแหน่ง 5 ช่องต่องวด)
        เลข 3 หลักนับจากรางวัลเลขหน้า/ท้าย 3 ตัว (รางวัลจริง) พร้อมระบุ positions.
        """
        stats = {
            'total_appearances': 0,
            'last_appeared': None,
            'days_since_last': 0,
            'appearance_dates': [],
            # None = ข้อมูลไม่พอคำนวณ (ออกครั้งเดียว/ไม่เคยออก) — ห้ามโชว์ 0 วัน
            'average_gap': None,
            'max_gap': None,
            'min_gap': None,
            'positions': '',
        }

        appearances = []
        first_prize_appearances = []

        for draw in self.all_draws:
            if len(number) == 2:
                if number == draw.two_digit:
                    appearances.append(draw.draw_date)
                if number in draw.get_all_two_digits():
                    first_prize_appearances.append(draw.draw_date)
            else:
                if number in draw.get_all_three_digits():
                    appearances.append(draw.draw_date)

        if len(number) == 2:
            stats['positions'] = 'รางวัลเลขท้าย 2 ตัว (two_digit งวดละ 1 ค่า)'
            stats['first_prize'] = self._summarize_appearances(first_prize_appearances)
            stats['first_prize']['positions'] = 'เลขคู่ 2 หลักทุกตำแหน่งในรางวัลที่ 1 (งวดละ 5 ค่า)'
        else:
            stats['positions'] = 'รางวัลเลขหน้า/ท้าย 3 ตัว'

        self._summarize_into(stats, appearances)
        return stats

    @staticmethod
    def _summarize_appearances(appearances):
        """สรุป list วันออกรางวัล (ใหม่สุดก่อน) เป็น dict สถิติ."""
        summary = {
            'total_appearances': 0,
            'last_appeared': None,
            'days_since_last': 0,
            'appearance_dates': [],
            'average_gap': None,
            'max_gap': None,
            'min_gap': None,
        }
        StatsCalculator._summarize_into(summary, appearances)
        return summary

    @staticmethod
    def _summarize_into(stats, appearances):
        if not appearances:
            return
        stats['total_appearances'] = len(appearances)
        stats['last_appeared'] = appearances[0]
        stats['days_since_last'] = (datetime.now().date() - appearances[0]).days
        stats['appearance_dates'] = [d.strftime('%d/%m/%Y') for d in appearances[:10]]

        if len(appearances) > 1:
            gaps = []
            for i in range(len(appearances) - 1):
                gap = (appearances[i] - appearances[i + 1]).days
                gaps.append(gap)

            stats['average_gap'] = round(sum(gaps) / len(gaps), 2)
            stats['max_gap'] = max(gaps)
            stats['min_gap'] = min(gaps)
    
    def get_statistics_summary(self):
        """สรุปสถิติทั้งหมด.

        นิยาม: `two_digit` นับเฉพาะรางวัลเลขท้าย 2 ตัว (งวดละ 1 ค่า),
        `first_prize_pairs` นับเลขคู่ 2 หลักทุกตำแหน่งในรางวัลที่ 1 (งวดละ 5 ค่า).
        """
        total_draws = len(self.all_draws)
        
        if total_draws == 0:
            return None
        
        # หาเลขที่ออกบ่อยที่สุดตลอดกาล (แยกตำแหน่ง)
        two_digit_counter = Counter()
        pair_counter = Counter()
        all_3d_counter = Counter()
        
        for draw in self.all_draws:
            two_digit_counter[draw.two_digit] += 1
            for num in draw.get_all_two_digits():
                pair_counter[num] += 1
            for num in draw.get_all_three_digits():
                all_3d_counter[num] += 1
        
        most_common_two = two_digit_counter.most_common(1)[0] if two_digit_counter else (None, 0)
        most_common_pair = pair_counter.most_common(1)[0] if pair_counter else (None, 0)
        most_common_3d = all_3d_counter.most_common(1)[0] if all_3d_counter else (None, 0)
        
        return {
            'total_draws': total_draws,
            'date_range': {
                'from': self.all_draws[-1].draw_date.strftime('%d/%m/%Y') if self.all_draws else None,
                'to': self.all_draws[0].draw_date.strftime('%d/%m/%Y') if self.all_draws else None
            },
            'most_common_all_time': {
                'two_digit': {'number': most_common_two[0], 'count': most_common_two[1]},
                'first_prize_pair': {'number': most_common_pair[0], 'count': most_common_pair[1]},
                '3d': {'number': most_common_3d[0], 'count': most_common_3d[1]}
            }
        }
    
    def get_running_number_stats(self):
        """สถิติเลขวิ่ง (0-9) ที่ออกในรางวัลเลขท้าย 2 ตัว และรางวัลที่ 1"""
        digit_stats = {}
        
        # Initialize counters for each digit
        for digit in range(10):
            digit_stats[str(digit)] = {
                'two_digit_count': 0,
                'first_prize_count': 0,
                'total_count': 0,
                'last_appeared': None,
                'days_since_last': 0
            }
        
        today = datetime.now().date()
        
        for draw in self.all_draws:
            # Count digits in two_digit (last 2 digits)
            for digit_char in draw.two_digit:
                digit_stats[digit_char]['two_digit_count'] += 1
                digit_stats[digit_char]['total_count'] += 1
                if digit_stats[digit_char]['last_appeared'] is None:
                    digit_stats[digit_char]['last_appeared'] = draw.draw_date
            
            # Count digits in first prize
            for digit_char in draw.first_prize:
                digit_stats[digit_char]['first_prize_count'] += 1
                digit_stats[digit_char]['total_count'] += 1
                if digit_stats[digit_char]['last_appeared'] is None:
                    digit_stats[digit_char]['last_appeared'] = draw.draw_date
        
        # Calculate days since last appearance
        for digit in digit_stats:
            if digit_stats[digit]['last_appeared']:
                digit_stats[digit]['days_since_last'] = (today - digit_stats[digit]['last_appeared']).days
                digit_stats[digit]['last_appeared_str'] = digit_stats[digit]['last_appeared'].strftime('%d/%m/%Y')
            else:
                digit_stats[digit]['days_since_last'] = 999
                digit_stats[digit]['last_appeared_str'] = '-'
        
        return digit_stats
    
    def get_double_number_stats(self, days_back=365):
        """สถิติเลขเบิ้ล/เลขหาม (เลขซ้ำ เช่น 22, 99, 111)"""
        cutoff_date = datetime.now().date() - timedelta(days=days_back)
        recent_draws = [d for d in self.all_draws if d.draw_date >= cutoff_date]
        
        double_stats = {
            '2d': {},  # เลขเบิ้ล 2 ตัว (00, 11, 22, ..., 99)
            '3d': {}   # เลขเบิ้ล 3 ตัว (000, 111, 222, ..., 999)
        }
        
        # Initialize 2D doubles
        for i in range(10):
            double_num = str(i) + str(i)
            double_stats['2d'][double_num] = {
                'count': 0,
                'count_two_digit': 0,  # พบในรางวัลเลขท้าย 2 ตัว
                'count_first_prize': 0,  # พบในรางวัลที่ 1 (ทุกตำแหน่ง)
                'last_appeared': None,
                'appearances': []
            }
        
        # Initialize 3D doubles
        for i in range(10):
            double_num = str(i) + str(i) + str(i)
            double_stats['3d'][double_num] = {
                'count': 0,
                'last_appeared': None,
                'appearances': []
            }
        
        for draw in recent_draws:
            # Check 2D doubles in two_digit
            if draw.two_digit in double_stats['2d']:
                entry = double_stats['2d'][draw.two_digit]
                entry['count'] += 1
                entry['count_two_digit'] += 1
                entry['last_appeared'] = draw.draw_date
                entry['appearances'].append({
                    'date': draw.draw_date.strftime('%d/%m/%Y'),
                    'type': 'เลขท้าย 2 ตัว'
                })
            
            # Check 2D doubles in first prize
            for i in range(len(draw.first_prize) - 1):
                two_digit = draw.first_prize[i:i+2]
                if two_digit in double_stats['2d']:
                    entry = double_stats['2d'][two_digit]
                    entry['count'] += 1
                    entry['count_first_prize'] += 1
                    entry['last_appeared'] = draw.draw_date
                    entry['appearances'].append({
                        'date': draw.draw_date.strftime('%d/%m/%Y'),
                        'type': f'รางวัลที่ 1 (ตำแหน่ง {i+1}-{i+2})'
                    })
            
            # Check 3D doubles in three digit prizes
            for three_digit in draw.get_all_three_digits():
                if len(three_digit) >= 3:
                    three_num = three_digit[:3]
                    if three_num in double_stats['3d']:
                        double_stats['3d'][three_num]['count'] += 1
                        double_stats['3d'][three_num]['last_appeared'] = draw.draw_date
                        double_stats['3d'][three_num]['appearances'].append({
                            'date': draw.draw_date.strftime('%d/%m/%Y'),
                            'type': 'รางวัล 3 ตัว'
                        })
        
        # Calculate days since last appearance
        today = datetime.now().date()
        for category in double_stats:
            for number in double_stats[category]:
                stats = double_stats[category][number]
                if stats['last_appeared']:
                    stats['days_since_last'] = (today - stats['last_appeared']).days
                    stats['last_appeared_str'] = stats['last_appeared'].strftime('%d/%m/%Y')
                else:
                    stats['days_since_last'] = 999
                    stats['last_appeared_str'] = '-'
        
        return double_stats
    
    def get_sequential_number_stats(self, days_back=365):
        """สถิติเลขเรียง (เลขต่อเนื่อง เช่น 123, 234, 456, 789)"""
        cutoff_date = datetime.now().date() - timedelta(days=days_back)
        recent_draws = [d for d in self.all_draws if d.draw_date >= cutoff_date]
        
        def is_sequential(number_str):
            """ตรวจสอบว่าเป็นเลขเรียงหรือไม่"""
            if len(number_str) < 2:
                return False
            
            digits = [int(d) for d in number_str]
            # ตรวจสอบเลขเรียงขึ้น (เช่น 123, 234)
            ascending = all(digits[i] + 1 == digits[i + 1] for i in range(len(digits) - 1))
            # ตรวจสอบเลขเรียงลง (เช่น 321, 987)
            descending = all(digits[i] - 1 == digits[i + 1] for i in range(len(digits) - 1))
            
            return ascending or descending
        
        sequential_stats = {
            '2d': {},
            '3d': {}
        }
        
        # Generate all possible sequential numbers
        # 2-digit sequences
        for i in range(10):
            for j in [-1, 1]:  # ascending and descending
                if 0 <= i + j <= 9:
                    seq_num = str(i) + str(i + j)
                    if seq_num not in sequential_stats['2d']:
                        sequential_stats['2d'][seq_num] = {
                            'count': 0,
                            'count_two_digit': 0,  # พบในรางวัลเลขท้าย 2 ตัว
                            'count_first_prize': 0,  # พบในรางวัลที่ 1 (ทุกตำแหน่ง)
                            'last_appeared': None,
                            'appearances': [],
                            'type': 'เรียงขึ้น' if j == 1 else 'เรียงลง'
                        }
        
        # 3-digit sequences
        for i in range(10):
            for j in [-1, 1]:  # ascending and descending
                if 0 <= i + j <= 9 and 0 <= i + 2*j <= 9:
                    seq_num = str(i) + str(i + j) + str(i + 2*j)
                    if seq_num not in sequential_stats['3d']:
                        sequential_stats['3d'][seq_num] = {
                            'count': 0,
                            'last_appeared': None,
                            'appearances': [],
                            'type': 'เรียงขึ้น' if j == 1 else 'เรียงลง'
                        }
        
        for draw in recent_draws:
            # Check 2D sequences in two_digit
            if draw.two_digit in sequential_stats['2d']:
                entry = sequential_stats['2d'][draw.two_digit]
                entry['count'] += 1
                entry['count_two_digit'] += 1
                entry['last_appeared'] = draw.draw_date
                entry['appearances'].append({
                    'date': draw.draw_date.strftime('%d/%m/%Y'),
                    'type': 'เลขท้าย 2 ตัว'
                })
            
            # Check 2D sequences in first prize
            for i in range(len(draw.first_prize) - 1):
                two_digit = draw.first_prize[i:i+2]
                if two_digit in sequential_stats['2d']:
                    entry = sequential_stats['2d'][two_digit]
                    entry['count'] += 1
                    entry['count_first_prize'] += 1
                    entry['last_appeared'] = draw.draw_date
                    entry['appearances'].append({
                        'date': draw.draw_date.strftime('%d/%m/%Y'),
                        'type': f'รางวัลที่ 1 (ตำแหน่ง {i+1}-{i+2})'
                    })
            
            # Check 3D sequences in three digit prizes
            for three_digit in draw.get_all_three_digits():
                if len(three_digit) >= 3:
                    three_num = three_digit[:3]
                    if three_num in sequential_stats['3d']:
                        sequential_stats['3d'][three_num]['count'] += 1
                        sequential_stats['3d'][three_num]['last_appeared'] = draw.draw_date
                        sequential_stats['3d'][three_num]['appearances'].append({
                            'date': draw.draw_date.strftime('%d/%m/%Y'),
                            'type': 'รางวัล 3 ตัว'
                        })
        
        # Calculate days since last appearance
        today = datetime.now().date()
        for category in sequential_stats:
            for number in sequential_stats[category]:
                stats = sequential_stats[category][number]
                if stats['last_appeared']:
                    stats['days_since_last'] = (today - stats['last_appeared']).days
                    stats['last_appeared_str'] = stats['last_appeared'].strftime('%d/%m/%Y')
                else:
                    stats['days_since_last'] = 999
                    stats['last_appeared_str'] = '-'
        
        return sequential_stats
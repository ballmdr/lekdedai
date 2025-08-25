#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lottery Dates - ตัวแปรวันที่หวยออกที่ใช้ร่วมกัน
"""

from datetime import date, datetime
from typing import List, Dict, Any

class LotteryDates:
    """จัดการวันที่หวยออก"""
    
    # วันที่หวยออกปกติ (1 และ 16 ของทุกเดือน)
    NORMAL_DRAW_DATES = [
        # 2568
        "2025-01-01", "2025-01-16",
        "2025-02-01", "2025-02-16", 
        "2025-03-01", "2025-03-16",
        "2025-04-01", "2025-04-16",
        "2025-05-01", "2025-05-16",
        "2025-06-01", "2025-06-16",
        "2025-07-01", "2025-07-16",
        "2025-08-01", "2025-08-16",
        "2025-09-01", "2025-09-16",
        "2025-10-01", "2025-10-16",
        "2025-11-01", "2025-11-16",
        "2025-12-01", "2025-12-16",
    ]
    
    # วันที่หวยออกที่อาจเลื่อน (กรณีพิเศษ)
    SPECIAL_DRAW_DATES = {
        "2025-05-02": "เลื่อนจาก 1 พฤษภาคม",  # ตัวอย่าง
        "2025-01-17": "เลื่อนจาก 16 มกราคม",  # ตัวอย่าง
    }
    
    @classmethod
    def get_all_draw_dates(cls) -> List[str]:
        """ดึงวันที่หวยออกทั้งหมด (ปกติ + พิเศษ)"""
        all_dates = cls.NORMAL_DRAW_DATES.copy()
        all_dates.extend(cls.SPECIAL_DRAW_DATES.keys())
        return sorted(all_dates, reverse=True)
    
    @classmethod
    def get_draw_dates_for_year(cls, year: int) -> List[str]:
        """ดึงวันที่หวยออกสำหรับปีที่ระบุ"""
        year_str = str(year)
        return [date_str for date_str in cls.get_all_draw_dates() if date_str.startswith(year_str)]
    
    @classmethod
    def get_draw_dates_for_month(cls, year: int, month: int) -> List[str]:
        """ดึงวันที่หวยออกสำหรับเดือนที่ระบุ"""
        month_str = f"{year:04d}-{month:02d}"
        return [date_str for date_str in cls.get_all_draw_dates() if date_str.startswith(month_str)]
    
    @classmethod
    def get_next_draw_date(cls, from_date: date = None) -> str:
        """ดึงวันที่หวยออกถัดไป"""
        if from_date is None:
            from_date = date.today()
        
        for date_str in cls.get_all_draw_dates():
            draw_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if draw_date > from_date:
                return date_str
        return None
    
    @classmethod
    def get_previous_draw_date(cls, from_date: date = None) -> str:
        """ดึงวันที่หวยออกก่อนหน้า"""
        if from_date is None:
            from_date = date.today()
        
        for date_str in reversed(cls.get_all_draw_dates()):
            draw_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if draw_date < from_date:
                return date_str
        return None
    
    @classmethod
    def is_draw_date(cls, check_date: date) -> bool:
        """ตรวจสอบว่าเป็นวันที่หวยออกหรือไม่"""
        date_str = check_date.strftime("%Y-%m-%d")
        return date_str in cls.get_all_draw_dates()
    
    @classmethod
    def get_draw_date_info(cls, date_str: str) -> Dict[str, Any]:
        """ดึงข้อมูลวันที่หวยออก"""
        if date_str in cls.SPECIAL_DRAW_DATES:
            return {
                "date": date_str,
                "is_special": True,
                "note": cls.SPECIAL_DRAW_DATES[date_str],
                "type": "special"
            }
        elif date_str in cls.NORMAL_DRAW_DATES:
            return {
                "date": date_str,
                "is_special": False,
                "note": "วันที่หวยออกปกติ",
                "type": "normal"
            }
        else:
            return None
    
    @classmethod
    def get_dropdown_options(cls, limit: int = 50) -> List[Dict[str, str]]:
        """สร้างตัวเลือกสำหรับ dropdown"""
        options = []
        for date_str in cls.get_all_draw_dates()[:limit]:
            draw_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            info = cls.get_draw_date_info(date_str)
            
            # แปลงเป็นภาษาไทย
            thai_month = cls._get_thai_month(draw_date.month)
            thai_year = draw_date.year + 543  # แปลงเป็น พ.ศ.
            
            if info["is_special"]:
                label = f"{draw_date.day} {thai_month} {thai_year} ({info['note']})"
            else:
                label = f"{draw_date.day} {thai_month} {thai_year}"
            
            options.append({
                "value": date_str,
                "label": label,
                "is_special": info["is_special"]
            })
        
        return options
    
    @classmethod
    def _get_thai_month(cls, month: int) -> str:
        """แปลงเดือนเป็นภาษาไทย"""
        thai_months = [
            "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน",
            "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม",
            "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
        ]
        return thai_months[month - 1]
    
    @classmethod
    def get_recent_draw_dates(cls, days_back: int = 365) -> List[str]:
        """ดึงวันที่หวยออกย้อนหลังตามจำนวนวันที่ระบุ"""
        from datetime import timedelta
        
        today = date.today()
        cutoff_date = today - timedelta(days=days_back)
        
        recent_dates = []
        for date_str in cls.get_all_draw_dates():
            draw_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if draw_date >= cutoff_date and draw_date <= today:
                recent_dates.append(date_str)
        
        # ถ้าไม่มีวันที่หวยออกในช่วงที่ระบุ ให้ดึงวันที่หวยออกล่าสุดที่ใกล้เคียง
        if not recent_dates:
            # ดึงวันที่หวยออกล่าสุดที่ใกล้เคียงกับวันปัจจุบัน
            all_dates = cls.get_all_draw_dates()
            for date_str in all_dates:
                draw_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                if draw_date <= today:  # วันที่หวยออกที่ผ่านมาแล้ว
                    recent_dates.append(date_str)
                    if len(recent_dates) >= 5:  # จำกัดจำนวน
                        break
        
        return recent_dates

# ตัวแปรสำหรับใช้งานง่าย
LOTTERY_DATES = LotteryDates()

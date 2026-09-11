#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lotto Service - บริการดึงข้อมูลหวยจาก GLO API และจัดการฐานข้อมูล
"""

import json
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from django.utils import timezone

from .models import LottoResult

# Configure logging
logger = logging.getLogger(__name__)

# รางวัลแบบจับเต็มเลข 6 หลัก (เรียงตามความสำคัญ)
FIXED_PRIZES = [
    ("first", "รางวัลที่ 1", "6,000,000"),
    ("second", "รางวัลที่ 2", "200,000"),
    ("third", "รางวัลที่ 3", "80,000"),
    ("fourth", "รางวัลที่ 4", "40,000"),
    ("fifth", "รางวัลที่ 5", "20,000"),
    ("near1", "รางวัลข้างเคียงรางวัลที่ 1", "100,000"),
]


def unwrap_result_data(lotto_data: Any) -> Optional[Dict[str, Any]]:
    """คืน dict ข้อมูลรางวัล (first/last3f/... ) จาก raw GLO payload หรือข้อมูลที่ unwrap แล้ว"""
    if not isinstance(lotto_data, dict):
        return None

    data = lotto_data
    if "response" in data:
        response = data.get("response") or {}
        result = response.get("result") or {}
        data = result.get("data")

    if not isinstance(data, dict):
        return None
    return data


def _prize_values(data: Dict[str, Any], key: str) -> list:
    item = data.get(key)
    if not isinstance(item, dict) or not isinstance(item.get("number"), list):
        return []
    return [str(n.get("value")) for n in item["number"] if isinstance(n, dict)]


def check_numbers_against_result(lotto_data: Any, lottery_number: str) -> Optional[list]:
    """ตรวจเลขต่องวดเดียว (source of truth ใช้ร่วมหน้าแรก/หน้ารายละเอียด/สมุดเลข)

    รองรับเลข 2/3/6 หลัก:
    - 6 หลัก: รางวัลเต็มใบ + เลขหน้า 3 ตัว + เลขท้าย 3 ตัว + เลขท้าย 2 ตัว
    - 3 หลัก: เลขหน้า 3 ตัว + เลขท้าย 3 ตัว
    - 2 หลัก: เลขท้าย 2 ตัว
    เลขยาว 4-5 หลักไม่มีกติการองรับ ผู้เรียกต้องกรองออกก่อน (คืน [] ถ้าเรียกมา)

    คืน list ชื่อรางวัลพร้อมจำนวนเงิน หรือ None ถ้าโครงสร้างข้อมูลไม่ถูกต้อง
    """
    data = unwrap_result_data(lotto_data)
    if data is None:
        return None

    number = str(lottery_number)
    prizes = []

    # รางวัลที่จับเต็มเลข (เทียบตรง; เลขสั้นจะไม่ตรงกับเลข 6 หลักอยู่แล้ว)
    for key, label, amount in FIXED_PRIZES:
        if number in _prize_values(data, key):
            prizes.append(f"{label} ({amount} บาท)")

    # รางวัลเลขหน้า/ท้าย 3 ตัว และท้าย 2 ตัว
    if len(number) == 6:
        if number[:3] in _prize_values(data, "last3f"):
            prizes.append("เลขหน้า 3 ตัว (4,000 บาท)")
        if number[3:6] in _prize_values(data, "last3b"):
            prizes.append("เลขท้าย 3 ตัว (4,000 บาท)")
        if number[4:6] in _prize_values(data, "last2"):
            prizes.append("เลขท้าย 2 ตัว (2,000 บาท)")
    elif len(number) == 3:
        if number in _prize_values(data, "last3f"):
            prizes.append("เลขหน้า 3 ตัว (4,000 บาท)")
        if number in _prize_values(data, "last3b"):
            prizes.append("เลขท้าย 3 ตัว (4,000 บาท)")
    elif len(number) == 2:
        if number in _prize_values(data, "last2"):
            prizes.append("เลขท้าย 2 ตัว (2,000 บาท)")

    return prizes


class LottoService:
    """บริการจัดการข้อมูลหวย"""
    
    def __init__(self):
        self.api_url = "https://www.glo.or.th/api/checking/getLotteryResult"
        self.timeout = 10
    
    def fetch_from_api(self, date, month, year) -> Optional[Dict[str, Any]]:
        """ดึงข้อมูลจาก GLO API"""
        # แปลงเป็น integer ถ้าเป็น string
        try:
            date = int(date)
            month = int(month)
            year = int(year)
        except (ValueError, TypeError):
            logger.error(f"❌ ค่า date, month, year ต้องเป็นตัวเลข: date={date}, month={month}, year={year}")
            return None
            
        payload = {
            "date": date,
            "month": month,
            "year": year
        }
        
        try:
            logger.info(f"🌐 กำลังดึงข้อมูลจาก GLO API สำหรับวันที่ {date}/{month}/{year}")
            
            response = requests.post(
                self.api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ ดึงข้อมูลจาก API สำเร็จ")
                return data
            else:
                logger.error(f"❌ API ส่งคืน status code: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ เกิดข้อผิดพลาดในการเรียก API: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"❌ ไม่สามารถแปลง JSON ได้: {e}")
            return None
    
    def get_or_fetch_result(self, date, month, year) -> Dict[str, Any]:
        """ดึงข้อมูลหวยจากฐานข้อมูล หรือดึงจาก API ถ้ายังไม่มี"""
        try:
            # แปลงเป็น integer ถ้าเป็น string
            try:
                date = int(date)
                month = int(month)
                year = int(year)
            except (ValueError, TypeError):
                return {
                    "success": False,
                    "error": f"ค่า date, month, year ต้องเป็นตัวเลข: date={date}, month={month}, year={year}"
                }
            
            # สร้างวันที่
            draw_date = datetime(year, month, date).date()
            
            # ตรวจสอบว่ามีข้อมูลในฐานข้อมูลแล้วหรือไม่
            existing_result = LottoResult.objects.filter(draw_date=draw_date).first()
            
            if existing_result:
                logger.info(f"📋 ดึงข้อมูลจากฐานข้อมูลสำหรับวันที่ {draw_date.strftime('%d/%m/%Y')}")
                return {
                    "success": True,
                    "source": "database",
                    "origin": existing_result.source,
                    "is_valid": existing_result.is_valid,
                    "data": existing_result.result_data,
                    "message": "ข้อมูลจากฐานข้อมูล",
                    "draw_date": existing_result.draw_date,
                    "updated_at": existing_result.updated_at
                }
            
            # ถ้าไม่มีในฐานข้อมูล ให้ดึงจาก API
            logger.info(f"🔍 ไม่พบข้อมูลในฐานข้อมูล ดึงจาก API สำหรับวันที่ {draw_date.strftime('%d/%m/%Y')}")
            api_result = self.fetch_from_api(date, month, year)
            
            if not api_result:
                return {
                    "success": False,
                    "error": "ไม่สามารถดึงข้อมูลจาก API ได้"
                }
            
            # บันทึกลงฐานข้อมูล
            db_saved = self.save_to_database(api_result, draw_date)
            
            return {
                "success": True,
                "source": "api",
                "origin": "GLO API",
                "data": api_result,
                "message": "ข้อมูลจาก API และบันทึกลงฐานข้อมูลแล้ว",
                "database_saved": db_saved,
                "draw_date": draw_date,
                "updated_at": timezone.now()
            }
            
        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดใน get_or_fetch_result: {e}")
            return {
                "success": False,
                "error": f"เกิดข้อผิดพลาด: {str(e)}"
            }
    
    def save_to_database(self, lotto_data: Dict[str, Any], draw_date: datetime.date) -> bool:
        """บันทึกข้อมูลหวยลงฐานข้อมูล (idempotent ต่อ draw_date).

        กติกา canonical (Task 6): LottoResult เป็น source-of-truth ไฟล์ดิบ —
        writer เดียวคือ service นี้เท่านั้น ห้ามเขียนจากที่อื่นโดยตรง.
        - sync ซ้ำไม่สร้างแถวซ้ำ (unique draw_date + update path)
        - ห้ามทับข้อมูลที่ valid แล้วด้วยข้อมูลเสีย
        """
        from django.db import IntegrityError

        try:
            validation_result = self.validate_lotto_data(lotto_data)
            is_valid = validation_result.get('is_valid', False)
            errors = validation_result.get('error', '') if not is_valid else ""

            # ตรวจสอบว่ามีข้อมูลในฐานข้อมูลแล้วหรือไม่
            existing_result = LottoResult.objects.filter(draw_date=draw_date).first()

            if existing_result:
                if existing_result.is_valid and not is_valid:
                    # ปกป้องข้อมูลที่ถูกแล้ว: อัปเดตแค่เวลาตรวจสอบ
                    logger.warning(
                        f"🛡️ ไม่ทับข้อมูลที่ valid แล้วสำหรับวันที่ {draw_date.strftime('%d/%m/%Y')}"
                    )
                    existing_result.last_checked = timezone.now()
                    existing_result.save(update_fields=['last_checked'])
                    return False
                logger.info(f"📝 อัปเดตข้อมูลหวยที่มีอยู่แล้วสำหรับวันที่ {draw_date.strftime('%d/%m/%Y')}")
                existing_result.result_data = lotto_data
                existing_result.raw_api_response = lotto_data
                existing_result.is_valid = is_valid
                existing_result.validation_errors = errors
                existing_result.last_checked = timezone.now()
                existing_result.save()
            else:
                logger.info(f"💾 บันทึกข้อมูลหวยใหม่สำหรับวันที่ {draw_date.strftime('%d/%m/%Y')}")

                # สร้างข้อมูลใหม่
                try:
                    LottoResult.objects.create(
                        draw_date=draw_date,
                        result_data=lotto_data,
                        source="GLO API",
                        is_valid=is_valid,
                        last_checked=timezone.now(),
                        raw_api_response=lotto_data,
                        validation_errors=errors
                    )
                except IntegrityError:
                    # แข่งกันสร้างพร้อมกัน: ถอยกลับไป update path
                    logger.warning(f"⚠️ แถวซ้ำสำหรับ {draw_date} ถอยไป update")
                    return self.save_to_database(lotto_data, draw_date)

            return True

        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดในการบันทึกลงฐานข้อมูล: {e}")
            return False
    
    def get_latest_results(self, days_back: int = 7) -> Dict[str, Any]:
        """ดึงข้อมูลหวยล่าสุดหลายวัน"""
        results = []
        today = timezone.now().date()
        
        for i in range(days_back):
            target_date = today - timedelta(days=i)
            
            result = self.get_or_fetch_result(
                date=str(target_date.day),
                month=str(target_date.month),
                year=str(target_date.year)
            )
            
            if result["success"]:
                results.append({
                    "date": target_date.strftime('%d/%m/%Y'),
                    "draw_date": target_date,
                    "data": result["data"],
                    "source": result["source"],
                    "updated_at": result.get("updated_at")
                })
        
        return {
            "success": True,
            "total_results": len(results),
            "results": results
        }
    
    def clear_all_data(self) -> bool:
        """ล้างข้อมูลทั้งหมดในฐานข้อมูล"""
        try:
            count = LottoResult.objects.count()
            LottoResult.objects.all().delete()
            logger.info(f"🗑️ ล้างข้อมูลทั้งหมด {count} รายการสำเร็จ")
            return True
        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดในการล้างข้อมูล: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """ดึงสถิติข้อมูล"""
        try:
            total_records = LottoResult.objects.count()
            today_records = LottoResult.objects.filter(
                draw_date=timezone.now().date()
            ).count()
            recent_records = LottoResult.objects.filter(
                draw_date__gte=timezone.now().date() - timedelta(days=7)
            ).count()
            
            return {
                "success": True,
                "statistics": {
                    "total_records": total_records,
                    "today_records": today_records,
                    "recent_records": recent_records,
                    "last_updated": timezone.now()
                }
            }
        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดในการดึงสถิติ: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def refresh_data_from_api(self, date, month, year) -> Dict[str, Any]:
        """อัปเดตข้อมูลจาก API กองสลากใหม่ (บังคับดึงใหม่)"""
        try:
            # แปลงเป็น integer ถ้าเป็น string
            try:
                date = int(date)
                month = int(month)
                year = int(year)
            except (ValueError, TypeError):
                return {
                    "success": False,
                    "error": f"ค่า date, month, year ต้องเป็นตัวเลข: date={date}, month={month}, year={year}"
                }
            
            # สร้างวันที่
            draw_date = datetime(year, month, date).date()
            
            logger.info(f"🔄 บังคับดึงข้อมูลใหม่จาก GLO API สำหรับวันที่ {draw_date.strftime('%d/%m/%Y')}")
            
            # ดึงข้อมูลใหม่จาก API
            api_result = self.fetch_from_api(date, month, year)
            
            if not api_result:
                return {
                    "success": False,
                    "error": "ไม่สามารถดึงข้อมูลจาก API ได้"
                }
            
            # บันทึกลงฐานข้อมูล (อัปเดตหรือสร้างใหม่)
            db_saved = self.save_to_database(api_result, draw_date)
            
            if db_saved:
                logger.info(f"✅ อัปเดตข้อมูลจาก API สำเร็จสำหรับวันที่ {draw_date.strftime('%d/%m/%Y')}")
                return {
                    "success": True,
                    "source": "api_refresh",
                    "data": api_result,
                    "message": "อัปเดตข้อมูลจาก API กองสลากใหม่แล้ว",
                    "database_saved": True,
                    "draw_date": draw_date,
                    "updated_at": timezone.now()
                }
            else:
                logger.error(f"❌ ไม่สามารถบันทึกลงฐานข้อมูลได้สำหรับวันที่ {draw_date.strftime('%d/%m/%Y')}")
                return {
                    "success": False,
                    "error": "ไม่สามารถบันทึกลงฐานข้อมูลได้"
                }
                
        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดใน refresh_data_from_api: {e}")
            return {
                "success": False,
                "error": f"เกิดข้อผิดพลาด: {str(e)}"
            }

    def validate_lotto_data(self, lotto_data: Dict[str, Any]) -> Dict[str, Any]:
        """ตรวจสอบความถูกต้องของข้อมูลหวย"""
        try:
            if not isinstance(lotto_data, dict):
                return {
                    "is_valid": False,
                    "error": "ข้อมูลไม่ใช่รูปแบบที่ถูกต้อง"
                }
            
            # ตรวจสอบ response structure
            if 'response' not in lotto_data or lotto_data['response'] is None:
                return {
                    "is_valid": False,
                    "error": "ไม่มีข้อมูล response หรือ response เป็น null"
                }
            
            response = lotto_data['response']
            
            # ตรวจสอบ result structure
            if 'result' not in response or response['result'] is None:
                return {
                    "is_valid": False,
                    "error": "ไม่มีข้อมูล result ในงวดนี้"
                }
            
            result = response['result']
            
            # ตรวจสอบ data structure (ข้อมูลรางวัล)
            if 'data' not in result:
                return {
                    "is_valid": False,
                    "error": "ไม่มีข้อมูลรางวัล"
                }
            
            data = result['data']
            
            # ตรวจสอบว่ามีข้อมูลรางวัลที่จำเป็นหรือไม่
            required_fields = ['first', 'second', 'third', 'fourth', 'fifth']
            missing_fields = []
            
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
                elif not isinstance(data[field], dict) or 'number' not in data[field]:
                    missing_fields.append(field)
                elif not data[field]['number'] or len(data[field]['number']) == 0:
                    missing_fields.append(f"{field} (ว่างเปล่า)")
            
            if missing_fields:
                return {
                    "is_valid": False,
                    "error": f"ข้อมูลรางวัลไม่ครบถ้วน: {', '.join(missing_fields)}",
                    "missing_fields": missing_fields
                }
            
            # ตรวจสอบรางวัลที่ 1 (สำคัญที่สุด)
            if not data['first']['number'][0]['value']:
                return {
                    "is_valid": False,
                    "error": "ไม่มีหมายเลขรางวัลที่ 1"
                }
            
            return {
                "is_valid": True,
                "message": "ข้อมูลครบถ้วนและถูกต้อง"
            }
            
        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดในการตรวจสอบข้อมูล: {e}")
            return {
                "is_valid": False,
                "error": f"เกิดข้อผิดพลาดในการตรวจสอบ: {str(e)}"
            }

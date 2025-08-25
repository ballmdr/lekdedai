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
        """บันทึกข้อมูลหวยลงฐานข้อมูล"""
        try:
            # ตรวจสอบว่ามีข้อมูลในฐานข้อมูลแล้วหรือไม่
            existing_result = LottoResult.objects.filter(draw_date=draw_date).first()
            
            if existing_result:
                logger.info(f"📝 อัปเดตข้อมูลหวยที่มีอยู่แล้วสำหรับวันที่ {draw_date.strftime('%d/%m/%Y')}")
                # อัปเดตข้อมูลที่มีอยู่
                existing_result.result_data = lotto_data
                existing_result.updated_at = timezone.now()
                existing_result.save()
            else:
                logger.info(f"💾 บันทึกข้อมูลหวยใหม่สำหรับวันที่ {draw_date.strftime('%d/%m/%Y')}")
                # สร้างข้อมูลใหม่
                LottoResult.objects.create(
                    draw_date=draw_date,
                    result_data=lotto_data,
                    source="GLO API"
                )
            
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
            
            # ตรวจสอบว่ามีข้อมูลรางวัลที่จำเป็นหรือไม่
            required_fields = ['first', 'second', 'third', 'fourth', 'fifth']
            missing_fields = []
            
            for field in required_fields:
                if field not in lotto_data:
                    missing_fields.append(field)
                elif not isinstance(lotto_data[field], dict) or 'number' not in lotto_data[field]:
                    missing_fields.append(field)
            
            if missing_fields:
                return {
                    "is_valid": False,
                    "error": f"ข้อมูลไม่ครบถ้วน: ขาด {', '.join(missing_fields)}",
                    "missing_fields": missing_fields
                }
            
            # ตรวจสอบว่าข้อมูลไม่ว่างเปล่า
            for field in required_fields:
                if not lotto_data[field]['number'] or len(lotto_data[field]['number']) == 0:
                    return {
                        "is_valid": False,
                        "error": f"ข้อมูล {field} ว่างเปล่า",
                        "empty_field": field
                    }
            
            return {
                "is_valid": True,
                "message": "ข้อมูลถูกต้อง"
            }
            
        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดในการตรวจสอบข้อมูล: {e}")
            return {
                "is_valid": False,
                "error": f"เกิดข้อผิดพลาดในการตรวจสอบ: {str(e)}"
            }

#!/bin/bash
# Daily Lucky Numbers Update Script
# วางไฟล์นี้ใน crontab เพื่ออัพเดทอัตโนมัติเวลา 09:00 ทุกวัน

# เข้าไปที่โฟลเดอร์โปรเจค
cd /path/to/your/lekdedai/app

# เรียกใช้ management command
python manage.py update_daily_numbers

# บันทึก log พร้อมวันที่
echo "$(date): Daily numbers updated" >> /var/log/lekdedai_daily_update.log
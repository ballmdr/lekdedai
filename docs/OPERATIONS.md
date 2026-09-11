# Operations Runbook — Scheduler & Freshness (Task 24)

โปรเจกต์ไม่ใช้ Docker: งานตามตารางรันด้วย cron/systemd timer เรียก
`manage.py run_scheduled_jobs` ถี่ ๆ (เช่นทุก 15 นาที) คำสั่งนี้เลือกเฉพาะ
งานที่ถึงกำหนด รันทีละตัวใน process แยกพร้อม timeout จริง

```cron
*/15 * * * * /opt/lekdedai/.venv/bin/python /opt/lekdedai/app/manage.py run_scheduled_jobs >> /var/log/lekdedai/scheduler.log 2>&1
```

## ตารางงาน (`app/qa/jobs.py` — แก้ที่นี่ที่เดียว)

| key | งาน | ทุก | ลองซ้ำ | timeout | stale เมื่อ |
|---|---|---|---|---|---|
| lotto_sync | ซิงค์ผลหวย 30 วัน | 24 ชม. | 3×/ชม. | 10 นาที | 48 ชม. |
| rss_ingest | ดึงข่าว RSS (limit 20) | 6 ชม. | 3×/30 นาที | 10 นาที | 12 ชม. |
| category_fallback | ขูด fallback (ข้ามถ้า RSS สด) | 12 ชม. | 2×/ชม. | 10 นาที | 48 ชม. |
| ai_generate | ทำนาย AI งวดถัดไป | 24 ชม. | 2×/2 ชม. | 20 นาที | 48 ชม. |
| accuracy_reconcile | ตรวจผลย้อนหลังสูตร | 24 ชม. | 2×/ชม. | 10 นาที | 72 ชม. |
| dreams_cleanup | ลบประวัติฝันเกิน 90 วัน | 7 วัน | 2×/2 ชม. | 10 นาที | 14 วัน |

รันเฉพาะตัว: `manage.py run_scheduled_jobs --job rss_ingest`
บังคับรัน (ยังเคารพ lock): `manage.py run_scheduled_jobs --force`

## กติกา

- lock กันรันทับ (`JobRun.status=running` + `locked_at`) ล็อกค้างเกิน timeout ยึดได้
- ล้ม → ตั้ง `next_run_at` ตาม retry delay จนหมดโควตา แล้วรอรอบปกติ
- ทุก job ต้อง idempotent (รันซ้ำไม่สร้างซ้ำ) — บังคับโดย test
- UI: `/news/` + หน้าแรกโชว์ป้าย stale ตามอายุข่าว, `/lotto_stats/` โชว์สถานะซิงค์
  จาก `JobRun` (ดู `qa.jobs.get_job_freshness`)

## เมื่อ job แดง (ดูใน admin: งานตามตาราง)

1. อ่าน `last_error` (ย่อ 1000 อักษรท้าย) + log เต็มใน scheduler.log
2. แก้ต้นเหตุ (API ล่ม/key หมด/ดิสก์เต็ม) แล้วรัน `--job <key>` ด้วยมือ 1 ครั้ง
3. ถ้าค้างสถานะ running เกิน timeout 2 เท่า: ตรวจสอบ process ซ้ำ แล้วลบแถว
   `JobRun` นั้นทิ้งได้ (รอบถัดไปสร้างใหม่เอง) — ห้ามลบแถว success/failure ปกติ
4. ห้ามแก้ `next_run_at` ด้วยมือเพื่อเร่งงาน ยกเว้นเหตุฉุกเฉิน (บันทึกเหตุผลไว้)

## เฝ้าระวัง + backup + rollback (Task 25)

- Health สาธารณะ: `GET /health/` (200 ok / 503 degraded พร้อมรายการปัญหา)
  เอาไว้ผูก uptime monitor ภายนอกได้เลย
- Metrics ละเอียด: `GET /metrics/` (staff เท่านั้น) — จำนวน request/latency/5xx/AI
- Logs: console เสมอ (production เป็น JSON) + ตั้ง `LOG_FILE` เพื่อเขียนไฟล์
- Alerts: `manage.py check_alerts` (cron ทุก 30 นาที) ตรวจ job ล้ม/stale,
  ingestion ล้ม, 5xx พุ่ง, AI ล้ม; `--send` ส่งอีเมลถ้าตั้ง SMTP ไว้
- Backup: `manage.py backup_db` (cron รายวัน, เก็บ 7 ไฟล์ล่าสุด)
- Restore (ซ้อม): หยุด web -> `manage.py restore_db --file <ไฟล์> --confirm`
  -> สตาร์ท web -> ตรวจ `/health/` และจำนวนแถวสำคัญ
- Rollback: `APP_DIR=/opt/lekdedai bash deploy/rollback.sh <commit-หรือ-tag>`
  (backup อัตโนมัติก่อนย้อนทุกครั้ง)

# Launch Checklist — LekdeDai (Task 29)

ใช้ก่อนเปิด staging dress rehearsal และก่อนเปิด public (Task 31)

## 1. Environment & secrets
- [ ] `SECRET_KEY` สุ่มยาวใหม่ (ไม่ใช้ค่า dev/ในgit)
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` = โดเมนจริงเท่านั้น (ไม่ใช่ `*`)
- [ ] `CSRF_TRUSTED_ORIGINS` = https โดเมนจริง
- [ ] `DATABASE_URL` ชี้ Postgres จริง (ไม่ใช่ SQLite)
- [ ] `DJANGO_SUPERUSER_PASSWORD` ตั้งใหม่ (ไม่ใช้ admin123)
- [ ] TLS อยู่ข้างหน้า + เปิด `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`,
      `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS` แล้วรัน `check --deploy` ผ่าน

## 2. Runtime
- [ ] รันด้วย gunicorn + systemd (`deploy/lekdedai.service`) ไม่ใช่ runserver
- [ ] `manage.py migrate` + `collectstatic` เป็น deploy step (ล้มแล้วหยุด)
- [ ] `GET /health/` = 200 ok

## 3. ข้อมูลตั้งต้น
- [ ] `setup_ai_data_sources --create-sources` (แหล่งข่าว + license approved)
- [ ] `populate_lottery_data` (สูตร)
- [ ] `add_dream_data` (คัมภีร์ฝัน)
- [ ] `sync_lotto_data` มีผลหวยย้อนหลังเพียงพอ

## 4. งานอัตโนมัติ
- [ ] cron: `run_scheduled_jobs` ทุก 15 นาที (ดู `docs/OPERATIONS.md`)
- [ ] cron: `check_alerts --send` ทุก 30 นาที
- [ ] cron: `backup_db` รายวัน (เก็บ ≥7 ไฟล์)
- [ ] cron: `analytics_report` รายงวด (Task 28)
- [ ] cron: `beta_report --draws 2 --output reports/beta-2draws.json --format json` รายงวด (Task 30)

## 4.1 Closed beta / staged rollout (Task 30–31)
- [ ] `BETA_MODE`/`BETA_INVITE_CODES` หรือ `ROLLOUT_STAGE` ตั้งถูก stage
- [ ] `seed_beta_invites` แล้ว และทดสอบ `/beta/` + รหัสจริง
- [ ] `ROLLOUT_KILL_SWITCH` ทดสอบแล้ว (ผู้ใช้ทั่วไปเห็น `/beta/closed/`, staff เข้าได้)
- [ ] `production_smoke --base-url <โดเมน>` ผ่าน
- [ ] เกณฑ์หยุดอัตโนมัติทำงาน (สร้าง `SystemFlag` P0 แล้วทดสอบ → closed)
- [ ] ดู `docs/BETA_RUNBOOK.md` + `docs/ROLLOUT_RUNBOOK.md`

## 5. Rehearsal & recovery
- [ ] `manage.py rehearsal_check` = pass/degraded (ไม่มี fail) + เก็บรายงาน
- [ ] restore drill ผ่าน (ดู OPERATIONS.md)
- [ ] rollback rehearsal ผ่าน: `deploy/rollback.sh <tag ก่อนหน้า>`

## 6. Policy & support
- [ ] `/privacy/`, `/terms/`, `/contact/` เปิดใช้และลิงก์จาก footer
- [ ] ประกาศช่องทาง support + ผู้รับผิดชอบ (ดู INCIDENT_RUNBOOK.md)
- [ ] ยืนยันว่า disclaimer อยู่ทุกจุดที่แสดงเลข

## ลงนาม (sign-off)

| รายการ | ผู้รับผิดชอบ | วันที่ | หลักฐาน |
|---|---|---|---|
| environment/secrets | _owner ops_ | | `check --deploy` output |
| rehearsal | _owner QA_ | | `reports/rehearsal-*.json` (sha256) |
| rollback | _owner ops_ | | บันทึกการซ้อม |
| นโยบาย/ซัพพอร์ต | _owner product_ | | ลิงก์หน้าเว็บ |

> หมายเหตุ: รายงาน rehearsal มี `git_rev` + `report_sha256` ให้ผูกกับ commit ที่ทดสอบ
> ต้องแนบ screenshot หน้าจอหลัก (desktop+mobile) และ incident notes (ถ้ามี) ไว้กับรายงาน

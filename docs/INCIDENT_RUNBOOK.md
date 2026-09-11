# Incident & Support Runbook — LekdeDai (Task 29)

## บทบาทและช่องทาง

| บทบาท | หน้าที่ | ช่องทาง |
|---|---|---|
| Ops owner | deploy/rollback, backup/restore, scheduler | _กำหนดตอน setup_ |
| Product owner | ตัดสินใจหยุด/เปิด rollout, ตอบผู้ใช้ | _อีเมล/ไลน์ทีม_ |
| Support | รับแจ้งจากผู้ใช้ (`/contact/` + admin ContactMessage) | `/contact/` |

ผู้ใช้แจ้งปัญหาได้ที่ `/contact/` → เข้า admin `ข้อความติดต่อ` (มี status ใหม่/อ่านแล้ว/ดำเนินการแล้ว)

## ระดับความรุนแรง

- **P0** — ผลหวยผิด, ข้อมูลผู้ใช้รั่ว, ระบบล่มทั้งเว็บ → หยุด rollout + rollback ทันที
- **P1** — ฟีเจอร์หลักพัง (ตรวจหวย/ฝัน/สมุดเลข ใช้ไม่ได้), ข้อมูล stale นานผิดปกติ
- **P2** — UI เพี้ยน, ข้อความผิด, ช้า

## P0: ผลหวยผิด (สำคัญสุด — กระทบความเชื่อมั่น)

1. ยืนยันกับ `/health/` และเทียบ `LottoResult` กับสำนักงานสลากฯ
2. ถ้าข้อมูลผิดจริง: `manage.py shell` แก้เฉพาะแถวที่ผิด **หรือ** ลบด้วย admin
   แล้ว `clear_and_fetch_lotto` / `run_scheduled_jobs --job lotto_sync --force`
3. ประกาศหยุดใช้ผลตรวจชั่วคราวถ้าแก้ไม่ทัน
4. บันทึก incident + แจ้ง product owner

## P0: ระบบล่ม / deploy ผิดปกติ

1. `systemctl status lekdedai` + `journalctl -u lekdedai -n 200`
2. Rollback: `APP_DIR=/opt/lekdedai bash deploy/rollback.sh <tag-ก่อนหน้า>`
   (สคริปต์ backup DB ก่อนย้อนเสมอ)
3. ตรวจ `/health/` = 200 แล้วประกาศกลับสู่ปกติ

## P0: ข้อมูลรั่ว

1. ตัดช่องทางที่สงสัย (ปิด endpoint/ปิดหน้า) ทันที
2. เก็บ log ไว้ตรวจ (`LOG_FILE`)
3. แจ้ง product owner ตัดสินใจแจ้งผู้ใช้/GDPR-CCPA ตามนโยบาย

## P1: job ล้ม / ข้อมูล stale

1. admin `งานตามตาราง` ดู `last_error` + log
2. รัน `manage.py run_scheduled_jobs --job <key>` ด้วยมือ 1 ครั้ง
3. ถ้า provider (AI/GLO) ล่ม: รอ retry อัตโนมัติ + ประกาศ degraded บน UI
   (ระบบแสดง stale/degraded เองอยู่แล้ว)
4. ถ้าล็อกค้าง: ปฏิบัติตาม OPERATIONS.md ข้อ 3

## P1: AI provider ล่ม

- ระบบออกแบบให้ best-effort: ข่าวบันทึกเป็น draft, ฝัน fallback ตำรา — ไม่ต้องแก้โค้ด
- ตรวจ `/metrics/` (external_ai_calls) และ `check_alerts`

## Backup / Restore (ซ้อมแล้วใน rehearsal)

```
manage.py backup_db                       # สำรอง
# หยุด web ก่อน
manage.py restore_db --file <ไฟล์> --confirm
# สตาร์ท web แล้วตรวจ /health/
```

## หลังปิดเหตุ (post-incident)

- [ ] บันทึก timeline, root cause, action
- [ ] เพิ่ม regression test / alert ถ้าจำเป็น
- [ ] อัปเดต runbook นี้ถ้าขั้นตอนเปลี่ยน

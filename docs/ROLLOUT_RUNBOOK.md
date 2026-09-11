# Staged Rollout Runbook — LekdeDai (Task 31)

ใช้หลังผ่าน closed beta (Task 30) เพื่อเปิดสาธารณะทีละขั้น พร้อม kill switch และ
post-launch review ครบ 24 ชั่วโมง / 7 วัน / หลังงวดแรก

## 1. ขั้นการเปิด (stages)

ตั้งค่า env แล้ว restart service:

```bash
ROLLOUT_STAGE=beta    # ปิดประตู ต้องมีรหัสเชิญ
ROLLOUT_STAGE=pct10   # เปิดอัตโนมัติ ~10% ของเซสชัน (deterministic ต่อ session)
ROLLOUT_STAGE=public  # เปิดเต็ม
ROLLOUT_PERCENT=10    # ปรับเปอร์เซ็นต์ตอน pct10 ได้
```

- `pct10` แบ่งผู้ใช้จาก hash ของ session key → ผู้ใช้เดิมได้ค่าเดิม ไม่สลับไปมา
- `BETA_MODE=True` ยังบังคับให้ต้องมีรหัสเสมอ (ใช้คู่กับ `ROLLOUT_STAGE=beta`)
- **Kill switch**: `ROLLOUT_KILL_SWITCH=True` → ผู้ใช้ทั่วไปเห็น `/beta/closed/`
  ทันที (staff ยังเข้าได้) ใช้เมื่อเกิด P0 โดยไม่ต้อง rollback โค้ด
- **ข่าว (สำคัญ)**: ค่าเริ่มต้น `NEWS_AUTO_PUBLISH=False` = ข่าวทุกชิ้นเป็น draft
  staff ต้องอนุมัติใน admin (`ข่าว` → action publish) ก่อนเผยแพร่ → เปิด Public ได้
  อย่างปลอดภัยโดยไม่มีข่าว auto หลุด. จะเปิด `NEWS_AUTO_PUBLISH=True` เฉพาะหลัง
  ทดสอบตัวกรองความเกี่ยวข้อง/แยกวันที่-ปี-จำนวน กับข่าวจริง และกำหนด precision gate แล้ว

## 2. เปิด public ทีละขั้น

1. **pct10** → เฝ้า 24 ชม. ตามเทมเพลตข้อ 4
2. ถ้าผ่าน → **public** → เฝ้า 7 วัน + หลังงวดแรก
3. ก่อนเปิดเต็ม ตรวจ `docs/LAUNCH_CHECKLIST.md` ครบและ sign-off

## 3. Production smoke test

```bash
# ตรวจจากในเครื่อง (มี DB) — HTTP + ผลหวยล่าสุด
SMOKE_BASE_URL=https://lekdedai.com python app/manage.py production_smoke

# หรือระบุเอง
python app/manage.py production_smoke --base-url https://lekdedai.com
python app/manage.py production_smoke --base-url https://lekdedai.com --max-stale-days 5
```

ตรวจ: `/health/` = 200, route หลัก (`/`, `/dreams/`, `/lottery_checker/`, `/notebook/`,
`/lotto_stats/`, `/news/`, `/lotto_formula/`, `/ai/`), `/static/css/tailwind.css`
และมีผลหวยล่าสุดไม่เก่าเกิน `--max-stale-days` — exit 1 เมื่อพบปัญหา
ใช้เป็น post-deploy check หรือผูกกับ monitor ภายนอก

## 4. Post-launch review templates

### 4.1 หลัง 24 ชั่วโมง (ทันทีหลังขยาย traffic)

| หัวข้อ | ค่า | เกณฑ์ผ่าน |
|---|---|---|
| `/health/` | ok / degraded | ok เป็นส่วนใหญ่ |
| 5xx (จาก `/metrics/`) | | ไม่มีแนวโน้มเพิ่ม |
| job ล้ม/ล้าสมัย | | 0 หรือมี mitigation |
| latency หน้าแรก | | ไม่ช้าผิดปกติ |
| feedback ใหม่ | | รับและตอบภายในวัน |
| provider cost (AI/GLO) | | อยู่ในงบ |

สรุป: ☐ ไปต่อ ☐ หยุดชั่วคราว (kill switch) — เหตุผล: ____

### 4.2 หลัง 7 วัน

| หัวข้อ | ค่า | เกณฑ์ผ่าน |
|---|---|---|
| error rate / stale rate | | ต่ำและคงที่ |
| activation + result-check | (จาก `beta_report`) | ไม่ตกลงชัดเจน |
| retention ข้ามงวด | | ≥ ระดับ beta |
| backup/restore/rollback | | ซ้อมผ่าน |
| P0/P1 | | 0 ค้าง |

สรุป: ☐ คง public ☐ ลด stage ☐ rollback — เหตุผล: ____

### 4.3 หลังงวดแรก (หลังเปิด public)

- [ ] ผลหวยงวดแรกตรงกับสำนักงานสลากฯ (`/health/`, `LottoResult`)
- [ ] ผู้ใช้ตรวจผลและเห็นประวัติถูกต้อง (`result_checked`)
- [ ] ไม่มี P0/P1 ใหม่
- [ ] เก็บรายงาน `beta_report`/`analytics_report` แนบ sign-off

## 5. Rollback / หยุดฉุกเฉิน

```bash
# หยุดรับผู้ใช้ทันทีโดยไม่ต้อง deploy
ROLLOUT_KILL_SWITCH=True   # แล้ว restart service

# ย้อนโค้ดทั้งชุด (backup DB ก่อนย้อนอัตโนมัติ)
APP_DIR=/opt/lekdedai bash deploy/rollback.sh <commit-หรือ-tag>
```

ดูรายละเอียดเหตุการณ์ที่ `docs/INCIDENT_RUNBOOK.md`

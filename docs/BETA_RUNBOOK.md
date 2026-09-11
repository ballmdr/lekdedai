# Closed Beta Runbook — LekdeDai (Task 30)

ใช้คู่กับ `docs/LAUNCH_CHECKLIST.md`, `docs/INCIDENT_RUNBOOK.md`, `docs/OPERATIONS.md`
เป้าหมาย: เปิดกลุ่มเล็ก ใช้งานจริงอย่างน้อย **2 งวด** เก็บ funnel/feedback แล้วตัดสิน go/no-go

## 1. เปิดประตู beta

ตั้งค่า env (ห้าม hard-code):

```bash
BETA_MODE=True
BETA_INVITE_CODES=code-กลุ่มA,code-กลุ่มB   # รหัสเชิญตั้งต้น
ROLLOUT_STAGE=beta                          # beta | pct10 | public
ROLLOUT_KILL_SWITCH=False                    # เปิดเพื่อปิดเว็บทันที
```

จากนั้น seed รหัสลงฐานข้อมูล (idempotent):

```bash
python app/manage.py seed_beta_invites --label "รอบแรก" --max-uses 1
```

- ผู้ใช้เห็นหน้า `/beta/` ให้กรอกรหัส ระบบจำกัด 20 ครั้ง/นาทีต่อ IP กันการเดารหัส
- รหัสที่ประกาศใน `BETA_INVITE_CODES` จะถูกบันทึกลงตาราง `รหัสเชิญ beta` อัตโนมัติเมื่อใช้ครั้งแรก
- จัดการ/เพิกถอนรหัสและดูจำนวนครั้งที่ใช้ได้ที่ admin → **รหัสเชิญ beta**
- staff เข้าเว็บได้เสมอไม่ต้องใช้รหัส

**ยกเว้นประตู:** `/beta/`, `/health/`, `/metrics/`, `/admin/`, static/media,
`/analytics/event/`, `/contact/`, `/privacy/`, `/terms/`

## 2. เชิญผู้ใช้

- เป้าหมายรอบแรก ~5–20 คน ผ่านช่องทางที่กำหนด (อีเมล/ไลน์กลุ่ม/ชุมชน)
- แนบคำชี้แจงว่าเป็นช่วงทดลอง ข้อมูลสมุดเลขเก็บในเบราว์เซอร์ และช่องทางแจ้งปัญหา
- อย่าใช้รหัสซ้ำหลายคน เว้นแต่ตั้ง `max_uses` ให้เหมาะ เพื่อวัด retention ต่อคน

## 3. ช่องทาง support และผู้รับผิดชอบ

| บทบาท | หน้าที่ | ช่องทาง |
|---|---|---|
| Product owner | ตอบ feedback, ตัดสิน go/no-go | อีเมล/ไลน์ทีม |
| Ops owner | deploy/scheduler/rollback | INCIDENT_RUNBOOK |
| Support | รับเรื่องจากผู้ใช้ | `/contact/?type=beta` → admin `ข้อความติดต่อ` |

ผู้ใช้เลือกประเภท **“ข้อเสนอแนะช่วง beta”** ได้จาก `/contact/` หรือลิงก์บนหน้า `/beta/`
ทีมงานติดตาม/ปิดสถานะได้ใน admin (ใหม่ → อ่านแล้ว → ดำเนินการแล้ว)

## 4. เกณฑ์หยุดอัตโนมัติ (stop criteria)

ระบบอ่านสัญญาณและหยุดให้เอง (`qa/rollout.py::compute_beta_status`) โดยแสดงประกาศบนหัวเว็บ:

| สัญญาณ | สถานะ | พฤติกรรม |
|---|---|---|
| `SystemFlag` ระดับ **P0** ที่ยัง active | **closed** | ไม่รับทุกคน (staff ยังเข้าได้) → หน้า `/beta/closed/` |
| `ROLLOUT_KILL_SWITCH=True` | **closed** | เหมือน P0 |
| job ล้มเหลว / ข้อมูลล้าสมัย / ดึงข่าวล้มเหลว | **paused** | ยังใช้งานได้ แต่ขึ้นแบนเนอร์เตือน “degraded” |
| ไม่มีสัญญาณ | **open** | ใช้งานปกติ |

เปิด/ปิด P0 ได้ที่ admin → **ธงเหตุการณ์** (เช่น `lottery-wrong`, `data-leak`)
ปิดเหตุแล้วระบบกลับสู่ `open` อัตโนมัติ (มี cache ~60 วินาที; ดู `BETA_STATUS_CACHE_SECONDS`)

## 5. รายงานต่อ 2 งวด

```bash
python app/manage.py beta_report --draws 2 --output reports/beta-2draws.txt
python app/manage.py beta_report --draws 2 --output reports/beta-2draws.json --format json
```

รายงานมี: activation (บันทึกเลข), dream completion, result-check rate,
cross-draw retention, feedback แยกประเภท, รหัสเชิญที่ใช้ และสถานะระบบ
นำตัวเลขไปกรอกใน `docs/CHECKPOINT_E.md`

## 6. เกณฑ์ go / no-go (สรุปให้ที่ประชุม)

**Go ต่อ (ไป Task 31 staged rollout) เมื่อ:**
- มีผู้ใช้จริงกลุ่มแรกและมี feedback เข้ามา
- งวดล่าสุด ≥2 งวดมีข้อมูล activation/result-check
- ไม่มี P0/P1 ค้าง หรือมี mitigation ที่ product owner ยอมรับ
- `/health/` = 200 ตลอดช่วงที่เฝ้า (หรือ degraded ที่อธิบายได้และปิดแล้ว)

**No-go / หยุด เมื่อ:**
- พบผลหวยผิด (P0) หรือข้อมูลรั่ว
- ฟีเจอร์หลัก (ตรวจหวย/ฝัน/สมุดเลข) ใช้ไม่ได้ต่อเนื่อง
- ข้อมูลล้าสมัยเกินเกณฑ์โดยไม่มีกำหนดแก้

## 7. ปิด beta

- ตั้ง `ROLLOUT_STAGE=pct10` หรือ `public` เมื่อ go (ดู `docs/ROLLOUT_RUNBOOK.md`)
- เก็บรายงาน `beta_report` + feedback ที่ยังไม่ปิดเป็นหลักฐานประกอบ sign-off
  `docs/LAUNCH_CHECKLIST.md`

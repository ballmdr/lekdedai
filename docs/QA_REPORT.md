# QA Report — Release Candidate Gate (Task 27)

อัปเดต: กันยายน 2569 · รันด้วย `manage.py quality_gate` (รวม `qa.tests_gates`)

## Performance budget (query ต่อ request)

ตรวจอัตโนมัติด้วย `QueryBudgetTests` — เกินเมื่อไหร่ test แดงทันที

| route | budget | วัดจริง |
|---|---:|---:|
| `/` | 25 | 17 |
| `/lotto_stats/` | 20 | 11 |
| `/news/` | 15 | 6 |
| `/ai/data-sources/` | 20 | 9 |
| `/dreams/` | 15 | 11 |
| `/ai/` | 15 | 6 |
| อื่น ๆ | 5–15 | ≤ 2 |

การปรับที่ทำในรอบนี้:
- `StatsCalculator` โหลดงวดครั้งเดียวเป็น list แล้วกรองใน memory (เดิมสแกนตารางซ้ำต่อ method)
- `/news/` และหน้าแรก `select_related('data_source')` ตัด N+1 provenance
- `/ai/data-sources/` ใช้ `annotate(Count(...))` แทน lambda ต่อแหล่ง
- `qa.jobs.get_job_freshness()` ใช้ `in_bulk` (เดิม query ต่อ job)

## Accessibility (critical violations = 0)

ตรวจอัตโนมัติจาก HTML จริงทุกหน้าหลัก (`AccessibilityGateTests`):
- ทุกหน้าต้องมี `<h1>` เดียว
- input/select/textarea ต้องมี label ผูก `for`/`id`, `aria-label`, หรือ wrapping label
- รูปต้องมี `alt`, ปุ่มต้องมีชื่อ, ห้าม `href="#"`, ห้าม onclick ที่ไม่มีฟังก์ชันรองรับ

แก้ที่พบในรอบนี้: `lottoInput`/`lottoDate` (เพิ่ม `for`), ช่องวันที่ ensemble history,
`sourceTypeFilter`/`statusFilter` ของ data-sources

**ยังต้องตรวจด้วยมือ (ไม่มี browser/Lighthouse ในเครื่อง):** contrast, focus order,
keyboard trap, screen reader จริง — ทำตอน browser rehearsal บน staging (Task 29)

## Compatibility

- มี `lang="th"`, `charset=UTF-8`, `viewport width=device-width`
- static (`tailwind.css`, `theme.css`, `format.js`) เสิร์ฟ 200
- ไม่มี horizontal overflow: ตาราง/การ์ดใช้ `overflow-x-auto`/`flex-wrap` (ตรวจ layout class)

**Browser matrix ที่ตั้งใจรองรับ (ตรวจมือบน staging):**
Chrome/Edge/Safari/Firefox เวอร์ชันปัจจุบัน 2 ล่าสุด + iOS Safari, Android Chrome

## Security headers (production)

`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: same-origin`
ทดสอบอัตโนมัติ (Task 27) และตรวจ `check --deploy` ใน deploy script

## ข้อจำกัดที่รู้ชัด

- ไม่มีการวัด Core Web Vitals (LCP/CLS/INP) อัตโนมัติ — ต้องใช้ Lighthouse/PSI บน staging
- metrics scheduler ยังเป็น in-memory ต่อ process (ดู Task 25) ไม่ได้แทน APM
- query budget อิงข้อมูลว่าง/น้อย — ต้องวัดซ้ำบน staging ที่มีข้อมูลจริงก่อน freeze

## Closed beta QA round (11 Sep 2026, หลัง deploy production)

ผู้รีวิวทดสอบบนเว็บจริง (มือถือ + desktop) แล้วแจ้งปัญหา — แก้รอบนี้:

**P0**
- ผลหวยสองหน้าไม่ตรงกัน → `sync_lotto_data` ใช้ `LottoSyncService` เป็นตัวแปลงเดียว
  (อ่าน `last3f`/`last3b`) และ re-sync production; เพิ่ม `SyncConsistencyTests`
- ข่าว "รอวิเคราะห์" ถูกใช้สร้างเลข → auto-publish เฉพาะ `analysis_status=analyzed`;
  หน้าแรก/ข่าวซ่อนเลขถ้ายังไม่วิเคราะห์; `demote_unanalyzed_news` (demote 19 รายการ)
- หน้าแรกกับ `/ai/` ขัดแย้ง → AI card แสดงเลขเฉพาะ `readiness=ready`
- สัญญาสูตร `even_odd`/`reverse` → คำอธิบายตรงกับผลลัพธ์ 3 หลัก + กติกาตรวจ
- สมุดเลข default งวดเก่า → ตั้งงวดถัดไปเป็นค่าเริ่มต้น + เพิ่มงวดล่วงหน้าในตัวเลือก
- `theme.js` duplicate declaration → ห่อ IIFE; ลบ `console.log` ใน production templates

**P1 ที่แก้แล้ว**
- ตรวจหวยแจ้งรายการที่ไม่ถูกต้อง (ไม่ตัดทิ้งเงียบ)
- สถิติ `average_gap` = null เมื่อออกครั้งเดียว + แบนเนอร์ตัวอย่างน้อย + เลิกคำว่า "ในรอบปี"
- หน้าข่าวไม่งอก intro ซ้ำกับ content; comment form มี label; mobile nav เพิ่มข่าว/AI/สูตร
- ฝัน: single-asterisk markdown แปลงปลอดภัย

**Backlog (ยังไม่แก้ / ต้องออกแบบเพิ่ม)**
- กรองความเกี่ยวข้องข่าว + แยกเลขวันที่/ปี/จำนวนทั่วไป ก่อนตั้ง auto-publish criteria
- รวมผลสัญลักษณ์ฝันซ้ำ (เช่น "งู" + "พญานาค") ให้เป็นชุดเดียว
- จัดรูปแบบวันที่ให้สม่ำเสมอ (พ.ศ./ค.ศ./ISO) ทั้งเว็บ
- วัด a11y/Core Web Vitals จริงด้วย Lighthouse/axe บน staging


# LekdeDai Delivery Checklist

เอกสารรายละเอียด: `tasks/plan.md`

## ระยะที่ 0: ยืนยันฐานระบบ

- [x] Task 1 — ทำแผนผัง runtime และเลือกหน้าบ้านที่ใช้งานจริง (Django = production, Next.js/React = prototype; หน้าแรก+ตรวจหวย 200 local)
- [x] Task 2 — คืน dependency วันที่หวยและทำให้ระบบเริ่มได้ (`app/utils/lottery_dates.py`, `manage.py check` 0 issues)
- [x] Task 3 — สร้าง baseline ที่รันซ้ำได้ (`.env.example` + `setup_local.ps1`, local venv, SQLite, ไม่ใช้ Docker)

### Checkpoint A

- [x] Django checks และ migrations ผ่าน
- [x] URL หลักไม่มี import error
- [x] ระบุ frontend production owner แล้ว
- [x] เริ่มระบบจากเครื่องใหม่ได้ตามเอกสาร

## ระยะที่ 1: ความปลอดภัยและความน่าเชื่อถือ

- [x] Task 4 — ปิดช่องทางเปลี่ยนข้อมูลโดยไม่มีสิทธิ์ (clear/refresh/bulk + ai ingestion = staff-only + POST, 13 tests เขียว)
- [x] Task 5 — ลบข้อมูลสาธิตออกจากเส้นทางจริง (score แทน confidence, empty state ซื่อสัตย์, mock ingestion gated, 17 tests เขียว)
- [x] Task 6 — กำหนดเจ้าของข้อมูลผลหวย (LottoResult canonical + sync valid-only + UI provenance, 20 tests เขียว)
- [x] Task 7 — วางขอบเขตข้อมูลส่วนบุคคล (เลิกเก็บ IP, notice ในฟอร์ม, retention 90 วัน, 23 tests เขียว)

### Checkpoint B

- [x] API สำคัญผ่าน authorization tests
- [x] Production UI ไม่มีข้อมูล mock/fallback ที่สื่อเป็นข้อมูลจริง
- [x] ทบทวนข้อความด้านคะแนนและความแม่นยำแล้ว
- [x] ตรวจเส้นทางเก็บและลบข้อมูลผู้ใช้แล้ว

## ระยะที่ 2: MVP ที่ทำให้คนกลับมาใช้

- [x] Task 8 — ทำหน้าแรกตามงานหลักหนึ่งเส้นทาง (CTA ฝัน→ตรวจผล, nav จริง, ตัด default ปลอม, 24 tests เขียว)
- [x] Task 9 — ทำสมุดเลขแบบไม่ล็อกอิน (localStorage + ผูกงวด + prefill, /notebook/ 200, 26 tests เขียว)
- [x] Task 10 — เชื่อมผลจากฝันเข้าสมุดเลข (ปุ่มบันทึกทีละเลข 3 จุด + prefill, 30 tests เขียว)
- [ ] Task 11 — ตรวจผลและสร้างประวัติงวด

### Checkpoint C

- [ ] เส้นทาง วิเคราะห์ → เลือก → บันทึก → ตรวจผล ผ่าน end-to-end
- [ ] empty/error/stale states ทำงานถูกต้อง
- [ ] backend tests และ browser tests สำคัญผ่าน
- [ ] เจ้าของผลิตภัณฑ์ทดลองบนมือถือจริง

## ระยะที่ 3: เปิดกลุ่มเล็กและเก็บหลักฐาน

- [ ] Task 12 — เพิ่ม analytics ขั้นต่ำ
- [ ] Task 13 — เตรียม production และ recovery
- [ ] Task 14 — เปิด closed beta และทำรอบเรียนรู้สองงวด

### Checkpoint D

- [ ] มี activation baseline
- [ ] มี cross-draw retention อย่างน้อยสองงวด
- [ ] ระบุฟีเจอร์ที่ทำให้ผู้ใช้กลับมาได้
- [ ] มีหลักฐานความตั้งใจจ่าย หรือข้อสรุปว่ายังไม่ควรสร้าง billing

## ระยะที่ 4: ทดลองรายได้

- [ ] เลือกทดลอง A — สมุดเลขแบบสมาชิก ตามหลักฐานการใช้ซ้ำ
- [ ] เลือกทดลอง B — เครื่องมือทำคอนเทนต์ ตามหลักฐานการแชร์/เจ้าของเพจ
- [ ] เลือกทดลอง C — Widget/API ตามความสนใจจาก partner
- [ ] ประเมิน D — โฆษณา/สปอนเซอร์ หลังมี traffic และตรวจนโยบายล่าสุด
- [ ] ทดลองทีละสมมติฐานและบันทึกเกณฑ์เดินหน้า/หยุดก่อนเริ่ม

## บันทึกการส่งมอบแต่ละรอบ

- [ ] สรุปสิ่งที่เปลี่ยนและเหตุผล
- [ ] ระบุไฟล์และ migration ที่กระทบ
- [ ] แนบหลักฐานการทดสอบ
- [ ] บันทึกข้อจำกัดและสิ่งที่ยังไม่ยืนยัน
- [ ] ระบุ task ถัดไปและ dependency

# แผนส่งต่อโครงการ LekdeDai

สถานะเอกสาร: แผนดำเนินงานต่อเนื่องหลังตรวจ UI, สูตรหวย, ข่าว และ production readiness
วันที่ปรับปรุงล่าสุด: 11 กันยายน 2026
เจ้าของผลิตภัณฑ์: ผู้ดูแลโครงการ LekdeDai
ที่เก็บรายการงาน: `tasks/todo.md`

## 1. เป้าหมายของโครงการ

ทำให้ LekdeDai เปิดใช้งานจริงในรูปแบบเล็กที่สุด เก็บข้อมูลพฤติกรรมผู้ใช้ และค่อยตัดสินใจว่าจะลงทุนพัฒนาหรือหารายได้จากส่วนใดต่อไป โดยยังไม่กำหนดเป้ารายได้ล่วงหน้า

แนวคิดผลิตภัณฑ์เบื้องต้นคือ **“สมุดเลขส่วนตัวที่จำที่มาและตรวจผลให้”** ผู้ใช้สามารถนำความฝัน ข่าว หรือสถิติมาสร้างรายการเลข บันทึกเหตุผลและงวดที่เกี่ยวข้อง แล้วกลับมาตรวจผลและดูประวัติย้อนหลังได้

ผลลัพธ์ที่ต้องการในรอบแรก:

- เว็บไซต์เปิดใช้งานได้อย่างปลอดภัยบน production
- ผู้ใช้ทำเส้นทางหลักได้ครบ: วิเคราะห์ฝันหรือดูข้อมูล → บันทึกเลข → เลือกงวด → กลับมาตรวจผล
- ข้อมูลจริง ข้อมูลสาธิต และคะแนนจัดอันดับถูกแยกชัดเจน
- มีข้อมูลเพียงพอให้ตัดสินใจจากพฤติกรรมจริงว่าจะสร้างสมาชิก เครื่องมือสำหรับเพจ หรือรายได้แบบอื่น

## 2. สถานะระบบปัจจุบัน

### ส่วนที่มีอยู่แล้ว

- Django ใน `app/` เป็นระบบที่เชื่อมฐานข้อมูลและฟังก์ชันหลักมากที่สุด
- `home` แสดงข่าว คำทำนาย ผลหวย และสถิติรวม
- `dreams` รับข้อความฝัน ค้นสัญลักษณ์ ตีความ สร้างเลข และบันทึกผล
- `lottery_checker` เรียกข้อมูลผลสลากจาก GLO และเก็บผลลงฐานข้อมูล
- `lotto_stats` เก็บผลย้อนหลังและคำนวณเลขฮอต/เลขเย็น
- `news` ดึงและวิเคราะห์ข่าวที่เกี่ยวข้องกับตัวเลข
- `ai_engine` รวมผลจากหลายแหล่งและเก็บประวัติคำทำนาย
- มีหน้าบ้านอีกสองชุด ได้แก่ Next.js ที่ root และ React/Webpack ใน `frontend/`
- มี Docker Compose สำหรับ Django และ PostgreSQL

### งานที่ยังเหลือจากการตรวจรอบล่าสุด

1. หน้าแรกส่วนวิเคราะห์ฝันแบบด่วนยังแสดง Markdown ดิบ เพราะผลถูกใส่ด้วย `textContent`
2. นิยามสถิติ “เลขท้าย 2 ตัว” ไม่ตรงกับวิธีนับในโค้ด ทำให้ตัวเลขอย่าง “ออก 3 ครั้ง จาก 2 งวด” ชวนให้เข้าใจผิด
3. ระบบสูตรหวยมีอยู่แล้ว แต่ข้อมูล seed บางส่วนยังสุ่มผล/ความแม่นยำ และสคริปต์ติดตั้งเรียกชื่อ command เก่า
4. ระบบข่าวมีทั้ง RSS และ scraper หน้า category อยู่แล้ว แต่ source registry ปัจจุบันว่าง ยังไม่มี scheduler และเส้นทาง draft-to-publish ที่พร้อมใช้งานจริง
5. ผลวิเคราะห์ AI ล่าสุดยังขาดงวดเป้าหมายที่ชัด และพบข้อความ metadata ไม่สมบูรณ์ เช่น `วิเคราะห์โดย v`
6. หน้าสูตรหวย ข่าวหวย และแหล่งข้อมูลยังเป็น empty state จนกว่าจะกู้ข้อมูลและต่อ ingestion สำเร็จ
7. Docker ยังใช้ development server, `DEBUG=True`, wildcard host, secret/password ตัวอย่าง และเปิดฐานข้อมูลเกินความจำเป็น
8. endpoint สาธารณะและงานดึงข้อมูลภายนอกยังต้องตรวจ authentication, authorization, CSRF, rate limit, timeout และ input validation ให้ครบ
9. ยังต้องเพิ่ม quality gate, monitoring, backup/restore, freshness alert และ rollback rehearsal ก่อนเปิด public
10. ต้องกำหนด privacy, retention, disclaimer และสิทธิ์การนำข่าว/ภาพ/ข้อความจากแหล่งภายนอกมาเผยแพร่

ข้อจำกัดของการตรวจครั้งล่าสุด: ตรวจทั้งหน้าเว็บที่กำลังรันและ source code แล้ว แต่ยังรัน `manage.py check --deploy` และ test suite บนเครื่องนี้ไม่ได้ เพราะ environment ปัจจุบันไม่มี Django และ Docker พร้อมใช้งาน

## 3. การตัดสินใจเบื้องต้น

### ใช้ Django เป็นแกนสำหรับ MVP

Django มี model, migration, management command และหน้าที่ต่อกับข้อมูลจริงมากที่สุด จึงให้ใช้เป็น application หลักในรอบแรก ส่วน Next.js และ React/Webpack ต้องถูกจัดประเภทว่าเป็นต้นแบบ ส่วนที่ยังใช้งาน หรือส่วนที่จะเลิกใช้ หลังจากตรวจ dependency จริงใน Task 1

### ขายความสะดวกก่อนขายความแม่นยำ

ยังไม่มีหลักฐานเพียงพอที่จะสื่อสารว่า AI ทำนายผลได้แม่นกว่าวิธีอื่น รายได้ระยะแรกควรมาจากคุณค่าที่ตรวจสอบได้ เช่น เก็บประวัติ จัดชุดเลข ส่งออก ทำภาพ แชร์ หรือตรวจผลอัตโนมัติ

### เปิดแบบเล็กและวัดพฤติกรรมก่อน

รอบแรกไม่ต้องเพิ่มสูตรหรือโมเดลจำนวนมาก ให้สร้างเส้นทางใช้งานเดียวที่ครบ แล้ววัด activation, การบันทึก, การกลับมาใช้ และการแชร์

### แยกคำสามคำให้ชัด

- **คะแนนจัดอันดับ**: ใช้เรียงข้อมูลภายในสูตรหนึ่งเท่านั้น
- **ผลย้อนหลัง**: ผลการตรวจกับงวดที่เกิดขึ้นจริง พร้อมจำนวนตัวอย่างและวิธีวัด
- **ความน่าจะเป็น**: ห้ามใช้จนกว่าจะมีวิธี calibration และ validation ที่รองรับ

## 4. ขอบเขต MVP

### อยู่ในขอบเขต

- หน้าแรกที่อธิบายคุณค่าหลักและนำไปยังเส้นทางใช้งาน
- ตรวจผลสลากพร้อมแหล่งข้อมูล งวด และเวลาอัปเดต
- วิเคราะห์ฝันพร้อมคำอธิบายที่มาและข้อความกำกับว่าเป็นความเชื่อ/ความบันเทิง
- สมุดเลข: บันทึกเลข ที่มา เหตุผล งวด และสถานะผล
- ประวัติรายการและการตรวจผลหลังออกรางวัล
- telemetry ขั้นต่ำโดยไม่เก็บข้อมูลเกินจำเป็น
- production configuration, logging, backup และ health check

### ยังไม่ทำใน MVP

- ขายแพ็กเกจ VIP โดยอ้างอัตราถูกรางวัลหรือความแม่นยำ
- เพิ่มโมเดล ML หรือสูตรหวยใหม่
- แอปมือถือ native
- ระบบ social feed หรือ community เต็มรูปแบบ
- marketplace ซื้อขายเลขหรือการเชื่อมเว็บพนัน
- ระบบชำระเงินก่อนมีหลักฐานว่าผู้ใช้กลับมาใช้ฟีเจอร์ใด
- rewrite หน้าบ้านใหม่ทั้งระบบ

## 5. เส้นทางผู้ใช้หลัก

```text
หน้าแรก
  ├─ วิเคราะห์ความฝัน ─┐
  ├─ ดูข่าว/สถิติ ─────┼─> เลือกเลขและบันทึกเหตุผล
  └─ กรอกเลขเอง ───────┘            │
                                     v
                                ผูกกับงวดหวย
                                     │
                                     v
                          กลับมาตรวจผลและดูประวัติ
```

นิยาม activation เบื้องต้น: ผู้ใช้สร้างหรือเลือกเลขอย่างน้อยหนึ่งรายการและผูกกับงวดสำเร็จ

## 6. ลำดับการดำเนินงาน

### ระยะที่ 0: ยืนยันฐานระบบ

#### Task 1: ทำแผนผัง runtime และเลือกหน้าบ้านที่ใช้งานจริง

**รายละเอียด:** ตรวจว่า Django, Next.js และ React/Webpack ถูกเรียกจากจุดใด มี asset/API ใดพึ่งพากัน แล้วบันทึกสถานะของแต่ละชุดเป็น production, retained dependency หรือ prototype

**เกณฑ์รับงาน:**

- มีแผนผัง request และ deployment path ที่ตรวจจากโค้ด/การรันจริง
- ระบุ frontend หลักสำหรับ MVP เพียงหนึ่งชุด
- ระบุไฟล์ที่ยังห้ามลบและเหตุผล

**การตรวจสอบ:** รันทั้งระบบ local หรือ Docker และบันทึก URL ที่เข้าถึงได้จริง

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** `docker-compose.yml`, `Dockerfile`, `app/lekdedai/urls.py`, `package.json`, `frontend/package.json`

**ขนาดงาน:** M
**Dependencies:** ไม่มี

#### Task 2: คืน dependency วันที่หวยและทำให้ระบบเริ่มได้

**รายละเอียด:** หาแหล่งเดิมหรือสร้าง contract ที่ชัดเจนสำหรับ `LotteryDates`/`LOTTERY_DATES` แล้วแก้ imports และ tests ที่เกี่ยวข้อง

**เกณฑ์รับงาน:**

- `python manage.py check` ผ่าน
- หน้าแรก หน้าสถิติ และหน้าตรวจหวย import ได้
- มี tests สำหรับงวดปกติ ช่วงข้ามเดือน/ปี และวันที่ไม่มีงวด

**การตรวจสอบ:** `python manage.py check` และ focused tests ของวันที่หวย

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** `app/utils/lottery_dates.py`, `app/home/views.py`, `app/lottery_checker/views.py`, `app/lotto_stats/lotto_sync_service.py`

**ขนาดงาน:** M
**Dependencies:** Task 1

#### Task 3: สร้าง baseline ที่รันซ้ำได้

**รายละเอียด:** ทำ `.env.example`, คำสั่ง setup, seed ข้อมูลขั้นต่ำ และคำสั่งตรวจระบบให้คนรับช่วงเริ่มงานได้โดยไม่ต้องเดาค่า

**เกณฑ์รับงาน:**

- เครื่องใหม่เริ่มระบบตาม README ได้
- ไม่มี secret จริงใน repository
- migration และ seed ขั้นต่ำทำซ้ำได้

**การตรวจสอบ:** เริ่มจากฐานข้อมูลว่าง แล้วเปิดหน้าหลักได้

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** `.env.example`, `README.md`, `docker-compose.yml`, setup scripts

**ขนาดงาน:** M
**Dependencies:** Task 2

### Checkpoint A: ระบบพื้นฐาน

- Django system check และ migrations ผ่าน
- URL หลักตอบสนองได้โดยไม่มี import error
- frontend ที่เป็นเจ้าของ production ถูกระบุชัด
- ขั้นตอนเริ่มระบบจากเครื่องใหม่ผ่านการทดสอบ

### ระยะที่ 1: ความปลอดภัยและความน่าเชื่อถือ

#### Task 4: ปิดช่องทางเปลี่ยนข้อมูลโดยไม่มีสิทธิ์

**รายละเอียด:** ตรวจทุก endpoint ที่ลบ รีเฟรช ดึงข้อมูลจำนวนมาก หรือสร้าง prediction แล้วกำหนด authentication, authorization, HTTP method และ CSRF ตามหน้าที่

**เกณฑ์รับงาน:**

- ผู้ใช้ทั่วไปเรียก clear/refresh/bulk/admin action ไม่ได้
- endpoint ที่เปลี่ยนข้อมูลไม่ใช้ GET
- มี tests ยืนยัน 401/403 และกรณีผู้ดูแลทำสำเร็จ

**การตรวจสอบ:** security-focused Django tests และ manual request tests

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** `app/lottery_checker/views.py`, `app/lottery_checker/urls.py`, `app/ai_engine/views.py`, tests ที่เกี่ยวข้อง

**ขนาดงาน:** M
**Dependencies:** Task 3

#### Task 5: ลบข้อมูลสาธิตออกจากเส้นทางจริง

**รายละเอียด:** ทำ inventory ของ hard-code, fallback, random และ mock data แล้วบังคับให้ production แสดงสถานะไม่มีข้อมูลหรือ degraded อย่างตรงไปตรงมา

**เกณฑ์รับงาน:**

- ไม่มี 87%, +150, confidence 90 หรือข้อมูลจำลองแสดงเป็นผลจริง
- คะแนนทุกชนิดมีชื่อและคำอธิบายความหมาย
- mock data ทำงานเฉพาะ test/dev ที่ระบุชัด

**การตรวจสอบ:** tests กรณีฐานข้อมูลว่างและกรณี upstream ล้มเหลว รวมถึงตรวจ UI ด้วยตา

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** `app/home/views.py`, `app/ai_engine/prediction_engine.py`, `app/ai_engine/data_ingestion.py`, templates/pages ที่แสดงคะแนน

**ขนาดงาน:** M
**Dependencies:** Task 3

#### Task 6: กำหนดเจ้าของข้อมูลผลหวย

**รายละเอียด:** ระบุ canonical model/source สำหรับผลหวย วางกติกา sync, idempotency, freshness และการ reconcile ระหว่าง `LottoResult` กับ `LotteryDraw`

**เกณฑ์รับงาน:**

- มี source-of-truth เดียวต่อข้อมูลหนึ่งประเภท
- sync ซ้ำไม่สร้างข้อมูลซ้ำและไม่ทำลายข้อมูลถูกต้อง
- UI แสดงแหล่งข้อมูล งวด เวลาอัปเดต และสถานะ stale/error

**การตรวจสอบ:** tests ด้วย fixture หลายงวด การ sync ซ้ำ และ upstream error

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** models/services/management commands ของ `lottery_checker` และ `lotto_stats`

**ขนาดงาน:** M โดยต้องแบ่งย่อยหาก migration กระทบหลายส่วน
**Dependencies:** Task 2

#### Task 7: วางขอบเขตข้อมูลส่วนบุคคล

**รายละเอียด:** ตัดสินใจว่าจำเป็นต้องเก็บข้อความฝันและ IP หรือไม่ กำหนด retention, delete flow, notice และการกรองข้อมูลใน logs

**เกณฑ์รับงาน:**

- ผู้ใช้เห็นว่าข้อมูลใดถูกเก็บและใช้เพื่ออะไร
- มีวิธีลบข้อมูลตาม identifier ที่ระบบรองรับ
- ไม่ log ข้อความฝันหรือข้อมูลระบุตัวบุคคลโดยไม่จำเป็น

**การตรวจสอบ:** privacy flow test และตรวจฐานข้อมูล/logs ด้วยข้อมูลตัวอย่าง

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** `app/dreams/views.py`, `app/dreams/models.py`, templates, settings

**ขนาดงาน:** M
**Dependencies:** Task 3

### Checkpoint B: พร้อมให้ผู้ใช้กลุ่มเล็กทดสอบ

- ไม่มี endpoint สำคัญที่บุคคลทั่วไปสั่งเปลี่ยนหรือล้างข้อมูลได้
- ทุกข้อมูลที่แสดงระบุว่าเป็นข้อมูลจริง ข้อมูลไม่พร้อม หรือข้อมูลตัวอย่าง
- ข้อความด้านความแม่นยำผ่านการทบทวน
- เส้นทางเก็บและลบข้อมูลผู้ใช้ผ่านการตรวจ

### ระยะที่ 2: สร้าง MVP ที่ทำให้คนกลับมาใช้

#### Task 8: ทำหน้าแรกตามงานหลักหนึ่งเส้นทาง

**รายละเอียด:** ปรับหน้าแรกให้สื่อว่าเว็บช่วยตีความ บันทึก และตรวจผล พร้อม CTA หลักเดียวและสถานะงวดล่าสุด

**เกณฑ์รับงาน:**

- ผู้ใช้ใหม่เข้าใจบริการและเริ่มเส้นทางหลักได้ภายในหน้าแรก
- ไม่มีสถิติความนิยม/ความแม่นยำที่ไม่มีหลักฐาน
- ใช้งานบนมือถือและผ่าน accessibility ขั้นพื้นฐาน

**การตรวจสอบ:** browser test ที่ขนาดมือถือ/desktop และทดสอบ CTA ทั้งหมด

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** Django home view/template และ shared navigation/styles ของ frontend ที่เลือก

**ขนาดงาน:** M
**Dependencies:** Tasks 1, 5, 6

#### Task 9: ทำสมุดเลขแบบไม่ล็อกอิน

**รายละเอียด:** ให้ผู้ใช้บันทึกเลข ที่มา เหตุผล และงวดใน browser เพื่อพิสูจน์คุณค่าก่อนสร้าง account system

**เกณฑ์รับงาน:**

- เพิ่ม แก้ และลบรายการได้
- ผูกเลขกับแหล่งที่มาและงวดได้
- แจ้งชัดว่าข้อมูลอยู่บนอุปกรณ์นี้และอาจหายได้

**การตรวจสอบ:** browser tests สำหรับ create/edit/delete และ reload

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** frontend หลัก, API/read-only draw endpoint หากจำเป็น

**ขนาดงาน:** M
**Dependencies:** Tasks 6, 8

#### Task 10: เชื่อมผลจากฝันเข้าสมุดเลข

**รายละเอียด:** หลังวิเคราะห์ความฝัน ผู้ใช้เลือกเลขบางตัว บันทึกที่มาและเหตุผลเข้าสมุดเลขได้ทันที

**เกณฑ์รับงาน:**

- ผู้ใช้เลือกเลขได้แทนการบันทึกทุกเลขอัตโนมัติ
- รายการเก็บ reference ถึงผลวิเคราะห์หรือข้อความสรุปที่เหมาะสม
- input ยาว ผิดรูปแบบ และ error state ถูกจัดการ

**การตรวจสอบ:** end-to-end browser test ตั้งแต่กรอกฝันจนเห็นรายการในสมุด

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** `app/dreams/views.py`, dream template/component, notebook storage module

**ขนาดงาน:** M
**Dependencies:** Task 9

#### Task 11: ตรวจผลและสร้างประวัติงวด

**รายละเอียด:** เมื่อมีผลจริง ระบบเทียบรายการที่บันทึกกับกติการางวัลที่ระบุชัด และแสดงประวัติโดยไม่ตีความผลเกินจริง

**เกณฑ์รับงาน:**

- ผลการเทียบตรงกับ fixture ที่ครอบคลุมเลขศูนย์นำหน้า
- แสดง pending/stale/error เมื่อยังตรวจไม่ได้
- ผู้ใช้เห็นที่มา เหตุผล งวด และผลในหน้าประวัติเดียวกัน

**การตรวจสอบ:** unit tests ของกติกาการเทียบ และ end-to-end test หน้าประวัติ

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** lottery checker service, notebook module, history UI

**ขนาดงาน:** M
**Dependencies:** Tasks 6, 9

#### Task 12: ปิดข้อบกพร่อง UX ที่ยังมองเห็นได้

**รายละเอียด:** แก้ผลวิเคราะห์ฝันด่วนหน้าแรกที่ยังแสดง Markdown ดิบ ปรับลำดับหัวข้อหน้าแรก และกำหนดพฤติกรรมของเมนูที่ยังไม่มีข้อมูลให้ผู้ใช้เข้าใจตรงกัน

**เกณฑ์รับงาน:**

- ผลฝันด่วนและหน้าวิเคราะห์ฝันใช้ formatter ที่ปลอดภัยและแสดงผลเหมือนกัน
- หน้าแรกมีลำดับ heading ที่ถูกต้อง และเมนูที่ยังไม่พร้อมถูกซ่อนหรือติดป้ายสถานะ
- desktop และ viewport 390px ไม่มี overflow, raw marker หรือข้อความ placeholder

**การตรวจสอบ:** browser test ทั้ง desktop/mobile, keyboard navigation และ console ไม่มี error/warning

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** `app/home/templates/home/index.html`, `app/dreams/templates/dreams/dream_form.html`, `app/templates/base.html`, tests ที่เกี่ยวข้อง

**ขนาดงาน:** M
**Dependencies:** Task 10

#### Task 13: กำหนดนิยามและแก้ความถูกต้องของสถิติ

**รายละเอียด:** แยก “เลขท้าย 2 ตัว” ออกจาก “เลข 2 หลักทุกตำแหน่งในรางวัลที่ 1” ให้ชัดทั้งการคำนวณ ชื่อ metric และคำอธิบายบน UI โดยใช้ข้อมูลผลหวย canonical จาก Task 6

**เกณฑ์รับงาน:**

- metric ทุกตัวมีนิยาม ตำแหน่งรางวัล ช่วงเวลา และจำนวนตัวอย่างชัดเจน
- ถ้าระบุว่าเลขท้าย 2 ตัว จำนวนครั้งต้องคำนวณจาก `two_digit` เท่านั้น
- fixture หลายงวด รวมเลขซ้ำและเลขศูนย์นำหน้า ให้ผลตรงกับการคำนวณด้วยมือ

**การตรวจสอบ:** focused unit tests ของ `StatsCalculator` และตรวจตัวเลขตัวอย่างบน `/lotto_stats/`

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** `app/lotto_stats/stats_calculator.py`, `app/lotto_stats/templates/lotto_stats/statistics.html`, `app/lotto_stats/tests.py`

**ขนาดงาน:** M
**Dependencies:** Task 6

#### Task 14: ทำ contract สูตรหวยและ seed ที่ใช้ production ได้

**รายละเอียด:** รวบรวมสูตร Django ที่มีอยู่ กำหนด input/output/version ของแต่ละสูตร และเปลี่ยน seed จากข้อมูลสุ่มเป็นข้อมูลสูตรแบบ deterministic โดยไม่สร้างผลหวยหรือผลความแม่นยำปลอม

**เกณฑ์รับงาน:**

- มีรายชื่อสูตรที่อนุมัติ ชื่อไม่ผูกกับ branch logic แบบเปราะ และมี version
- seed รันซ้ำได้โดยไม่สร้างซ้ำ และไม่สร้าง random result/prediction
- script ติดตั้งเรียกชื่อ command ที่มีอยู่จริง และฐานข้อมูลใหม่เห็นสูตรหลัง setup

**การตรวจสอบ:** เริ่มจากฐานข้อมูลว่าง รัน migration/seed สองครั้ง แล้วตรวจจำนวนและรายละเอียดสูตรเท่าเดิม

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** `app/lotto_formula/models.py`, `app/lotto_formula/management/commands/populate_lottery_data.py`, setup scripts, migration/fixture ที่จำเป็น

**ขนาดงาน:** M
**Dependencies:** Tasks 3, 6

#### Task 15: เชื่อมสูตรกับผลจริงและวัดผลย้อนหลังอย่างซื่อสัตย์

**รายละเอียด:** ให้เครื่องคำนวณใช้ข้อมูลผลหวย canonical บันทึก prediction ก่อนวันออกผล และคำนวณผลย้อนหลังจากกติกาที่ประกาศ ไม่ใช้เปอร์เซ็นต์ hard-code จาก Next.js หรือ sample data

**เกณฑ์รับงาน:**

- สูตรคำนวณจาก input เดิมให้ output เดิม และระบุงวดเป้าหมาย
- prediction หลังวันออกรางวัลถูกตรวจด้วยผลจริง พร้อม numerator, denominator และช่วงวันที่
- UI ใช้คำว่า “คะแนน”, “ผลย้อนหลัง” และ “ความน่าจะเป็น” ตามนิยามในแผนเท่านั้น

**การตรวจสอบ:** unit tests รายสูตร, historical fixture test และ browser flow เลือกสูตร → คำนวณ → บันทึก → ตรวจผล

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** `app/lotto_formula/views.py`, model/service ของสูตร, formula templates, tests

**ขนาดงาน:** M โดยแยกทีละสูตรหากเกิน 5 ไฟล์
**Dependencies:** Tasks 11, 13, 14

#### Task 16: คืนทะเบียนแหล่งข่าวและ provenance

**รายละเอียด:** สร้างรายการแหล่ง RSS ที่อนุมัติจากหลักฐานเดิม กำหนดชนิดแหล่ง URL สถานะ active ช่วงดึง และนโยบายเก็บเนื้อหา โดยไม่พึ่ง database backup เป็น configuration หลัก

**เกณฑ์รับงาน:**

- source registry แบบ version-controlled สร้าง DataSource ได้แบบ idempotent
- แต่ละแหล่งระบุ RSS/category/API, attribution, freshness และสถานะเปิดใช้
- `/ai/data-sources/` แสดงแหล่งจริงและเวลาสำเร็จ/ล้มเหลวล่าสุด

**การตรวจสอบ:** seed registry บนฐานข้อมูลว่างและตรวจ URL/จำนวน/สถานะตรงกับไฟล์กำหนด

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** `app/ai_engine/management/commands/setup_ai_data_sources.py`, DataSource config/fixture, tests

**ขนาดงาน:** M
**Dependencies:** Task 3

#### Task 17: ทำ RSS ingestion เป็นเส้นทางหลัก

**รายละเอียด:** ปรับ `scrape_rss_feeds` ให้ดึง feed, normalize, deduplicate, บันทึก provenance และเข้าสถานะ draft/published ตาม policy โดยไม่บังคับว่า AI สองตัวต้องสำเร็จพร้อมกันจึงจะเก็บข่าว

**เกณฑ์รับงาน:**

- feed ปกติ, feed ผิดรูปแบบ, timeout และ duplicate มีผลลัพธ์ที่คาดเดาได้
- เก็บ source URL, published time, fetched time, content hash และสถานะวิเคราะห์
- AI ล้มเหลวไม่ทำให้ข้อมูลต้นฉบับหาย และไม่มีข้อความ exception ภายในรั่วสู่ผู้ใช้

**การตรวจสอบ:** fixture RSS/XML แบบ offline, mocked network tests และ dry run บน staging

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** `app/news/management/commands/scrape_rss_feeds.py`, news ingestion service, models/migration, tests

**ขนาดงาน:** M
**Dependencies:** Task 16

#### Task 18: ทำ category scraper เป็น fallback พร้อม editorial gate

**รายละเอียด:** รวม `scrape_thairath`, `scrape_thairath_local` และ scraper รุ่นเก่าให้เหลือ owner ชัดเจน ใช้เฉพาะเมื่อ RSS ไม่มีข้อมูล และส่งข่าวเข้า review queue ก่อนเผยแพร่ เว้นแต่ผ่านเกณฑ์ auto-publish ที่ตรวจสอบได้

**เกณฑ์รับงาน:**

- selector เปลี่ยนหรือหน้าเว็บตอบผิดปกติแล้วหยุดอย่างปลอดภัยและแจ้งเตือน
- ข่าวซ้ำไม่ถูกสร้างแม้ URL เปลี่ยนเล็กน้อย
- ผู้ดูแลเห็นข้อความต้นทาง สรุป AI ตัวเลข เหตุผล และอนุมัติ/ปฏิเสธก่อนเผยแพร่ได้

**การตรวจสอบ:** HTML fixtures, duplicate tests, admin review flow และ staging scrape แบบจำกัดจำนวน

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** category scraper command/service, `app/news/admin.py`, `app/news/models.py`, tests

**ขนาดงาน:** M โดยแยก source adapter ทีละเว็บ
**Dependencies:** Tasks 16, 17

#### Task 19: เชื่อมข่าวที่ผ่านการคัดเข้าสู่หน้าเว็บ

**รายละเอียด:** ให้หน้าข่าวและหน้าแรกแสดงเฉพาะข่าว published ที่มีแหล่งที่มา เวลาข้อมูล และสรุปเลขที่ตรวจย้อนกลับได้ พร้อม empty/stale state ที่ตรงกับสถานะ ingestion

**เกณฑ์รับงาน:**

- ข่าวใหม่ที่อนุมัติปรากฏใน `/news/` และส่วนข่าวหน้าแรกเพียงครั้งเดียว
- ทุกบทความมี source link, วันเผยแพร่, วันดึง และป้ายสถานะการวิเคราะห์
- ข่าวเก่าหรือ ingestion ล้มเหลวไม่ถูกนำเสนอเป็น “ข่าวล่าสุด”

**การตรวจสอบ:** end-to-end จาก RSS fixture → review/publish → news list/detail → homepage

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** `app/news/views.py`, news templates, `app/home/views.py`, tests

**ขนาดงาน:** M
**Dependencies:** Tasks 17, 18

#### Task 20: ทำ metadata และ readiness gate ของ AI prediction

**รายละเอียด:** บังคับให้ prediction มีงวดเป้าหมาย model/version เวลาสร้าง ช่วงข้อมูล และสถานะ input ก่อนเผยแพร่ ป้องกันข้อความเช่น `วิเคราะห์โดย v` หรือ prediction ที่ไม่ทราบว่าเป็นงวดใด

**เกณฑ์รับงาน:**

- prediction ที่ขาด `for_draw_date`, model/version หรือ provenance ไม่ถูก featured
- หน้า AI, history และหน้าแรกแสดง metadata ชุดเดียวกัน
- stale/incomplete prediction มีสถานะชัดและไม่แสดง confidence เหมือนพร้อมใช้

**การตรวจสอบ:** model validation tests, view tests และ browser comparison ทั้งสามหน้า

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** `app/ai_engine/models.py`, prediction service/views, AI templates, tests

**ขนาดงาน:** M
**Dependencies:** Tasks 6, 17, 19

### Checkpoint C: MVP ใช้งานครบเส้นทาง

- ผู้ใช้ทำเส้นทาง วิเคราะห์ → เลือก → บันทึก → ตรวจผล ได้ครบ
- ผู้ใช้ทำเส้นทาง ข่าว/สถิติ/สูตร → เลือกเลข → บันทึก → ตรวจผล ได้ครบ
- สูตร ข่าว สถิติ และ AI ไม่มีข้อมูลสุ่มหรือ metadata กำกวมใน production path
- กรณีไม่มีข้อมูลและ upstream error ไม่แสดงข้อมูลผิด
- critical browser flow และ focused backend tests ผ่าน
- เจ้าของผลิตภัณฑ์ทดลองใช้บนมือถือจริง

### ระยะที่ 3: เตรียมระบบสำหรับ staging และ production

#### Task 21: สร้าง automated quality gate

**รายละเอียด:** ทำคำสั่งทดสอบมาตรฐานและ CI สำหรับ Django checks, migrations, unit/integration tests, static assets และ smoke tests ของ route สำคัญ

**เกณฑ์รับงาน:**

- `manage.py check --deploy`, migrations check และ test suite รันได้ใน environment เดียวกับ deploy
- build ล้มทันทีเมื่อ test, migration หรือ static collection ผิด
- มี regression tests สำหรับสูตร ข่าว สถิติ AI และ flow สมุดเลข

**การตรวจสอบ:** CI run จาก clean checkout ผ่านทั้งหมด

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** CI workflow, test configuration, `requirements.txt`, test documentation

**ขนาดงาน:** M
**Dependencies:** Checkpoint C

#### Task 22: แยก production runtime และจัดการ secrets

**รายละเอียด:** สร้าง production settings/runtime ที่ใช้ application server จริง ปิด DEBUG จำกัด host ทำ static/media ให้ถูกต้อง และย้าย secret/password ออกจาก repository

**เกณฑ์รับงาน:**

- production ไม่ใช้ `runserver`, ไม่มี hard-coded admin/database password และไม่เปิด PostgreSQL สู่ public
- `DEBUG=False`, `ALLOWED_HOSTS` และ trusted origins ตรงกับ domain จริง
- migration/collectstatic เป็น deploy step ที่ fail แล้วหยุด deploy

**การตรวจสอบ:** build/deploy staging จาก clean image และ `manage.py check --deploy`

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** `Dockerfile`, production compose/manifest, Django settings, entrypoint

**ขนาดงาน:** M
**Dependencies:** Task 21

#### Task 23: ปิดช่องโหว่ endpoint และจำกัดการใช้งานเกินขอบเขต

**รายละเอียด:** ทบทวน `csrf_exempt`, admin/mutation APIs, public AI/news analysis, input size, rate limit, timeout และ error response ก่อนเปิดให้บุคคลภายนอกเรียกใช้

**เกณฑ์รับงาน:**

- endpoint เปลี่ยนข้อมูลต้องมีสิทธิ์, CSRF/authorization และ audit trail ตามหน้าที่
- public endpoint มี rate limit, payload limit และ timeout
- response 4xx/5xx ไม่เผย stack trace, key หรือข้อความภายใน provider

**การตรวจสอบ:** authorization/abuse tests, dependency scan และ staging security smoke test

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** views/URLs ของ news, AI และ lottery checker, middleware/config, tests

**ขนาดงาน:** M โดยแยก endpoint family
**Dependencies:** Tasks 4, 22

#### Task 24: ตั้ง schedule และ freshness control

**รายละเอียด:** ตั้งงาน sync ผลหวย, RSS, category fallback, AI generation, accuracy reconciliation และ cleanup ให้ idempotent มี lock และไม่รันทับกัน

**เกณฑ์รับงาน:**

- แต่ละ job มี schedule, owner, retry, timeout และ last-success timestamp
- UI เปลี่ยนเป็น stale/degraded เมื่อเกิน freshness threshold
- rerun job เดิมไม่สร้างข้อมูลซ้ำหรือเผยแพร่ prediction ซ้ำ

**การตรวจสอบ:** staging scheduler run, forced failure/retry และ idempotency tests

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** management commands, scheduler config, locking/state model, runbook

**ขนาดงาน:** M
**Dependencies:** Tasks 17, 20, 22

#### Task 25: เพิ่ม observability, backup และ rollback

**รายละเอียด:** ทำ health checks, structured logs, error tracking, metrics, alerting, database backup/restore และขั้นตอนย้อนเวอร์ชัน

**เกณฑ์รับงาน:**

- monitor 5xx, latency, job failure, stale data, AI/provider failure และค่าใช้จ่ายภายนอกได้
- backup อัตโนมัติและ restore drill ผ่านด้วยข้อมูล staging
- deploy ใหม่ผิดปกติสามารถ rollback ได้ตาม runbook ที่ทดสอบแล้ว

**การตรวจสอบ:** fault injection บน staging, alert test, restore drill และ rollback rehearsal

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** health endpoint, logging/monitor config, backup scripts/manifest, operations runbook

**ขนาดงาน:** M โดยแยก observability กับ recovery
**Dependencies:** Tasks 22, 24

#### Task 26: จัดทำนโยบายผู้ใช้และสิทธิ์เนื้อหา

**รายละเอียด:** จัดทำ Privacy Policy, Terms, disclaimer, contact/report flow และกติกาการใช้ข่าวจากภายนอก โดยเก็บเพียง title/excerpt/analysis/source link เว้นแต่มีสิทธิ์เผยแพร่เนื้อหาเต็ม

**เกณฑ์รับงาน:**

- ผู้ใช้เห็นคำเตือนเรื่องความบันเทิงและไม่รับประกันผลในจุดสำคัญ
- นโยบายระบุข้อมูลฝัน, localStorage, retention, analytics และวิธีขอลบข้อมูล
- ทุก source ผ่านการตรวจเงื่อนไข RSS/robots/ลิขสิทธิ์ก่อนเปิดใช้งาน

**การตรวจสอบ:** content/legal checklist โดยเจ้าของผลิตภัณฑ์ และตรวจหน้าเว็บจริงทุกลิงก์

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** policy templates, footer/navigation, source registry, content runbook

**ขนาดงาน:** M
**Dependencies:** Tasks 7, 16, 19

#### Task 27: ทำ performance, accessibility และ compatibility gate

**รายละเอียด:** ตรวจ Core Web Vitals, query count, static caching, keyboard/focus, contrast, form labels และ browser/mobile หลักก่อน freeze release candidate

**เกณฑ์รับงาน:**

- ไม่มี critical accessibility violation และ flow หลักใช้งานด้วย keyboard ได้
- ไม่มีหน้าใดเกิด horizontal overflow หรือ network request ที่ล้มเงียบ
- กำหนด performance budget และ route สำคัญผ่านบน staging

**การตรวจสอบ:** Lighthouse/axe, browser matrix, network throttling และ query profiling

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** templates/CSS, selected views/queries, static/deploy config, QA report

**ขนาดงาน:** M โดยแก้ทีละ route
**Dependencies:** Tasks 12, 19, 20, 22

### Checkpoint D: พร้อมเป็น release candidate บน staging

- CI, deploy checks และ browser smoke tests ผ่านจาก clean build
- production secrets/config/security headers ผ่าน review
- scheduler, freshness, alerts, backup, restore และ rollback ผ่าน rehearsal
- สูตร ข่าว สถิติ AI และผลหวยมี provenance และไม่มีข้อมูลสาธิตปะปน
- policy/contact/disclaimer พร้อม และไม่มี critical accessibility issue

### ระยะที่ 4: Beta และเปิดสาธารณะ

#### Task 28: เพิ่ม analytics ขั้นต่ำแบบรักษาความเป็นส่วนตัว

**รายละเอียด:** เก็บ event เพื่อวัด funnel โดยไม่ส่งข้อความฝัน เลขที่ผู้ใช้บันทึก หรือ IP เป็น payload

**Events ขั้นต่ำ:** `landing_view`, `dream_started`, `dream_completed`, `formula_used`, `news_opened`, `number_saved`, `result_checked`, `history_viewed`, `share_used`

**เกณฑ์รับงาน:**

- event/schema/retention ระบุชัดและเปิดตาม consent policy
- ไม่มีข้อความฝัน เลข หรือ identifier เกินจำเป็น
- มีรายงาน activation, result-check และ cross-draw retention รายงวด

**การตรวจสอบ:** debug event stream, payload inspection และ consent test

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** event client/endpoint, analytics config, privacy documentation

**ขนาดงาน:** M
**Dependencies:** Tasks 7, 26, Checkpoint D

#### Task 29: ทำ staging dress rehearsal

**รายละเอียด:** จำลองหนึ่งรอบงวดตั้งแต่ก่อนออกรางวัล ดึงข่าว/สร้าง prediction ผู้ใช้บันทึกเลข จนผลจริงเข้าและตรวจประวัติ พร้อมทดสอบเหตุขัดข้อง

**เกณฑ์รับงาน:**

- happy path ครบทุกขั้นโดยไม่แก้ฐานข้อมูลด้วยมือ
- upstream ล่ม, ข่าวว่าง, AI ล้ม และผลหวยช้าทำให้ระบบเข้า degraded state ถูกต้อง
- launch checklist, rollback owner และช่องทาง support พร้อม

**การตรวจสอบ:** signed staging rehearsal report พร้อมเวลา job, screenshot และ incident notes

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** staging fixtures/config, launch checklist, support/incident runbook

**ขนาดงาน:** M
**Dependencies:** Tasks 24, 25, 27, 28

#### Task 30: เปิด closed beta อย่างน้อยสองงวด

**รายละเอียด:** เชิญผู้ใช้กลุ่มเล็ก ใช้งานจริงอย่างน้อยสองงวด เก็บ feedback และ funnel โดยหยุด rollout หากพบข้อมูลหวยผิด การรั่วไหล หรือการใช้งานหลักล้มเหลว

**เกณฑ์รับงาน:**

- มีผู้ใช้กลุ่มแรก ช่องทางแจ้งปัญหา และผู้รับผิดชอบตอบสนอง
- มีข้อมูล activation, completion, result-check และ retention ครบสองงวด
- ปัญหา P0/P1 ถูกปิดหรือมี mitigation ที่เจ้าของผลิตภัณฑ์ยอมรับ

**การตรวจสอบ:** beta report, incident review และ go/no-go meeting

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** beta runbook, feedback form/config, metrics report

**ขนาดงาน:** M
**Dependencies:** Task 29

#### Task 31: เปิด public แบบ staged rollout

**รายละเอียด:** เปิด traffic เป็นช่วง เฝ้าดู error, latency, stale data, provider cost และ feedback ก่อนขยายเต็ม พร้อม rollback เมื่อเกินเกณฑ์ที่กำหนด

**เกณฑ์รับงาน:**

- domain/HTTPS/DNS และ production smoke tests ผ่าน
- ไม่มี P0/P1 ค้าง และ alert/backup/rollback ทำงานจริง
- มี post-launch review หลัง 24 ชั่วโมง, 7 วัน และหลังงวดแรก

**การตรวจสอบ:** production smoke test, monitoring evidence และ post-launch reports

**ไฟล์ที่คาดว่าจะเกี่ยวข้อง:** launch runbook, deployment config, status/support documentation

**ขนาดงาน:** M
**Dependencies:** Task 30

### Checkpoint E: ตัดสินใจทิศทางรายได้

- มีข้อมูล activation และ retention อย่างน้อยสองงวด
- ระบุได้ว่าผู้ใช้กลับมาเพราะสมุดเลข วิเคราะห์ฝัน ตรวจผล หรือคอนเทนต์
- มีปัญหาที่ผู้ใช้ยอมเสียเงินแก้อย่างน้อยหนึ่งข้อ หรือมีหลักฐานว่ายังไม่ควรสร้างระบบจ่ายเงิน

### ระยะที่ 5: ทดลองรายได้ทีละสมมติฐาน

#### Experiment A: สมุดเลขแบบสมาชิก

เหมาะเมื่อคนกลับมาเปิดสมุด/ประวัติข้ามงวดอย่างสม่ำเสมอ ทดลองด้วย landing page หรือ waitlist ก่อนสร้าง billing ฟีเจอร์ที่อาจขายคือ sync ข้ามเครื่อง, ประวัติไม่จำกัด, export และการแจ้งผล

เกณฑ์เดินหน้าตัวอย่าง: มีผู้ใช้กลุ่มเป้าหมายแสดงความตั้งใจจ่ายหรือสมัครทดลองอย่างมีนัยสำคัญตามจำนวนผู้เข้าร่วมจริง ไม่ใช้เปอร์เซ็นต์จาก sample ที่เล็กเกินไป

#### Experiment B: เครื่องมือทำคอนเทนต์ให้เจ้าของเพจ

เหมาะเมื่อผู้ใช้แชร์การ์ดหรือมีเจ้าของเพจสนใจ ทดลองทำตัวอย่างแบบ manual concierge ก่อน ระบบในอนาคตอาจสร้างภาพ/ข้อความติดแบรนด์จากข้อมูลที่ตรวจสอบแหล่งได้

เกณฑ์เดินหน้า: มีเจ้าของเพจใช้งานซ้ำหรือยอมจ่ายกับงานแบบ manual ก่อนลงทุนสร้างระบบอัตโนมัติ

#### Experiment C: Widget/API สำหรับเว็บอื่น

เหมาะเมื่อผลหวยและระบบฝันมี uptime/contract ที่นิ่ง ทดลองกับ partner จำนวนน้อยก่อน ฟีเจอร์คือ widget ตรวจผลหรือวิเคราะห์ฝันปรับสีและแบรนด์ได้

เกณฑ์เดินหน้า: partner นำไปติดจริงและเรียกใช้ซ้ำ พร้อมยอมรับราคาและข้อจำกัด API

#### Experiment D: โฆษณาหรือสปอนเซอร์

พิจารณาหลังมี traffic และกลุ่มผู้ใช้ชัด ตรวจนโยบายแพลตฟอร์มโฆษณาและกฎหมายตามเนื้อหา/ลิงก์ที่เปิดจริง ห้ามพึ่งรายได้ทางนี้เป็นเหตุผลหลักในการสร้าง MVP

## 7. ตัวชี้วัดสำหรับตัดสินใจ

วัดเป็นรายงวดและราย cohort ไม่ใช้ยอดสะสมอย่างเดียว:

- **Activation:** สัดส่วนผู้เข้าใหม่ที่บันทึกเลขพร้อมงวดสำเร็จ
- **Dream completion:** สัดส่วนผู้เริ่มวิเคราะห์ฝันที่ได้รับผลสำเร็จ
- **Save rate:** สัดส่วนผลวิเคราะห์ที่นำไปบันทึกอย่างน้อยหนึ่งเลข
- **Cross-draw retention:** ผู้ใช้ที่กลับมาในงวดถัดไป
- **Result-check rate:** ผู้มีรายการที่กลับมาตรวจผลหลังประกาศ
- **Share rate:** ผู้ใช้ที่สร้างหรือแชร์การ์ด
- **Reliability:** error rate, stale data rate และเวลาตั้งแต่ประกาศผลจนระบบอัปเดต
- **Revenue validation:** จำนวนผู้แสดงเจตนาจ่าย ทดลองจ่าย และกลับมาจ่ายซ้ำ แยกตามผลิตภัณฑ์

ยังไม่กำหนด threshold ตายตัวก่อนเห็นฐานผู้ใช้จริง รอบ beta แรกใช้เพื่อสร้าง baseline แล้วจึงตั้งเป้ารอบถัดไป

## 8. ความเสี่ยงและวิธีลดความเสี่ยง

| ความเสี่ยง | ผลกระทบ | วิธีรับมือ |
|---|---|---|
| สื่อความแม่นยำเกินหลักฐาน | สูง | แยก ranking/backtest/probability และเผยจำนวนตัวอย่าง/วิธีวัด |
| API ลบหรือแก้ข้อมูลถูกเรียกจากภายนอก | สูง | authentication, authorization, POST/CSRF, audit log และ tests |
| ผลหวยผิดหรือล่าช้า | สูง | canonical source, freshness status, reconciliation และ degraded state |
| ข้อความฝันมีข้อมูลส่วนบุคคล | สูง | data minimization, retention, delete flow และไม่ส่งเข้า analytics |
| frontend หลายชุดทำให้แก้ซ้ำ | กลาง | เลือก production owner หนึ่งชุดก่อนเพิ่มฟีเจอร์ |
| ข่าวจำลองปะปน production | สูง | environment boundary และ provenance label ที่บังคับใช้ |
| สูตร seed แบบสุ่มถูกเข้าใจว่าเป็นสถิติจริง | สูง | เปลี่ยนเป็น deterministic fixture และห้ามเผย accuracy ที่ไม่มีผลย้อนหลังรองรับ |
| scraper พังเมื่อหน้าเว็บต้นทางเปลี่ยน | กลาง | ใช้ RSS เป็นเส้นทางหลัก มี parser test, alert และปิด fallback อัตโนมัติเมื่อโครงสร้างเปลี่ยน |
| นำข่าวหรือภาพมาใช้เกินสิทธิ์ | สูง | เก็บ provenance ตรวจข้อกำหนดแหล่งข่าว ใช้ข้อความสรุปและภาพที่มีสิทธิ์เท่านั้น |
| scheduler หรือผู้ให้บริการ AI ใช้งบเกินคาด | กลาง | quota, timeout, cache, rate limit, cost alert และ fallback ที่ไม่สร้างข้อมูลเท็จ |
| งวดเป้าหมายหรือเวอร์ชันโมเดลไม่ชัด | สูง | บังคับ metadata contract ก่อน publish และซ่อนผลที่ readiness gate ไม่ผ่าน |
| ผู้ใช้เข้าเว็บเฉพาะวันหวยออก | กลาง | สมุดเลขและประวัติเป็นวงจรข้ามงวด วัด retention จริง |
| ทำระบบจ่ายเงินก่อนรู้คุณค่า | กลาง | ทดลอง waitlist/manual concierge ก่อน billing |
| เนื้อหาหวยกระทบนโยบายโฆษณา | กลาง | ตรวจนโยบายล่าสุดก่อนเปิดโฆษณาหรือ affiliate ทุกครั้ง |

## 9. คำถามที่ต้องตัดสินใจระหว่างทำ

- สูตรใดได้รับอนุมัติให้แสดงต่อสาธารณะ และ contract input/output ของแต่ละสูตรคืออะไร?
- จะใช้แหล่ง RSS ใดบ้าง แต่ละแหล่งอนุญาตให้นำหัวข้อ ภาพ และข้อความสรุปมาเผยแพร่ในรูปแบบใด?
- ข่าวระดับใด auto-publish ได้ และข่าวระดับใดต้องผ่านผู้ดูแลก่อนเผยแพร่?
- จะ deploy ที่ผู้ให้บริการใด ใช้ domain ใด และใครเป็นเจ้าของ DNS, secret และบัญชี production?
- งบและ quota ของ AI/บริการภายนอกต่อวันเท่าใด และเมื่อ provider ใช้งานไม่ได้ต้องแสดงผลแบบใด?
- ข้อมูลฝันควรเก็บแบบ anonymous, account-bound หรือไม่เก็บข้อความดิบหลังวิเคราะห์?
- beta รุ่นแรกจะเชิญผู้ใช้จากช่องทางใด และใครเป็นผู้ตอบปัญหา?
- หลังได้ baseline สองงวด จะทดลองรายได้ A, B หรือ C ก่อนตามพฤติกรรมที่พบ?

## 10. Definition of Done สำหรับทุก Task

งานหนึ่งถือว่าเสร็จเมื่อ:

- ผ่าน acceptance criteria ของ task
- focused tests ผ่าน และเพิ่ม regression test เมื่อแก้ bug/behavior
- ไม่มีข้อมูลจำลองหรือ secret หลุดเข้าสู่ production path
- error state และ empty state ถูกตรวจ
- เอกสารที่เกี่ยวข้องถูกอัปเดต
- มีหลักฐานการตรวจ เช่น command output, screenshot หรือ test report
- ผู้รีวิวที่ไม่ได้เขียนงานสามารถทำตามขั้นตอนและยืนยันผลได้

## 11. วิธีส่งต่องาน

ผู้รับช่วงควรเริ่มจาก Task 11 ตามลำดับใน `tasks/todo.md` และอัปเดต checklist หลังจบแต่ละ task ในแต่ละรอบส่งมอบให้ระบุ:

1. สิ่งที่เปลี่ยนและเหตุผล
2. ไฟล์หรือ migration ที่กระทบ
3. คำสั่งและผลการทดสอบ
4. ข้อจำกัดหรือสิ่งที่ยังไม่ยืนยัน
5. task ถัดไปที่พร้อมเริ่มและ dependency ที่ยังค้าง

ห้ามเริ่มระยะสร้างรายได้ก่อนผ่าน Checkpoint E เว้นแต่เป็นการทดลองแบบ landing page, waitlist หรือ manual concierge ที่ยังไม่ต้องสร้างระบบชำระเงินจริง

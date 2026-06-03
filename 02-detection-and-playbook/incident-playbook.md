# Incident Response Playbook — SQL Injection Auth Bypass

**Trigger:** alert `sqli-login-success.yml` (critical) — login `result: success` ที่ field username มี `'`
**Scope:** SQLi (' OR 1=1 --)
**Author:** EDSON· **Updated:** 02/06/2026

---

## 1. Scenario
alert sqli-login-success.yml (critical) → หมายความว่าระบบการ login ถูกโจมตีด้วย SQLi (auth bypass success = attacker เข้าสู่ระบบสำเร็จ) จัดเป็นความรุนแรง critical

## 2. Response Overview
Flow: 5 phase + 2 branch
Triage → Containment → Eradication (app-level / host-level) → Recovery → Lessons Learned · ตลอดทุก phase: Communication + Documentation

---

## Phase 1 — Triage
> *เป้าหมาย: ยืนยันว่าเป็นการโจมตีของจริง + ประเมินขอบเขต ก่อนดำเนินการต่อ*
- [ ] Check account ที่ถูก login — เป็นใคร / มีสิทธิ์ระดับไหน
- [ ] ยืนยันกับทีม — เช็คว่ามีการ test ระบบภายในหรือไม่
- [ ] dwell time: ตรวจสอบว่าปัญหานี้เกิดขึ้นมานานแค่ไหนแล้ว

## Phase 2 — Containment
> *เป้าหมาย: หยุดเลือด โดยไม่ทำลายหลักฐาน*
> **ลำดับสำคัญ:** เก็บหลักฐานก่อน → จากนั้นค่อยทำ action ต่อก่อนเปลี่ยน state
- [ ] เก็บหลักฐาน: snapshot + clone + log ทั้งหมดที่เกี่ยวข้อง
- [ ] virtual patch: ระบบป้องกันการโจมตีครั้งใหม่ ด้วย rule block การรับค่า " ' " จากช่องทาง input
- [ ] kill session: เคลียร์ session ที่ค้างในระบบ เพื่อให้ attacker ไม่สามารถใช้งานระบบได้ต่อ

## Phase 3 — Eradication
> *เป้าหมาย: ลบ foothold ที่ attacker ทิ้งไว้ — แยกเป็น 2 branch ตามความลึกของปัญหา*
### Branch A — App-level (attacker ยังไม่ได้ shell)
- [ ] Clean environment: ดำเนินการลบ backdoor, script, หรือไฟล์ที่น่าสงสัยที่ถูกสร้างในช่วงเวลาดังกล่าว รวมทั้งไฟล์ที่ถูกทำการแก้ไข อาจมีการถูกฝัง code ที่ไม่ปลอดภัย(สามารถใช้แพคเกจที่ตรวจจับไฟล์ในระบบช่วยได้ watchdog, inotify)
- [ ] Clean Database: ตรวจสอบ Database มีการจัดเก็บข้อมูลที่เป็นอันตรายหรือไหม เพื่อตรวจสอบป้องกัน Stored XSS

### Branch B — Host-level (attacker ได้ shell / RCE)
- [ ] rebuild: ควรดำเนินการสร้างระบบใหม่ เพื่อกลับไปใช้งานระบบที่ปลอดภัยไม่มีอะไรแอบแฝง
- [ ] rotate secret: เปลี่ยนรหัสผ่าน คีย์การเข้าถึง (Access Key) หรือรหัสลับ (Secret) ที่ใช้ในการยืนยันตัวตนในระบบต่างๆ ใหม่ทั้งหมด

## Phase 4 — Recovery
> *เป้าหมาย: กู้บริการกลับอย่างปลอดภัย + ยืนยันว่า fix ได้ผลจริง*
> ⚠️ known-good image สะอาดจาก artifact ของ attacker — **แต่ code โหว่เดิมยังอยู่**
- [ ] **Permanent code fix:** ใช้ parameterized query — ใช้ ? placeholder ทำให้ database มองทุกอย่างที่ใส่เข้ามาเป็น data ไม่ใช่ code ดังนั้น payload จะถูกเก็บเป็น plain text ธรรมดา
- [ ] กู้ระบบจาก version ที่ปลอดภัย โดยอ้างอิง timeline จาก log
- [ ] new code: ตรวจสอบว่า code ได้รับการแก้ไขปัญหาเป็นเวอร์ชันที่ไม่มีช่องโหว่แล้ว
- [ ] monitor ต่อเนื่อง: ยืนยันว่าช่องโหว่ไม่กลับมา แปลว่า root fix ถูกต้อง

## Phase 5 — Lessons Learned
> *เป้าหมาย: ตรวจจับการโจมตีครั้งใหม่/ป้องกันได้ดียิ่งขึ้น*
- [ ] detection rule ใหม่ที่ดียิ่งขึ้น: ออกแบบ rule ที่ครอบคลุมมากยิ่งขึ้น ในระบบ persistence เพื่อให้ทราบว่า attacker ทิ้งไว้บ้าง เช่น backdoor account, token, key
- [ ] honeypot / canary account: ควรมองหาประโยชน์จากวิกฤต เพื่อใช้ประโยชน์จาก attacker หากสร้างระบบจำลองที่สามารถควบคุมผลกระทบได้ การที่ปล่อยให้ attacker เข้ามาในช่องโหว่เดิมจะเป็นการเรียนรู้ว่าอีกฝ่ายสามารถทำอะไรได้บ้าง ต้องการอะไร เพื่อให้ทราบข้อมูลและใช้ข้อมูลเหล่านั้นในการออกแบบระบบป้องกันที่ดียิ่งขึ้น

---

## Cross-cutting (ทำตลอดทุก phase)

### Communication / Escalation
- **Escalate ทันทีเมื่อ:** สามารถระบุ trigger — เช่น ยืนยัน host-level / PII ถูกเข้าถึง เป็นต้น
- **แจ้งใคร:** Tier 2 / system owner / legal-compliance ถ้ามี data breach

### Documentation / Timeline
- ควรทำการจด action + timestamp ตลอด หรือใช้ Issue Tracking System — เพื่อ chain of custody + วัตถุดิบ Lessons Learned

---

## Lessons / Challenges
ปัญหา/insight จริงที่เจอตอนคิด playbook นี้
- หากไม่มีมาตราฐาน หรือข้อมูลอ้างอิง NIST/SANS IR lifecycle การคิดขั้นตอนการรับมือกับปัญหาเป็นเรื่องยาก ในบางครั้งวิธีที่ใช้จัดการปัญหานั้นได้ผลจริงแต่ไม่ได้แก้ที่ต้นเหตุ เป็นการแก้ไขที่ปลายเหตุ หรือแม้แต่บางครั้งสิ่งที่คิดว่าแก้ไขปัญหาได้อย่างที่เคยได้พบเจอมาอย่าง ถ้าถูกโจมตีจากต่างประเทศ ก็ทำการ block IP ต่างประเทศสิ แต่ไม่ได้มองว่า attacker สามารถ VPN มาภายในประเทศได้เหมือนกัน 
- playbook นี้ผมอิงจาก NIST/SANS IR lifecycle โดยย่อให้เหมาะสมกับ lab ที่ออกแบบไว้ โดยที่ตัวเต็มตามมาตราฐานจะเพิ่ม preparation phase กับ formal communication plan เข้ามาด้วย

---
*Section 02 · security-analyst-toolkit*
# Internet Speed Test Monitoring - Railway Setup

🚀 **วัดความเร็วอินเทอร์เน็ตทุกชั่วโมง เก็บเป็นสถิติ** (ทุกชั่วโมงแบบอัตโนมัติ)

---

## 📋 ขั้นตอนการตั้ง Railway (5 นาที)

### ขั้นที่ 1: สร้าง GitHub Repository
1. ไปที่ https://github.com/new
2. สร้าง repo ชื่อ `speedtest-monitor` (ห้ามเป็น Private ให้เป็น Public)
3. Clone หรือ upload ไฟล์ต่อไปนี้:
   ```
   app.py
   requirements.txt
   Procfile
   .gitignore
   ```

### ขั้นที่ 2: สร้าง .gitignore
สร้างไฟล์ `.gitignore` ด้วยเนื้อหา:
```
speedtest_results.csv
__pycache__/
*.pyc
.env
```

### ขั้นที่ 3: สมัครสมาชิก Railway
1. ไปที่ https://railway.app
2. คลิก "Start Now" → Sign up ด้วย GitHub
3. Authorize Railway เข้า GitHub account

### ขั้นที่ 4: Deploy บน Railway
1. ใน Railway Dashboard → คลิก "New Project"
2. เลือก "Deploy from GitHub repo"
3. เลือก repo `speedtest-monitor` ที่คุณสร้าง
4. Railway จะ auto-deploy เมื่อ push code

### ขั้นที่ 5: ตรวจสอบ
รอสัก 2-3 นาที ให้ deploy เสร็จ จากนั้น:
- คลิก "View Deployment" ก็จะเห็น domain ของคุณ

---

## 🔗 API Endpoints

หลังจาก deploy แล้ว ที่ domain ของ Railway:

### 1. ตรวจสอบความเร็ว ล่าสุด
```
GET https://your-domain.railway.app/latest
```
ตัวอย่าง response:
```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "download_mbps": 45.67,
  "upload_mbps": 12.34,
  "ping_ms": 25.5,
  "server": "Bangkok ISP"
}
```

### 2. ดูสถิติรวม (เฉลี่ย/max/min)
```
GET https://your-domain.railway.app/stats
```
ตัวอย่าง response:
```json
{
  "total_tests": 24,
  "download": {
    "avg": 45.2,
    "max": 52.1,
    "min": 38.9
  },
  "upload": {
    "avg": 12.0,
    "max": 15.2,
    "min": 10.1
  },
  "ping": {
    "avg": 24.5,
    "max": 35.2,
    "min": 20.1
  }
}
```

### 3. ดูประวัติทั้งหมด
```
GET https://your-domain.railway.app/history
```

### 4. ตรวจสอบว่า App ยังทำงาน
```
GET https://your-domain.railway.app/health
```

---

## ⚙️ วิธีการทำงาน

- **อัตโนมัติ**: App จะวัดความเร็วอินเทอร์เน็ต **ทุกชั่วโมง** โดยไม่ต้องทำอะไร
- **เก็บข้อมูล**: บันทึกไว้ใน file `speedtest_results.csv`
- **ดึงข้อมูล**: ใช้ API endpoints ด้านบนเพื่อดูผล
- **ตัวเมื่อไหร่**: ทันทีที่ deploy ก็เริ่มวัดอัตโนมัติ

---

## 📊 ดูข้อมูล (ตัวเลือก)

### ตัวเลือก 1: ใช้ Postman/Insomnia
- ดาวน์โหลด Postman: https://www.postman.com/downloads/
- Paste URL เช่น `https://your-domain.railway.app/latest`

### ตัวเลือก 2: ใช้ Browser
- เปิด `https://your-domain.railway.app/latest` ใน browser ก็ได้

### ตัวเลือก 3: ใช้ Command line
```bash
curl https://your-domain.railway.app/stats
```

---

## 🆓 ราคา Railway

- **Free credit**: $5 ต่อเดือน (มาจาก Railway สมาชิกใหม่)
- **ใช้ประมาณเท่าไหร่**: Speedtest ทุกชั่วโมง ≈ $1-2/month
- **หลังหมดเงิน**: Railway จะส่ง notification มาก่อน

---

## 🚨 Troubleshooting

### App ไม่ทำงาน/Crash
1. ไปที่ Railway Dashboard → เลือก Project
2. คลิก "Deployment" → ดู Logs
3. Search `error` ในลอก

### ไม่เห็น speedtest results
1. รอสัก 1+ ชั่วโมง (ครั้งแรกอาจใช้เวลา)
2. ลองเรียก `/health` ดูว่า app ยังทำงาน
3. ลองเรียก `/history` เพื่อดูว่ามีข้อมูลหรือไม่

### ต้องการ Update code
1. Edit `app.py` ใน GitHub
2. Push ขึ้น repository
3. Railway จะ auto-deploy ใหม่

---

## 💡 Tips

- **ดู domain**: Railway Dashboard → Project → Settings ด้านขวา
- **ตั้ง custom domain**: Railway Dashboard → Project → Settings → Domains
- **ดู logs**: Railway Dashboard → Project → Deployments → View Logs

---

## 📝 Notes

- ครั้งแรก speedtest อาจใช้เวลา 1-2 นาที
- ข้อมูลจะเก็บไว้ตลอด (หรือจนกว่า Railway auto-cleanup)
- สามารถ export data ออกมาเป็น CSV ได้

**สนใจเพิ่มเติม?** ติดต่อ support หรือทำการ customize เอง 🚀

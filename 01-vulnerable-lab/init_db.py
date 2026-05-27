import sqlite3

conn = sqlite3.connect('app.db') #สร้างไฟล์ชื่อ app.db + เชื่อมต่อ sqlite3
cursor = conn.cursor() #cursor สำหรับสั่ง SQL

#Python สั่ง SQL — ใช้ cursor.execute ในการสร้าง
# 1.สร้างตาราง users + row ภายใน
cursor.execute('''CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    email TEXT,
    phone TEXT
)''')

#Python สั่ง SQL — ใช้ cursor.execute
# 2.สร้างตาราง reviews + row ภายใน
cursor.execute('''CREATE TABLE reviews (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    review_text TEXT NOT NULL
)''')

#บันทึก
conn.commit()

#ปิดการทำงาน
conn.close()

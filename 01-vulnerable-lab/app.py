from flask import Flask, render_template, request, redirect    
import sqlite3
import logging, json
from datetime import datetime, timezone

# --- security event logger (แยกออกจาก root / Werkzeug) ---
security_logger = logging.getLogger('security')        # 1. ขอ logger ชื่อ 'security'
security_logger.setLevel(logging.INFO)                 # 2. เก็บตั้งแต่ระดับ INFO ขึ้นไป
handler = logging.FileHandler('security.log')          # 3. ปลายทาง = ไฟล์
handler.setFormatter(logging.Formatter('%(message)s')) # 4. เอาแค่ message ดิบ (JSON ล้วนๆ)
security_logger.addHandler(handler)                    # 5. ผูก handler เข้ากับ logger
security_logger.propagate = False                      # 6. ห้าม bubble ขึ้นไป root
# ---

app = Flask(__name__)             # สร้าง app

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # รับข้อมูลจาก form ก่อน > จากนั้นบันทึกข้อมูลลง database
        username = request.form['username'] 
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor() 
        cursor.execute(f"INSERT INTO users (username, password, email, phone) VALUES ('{username}', '{password}', '{email}', '{phone}')")
        conn.commit() 
        conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'] 
        password = request.form['password']
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()       
        cursor.execute(f"SELECT * FROM users WHERE username='{username}' AND password='{password}'")
        user = cursor.fetchone()  
        conn.close()

        result = "success" if user else "failed"   # ← แปลงผลก่อน
        security_logger.info(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "login_attempt",
            "src_ip": request.remote_addr,           # ← Flask ให้ IP มาทางนี้
            "username": username,
            "result": result
        }))

        if user: 
            return redirect('/profile?id=' + str(user[0]))
        else:
            return render_template('login.html')
    return render_template('login.html')

@app.route('/profile')
def profile():
    user_id = request.args.get('id')
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE id='{user_id}'")
    user = cursor.fetchone()
    conn.close()
    return render_template('profile.html', user=user)

@app.route('/review', methods=['GET', 'POST'])
def review():
    if request.method == 'POST':
        user_id = request.args.get('id')
        review = request.form['review']
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()       
        cursor.execute(f"INSERT INTO reviews (user_id, review_text) VALUES ('{user_id}', '{review}')")
        conn.commit()
        conn.close()
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()       
    cursor.execute("SELECT * FROM reviews")
    reviews = cursor.fetchall()
    conn.close()
    return render_template('review.html', reviews=reviews)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    message = ""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        new_password = request.form['new_password']

        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()

        # VULNERABLE: ใช้ f-string
        cursor.execute(f"""
            SELECT * FROM users 
            WHERE username='{username}' AND email='{email}'
        """)
        user = cursor.fetchone()

        if user:
            # VULNERABLE: update password ตรง ๆ 
            cursor.execute(f"""
                UPDATE users 
                SET password='{new_password}'
                WHERE username='{username}'
            """)
            conn.commit()
            message = "Password updated successfully"
        else:
            message = "Invalid username or email"

        conn.close()
    return render_template('forgot_password.html', message=message)

# สั่งให้ app เริ่มทำงาน
app.run(debug=True, host='0.0.0.0')

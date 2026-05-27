from flask import Flask, render_template, request, redirect    
import sqlite3

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
    cursor.execute(f"SELECT * FROM reviews")
    reviews = cursor.fetchall()
    conn.close()
    return render_template('review.html', reviews=reviews)

# สั่งให้ app เริ่มทำงาน
app.run(debug=True)


from flask import Flask, request, redirect, render_template, session, url_for
import pyodbc
import os
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ==========================
# Database connection
# ==========================
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=GAB\\SQLEXPRESS;'
    'DATABASE=SMARTPARK;'
    'Trusted_Connection=yes;'
)
cursor = conn.cursor()

# ==========================
# ESP32 Microdot Server IP
# ==========================
ESP32_IP = 'http://192.168.1.100'  # Change to your ESP32's IP from Microdot logs

# ==========================
# Routes
# ==========================
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        profile = request.files['profile']
        id_front = request.files['idfront']
        id_back = request.files['idback']

        # Save uploaded files
        profile_filename = os.path.join(app.config['UPLOAD_FOLDER'], profile.filename)
        id_front_filename = os.path.join(app.config['UPLOAD_FOLDER'], id_front.filename)
        id_back_filename = os.path.join(app.config['UPLOAD_FOLDER'], id_back.filename)

        profile.save(profile_filename)
        id_front.save(id_front_filename)
        id_back.save(id_back_filename)

        # Insert into DB via stored procedure
        cursor.execute("""
            EXEC sp_InsertCustomer ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        """, data['firstname'], data['middlename'], data['lastname'],
             data['email'], data['phone'], data['username'], data['password'],
             profile.filename, id_front.filename, id_back.filename)

        conn.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute("EXEC sp_ValidateLogin ?, ?", username, password)
        user = cursor.fetchone()

        if user:
            session['user'] = username
            session['customer_id'] = user.CUSTOMERID
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid login credentials.'
    return render_template('login.html', error=error)

@app.route('/dashboard')
def dashboard():
    if 'customer_id' not in session:
        return redirect(url_for('login'))

    customer_id = session['customer_id']

    # Get customer info
    cursor.execute("SELECT * FROM CUSTOMER WHERE CUSTOMERID = ?", customer_id)
    customer = cursor.fetchone()

    # Get LED status from ESP32
    try:
        status = requests.get(f'{ESP32_IP}/status', timeout=2).text.strip()
    except requests.RequestException:
        status = 'Unavailable'

    return render_template('dashboard.html', led_status=status, customer=customer)

@app.route('/api/led-status')
def led_status():
    try:
        status = requests.get(f'{ESP32_IP}/status', timeout=2).text.strip()
    except requests.RequestException:
        status = 'Unavailable'
    return status

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    

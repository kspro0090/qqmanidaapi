from flask import Flask, render_template_string, request, redirect, session, flash, url_for
import sqlite3
from datetime import datetime
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import os
from functools import wraps

def append_to_sheet(data_list):
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open("پرسش و پاسخ سیستم").sheet1  # اسم شیت شما
    sheet.append_row(data_list)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Database Migration Function
def migrate_database():
    """Automatically add missing columns to violation_reports table"""
    conn = sqlite3.connect('system.db')
    c = conn.cursor()
    
    try:
        # Check if manager_notes column exists
        c.execute("PRAGMA table_info(violation_reports)")
        columns = [column[1] for column in c.fetchall()]
        
        if 'manager_notes' not in columns:
            c.execute("ALTER TABLE violation_reports ADD COLUMN manager_notes TEXT")
            print("✅ Added manager_notes column to violation_reports table")
        
        if 'notes' not in columns:
            c.execute("ALTER TABLE violation_reports ADD COLUMN notes TEXT")
            print("✅ Added notes column to violation_reports table")
        
        conn.commit()
    except Exception as e:
        print(f"⚠️ Migration error (may be normal if columns already exist): {e}")
    finally:
        conn.close()

# Run migration on app startup
migrate_database()

# Authentication decorators
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'manager_logged_in' not in session:
            return redirect(url_for('manager_login'))
        return f(*args, **kwargs)
    return decorated_function

def violation_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'violation_admin_logged_in' not in session:
            return redirect(url_for('violation_admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# مشخصات sms.ir
USERNAME = "9195134535"
PASSWORD = "an5zQbIoXsdwiPUxrrMXySa6K3EJhekRrhz3IySVwl6HuSCy"
LINE_NUMBER = "30005675123456"

import requests

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>سیستم پرسش و پاسخ</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');
            body { font-family: 'Vazirmatn', sans-serif; direction: rtl; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
            .main-card { background: rgba(255, 255, 255, 0.95); border-radius: 20px; padding: 40px; max-width: 600px; width: 100%; box-shadow: 0 15px 35px rgba(0,0,0,0.1); text-align: center; }
            .main-title { font-size: 2.5rem; font-weight: 700; color: #2d3436; margin-bottom: 30px; }
            .btn-main { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; border-radius: 15px; padding: 20px 30px; font-weight: 600; font-size: 1.1rem; margin: 10px; transition: all 0.3s ease; text-decoration: none; color: white; display: inline-block; }
            .btn-main:hover { transform: translateY(-3px); box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4); color: white; }
            .btn-admin { background: linear-gradient(135deg, #2d3436 0%, #636e72 100%); }
            .btn-admin:hover { box-shadow: 0 8px 25px rgba(45, 52, 54, 0.4); }
            .btn-manager { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
            .btn-manager:hover { box-shadow: 0 8px 25px rgba(240, 147, 251, 0.4); }
            .btn-violation { background: linear-gradient(135deg, #e17055 0%, #d63031 100%); }
            .btn-violation:hover { box-shadow: 0 8px 25px rgba(225, 112, 85, 0.4); }
        </style>
    </head>
    <body>
        <div class="main-card">
            <h1 class="main-title"><i class="bi bi-chat-square-text me-3"></i>سیستم پرسش و پاسخ</h1>
            <div class="d-flex flex-wrap justify-content-center">
                <a href="/form" class="btn btn-main">
                    <i class="bi bi-plus-circle me-2"></i>ارسال سؤال جدید
                </a>
                <a href="/manager/login" class="btn btn-main btn-manager">
                    <i class="bi bi-person-badge me-2"></i>ورود مدیر
                </a>
                <a href="/admin/login" class="btn btn-main btn-admin">
                    <i class="bi bi-shield-lock me-2"></i>ورود ادمین کل
                </a>
                <a href="/violation-admin/login" class="btn btn-main btn-violation">
                    <i class="bi bi-exclamation-triangle me-2"></i>ورود ادمین تخلفات
                </a>
            </div>
        </div>
    </body>
    </html>
    ''')

def send_sms(phone, message):
    url = "https://rest.payamak-panel.com/api/SendSMS/SendSMS"

    payload = {
        "username": "PR.mehramen",
        "password": "PR*mehramen.3004",
        "to":phone,
        "from": "90001953",
        "text": message,
        "isFlash": False
    }

    try:
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            result = response.json()
            if result.get("RetStatus") == 1:
                print(f"✅ پیامک با موفقیت به {phone} ارسال شد.")
            else:
                print(f"❌ خطا در ارسال: {result.get('StrRetStatus')}")
        else:
            print(f"❌ خطای HTTP: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ خطا در شبکه یا سیستم: {e}")

def calculate_current_reward(created_at_str, timer_hours, fixed_reward, waiting_deadline=None, penalty_multiplier=3, violation_status=None, paused_reward=None):
    """Calculate current reward based on elapsed time and waiting periods"""
    
    # If question is paused due to violation, return the paused reward
    if violation_status == 'paused' and paused_reward is not None:
        return paused_reward
    
    created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S.%f")
    current_time = datetime.now()
    
    # If we have a waiting deadline, use it as the current deadline
    if waiting_deadline:
        deadline = datetime.fromisoformat(waiting_deadline)
        if current_time <= deadline:
            # Still in waiting period - reward is frozen at fixed_reward
            return fixed_reward
        else:
            # Waiting period ended, calculate penalty from deadline
            elapsed_seconds = (current_time - deadline).total_seconds()
            allowed_seconds = timer_hours * 3600  # Base allowed time for penalty calculation
            penalty_per_second = fixed_reward / allowed_seconds
            penalty = int(elapsed_seconds * penalty_per_second * penalty_multiplier)
            return -penalty
    else:
        # No waiting period, calculate from creation time
        deadline = created_at + timedelta(hours=timer_hours)
        if current_time <= deadline:
            # Still within allowed time
            remaining_seconds = (deadline - current_time).total_seconds()
            allowed_seconds = timer_hours * 3600
            current_reward = int(fixed_reward * (remaining_seconds / allowed_seconds))
            return max(current_reward, 0)  # Don't go below 0 during countdown
        else:
            # Past deadline, calculate penalty
            elapsed_seconds = (current_time - deadline).total_seconds()
            allowed_seconds = timer_hours * 3600
            penalty_per_second = fixed_reward / allowed_seconds
            penalty = int(elapsed_seconds * penalty_per_second * penalty_multiplier)
            return -penalty

def calculate_reward(created_at_str, answered_at_str, base_reward, base_hours):
    created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S.%f")
    answered_at = datetime.strptime(answered_at_str, "%Y-%m-%d %H:%M:%S.%f")

    elapsed_seconds = (answered_at - created_at).total_seconds()
    allowed_seconds = base_hours * 3600

    if elapsed_seconds <= allowed_seconds:
        remaining_seconds = allowed_seconds - elapsed_seconds
        reward = int(base_reward * (remaining_seconds / allowed_seconds))
    else:
        penalty_per_second = base_reward / allowed_seconds
        reward = -int((elapsed_seconds - allowed_seconds) * penalty_per_second)
        if reward < -base_reward:
            reward = -base_reward

    return reward

@app.route('/form', methods=['GET', 'POST'])
def form():
    conn = sqlite3.connect('system.db')
    c = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        question_text = request.form['question']
        department_id = request.form['department']

        # گرفتن مقدار base_reward و base_hours
        c.execute("SELECT base_reward_amount, base_timer_hours FROM admin_settings WHERE id = 1")
        settings = c.fetchone()
        base_reward = settings[0] if settings else 200000
        base_hours = settings[1] if settings else 24

        now = datetime.now()

        # بررسی وجود کاربر یا اضافه کردن
        c.execute("SELECT id FROM users WHERE phone = ?", (phone,))
        user = c.fetchone()
        if user:
            user_id = user[0]
        else:
            c.execute("INSERT INTO users (name, phone) VALUES (?, ?)", (name, phone))
            user_id = c.lastrowid

        # ثبت سؤال با مقداردهی ستون fixed_reward برابر با base_reward
        c.execute("""INSERT INTO questions 
                     (user_id, department_id, question_text, status, created_at, reward_amount, timer_hours, fixed_reward, waiting_count, penalty_multiplier) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (user_id, department_id, question_text, 'pending', now, 0, base_hours, base_reward, 0, 3))
        conn.commit()

        # گرفتن شماره مدیر
        c.execute("SELECT manager_phone FROM departments WHERE id = ?", (department_id,))
        manager_row = c.fetchone()
        manager_phone = manager_row[0] if manager_row else ''

        conn.close()

        # ارسال SMS به مدیر (اگر بخوای)
        sms_text = f"یک سؤال جدید برای شما ثبت شد."
        send_sms(manager_phone, sms_text)

        return '''
        <!DOCTYPE html>
        <html lang="fa" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>سؤال ثبت شد</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');
                body { font-family: 'Vazirmatn', sans-serif; direction: rtl; background: linear-gradient(135deg, #00b894 0%, #55efc4 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
                .success-card { background: white; border-radius: 20px; padding: 40px; text-align: center; box-shadow: 0 15px 35px rgba(0,0,0,0.1); max-width: 400px; }
                .success-icon { font-size: 4rem; color: #00b894; margin-bottom: 20px; }
                h3 { color: #2d3436; margin-bottom: 20px; }
                .btn-return { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 12px; padding: 12px 25px; text-decoration: none; font-weight: 600; transition: all 0.3s ease; }
                .btn-return:hover { transform: translateY(-2px); color: white; }
            </style>
        </head>
        <body>
            <div class="success-card">
                <div class="success-icon"><i class="bi bi-check-circle-fill"></i></div>
                <h3>سؤال با موفقیت ثبت شد!</h3>
                <p>سؤال شما ارسال شده و به زودی پاسخ دریافت خواهید کرد.</p>
                <a href="/form" class="btn btn-return"><i class="bi bi-plus-circle me-2"></i>ارسال سؤال جدید</a>
            </div>
        </body>
        </html>
        '''

    c.execute("SELECT id, name FROM departments")
    departments = c.fetchall()
    conn.close()

    html = '''
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>فرم ارسال سؤال</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');
            
            body { 
                direction: rtl; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                font-family: 'Vazirmatn', sans-serif;
                min-height: 100vh;
                padding: 20px 0;
            }
            
            .main-card { 
                border: none; 
                border-radius: 20px; 
                box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                max-width: 600px;
                margin: 0 auto;
            }
            
            .form-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 20px 20px 0 0;
                text-align: center;
                position: relative;
                overflow: hidden;
            }
            
            .form-header::before {
                content: '';
                position: absolute;
                top: -50%;
                right: -50%;
                width: 200%;
                height: 200%;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="2" fill="rgba(255,255,255,0.1)"/></svg>') repeat;
                animation: float 20s infinite linear;
            }
            
            @keyframes float {
                0% { transform: translate(-50%, -50%) rotate(0deg); }
                100% { transform: translate(-50%, -50%) rotate(360deg); }
            }
            
            .form-header h3 {
                margin: 0;
                font-weight: 600;
                font-size: 1.8rem;
                position: relative;
                z-index: 2;
            }
            
            .form-body {
                padding: 40px;
            }
            
            .form-label {
                font-weight: 500;
                color: #4a5568;
                margin-bottom: 8px;
                font-size: 0.95rem;
            }
            
            .form-control, .form-select {
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 1rem;
                transition: all 0.3s ease;
                background: rgba(255, 255, 255, 0.9);
            }
            
            .form-control:focus, .form-select:focus {
                border-color: #667eea;
                box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
                background: white;
            }
            
            .btn-submit {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: none;
                border-radius: 12px;
                padding: 15px 30px;
                font-weight: 600;
                font-size: 1.1rem;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            }
            
            .btn-submit:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
                background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
            }
            
            .input-group {
                position: relative;
                margin-bottom: 25px;
            }
            
            .input-icon {
                position: absolute;
                right: 16px;
                top: 50%;
                transform: translateY(-50%);
                color: #a0aec0;
                z-index: 3;
            }
            
            .form-control.with-icon {
                padding-right: 45px;
            }
            
            .form-select.with-icon {
                padding-right: 45px;
            }
            
            @media (max-width: 768px) {
                .container {
                    padding: 10px;
                }
                
                .form-body {
                    padding: 30px 25px;
                }
                
                .form-header {
                    padding: 25px;
                }
                
                .form-header h3 {
                    font-size: 1.5rem;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="main-card">
                <div class="form-header">
                    <h3><i class="bi bi-question-circle-fill me-2"></i>فرم ارسال سؤال</h3>
                </div>
                <div class="form-body">
                    <form method="post">
                        <div class="input-group">
                            <label class="form-label">نام کامل</label>
                            <div class="position-relative">
                                <i class="bi bi-person-fill input-icon"></i>
                                <input type="text" name="name" class="form-control with-icon" placeholder="نام و نام خانوادگی خود را وارد کنید" required>
                            </div>
                        </div>
                        
                        <div class="input-group">
                            <label class="form-label">شماره موبایل</label>
                            <div class="position-relative">
                                <i class="bi bi-phone-fill input-icon"></i>
                                <input type="tel" name="phone" class="form-control with-icon" placeholder="09xxxxxxxxx" pattern="[0-9]{11}" required>
                            </div>
                        </div>
                        
                        <div class="input-group">
                            <label class="form-label">متن سؤال</label>
                            <div class="position-relative">
                                <i class="bi bi-chat-text-fill input-icon" style="top: 20px;"></i>
                                <textarea name="question" class="form-control with-icon" rows="4" placeholder="سؤال خود را به طور کامل و واضح بنویسید..." required></textarea>
                            </div>
                        </div>
                        
                        <div class="input-group">
                            <label class="form-label">انتخاب واحد مربوطه</label>
                            <div class="position-relative">
                                <i class="bi bi-building-fill input-icon"></i>
                                <select name="department" class="form-select with-icon" required>
                                    <option value="">واحد مورد نظر را انتخاب کنید</option>
                                    {% for d in departments %}
                                        <option value="{{ d[0] }}">{{ d[1] }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                        
                        <button type="submit" class="btn btn-submit w-100">
                            <i class="bi bi-send-fill me-2"></i>ارسال سؤال
                        </button>
                    </form>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''
    return render_template_string(html, departments=departments)

@app.route('/manager', methods=['GET', 'POST'])
@manager_required
def manager_dashboard():
    manager_phone = session.get('manager_phone')
    department_id = session.get('department_id')
    department_name = session.get('department_name')
    
    conn = sqlite3.connect('system.db')
    c = conn.cursor()

    # Handle SMS Report functionality
    if request.method == 'POST' and 'send_report' in request.form:
        # Calculate total rewards and penalties
        c.execute("SELECT SUM(reward_amount) FROM questions WHERE department_id = ? AND reward_amount > 0", (department_id,))
        total_rewards = c.fetchone()[0] or 0
        
        c.execute("SELECT SUM(reward_amount) FROM questions WHERE department_id = ? AND reward_amount < 0", (department_id,))
        total_penalties = c.fetchone()[0] or 0
        
        # Calculate question statistics by status
        c.execute("SELECT COUNT(*) FROM questions WHERE department_id = ? AND status = 'pending'", (department_id,))
        unanswered_questions = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(*) FROM questions WHERE department_id = ? AND user_feedback = 'solved'", (department_id,))
        solved_questions = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(*) FROM questions WHERE department_id = ? AND user_feedback = 'waiting'", (department_id,))
        waiting_questions = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(*) FROM questions WHERE department_id = ? AND (user_feedback IS NULL OR user_feedback = '')", (department_id,))
        no_action_questions = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(*) FROM questions WHERE department_id = ? AND user_feedback = 'end'", (department_id,))
        end_request_questions = c.fetchone()[0] or 0
        
        # Send enhanced SMS report
        sms_text = f"""گزارش عملکرد {department_name}

📊 آمار مالی:
💰 مجموع پاداش: {total_rewards:,} تومان
⚠️ مجموع جریمه: {total_penalties:,} تومان

📈 آمار سوالات:
❓ بدون پاسخ: {unanswered_questions}
✅ حل شده: {solved_questions}
⏳ در انتظار: {waiting_questions}
📝 بدون اقدام: {no_action_questions}
🚫 پایان درخواست: {end_request_questions}

موفق باشید!"""
        send_sms(manager_phone, sms_text)
        flash('گزارش با موفقیت ارسال شد', 'success')

    # گرفتن سوالات
    c.execute("""
        SELECT q.id, u.name, q.question_text, q.status, q.created_at, q.timer_hours,
               q.fixed_reward, q.waiting_deadline, q.waiting_count, q.penalty_multiplier, q.violation_status,
               q.paused_at, q.paused_reward, q.paused_timer_remaining
        FROM questions q
        JOIN users u ON q.user_id = u.id
        WHERE q.department_id = ?
        ORDER BY q.created_at DESC
    """, (department_id,))
    questions = c.fetchall()

    # Calculate total rewards and penalties for display
    c.execute("SELECT SUM(reward_amount) FROM questions WHERE department_id = ? AND reward_amount > 0", (department_id,))
    total_rewards = c.fetchone()[0] or 0
    
    c.execute("SELECT SUM(reward_amount) FROM questions WHERE department_id = ? AND reward_amount < 0", (department_id,))
    total_penalties = c.fetchone()[0] or 0

    # گرفتن مبلغ پایه از تنظیمات
    c.execute("SELECT base_reward_amount FROM admin_settings WHERE id=1")
    reward_row = c.fetchone()
    base_reward = reward_row[0] if reward_row else 200000

    conn.close()

    html = '''
        <!DOCTYPE html>
        <html lang="fa" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>داشبورد مدیر</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');
                
                body { 
                    direction: rtl; 
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    font-family: 'Vazirmatn', sans-serif;
                    min-height: 100vh;
                    padding: 20px 0;
                }
                
                .dashboard-header {
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 30px;
                    margin-bottom: 30px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                    text-align: center;
                }
                
                .dashboard-header h3 {
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    font-weight: 700;
                    font-size: 2rem;
                    margin: 0;
                }
                
                .stats-cards {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }
                
                .stat-card {
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    border-radius: 15px;
                    padding: 25px;
                    text-align: center;
                    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                    transition: transform 0.3s ease;
                }
                
                .stat-card:hover {
                    transform: translateY(-5px);
                }
                
                .stat-value {
                    font-size: 2.5rem;
                    font-weight: 700;
                    margin-bottom: 10px;
                }
                
                .stat-label {
                    font-size: 1.1rem;
                    color: #666;
                    margin-bottom: 15px;
                }
                
                .reward-card .stat-value {
                    color: #00b894;
                }
                
                .penalty-card .stat-value {
                    color: #e17055;
                }
                
                .report-btn {
                    background: linear-gradient(135deg, #fdcb6e 0%, #f39c12 100%);
                    border: none;
                    border-radius: 12px;
                    padding: 12px 25px;
                    color: white;
                    font-weight: 600;
                    transition: all 0.3s ease;
                    text-decoration: none;
                    display: inline-block;
                    margin-top: 15px;
                }
                
                .report-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(243, 156, 18, 0.4);
                    color: white;
                }
                
                .logout-btn {
                    background: linear-gradient(135deg, #e17055 0%, #d63031 100%);
                    border: none;
                    border-radius: 12px;
                    padding: 8px 16px;
                    color: white;
                    font-weight: 600;
                    text-decoration: none;
                    font-size: 0.9rem;
                }
                
                .questions-container {
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    overflow: hidden;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                }
                
                .table-responsive {
                    border-radius: 20px;
                    overflow: hidden;
                }
                
                .table {
                    margin: 0;
                    font-size: 0.9rem;
                }
                
                .table thead th {
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    color: white;
                    border: none;
                    padding: 20px 15px;
                    font-weight: 600;
                    font-size: 0.95rem;
                }
                
                .table tbody td {
                    padding: 20px 15px;
                    vertical-align: middle;
                    border-bottom: 1px solid #e2e8f0;
                }
                
                .table tbody tr:hover {
                    background-color: rgba(240, 147, 251, 0.05);
                }
                
                .question-cell {
                    max-width: 300px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }
                
                .status-badge {
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-size: 0.85rem;
                    font-weight: 500;
                }
                
                .status-pending {
                    background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
                    color: #e17055;
                }
                
                .status-answered {
                    background: linear-gradient(135deg, #55efc4 0%, #00b894 100%);
                    color: white;
                }
                
                .timer-display {
                    font-weight: 600;
                    font-family: 'Courier New', monospace;
                }
                
                .reward-positive {
                    color: #00b894;
                    font-weight: 600;
                }
                
                .reward-negative {
                    color: #e17055;
                    font-weight: 600;
                }
                
                .reward-frozen {
                    color: #0984e3;
                    font-weight: 600;
                }
                
                .reward-paused {
                    color: #f39c12;
                    font-weight: 600;
                    background: rgba(255, 193, 7, 0.1);
                    padding: 4px 8px;
                    border-radius: 8px;
                    border: 1px solid rgba(255, 193, 7, 0.3);
                }
                
                .answer-form {
                    background: rgba(240, 147, 251, 0.1);
                    border-radius: 12px;
                    padding: 15px;
                    margin: 0;
                }
                
                .answer-input {
                    border: 2px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 10px 12px;
                    font-size: 0.9rem;
                    margin-bottom: 10px;
                    transition: all 0.3s ease;
                }
                
                .answer-input:focus {
                    border-color: #f093fb;
                    box-shadow: 0 0 0 0.2rem rgba(240, 147, 251, 0.25);
                }
                
                .btn-answer {
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: 600;
                    font-size: 0.9rem;
                    color: white;
                    transition: all 0.3s ease;
                }
                
                .btn-answer:hover {
                    transform: translateY(-1px);
                    box-shadow: 0 4px 15px rgba(240, 147, 251, 0.4);
                    color: white;
                }
                
                .completed-icon {
                    font-size: 1.5rem;
                    color: #00b894;
                }
                
                @media (max-width: 768px) {
                    .container {
                        padding: 10px;
                    }
                    
                    .dashboard-header {
                        padding: 20px;
                    }
                    
                    .dashboard-header h3 {
                        font-size: 1.5rem;
                    }
                    
                    .table {
                        font-size: 0.8rem;
                    }
                    
                    .table thead th,
                    .table tbody td {
                        padding: 12px 8px;
                    }
                    
                    .question-cell {
                        max-width: 150px;
                    }
                    
                    .answer-form {
                        padding: 10px;
                    }
                }
                
                @media (max-width: 576px) {
                    .table thead th,
                    .table tbody td {
                        padding: 8px 5px;
                        font-size: 0.75rem;
                    }
                    
                    .question-cell {
                        max-width: 100px;
                    }
                    
                    .btn-answer {
                        padding: 8px 12px;
                        font-size: 0.8rem;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="dashboard-header">
                    <div class="d-flex justify-content-between align-items-center">
                        <h3><i class="bi bi-speedometer2 me-3"></i>داشبورد مدیر - {{ department_name }}</h3>
                        <a href="/manager/logout" class="logout-btn"><i class="bi bi-box-arrow-right me-2"></i>خروج</a>
                    </div>
                </div>
                
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }} alert-dismissible fade show" role="alert">
                                {{ message }}
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            </div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                <div class="stats-cards">
                    <div class="stat-card reward-card">
                        <div class="stat-value">{{ "{:,}".format(total_rewards) }}</div>
                        <div class="stat-label">مجموع پاداش‌ها (تومان)</div>
                        <i class="bi bi-gift" style="font-size: 2rem; color: #00b894;"></i>
                    </div>
                    <div class="stat-card penalty-card">
                        <div class="stat-value">{{ "{:,}".format(abs(total_penalties)) }}</div>
                        <div class="stat-label">مجموع جریمه‌ها (تومان)</div>
                        <i class="bi bi-exclamation-triangle" style="font-size: 2rem; color: #e17055;"></i>
                    </div>
                </div>
                
                <div class="text-center mb-4">
                    <form method="post" style="display: inline;">
                        <input type="hidden" name="send_report" value="1">
                        <button type="submit" class="report-btn">
                            <i class="bi bi-file-earmark-text me-2"></i>گزارش گیری
                        </button>
                    </form>
                </div>
                
                <div class="questions-container">
                    <div class="table-responsive">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>شناسه</th>
                                    <th>کاربر</th>
                                    <th>سوال</th>
                                    <th>زمان باقی‌مانده</th>
                                    <th>پاداش/جریمه</th>
                                    <th>وضعیت</th>
                                    <th>عملیات</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for q in questions %}
                                <tr>
                                    <td><strong>#{{ q[0] }}</strong></td>
                                    <td>{{ q[1] }}</td>
                                    <td>
                                        <div class="question-cell" title="{{ q[2] }}">{{ q[2] }}</div>
                                    </td>
                                    <td class="timer-display">
                                        {% if q[3] == 'pending' %}
                                            {% if q[7] %}
                                                <!-- In waiting period -->
                                                {% set deadline = datetime.fromisoformat(q[7]) %}
                                                {% set remaining = deadline - now %}
                                                {% set seconds_left = remaining.total_seconds()|int %}
                                                {% set fixed_reward = q[6] if q[6] else base_reward %}
                                                {% set penalty_multiplier = q[9] or 3 %}
                                                {% set timer_hours = q[5] %}
                                                <span id="timer-{{ q[0] }}" 
                                                      data-seconds="{{ seconds_left }}" 
                                                      data-fixed="{{ fixed_reward }}" 
                                                      data-base="{{ base_reward }}" 
                                                      data-multiplier="{{ penalty_multiplier }}"
                                                      data-timer-hours="{{ timer_hours }}"
                                                      data-waiting="true"
                                                      data-violation-status="{{ q[10] if q[10] else 'none' }}"
                                                      data-paused-reward="{{ q[12] if q[12] else 0 }}"></span>
                                            {% else %}
                                                <!-- Normal countdown -->
                                {% set created_at = q[4] %}
                                {% set timer_hours = q[5] %}
                                {% set deadline = (datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S.%f") + timedelta(hours=timer_hours)) %}
                                {% set remaining = deadline - now %}
                                {% set seconds_left = remaining.total_seconds()|int %}
                                {% set fixed_reward = q[6] if q[6] else base_reward %}
                                {% set penalty_multiplier = q[9] or 3 %}
                                <span id="timer-{{ q[0] }}" 
                                      data-seconds="{{ seconds_left }}" 
                                      data-fixed="{{ fixed_reward }}" 
                                      data-base="{{ base_reward }}" 
                                      data-multiplier="{{ penalty_multiplier }}"
                                      data-timer-hours="{{ timer_hours }}"
                                      data-waiting="false"
                                      data-violation-status="{{ q[10] if q[10] else 'none' }}"
                                      data-paused-reward="{{ q[12] if q[12] else 0 }}"></span>
                                            {% endif %}
                                        {% else %}
                                            <span class="text-muted">تمام شده</span>
                                        {% endif %}
                                    </td>
                                    <td><span id="reward-{{ q[0] }}"></span></td>
                                    <td>
                                        {% if q[3] == 'pending' %}
                                            <span class="status-badge status-pending">
                                                <i class="bi bi-clock me-1"></i>در انتظار پاسخ
                                            </span>
                                        {% elif q[3] == 'answered' %}
                                            <span class="status-badge status-answered">
                                                <i class="bi bi-check-circle me-1"></i>پاسخ داده شده
                                            </span>
                                        {% else %}
                                            <span class="text-muted">-</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if q[3] == 'pending' %}
                                            {% if q[10] == 'paused' %}
                                                <div class="text-center">
                                                    <span class="badge bg-warning text-dark mb-2">
                                                        <i class="bi bi-pause-circle me-1"></i>متوقف شده (گزارش تخلف)
                                                    </span>
                                                </div>
                                            {% else %}
                                                <form method="post" action="/answer" class="answer-form">
                                                    <input type="hidden" name="question_id" value="{{ q[0] }}">
                                                    <input type="text" name="answer_text" placeholder="پاسخ خود را بنویسید..." class="form-control answer-input" required>
                                                    <button type="submit" class="btn btn-answer w-100 mb-2">
                                                        <i class="bi bi-reply me-1"></i>ارسال پاسخ
                                                    </button>
                                                </form>
                                                <form method="post" action="/report_violation" class="mt-2">
                                                    <input type="hidden" name="question_id" value="{{ q[0] }}">
                                                    <div class="mb-2">
                                                        <textarea name="manager_notes" class="form-control" rows="2" 
                                                                placeholder="یادداشت مدیر (اختیاری): دلیل گزارش تخلف یا توضیحات اضافی..."
                                                                style="font-size: 0.9rem; border-radius: 8px;"></textarea>
                                                    </div>
                                                    <button type="submit" class="btn btn-outline-warning btn-sm w-100" onclick="return confirm('آیا از گزارش این سوال به عنوان تخلف مطمئن هستید؟')">
                                                        <i class="bi bi-exclamation-triangle me-1"></i>گزارش تخلف
                                                    </button>
                                                </form>
                                            {% endif %}
                                        {% else %}
                                            <i class="bi bi-check-circle-fill completed-icon"></i>
                                        {% endif %}
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <script>
                function startCountdownAndReward(id, seconds, fixedReward, baseReward, multiplier, timerHours, isWaiting, violationStatus, pausedReward) {
                    const timerEl = document.getElementById("timer-" + id);
                    const rewardEl = document.getElementById("reward-" + id);
                    if (!timerEl || !rewardEl) return;

                    // Check if question is paused due to violation
                    if (violationStatus === 'paused') {
                        timerEl.innerHTML = `<i class="bi bi-pause-circle-fill text-warning me-1"></i>متوقف شده`;
                        rewardEl.innerHTML = `<span class="reward-paused"><i class="bi bi-lock-fill me-1"></i>${pausedReward.toLocaleString()} تومان</span>`;
                        return; // Don't start countdown
                    }

                    const allowedSeconds = timerHours * 3600;
                    let currentSeconds = seconds;

                    function update() {
                        const absSeconds = Math.abs(currentSeconds);
                        const hrs = Math.floor(absSeconds / 3600);
                        const mins = Math.floor((absSeconds % 3600) / 60);
                        const secs = absSeconds % 60;

                        if (currentSeconds >= 0) {
                            // Time is positive
                            timerEl.innerHTML = `<i class="bi bi-clock me-1"></i>${hrs}:${mins.toString().padStart(2,'0')}:${secs.toString().padStart(2,'0')}`;
                            
                            if (isWaiting) {
                                // In waiting period - reward is frozen
                                rewardEl.innerHTML = `<span class="reward-frozen"><i class="bi bi-currency-dollar me-1"></i>${fixedReward.toLocaleString()} تومان</span>`;
                            } else {
                                // Normal countdown - calculate decreasing reward
                                const currentReward = Math.max(0, Math.floor(fixedReward * (currentSeconds / allowedSeconds)));
                                rewardEl.innerHTML = `<span class="reward-positive"><i class="bi bi-currency-dollar me-1"></i>${currentReward.toLocaleString()} تومان</span>`;
                            }
                        } else {
                            // Time is negative (penalty)
                            timerEl.innerHTML = `<i class="bi bi-exclamation-triangle text-danger me-1"></i>-${hrs}:${mins.toString().padStart(2,'0')}:${secs.toString().padStart(2,'0')}`;
                            
                            const overtime = Math.abs(currentSeconds);
                            const penaltyPerSecond = fixedReward / allowedSeconds;
                            const penalty = Math.floor(overtime * penaltyPerSecond * multiplier);
                            
                            rewardEl.innerHTML = `<span class="reward-negative"><i class="bi bi-exclamation-circle me-1"></i>-${penalty.toLocaleString()} تومان</span>`;
                        }

                        currentSeconds--;
                        setTimeout(update, 1000);
                    }

                    update();
                }

                window.onload = function() {
                    const timers = document.querySelectorAll("[id^='timer-']");
                    timers.forEach(function(timer) {
                        const id = timer.id.replace("timer-", "");
                        const seconds = parseInt(timer.getAttribute("data-seconds"));
                        const fixedReward = parseInt(timer.getAttribute("data-fixed")) || 0;
                        const baseReward = parseInt(timer.getAttribute("data-base")) || 0;
                        const multiplier = parseInt(timer.getAttribute("data-multiplier")) || 3;
                        const timerHours = parseFloat(timer.getAttribute("data-timer-hours")) || 1;
                        const isWaiting = timer.getAttribute("data-waiting") === "true";
                        const violationStatus = timer.getAttribute("data-violation-status") || "none";
                        const pausedReward = parseInt(timer.getAttribute("data-paused-reward")) || 0;

                        startCountdownAndReward(id, seconds, fixedReward, baseReward, multiplier, timerHours, isWaiting, violationStatus, pausedReward);
                    });
                }
            </script>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        '''

    from datetime import datetime, timedelta
    now = datetime.now()

    return render_template_string(html, questions=questions, now=now, datetime=datetime, timedelta=timedelta,  
                                  total_rewards=total_rewards, total_penalties=total_penalties, 
                                  department_name=department_name, base_reward=base_reward, abs=abs)

    # فرم ورود مدیر
    html_form = '''
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ورود مدیر</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');
            
            body { 
                direction: rtl; 
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                font-family: 'Vazirmatn', sans-serif;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            
            .login-container {
                max-width: 450px;
                width: 100%;
            }
            
            .login-card { 
                border: none; 
                border-radius: 20px; 
                box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                overflow: hidden;
            }
            
            .login-header {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                color: white;
                padding: 40px 30px;
                text-align: center;
                position: relative;
            }
            
            .login-header::before {
                content: '';
                position: absolute;
                top: -50%;
                right: -50%;
                width: 200%;
                height: 200%;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="2" fill="rgba(255,255,255,0.1)"/></svg>') repeat;
                animation: float 20s infinite linear;
            }
            
            @keyframes float {
                0% { transform: translate(-50%, -50%) rotate(0deg); }
                100% { transform: translate(-50%, -50%) rotate(360deg); }
            }
            
            .login-header h3 {
                margin: 0;
                font-weight: 600;
                font-size: 1.8rem;
                position: relative;
                z-index: 2;
            }
            
            .login-icon {
                font-size: 3rem;
                margin-bottom: 15px;
                position: relative;
                z-index: 2;
            }
            
            .login-body {
                padding: 40px 30px;
            }
            
            .form-label {
                font-weight: 500;
                color: #4a5568;
                margin-bottom: 8px;
                font-size: 0.95rem;
            }
            
            .form-control {
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                padding: 15px 20px;
                font-size: 1rem;
                transition: all 0.3s ease;
                background: rgba(255, 255, 255, 0.9);
            }
            
            .form-control:focus {
                border-color: #f093fb;
                box-shadow: 0 0 0 0.2rem rgba(240, 147, 251, 0.25);
                background: white;
            }
            
            .input-group {
                position: relative;
                margin-bottom: 25px;
            }
            
            .input-icon {
                position: absolute;
                right: 20px;
                top: 50%;
                transform: translateY(-50%);
                color: #a0aec0;
                z-index: 3;
                font-size: 1.1rem;
            }
            
            .form-control.with-icon {
                padding-right: 55px;
            }
            
            .btn-login {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                border: none;
                border-radius: 12px;
                padding: 15px 30px;
                font-weight: 600;
                font-size: 1.1rem;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(240, 147, 251, 0.4);
                color: white;
                width: 100%;
            }
            
            .btn-login:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(240, 147, 251, 0.6);
                background: linear-gradient(135deg, #e084f0 0%, #eb4a64 100%);
                color: white;
            }
            
            @media (max-width: 768px) {
                .login-header {
                    padding: 30px 20px;
                }
                
                .login-body {
                    padding: 30px 20px;
                }
                
                .login-header h3 {
                    font-size: 1.5rem;
                }
                
                .login-icon {
                    font-size: 2.5rem;
                }
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="login-card">
                <div class="login-header">
                    <div class="login-icon">
                        <i class="bi bi-person-badge"></i>
                    </div>
                    <h3>ورود مدیر</h3>
                </div>
                <div class="login-body">
                    <form method="post">
                        <div class="input-group">
                            <label class="form-label">شماره موبایل مدیر</label>
                            <div class="position-relative">
                                <i class="bi bi-phone-fill input-icon"></i>
                                <input type="tel" name="manager_phone" class="form-control with-icon" placeholder="09xxxxxxxxx" pattern="[0-9]{11}" required>
                            </div>
                        </div>
                        
                        <button type="submit" class="btn btn-login">
                            <i class="bi bi-box-arrow-in-right me-2"></i>ورود به داشبورد
                        </button>
                    </form>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''
    return html_form

@app.route('/answer', methods=['POST'])
def answer_question():
    question_id = request.form['question_id']
    answer_text = request.form['answer_text']

    conn = sqlite3.connect('system.db')
    c = conn.cursor()

    # گرفتن شماره کاربر
    c.execute("SELECT u.phone FROM questions q JOIN users u ON q.user_id = u.id WHERE q.id = ?", (question_id,))
    user_row = c.fetchone()
    user_phone = user_row[0] if user_row else ''

    answered_time = datetime.now()

    # Check if there's an active violation report for this question
    c.execute("SELECT id FROM violation_reports WHERE question_id = ? AND status = 'pending'", (question_id,))
    violation_report = c.fetchone()

    if violation_report:
        # If there's a violation report, store this as an additional answer
        c.execute("""INSERT INTO violation_report_answers 
                     (violation_report_id, answer_text, answered_at, is_primary_answer)
                     VALUES (?, ?, ?, 0)""", 
                  (violation_report[0], answer_text, answered_time))
        flash('پاسخ شما ثبت شد و به گزارش تخلف اضافه شد', 'info')
    else:
        # Normal answer processing
        # ثبت پاسخ و متن پاسخ در دیتابیس
        c.execute("UPDATE questions SET status = ?, answered_at = ?, answer_text = ? WHERE id = ?", ('answered', answered_time, answer_text, question_id))

        # ساخت لینک فیدبک
        feedback_link = f"http://qq.manida.co/feedback/{question_id}"
        sms_text = f"مدیر به سوال شما پاسخ داد: {answer_text}. لطفاً وضعیت را در این لینک مشخص کنید: {feedback_link}"

        print(f"📲 SMS به کاربر ({user_phone}): {sms_text}")
        send_sms(user_phone, sms_text)

    conn.commit()
    conn.close()

    if violation_report:
        return redirect(url_for('manager_dashboard'))

    return '''
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>پاسخ ثبت شد</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');
            body { font-family: 'Vazirmatn', sans-serif; direction: rtl; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
            .success-card { background: white; border-radius: 20px; padding: 40px; text-align: center; box-shadow: 0 15px 35px rgba(0,0,0,0.1); max-width: 400px; }
            .success-icon { font-size: 4rem; color: #f093fb; margin-bottom: 20px; }
            h3 { color: #2d3436; margin-bottom: 20px; }
            .btn-return { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; border: none; border-radius: 12px; padding: 12px 25px; text-decoration: none; font-weight: 600; transition: all 0.3s ease; }
            .btn-return:hover { transform: translateY(-2px); color: white; }
        </style>
    </head>
    <body>
        <div class="success-card">
            <div class="success-icon"><i class="bi bi-reply-fill"></i></div>
            <h3>پاسخ با موفقیت ثبت شد!</h3>
            <p>پاسخ شما برای کاربر ارسال شده و پیامک اطلاع‌رسانی فرستاده شد.</p>
            <a href="/manager" class="btn btn-return"><i class="bi bi-speedometer2 me-2"></i>بازگشت به داشبورد</a>
        </div>
    </body>
    </html>
    '''

@app.route('/report_violation', methods=['POST'])
@manager_required
def report_violation():
    question_id = request.form['question_id']
    manager_notes = request.form.get('manager_notes', '').strip()
    manager_phone = session.get('manager_phone')
    
    conn = sqlite3.connect('system.db')
    c = conn.cursor()
    
    # Check if question is already reported
    c.execute("SELECT id FROM violation_reports WHERE question_id = ? AND status = 'pending'", (question_id,))
    existing_report = c.fetchone()
    
    if existing_report:
        flash('این سوال قبلاً گزارش شده است', 'error')
        conn.close()
        return redirect(url_for('manager_dashboard'))
    
    # Get current question details for pausing
    c.execute("""SELECT created_at, timer_hours, fixed_reward, waiting_deadline, 
                        answer_text, answered_at, user_id, department_id
                 FROM questions WHERE id = ?""", (question_id,))
    question_data = c.fetchone()
    
    if not question_data:
        flash('سوال پیدا نشد', 'error')
        conn.close()
        return redirect(url_for('manager_dashboard'))
    
    created_at_str, timer_hours, fixed_reward, waiting_deadline, answer_text, answered_at, user_id, department_id = question_data
    
    # Calculate current reward and remaining time to pause them
    current_time = datetime.now()
    current_reward = calculate_current_reward(created_at_str, timer_hours, fixed_reward, waiting_deadline, 3)
    
    # Calculate remaining time
    if waiting_deadline:
        deadline = datetime.fromisoformat(waiting_deadline)
        remaining_seconds = max(0, (deadline - current_time).total_seconds())
    else:
        created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S.%f")
        deadline = created_at + timedelta(hours=timer_hours)
        remaining_seconds = max(0, (deadline - current_time).total_seconds())
    
    # Update question to paused state
    c.execute("""UPDATE questions SET 
                 violation_status = 'paused',
                 paused_at = ?,
                 paused_timer_remaining = ?,
                 paused_reward = ?
                 WHERE id = ?""", 
              (current_time, int(remaining_seconds), current_reward, question_id))
    
    # Create violation report
    c.execute("""INSERT INTO violation_reports 
                 (question_id, reported_by_manager_phone, reported_at, status, manager_notes)
                 VALUES (?, ?, ?, 'pending', ?)""", 
              (question_id, manager_phone, current_time, manager_notes))
    violation_report_id = c.lastrowid
    
    # Store the initial answer in violation_report_answers if exists
    if answer_text and answered_at:
        c.execute("""INSERT INTO violation_report_answers 
                     (violation_report_id, answer_text, answered_at, is_primary_answer)
                     VALUES (?, ?, ?, 1)""", 
                  (violation_report_id, answer_text, answered_at))
    
    conn.commit()
    conn.close()
    
    flash('گزارش تخلف با موفقیت ثبت شد. سوال متوقف شده و در انتظار بررسی ادمین است.', 'success')
    return redirect(url_for('manager_dashboard'))

@app.route('/feedback/<int:question_id>', methods=['GET', 'POST'])
def feedback(question_id):
    conn = sqlite3.connect('system.db')
    c = conn.cursor()

    if request.method == 'POST':
        action = request.form['action']

        c.execute("SELECT created_at, answered_at, timer_hours, answer_text, waiting_count, penalty_multiplier, fixed_reward, waiting_deadline FROM questions WHERE id = ?", (question_id,))
        row = c.fetchone()
        if not row or not row[1]:
            conn.close()
            return '''
            <!DOCTYPE html>
            <html lang="fa" dir="rtl">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>خطا</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');
                    body { font-family: 'Vazirmatn', sans-serif; direction: rtl; background: linear-gradient(135deg, #e17055 0%, #d63031 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
                    .error-card { background: white; border-radius: 20px; padding: 40px; text-align: center; box-shadow: 0 15px 35px rgba(0,0,0,0.1); max-width: 400px; }
                    .error-icon { font-size: 4rem; color: #e17055; margin-bottom: 20px; }
                    h3 { color: #2d3436; margin-bottom: 20px; }
                    .btn-return { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 12px; padding: 12px 25px; text-decoration: none; font-weight: 600; transition: all 0.3s ease; }
                    .btn-return:hover { transform: translateY(-2px); color: white; }
                </style>
            </head>
            <body>
                <div class="error-card">
                    <div class="error-icon"><i class="bi bi-exclamation-triangle-fill"></i></div>
                    <h3>خطا در بازخورد</h3>
                    <p>سوال یا زمان پاسخ پیدا نشد! لطفاً دوباره تلاش کنید.</p>
                    <a href="/form" class="btn btn-return"><i class="bi bi-house me-2"></i>صفحه اصلی</a>
                </div>
            </body>
            </html>
            '''

        created_at = row[0]
        answered_at = row[1]
        timer_hours = row[2]
        answer_text = row[3] if row[3] else "پاسخ داده شد"
        waiting_count = row[4] or 0
        penalty_multiplier = row[5] or 3
        fixed_reward = row[6]
        waiting_deadline = row[7]

        # گرفتن مبلغ پایه
        c.execute("SELECT base_reward_amount FROM admin_settings WHERE id=1")
        settings = c.fetchone()
        base_reward = settings[0] if settings else 200000

        if action == 'solved':
            current_reward = calculate_current_reward(created_at, timer_hours, fixed_reward, waiting_deadline, penalty_multiplier)
            c.execute("UPDATE questions SET reward_amount = ?, user_feedback = 'solved', status = 'answered' WHERE id = ?", (current_reward, question_id))
            conn.commit()

            # ثبت در شیت
            conn2 = sqlite3.connect('system.db')
            c2 = conn2.cursor()
            c2.execute("SELECT u.name, d.name, q.question_text, q.answer_text, q.answered_at, q.reward_amount FROM questions q JOIN users u ON q.user_id = u.id JOIN departments d ON q.department_id = d.id WHERE q.id = ?", (question_id,))
            info = c2.fetchone()
            conn2.close()

            if info:
                append_to_sheet([info[0], info[1], info[2], info[3], str(info[4]), info[5]])

            message = "✅ مشکل حل شد! ممنون از ثبت بازخورد شما."

        elif action == 'waiting':
            waiting_count += 1
            if waiting_count == 1:
                new_hours = 72
            else:
                new_hours = 72 / (2 ** (waiting_count - 1))
            
            new_deadline = datetime.now() + timedelta(hours=new_hours)
            new_penalty_multiplier = penalty_multiplier + 1

            if waiting_deadline and datetime.now() <= datetime.fromisoformat(waiting_deadline):
                next_fixed_reward = fixed_reward
            else:
                current_reward = calculate_current_reward(created_at, timer_hours, fixed_reward, waiting_deadline, penalty_multiplier)
                next_fixed_reward = max(current_reward, 0)

            c.execute("UPDATE questions SET fixed_reward = ?, waiting_deadline = ?, waiting_count = ?, penalty_multiplier = ?, status = 'pending', user_feedback = 'waiting' WHERE id = ?",
                      (next_fixed_reward, new_deadline.isoformat(), waiting_count, new_penalty_multiplier, question_id))
            message = "⏳ زمان پاسخ تمدید شد، مبلغ تا پایان زمان ثابت است، سپس شروع به کاهش می‌کند."

        elif action == 'end':
            c.execute("UPDATE questions SET reward_amount = 0, user_feedback = 'end', status = 'answered' WHERE id = ?", (question_id,))
            message = "❌ درخواست بدون پاداش یا جریمه بسته شد."

        conn.commit()
        conn.close()
        return f'''
        <!DOCTYPE html>
        <html lang="fa" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>بازخورد ثبت شد</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');
                body {{ font-family: 'Vazirmatn', sans-serif; direction: rtl; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }}
                .message-card {{ background: white; border-radius: 20px; padding: 40px; text-align: center; box-shadow: 0 15px 35px rgba(0,0,0,0.1); max-width: 500px; }}
                .message-icon {{ font-size: 4rem; color: #667eea; margin-bottom: 20px; }}
                h3 {{ color: #2d3436; margin-bottom: 20px; }}
                .btn-return {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 12px; padding: 12px 25px; text-decoration: none; font-weight: 600; transition: all 0.3s ease; }}
                .btn-return:hover {{ transform: translateY(-2px); color: white; }}
            </style>
        </head>
        <body>
            <div class="message-card">
                <div class="message-icon"><i class="bi bi-check-circle-fill"></i></div>
                <h3>بازخورد شما ثبت شد</h3>
                <p>{message}</p>
                <a href="/form" class="btn btn-return"><i class="bi bi-house me-2"></i>ارسال سؤال جدید</a>
            </div>
        </body>
        </html>
        '''

    conn.close()
    html = '''
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>بازخورد کاربر</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');
            
            body { 
                direction: rtl; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                font-family: 'Vazirmatn', sans-serif;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            
            .feedback-container {
                max-width: 500px;
                width: 100%;
            }
            
            .feedback-card { 
                border: none; 
                border-radius: 20px; 
                box-shadow: 0 15px 35px rgba(0,0,0,0.15);
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                overflow: hidden;
            }
            
            .feedback-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px 30px;
                text-align: center;
                position: relative;
            }
            
            .feedback-header::before {
                content: '';
                position: absolute;
                top: -50%;
                right: -50%;
                width: 200%;
                height: 200%;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="2" fill="rgba(255,255,255,0.1)"/></svg>') repeat;
                animation: float 20s infinite linear;
            }
            
            @keyframes float {
                0% { transform: translate(-50%, -50%) rotate(0deg); }
                100% { transform: translate(-50%, -50%) rotate(360deg); }
            }
            
            .feedback-icon {
                font-size: 3rem;
                margin-bottom: 15px;
                position: relative;
                z-index: 2;
            }
            
            .feedback-header h4 {
                margin: 0;
                font-weight: 600;
                font-size: 1.6rem;
                position: relative;
                z-index: 2;
                line-height: 1.4;
            }
            
            .feedback-body {
                padding: 40px 30px;
            }
            
            .feedback-btn {
                border: none;
                border-radius: 15px;
                padding: 18px 25px;
                font-weight: 600;
                font-size: 1.1rem;
                margin-bottom: 15px;
                transition: all 0.3s ease;
                width: 100%;
                position: relative;
                overflow: hidden;
            }
            
            .feedback-btn::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                transition: left 0.5s;
            }
            
            .feedback-btn:hover::before {
                left: 100%;
            }
            
            .btn-solved {
                background: linear-gradient(135deg, #00b894 0%, #55efc4 100%);
                color: white;
                box-shadow: 0 4px 15px rgba(0, 184, 148, 0.3);
            }
            
            .btn-solved:hover {
                transform: translateY(-3px);
                box-shadow: 0 6px 20px rgba(0, 184, 148, 0.4);
                background: linear-gradient(135deg, #00a085 0%, #4de6b8 100%);
                color: white;
            }
            
            .btn-waiting {
                background: linear-gradient(135deg, #fdcb6e 0%, #f39c12 100%);
                color: white;
                box-shadow: 0 4px 15px rgba(253, 203, 110, 0.3);
            }
            
            .btn-waiting:hover {
                transform: translateY(-3px);
                box-shadow: 0 6px 20px rgba(253, 203, 110, 0.4);
                background: linear-gradient(135deg, #fcbb47 0%, #e67e22 100%);
                color: white;
            }
            
            .btn-end {
                background: linear-gradient(135deg, #e17055 0%, #d63031 100%);
                color: white;
                box-shadow: 0 4px 15px rgba(225, 112, 85, 0.3);
            }
            
            .btn-end:hover {
                transform: translateY(-3px);
                box-shadow: 0 6px 20px rgba(225, 112, 85, 0.4);
                background: linear-gradient(135deg, #dd5a3a 0%, #c0392b 100%);
                color: white;
            }
            
            .btn-icon {
                margin-left: 10px;
                font-size: 1.2rem;
            }
            
            @media (max-width: 768px) {
                .feedback-header {
                    padding: 30px 20px;
                }
                
                .feedback-body {
                    padding: 30px 20px;
                }
                
                .feedback-header h4 {
                    font-size: 1.4rem;
                }
                
                .feedback-icon {
                    font-size: 2.5rem;
                }
                
                .feedback-btn {
                    padding: 15px 20px;
                    font-size: 1rem;
                }
            }
        </style>
    </head>
    <body>
        <div class="feedback-container">
            <div class="feedback-card">
                <div class="feedback-header">
                    <div class="feedback-icon">
                        <i class="bi bi-emoji-smile"></i>
                    </div>
                    <h4>لطفاً وضعیت پاسخ را مشخص کنید</h4>
                </div>
                <div class="feedback-body">
                    <form method="post">
                        <button type="submit" name="action" value="solved" class="feedback-btn btn-solved">
                            <i class="bi bi-check-circle-fill btn-icon"></i>مشکل حل شد
                        </button>
                        
                        <button type="submit" name="action" value="waiting" class="feedback-btn btn-waiting">
                            <i class="bi bi-hourglass-split btn-icon"></i>در انتظار حل مشکل
                        </button>
                        
                        <button type="submit" name="action" value="end" class="feedback-btn btn-end">
                            <i class="bi bi-x-circle-fill btn-icon"></i>پایان درخواست
                        </button>
                    </form>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''
    return html

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('system.db')
        c = conn.cursor()
        c.execute("SELECT id FROM admin_users WHERE username = ? AND password = ?", (username, password))
        admin = c.fetchone()
        conn.close()
        
        if admin:
            session['admin_logged_in'] = True
            session['admin_id'] = admin[0]
            return redirect(url_for('admin_panel'))
        else:
            flash('نام کاربری یا رمز عبور اشتباه است', 'error')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ورود ادمین</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');
            body { font-family: 'Vazirmatn', sans-serif; direction: rtl; background: linear-gradient(135deg, #2d3436 0%, #636e72 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
            .login-card { background: white; border-radius: 20px; padding: 40px; max-width: 400px; width: 100%; box-shadow: 0 15px 35px rgba(0,0,0,0.2); }
            .login-header { text-align: center; margin-bottom: 30px; }
            .login-header h3 { color: #2d3436; font-weight: 700; }
            .form-control { border-radius: 12px; border: 2px solid #e2e8f0; padding: 12px 16px; }
            .btn-login { background: linear-gradient(135deg, #2d3436 0%, #636e72 100%); border: none; border-radius: 12px; padding: 12px 25px; font-weight: 600; }
            .alert { border-radius: 12px; }
        </style>
    </head>
    <body>
        <div class="login-card">
            <div class="login-header">
                <i class="bi bi-shield-lock-fill" style="font-size: 3rem; color: #2d3436;"></i>
                <h3>ورود ادمین</h3>
            </div>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-danger">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            <form method="post">
                <div class="mb-3">
                    <label class="form-label">نام کاربری</label>
                    <input type="text" name="username" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">رمز عبور</label>
                    <input type="password" name="password" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-login w-100 text-white">ورود</button>
            </form>
        </div>
    </body>
    </html>
    ''')

@app.route('/manager/login', methods=['GET', 'POST'])
def manager_login():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']
        
        conn = sqlite3.connect('system.db')
        c = conn.cursor()
        c.execute("SELECT id, name FROM departments WHERE manager_phone = ? AND password = ? AND active = 1", (phone, password))
        department = c.fetchone()
        conn.close()
        
        if department:
            session['manager_logged_in'] = True
            session['manager_phone'] = phone
            session['department_id'] = department[0]
            session['department_name'] = department[1]
            return redirect(url_for('manager_dashboard'))
        else:
            flash('شماره تلفن یا رمز عبور اشتباه است', 'error')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ورود مدیر</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');
            body { font-family: 'Vazirmatn', sans-serif; direction: rtl; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
            .login-card { background: white; border-radius: 20px; padding: 40px; max-width: 400px; width: 100%; box-shadow: 0 15px 35px rgba(0,0,0,0.2); }
            .login-header { text-align: center; margin-bottom: 30px; }
            .login-header h3 { color: #f5576c; font-weight: 700; }
            .form-control { border-radius: 12px; border: 2px solid #e2e8f0; padding: 12px 16px; }
            .btn-login { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border: none; border-radius: 12px; padding: 12px 25px; font-weight: 600; }
            .alert { border-radius: 12px; }
        </style>
    </head>
    <body>
        <div class="login-card">
            <div class="login-header">
                <i class="bi bi-person-badge-fill" style="font-size: 3rem; color: #f5576c;"></i>
                <h3>ورود مدیر</h3>
            </div>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-danger">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            <form method="post">
                <div class="mb-3">
                    <label class="form-label">شماره تلفن</label>
                    <input type="tel" name="phone" class="form-control" placeholder="09xxxxxxxxx" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">رمز عبور</label>
                    <input type="password" name="password" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-login w-100 text-white">ورود</button>
            </form>
        </div>
    </body>
    </html>
    ''')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/manager/logout')
def manager_logout():
    session.clear()
    return redirect(url_for('manager_login'))

@app.route('/violation-admin/login', methods=['GET', 'POST'])
def violation_admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('system.db')
        c = conn.cursor()
        c.execute("SELECT id, username FROM violation_admins WHERE username = ? AND password = ? AND active = 1", (username, password))
        violation_admin = c.fetchone()
        conn.close()
        
        if violation_admin:
            session['violation_admin_logged_in'] = True
            session['violation_admin_id'] = violation_admin[0]
            session['violation_admin_username'] = violation_admin[1]
            return redirect(url_for('violation_admin_dashboard'))
        else:
            flash('نام کاربری یا رمز عبور اشتباه است', 'error')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ورود ادمین تخلفات</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');
            body { font-family: 'Vazirmatn', sans-serif; direction: rtl; background: linear-gradient(135deg, #e17055 0%, #d63031 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
            .login-card { background: white; border-radius: 20px; padding: 40px; max-width: 400px; width: 100%; box-shadow: 0 15px 35px rgba(0,0,0,0.2); }
            .login-header { text-align: center; margin-bottom: 30px; }
            .login-header h3 { color: #d63031; font-weight: 700; }
            .form-control { border-radius: 12px; border: 2px solid #e2e8f0; padding: 12px 16px; }
            .btn-login { background: linear-gradient(135deg, #e17055 0%, #d63031 100%); border: none; border-radius: 12px; padding: 12px 25px; font-weight: 600; }
            .alert { border-radius: 12px; }
            .btn-back { background: linear-gradient(135deg, #636e72 0%, #2d3436 100%); color: white; text-decoration: none; border-radius: 12px; padding: 8px 16px; font-weight: 500; }
            .btn-back:hover { color: white; }
        </style>
    </head>
    <body>
        <div class="login-card">
            <div class="login-header">
                <i class="bi bi-exclamation-triangle-fill" style="font-size: 3rem; color: #d63031;"></i>
                <h3>ورود ادمین تخلفات</h3>
            </div>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-danger">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            <form method="post">
                <div class="mb-3">
                    <label class="form-label">نام کاربری</label>
                    <input type="text" name="username" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">رمز عبور</label>
                    <input type="password" name="password" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-login w-100 text-white mb-3">ورود</button>
                <div class="text-center">
                    <a href="/" class="btn-back">
                        <i class="bi bi-arrow-right me-2"></i>بازگشت به صفحه اصلی
                    </a>
                </div>
            </form>
        </div>
    </body>
    </html>
    ''')

@app.route('/violation-admin/logout')
def violation_admin_logout():
    session.clear()
    return redirect(url_for('violation_admin_login'))

@app.route('/violation-admin/dashboard')
@violation_admin_required
def violation_admin_dashboard():
    violation_admin_username = session.get('violation_admin_username')
    violation_admin_id = session.get('violation_admin_id')
    
    conn = sqlite3.connect('system.db')
    c = conn.cursor()
    
    # Get all violation reports with question details
    c.execute("""
        SELECT vr.id, vr.question_id, vr.reported_by_manager_phone, vr.reported_at, 
               vr.status, vr.admin_action, vr.admin_action_at,
               q.question_text, u.name, u.phone, d.name
        FROM violation_reports vr
        JOIN questions q ON vr.question_id = q.id
        JOIN users u ON q.user_id = u.id
        JOIN departments d ON q.department_id = d.id
        ORDER BY vr.reported_at DESC
    """)
    violation_reports = c.fetchall()
    
    # Get statistics for this violation admin
    c.execute("SELECT COUNT(*) FROM violation_reports WHERE status = 'pending'")
    pending_reports = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM violation_reports WHERE status = 'resolved' AND handled_by_violation_admin = ?", (violation_admin_id,))
    resolved_by_me = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM violation_reports WHERE status = 'resolved'")
    total_resolved = c.fetchone()[0]
    
    conn.close()
    
    html = '''
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>داشبورد ادمین تخلفات</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');
            
            body { 
                direction: rtl; 
                background: linear-gradient(135deg, #e17055 0%, #d63031 100%);
                font-family: 'Vazirmatn', sans-serif;
                min-height: 100vh;
                padding: 20px 0;
            }
            
            .dashboard-header {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 30px;
                margin-bottom: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            
            .dashboard-header h3 {
                background: linear-gradient(135deg, #e17055 0%, #d63031 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                font-weight: 700;
                font-size: 2.2rem;
                margin: 0;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .stat-card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 25px;
                text-align: center;
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
            }
            
            .stat-card:hover {
                transform: translateY(-5px);
            }
            
            .stat-value {
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 10px;
            }
            
            .stat-label {
                font-size: 1rem;
                color: #666;
                margin-bottom: 15px;
            }
            
            .pending-card .stat-value { color: #f39c12; }
            .resolved-card .stat-value { color: #00b894; }
            .total-card .stat-value { color: #6c5ce7; }
            
            .violation-card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border: none;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                margin-bottom: 30px;
                overflow: hidden;
            }
            
            .violation-header {
                background: linear-gradient(135deg, #e17055 0%, #d63031 100%);
                color: white;
                padding: 20px 25px;
                margin: 0;
                font-weight: 600;
                font-size: 1.2rem;
            }
            
            .table {
                margin: 0;
                font-size: 0.9rem;
            }
            
            .table thead th {
                background: linear-gradient(135deg, #e17055 0%, #d63031 100%);
                color: white;
                border: none;
                padding: 15px 12px;
                font-weight: 600;
            }
            
            .table tbody td {
                padding: 15px 12px;
                vertical-align: middle;
                border-bottom: 1px solid #e2e8f0;
            }
            
            .table tbody tr:hover {
                background-color: rgba(225, 112, 85, 0.05);
            }
            
            .status-pending {
                background: linear-gradient(135deg, #fdcb6e 0%, #f39c12 100%);
                color: white;
                padding: 6px 12px;
                border-radius: 15px;
                font-size: 0.85rem;
                font-weight: 500;
            }
            
            .status-resolved {
                background: linear-gradient(135deg, #00b894 0%, #55efc4 100%);
                color: white;
                padding: 6px 12px;
                border-radius: 15px;
                font-size: 0.85rem;
                font-weight: 500;
            }
            
            .btn-view {
                background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);
                border: none;
                border-radius: 10px;
                padding: 8px 16px;
                color: white;
                font-weight: 500;
                font-size: 0.9rem;
                transition: all 0.3s ease;
                text-decoration: none;
            }
            
            .btn-view:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(108, 92, 231, 0.4);
                color: white;
            }
            
            .logout-btn {
                background: linear-gradient(135deg, #636e72 0%, #2d3436 100%);
                border: none;
                border-radius: 12px;
                padding: 8px 16px;
                color: white;
                font-weight: 600;
                text-decoration: none;
                font-size: 0.9rem;
            }
            
            .logout-btn:hover {
                color: white;
                transform: translateY(-1px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="dashboard-header">
                <div class="d-flex justify-content-between align-items-center">
                    <h3><i class="bi bi-exclamation-triangle me-3"></i>داشبورد ادمین تخلفات</h3>
                    <div>
                        <span class="badge bg-secondary me-3">{{ violation_admin_username }}</span>
                        <a href="/violation-admin/logout" class="logout-btn">
                            <i class="bi bi-box-arrow-right me-2"></i>خروج
                        </a>
                    </div>
                </div>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }} alert-dismissible fade show" role="alert">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <div class="stats-grid">
                <div class="stat-card pending-card">
                    <div class="stat-value">{{ pending_reports }}</div>
                    <div class="stat-label">گزارش‌های در انتظار</div>
                    <i class="bi bi-hourglass-split" style="font-size: 2rem; color: #f39c12;"></i>
                </div>
                <div class="stat-card resolved-card">
                    <div class="stat-value">{{ resolved_by_me }}</div>
                    <div class="stat-label">حل شده توسط شما</div>
                    <i class="bi bi-check-circle" style="font-size: 2rem; color: #00b894;"></i>
                </div>
                <div class="stat-card total-card">
                    <div class="stat-value">{{ total_resolved }}</div>
                    <div class="stat-label">کل حل شده‌ها</div>
                    <i class="bi bi-list-check" style="font-size: 2rem; color: #6c5ce7;"></i>
                </div>
            </div>
            
            <div class="violation-card">
                <h5 class="violation-header">
                    <i class="bi bi-list-check me-2"></i>لیست گزارش‌های تخلف
                </h5>
                <div class="table-responsive">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>شناسه</th>
                                <th>سوال</th>
                                <th>کاربر</th>
                                <th>دپارتمان</th>
                                <th>گزارش‌دهنده</th>
                                <th>تاریخ گزارش</th>
                                <th>وضعیت</th>
                                <th>اقدام انجام شده</th>
                                <th>عملیات</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for vr in violation_reports %}
                            <tr>
                                <td><strong>#{{ vr[1] }}</strong></td>
                                <td>
                                    <div style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="{{ vr[7] }}">
                                        {{ vr[7] }}
                                    </div>
                                </td>
                                <td>
                                    <div><strong>{{ vr[8] }}</strong></div>
                                    <small class="text-muted">{{ vr[9] }}</small>
                                </td>
                                <td>{{ vr[10] }}</td>
                                <td>{{ vr[2] }}</td>
                                <td style="font-size: 0.8rem;">{{ vr[3] }}</td>
                                <td>
                                    {% if vr[4] == 'pending' %}
                                        <span class="status-pending">در انتظار بررسی</span>
                                    {% else %}
                                        <span class="status-resolved">بررسی شده</span>
                                    {% endif %}
                                </td>
                                <td>
                                    {% if vr[5] %}
                                        <span class="badge bg-info">{{ vr[5] }}</span>
                                        <br><small class="text-muted">{{ vr[6] }}</small>
                                    {% else %}
                                        <span class="text-muted">-</span>
                                    {% endif %}
                                </td>
                                <td>
                                    <a href="/violation-admin/violation/{{ vr[0] }}" class="btn-view">
                                        <i class="bi bi-eye me-1"></i>مشاهده جزئیات
                                    </a>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''
    
    return render_template_string(html, 
                                  violation_reports=violation_reports,
                                  violation_admin_username=violation_admin_username,
                                  pending_reports=pending_reports,
                                  resolved_by_me=resolved_by_me,
                                  total_resolved=total_resolved)

@app.route('/violation-admin/violation/<int:violation_id>', methods=['GET', 'POST'])
@violation_admin_required
def violation_admin_detail(violation_id):
    violation_admin_id = session.get('violation_admin_id')
    
    conn = sqlite3.connect('system.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        action = request.form['action']
        admin_notes = request.form.get('admin_notes', '').strip()
        current_time = datetime.now()
        
        # Get violation report details
        c.execute("""SELECT vr.question_id, vr.reported_by_manager_phone, q.user_id, d.name
                     FROM violation_reports vr 
                     JOIN questions q ON vr.question_id = q.id
                     JOIN departments d ON q.department_id = d.id
                     WHERE vr.id = ?""", (violation_id,))
        violation_data = c.fetchone()
        
        if not violation_data:
            flash('گزارش تخلف پیدا نشد', 'error')
            return redirect(url_for('violation_admin_dashboard'))
        
        question_id, manager_phone, user_id, department_name = violation_data
        
        # Get user phone for SMS
        c.execute("SELECT phone FROM users WHERE id = ?", (user_id,))
        user_phone = c.fetchone()[0]
        
        if action == 'solve':
            # Mark question as solved and calculate final reward
            c.execute("SELECT paused_reward FROM questions WHERE id = ?", (question_id,))
            paused_reward = c.fetchone()[0] or 0
            
            c.execute("""UPDATE questions SET 
                         status = 'answered',
                         reward_amount = ?,
                         user_feedback = 'solved',
                         violation_status = 'resolved'
                         WHERE id = ?""", (paused_reward, question_id))
            
            # Update violation report
            c.execute("""UPDATE violation_reports SET 
                         status = 'resolved',
                         admin_action = 'solved',
                         admin_action_at = ?,
                         handled_by_violation_admin = ?,
                         notes = ?
                         WHERE id = ?""", (current_time, violation_admin_id, admin_notes, violation_id))
            
            # Send SMS to manager
            sms_base = f"ادمین تخلفات اقدام به حل سوال شماره {question_id} کرده است. پاداش نهایی محاسبه شد."
            sms_text = f"{sms_base}\n\n📝 یادداشت ادمین: {admin_notes}" if admin_notes else sms_base
            send_sms(manager_phone, sms_text)
            
            flash('سوال به عنوان حل شده علامت‌گذاری شد', 'success')
            
        elif action == 'waiting':
            # Apply waiting logic
            c.execute("""SELECT waiting_count, paused_reward, penalty_multiplier 
                         FROM questions WHERE id = ?""", (question_id,))
            question_data = c.fetchone()
            waiting_count, paused_reward, penalty_multiplier = question_data
            
            waiting_count = (waiting_count or 0) + 1
            if waiting_count == 1:
                new_hours = 72
            else:
                new_hours = 72 / (2 ** (waiting_count - 1))
            
            new_deadline = current_time + timedelta(hours=new_hours)
            new_penalty_multiplier = (penalty_multiplier or 3) + 1
            
            c.execute("""UPDATE questions SET 
                         status = 'pending',
                         user_feedback = 'waiting',
                         fixed_reward = ?,
                         waiting_deadline = ?,
                         waiting_count = ?,
                         penalty_multiplier = ?,
                         violation_status = 'resolved',
                         paused_at = NULL,
                         paused_timer_remaining = NULL,
                         paused_reward = NULL
                         WHERE id = ?""", 
                      (paused_reward, new_deadline.isoformat(), waiting_count, new_penalty_multiplier, question_id))
            
            # Update violation report
            c.execute("""UPDATE violation_reports SET 
                         status = 'resolved',
                         admin_action = 'waiting',
                         admin_action_at = ?,
                         handled_by_violation_admin = ?,
                         notes = ?
                         WHERE id = ?""", (current_time, violation_admin_id, admin_notes, violation_id))
            
            # Send SMS to manager
            sms_base = f"ادمین تخلفات سوال شماره {question_id} را به حالت انتظار تغییر داده است. زمان جدید تمدید شد."
            sms_text = f"{sms_base}\n\n📝 یادداشت ادمین: {admin_notes}" if admin_notes else sms_base
            send_sms(manager_phone, sms_text)
            
            flash('سوال به حالت انتظار تغییر کرد', 'success')
            
        elif action == 'end':
            # End request without reward/penalty
            c.execute("""UPDATE questions SET 
                         status = 'answered',
                         reward_amount = 0,
                         user_feedback = 'end',
                         violation_status = 'resolved'
                         WHERE id = ?""", (question_id,))
            
            # Update violation report
            c.execute("""UPDATE violation_reports SET 
                         status = 'resolved',
                         admin_action = 'end_request',
                         admin_action_at = ?,
                         handled_by_violation_admin = ?,
                         notes = ?
                         WHERE id = ?""", (current_time, violation_admin_id, admin_notes, violation_id))
            
            # Send SMS to manager
            sms_base = f"ادمین تخلفات درخواست سوال شماره {question_id} را بدون پاداش یا جریمه پایان داده است."
            sms_text = f"{sms_base}\n\n📝 یادداشت ادمین: {admin_notes}" if admin_notes else sms_base
            send_sms(manager_phone, sms_text)
            
            flash('درخواست پایان یافت', 'success')
            
        elif action == 'invalid':
            # Resume normal timer and reward calculation from paused state
            c.execute("""SELECT paused_timer_remaining, paused_reward, created_at, timer_hours, fixed_reward,
                         waiting_deadline, penalty_multiplier
                         FROM questions WHERE id = ?""", (question_id,))
            question_data = c.fetchone()
            paused_timer_remaining, paused_reward, created_at_str, timer_hours, fixed_reward, existing_waiting_deadline, penalty_multiplier = question_data
            
            # Calculate new virtual created_at to resume from paused state
            if paused_timer_remaining is not None and paused_timer_remaining > 0:
                # Calculate new created_at that would give us the paused_timer_remaining
                # new_created_at = current_time - (timer_hours * 3600 - paused_timer_remaining)
                total_seconds = timer_hours * 3600
                elapsed_seconds = total_seconds - paused_timer_remaining
                new_created_at = current_time - timedelta(seconds=elapsed_seconds)
                
                c.execute("""UPDATE questions SET 
                             created_at = ?,
                             fixed_reward = ?,
                             violation_status = 'resolved',
                             paused_at = NULL,
                             paused_timer_remaining = NULL,
                             paused_reward = NULL,
                             penalty_multiplier = ?
                             WHERE id = ?""", 
                          (new_created_at.strftime("%Y-%m-%d %H:%M:%S.%f"), 
                           paused_reward or fixed_reward, 
                           penalty_multiplier or 3, 
                           question_id))
            else:
                # No paused timer, just clear the paused state
                c.execute("""UPDATE questions SET 
                             violation_status = 'resolved',
                             paused_at = NULL,
                             paused_timer_remaining = NULL,
                             paused_reward = NULL,
                             fixed_reward = ?,
                             penalty_multiplier = ?
                             WHERE id = ?""", 
                          (paused_reward or fixed_reward, penalty_multiplier or 3, question_id))
            
            # Update violation report
            c.execute("""UPDATE violation_reports SET 
                         status = 'resolved',
                         admin_action = 'invalid_report',
                         admin_action_at = ?,
                         handled_by_violation_admin = ?,
                         notes = ?
                         WHERE id = ?""", (current_time, violation_admin_id, admin_notes, violation_id))
            
            # Send SMS to manager
            sms_base = f"ادمین تخلفات گزارش تخلف سوال شماره {question_id} را نامعتبر تشخیص داده است. زمان‌بندی عادی ادامه می‌یابد."
            sms_text = f"{sms_base}\n\n📝 یادداشت ادمین: {admin_notes}" if admin_notes else sms_base
            send_sms(manager_phone, sms_text)
            
            flash('گزارش نامعتبر تشخیص داده شد و زمان‌بندی عادی ادامه یافت', 'success')
        
        conn.commit()
        conn.close()
        return redirect(url_for('violation_admin_detail', violation_id=violation_id))
    
    # GET request - show violation details
    c.execute("""
        SELECT vr.id, vr.question_id, vr.reported_by_manager_phone, vr.reported_at, 
               vr.status, vr.admin_action, vr.admin_action_at, vr.notes,
               q.question_text, q.status as question_status, q.created_at,
               u.name, u.phone, d.name, vr.manager_notes
        FROM violation_reports vr
        JOIN questions q ON vr.question_id = q.id
        JOIN users u ON q.user_id = u.id
        JOIN departments d ON q.department_id = d.id
        WHERE vr.id = ?
    """, (violation_id,))
    violation_report = c.fetchone()
    
    if not violation_report:
        flash('گزارش تخلف پیدا نشد', 'error')
        conn.close()
        return redirect(url_for('violation_admin_dashboard'))
    
    # Get all answers for this violation
    c.execute("""
        SELECT answer_text, answered_at, is_primary_answer
        FROM violation_report_answers
        WHERE violation_report_id = ?
        ORDER BY answered_at ASC
    """, (violation_id,))
    violation_answers = c.fetchall()
    
    conn.close()
    
    # Violation Admin Detail Template
    html = '''
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>جزئیات گزارش تخلف</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');
            
            body { 
                direction: rtl; 
                background: linear-gradient(135deg, #e17055 0%, #d63031 100%);
                font-family: 'Vazirmatn', sans-serif;
                min-height: 100vh;
                padding: 20px 0;
            }
            
            .detail-card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border: none;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                margin-bottom: 30px;
                overflow: hidden;
            }
            
            .detail-header {
                background: linear-gradient(135deg, #e17055 0%, #d63031 100%);
                color: white;
                padding: 25px;
                font-weight: 600;
                font-size: 1.3rem;
            }
            
            .info-section {
                padding: 25px;
                border-bottom: 1px solid #e2e8f0;
            }
            
            .info-row {
                display: flex;
                justify-content: space-between;
                margin-bottom: 15px;
                padding: 10px 0;
            }
            
            .info-label {
                font-weight: 600;
                color: #4a5568;
                flex: 0 0 30%;
            }
            
            .info-value {
                flex: 1;
                text-align: left;
                color: #2d3748;
            }
            
            .answer-item {
                background: rgba(108, 92, 231, 0.05);
                border: 1px solid rgba(108, 92, 231, 0.2);
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 15px;
                position: relative;
            }
            
            .answer-primary {
                background: rgba(0, 184, 148, 0.05);
                border-color: rgba(0, 184, 148, 0.3);
            }
            
            .answer-additional {
                background: rgba(253, 203, 110, 0.05);
                border-color: rgba(253, 203, 110, 0.3);
            }
            
            .answer-badge {
                position: absolute;
                top: -8px;
                right: 15px;
                padding: 4px 12px;
                border-radius: 15px;
                font-size: 0.8rem;
                font-weight: 600;
            }
            
            .badge-primary {
                background: linear-gradient(135deg, #00b894 0%, #55efc4 100%);
                color: white;
            }
            
            .badge-additional {
                background: linear-gradient(135deg, #fdcb6e 0%, #f39c12 100%);
                color: white;
            }
            
            .action-buttons {
                padding: 25px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
            }
            
            .action-btn {
                border: none;
                border-radius: 12px;
                padding: 15px 20px;
                font-weight: 600;
                font-size: 1rem;
                transition: all 0.3s ease;
                text-decoration: none;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
            }
            
            .btn-solve {
                background: linear-gradient(135deg, #00b894 0%, #55efc4 100%);
                color: white;
            }
            
            .btn-waiting {
                background: linear-gradient(135deg, #fdcb6e 0%, #f39c12 100%);
                color: white;
            }
            
            .btn-end {
                background: linear-gradient(135deg, #e17055 0%, #d63031 100%);
                color: white;
            }
            
            .btn-invalid {
                background: linear-gradient(135deg, #636e72 0%, #2d3436 100%);
                color: white;
            }
            
            .action-btn:hover {
                transform: translateY(-3px);
                box-shadow: 0 6px 20px rgba(0,0,0,0.3);
                color: white;
            }
            
            .nav-buttons {
                text-align: center;
                margin-bottom: 20px;
            }
            
            .nav-btn {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 12px;
                padding: 10px 20px;
                margin: 5px;
                text-decoration: none;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            
            .nav-btn:hover {
                background: rgba(255, 255, 255, 0.3);
                color: white;
                transform: translateY(-2px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="nav-buttons">
                <a href="/violation-admin/dashboard" class="nav-btn">
                    <i class="bi bi-arrow-right me-2"></i>بازگشت به داشبورد
                </a>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }} alert-dismissible fade show" role="alert">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <div class="detail-card">
                <div class="detail-header">
                    <i class="bi bi-exclamation-triangle me-3"></i>جزئیات گزارش تخلف #{{ violation_report[1] }}
                </div>
                
                <div class="info-section">
                    <div class="info-row">
                        <span class="info-label"><i class="bi bi-question-circle me-2"></i>متن سوال:</span>
                        <span class="info-value">{{ violation_report[8] }}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label"><i class="bi bi-person me-2"></i>کاربر:</span>
                        <span class="info-value">{{ violation_report[11] }} ({{ violation_report[12] }})</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label"><i class="bi bi-building me-2"></i>دپارتمان:</span>
                        <span class="info-value">{{ violation_report[13] }}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label"><i class="bi bi-phone me-2"></i>گزارش‌دهنده:</span>
                        <span class="info-value">{{ violation_report[2] }}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label"><i class="bi bi-calendar me-2"></i>تاریخ گزارش:</span>
                        <span class="info-value">{{ violation_report[3] }}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label"><i class="bi bi-clock me-2"></i>تاریخ ایجاد سوال:</span>
                        <span class="info-value">{{ violation_report[10] }}</span>
                    </div>
                </div>
                
                {% if violation_report[14] %}
                <div class="info-section">
                    <h6 class="mb-3"><i class="bi bi-sticky me-2"></i>یادداشت مدیر:</h6>
                    <div class="p-3" style="background: rgba(240, 147, 251, 0.1); border-radius: 12px; border: 1px solid rgba(240, 147, 251, 0.3); font-weight: 500; line-height: 1.6;">
                        {{ violation_report[14] }}
                    </div>
                </div>
                {% endif %}
                
                {% if violation_answers %}
                <div class="info-section">
                    <h6 class="mb-3"><i class="bi bi-chat-dots me-2"></i>پاسخ‌های مدیر:</h6>
                    {% for answer in violation_answers %}
                    <div class="answer-item {{ 'answer-primary' if answer[2] else 'answer-additional' }}">
                        <div class="answer-badge {{ 'badge-primary' if answer[2] else 'badge-additional' }}">
                            {{ 'پاسخ اولیه' if answer[2] else 'پاسخ اضافی' }}
                        </div>
                        <div class="mt-2 mb-2" style="font-weight: 500;">{{ answer[0] }}</div>
                        <small class="text-muted">
                            <i class="bi bi-clock me-1"></i>{{ answer[1] }}
                        </small>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
                
                {% if violation_report[4] == 'pending' %}
                <div class="info-section">
                    <h6 class="mb-3"><i class="bi bi-chat-text me-2"></i>اقدام ادمین تخلفات:</h6>
                    <form method="post">
                        <div class="mb-3">
                            <label class="form-label fw-semibold">یادداشت ادمین (اختیاری):</label>
                            <textarea name="admin_notes" class="form-control" rows="3" 
                                    placeholder="توضیحات، دلیل تصمیم یا راهنمایی برای مدیر..."
                                    style="border-radius: 12px; border: 2px solid #e2e8f0;"></textarea>
                        </div>
                        <div class="action-buttons">
                            <button type="submit" name="action" value="solve" class="action-btn btn-solve" onclick="return confirm('آیا از حل کردن این سوال مطمئن هستید؟')">
                                <i class="bi bi-check-circle"></i>حل مشکل
                            </button>
                            <button type="submit" name="action" value="waiting" class="action-btn btn-waiting" onclick="return confirm('آیا از تمدید زمان این سوال مطمئن هستید؟')">
                                <i class="bi bi-hourglass-split"></i>در انتظار
                            </button>
                            <button type="submit" name="action" value="end" class="action-btn btn-end" onclick="return confirm('آیا از پایان دادن به این درخواست مطمئن هستید؟')">
                                <i class="bi bi-x-circle"></i>پایان درخواست
                            </button>
                            <button type="submit" name="action" value="invalid" class="action-btn btn-invalid" onclick="return confirm('آیا از نامعتبر بودن این گزارش مطمئن هستید؟')">
                                <i class="bi bi-shield-x"></i>گزارش نامعتبر
                            </button>
                        </div>
                    </form>
                </div>
                {% else %}
                <div class="info-section text-center">
                    <div class="alert alert-info">
                        <i class="bi bi-info-circle me-2"></i>
                        این گزارش قبلاً بررسی شده است. 
                        اقدام انجام شده: <strong>{{ violation_report[5] }}</strong>
                        در تاریخ {{ violation_report[6] }}
                    </div>
                </div>
                {% endif %}
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''
    
    return render_template_string(html, violation_report=violation_report, violation_answers=violation_answers)

@app.route('/admin')
def admin_dashboard():
    # Redirect to admin login page
    return redirect('/admin/login')

@app.route('/admin/panel', methods=['GET', 'POST'])
@admin_required
def admin_panel():
    conn = sqlite3.connect('system.db')
    c = conn.cursor()

    if request.method == 'POST':
        if 'base_reward' in request.form:
            new_reward = int(request.form['base_reward'])
            new_minutes = float(request.form['base_minutes'])
            new_hours = new_minutes / 60
            c.execute("UPDATE admin_settings SET base_reward_amount = ?, base_timer_hours = ? WHERE id = 1", (new_reward, new_hours))
            conn.commit()

        if 'new_department_name' in request.form:
            dep_name = request.form['new_department_name']
            manager_phone = request.form['manager_phone']
            dep_password = request.form['department_password']
            c.execute("INSERT INTO departments (name, manager_phone, password, active) VALUES (?, ?, ?, ?)", 
                      (dep_name, manager_phone, dep_password, 1))
            conn.commit()

        if 'edit_department_id' in request.form:
            dep_id = int(request.form['edit_department_id'])
            dep_name = request.form['edit_department_name']
            manager_phone = request.form['edit_manager_phone']
            dep_password = request.form['edit_department_password']
            c.execute("UPDATE departments SET name = ?, manager_phone = ?, password = ? WHERE id = ?", 
                      (dep_name, manager_phone, dep_password, dep_id))
            conn.commit()

        if 'toggle_department_id' in request.form:
            dep_id = int(request.form['toggle_department_id'])
            c.execute("SELECT active FROM departments WHERE id = ?", (dep_id,))
            current_status = c.fetchone()[0]
            new_status = 0 if current_status == 1 else 1
            c.execute("UPDATE departments SET active = ? WHERE id = ?", (new_status, dep_id))
            conn.commit()

        if 'delete_department_id' in request.form:
            dep_id = int(request.form['delete_department_id'])
            c.execute("DELETE FROM departments WHERE id = ?", (dep_id,))
            conn.commit()

        # Handle creating new violation admin
        if 'new_violation_admin_username' in request.form:
            username = request.form['new_violation_admin_username']
            password = request.form['new_violation_admin_password']
            admin_id = session.get('admin_id')
            
            # Check if username already exists
            c.execute("SELECT id FROM violation_admins WHERE username = ?", (username,))
            existing = c.fetchone()
            
            if existing:
                flash('نام کاربری قبلاً وجود دارد', 'error')
            else:
                c.execute("""INSERT INTO violation_admins (username, password, created_by, active) 
                             VALUES (?, ?, ?, 1)""", (username, password, admin_id))
                conn.commit()
                flash('ادمین تخلفات جدید با موفقیت ایجاد شد', 'success')

    # آمار کلی
    c.execute("SELECT COUNT(*) FROM questions")
    total_questions = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM questions WHERE status = 'answered'")
    answered_questions = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM questions WHERE reward_amount > 0")
    total_rewards = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM questions WHERE reward_amount < 0")
    total_penalties = c.fetchone()[0]

    c.execute("SELECT SUM(reward_amount) FROM questions WHERE reward_amount > 0")
    sum_rewards = c.fetchone()[0] or 0

    c.execute("SELECT SUM(reward_amount) FROM questions WHERE reward_amount < 0")
    sum_penalties = c.fetchone()[0] or 0

    # آمار وضعیت فیدبک کاربران
    c.execute("SELECT COUNT(*) FROM questions WHERE user_feedback = 'solved'")
    count_solved = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM questions WHERE user_feedback = 'waiting'")
    count_waiting = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM questions WHERE user_feedback = 'end'")
    count_end = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM questions WHERE user_feedback IS NULL OR user_feedback = ''")
    count_none = c.fetchone()[0]

    feedback_total = count_solved + count_waiting + count_end + count_none

    percent_solved = (count_solved / feedback_total * 100) if feedback_total else 0
    percent_waiting = (count_waiting / feedback_total * 100) if feedback_total else 0
    percent_end = (count_end / feedback_total * 100) if feedback_total else 0
    percent_none = (count_none / feedback_total * 100) if feedback_total else 0

    # آمار گزارش‌های تخلف
    c.execute("SELECT COUNT(*) FROM violation_reports")
    total_violation_reports = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM violation_reports WHERE status = 'pending'")
    pending_violation_reports = c.fetchone()[0]

    # آمار گزارش‌های تخلف هر مدیر
    c.execute("""
        SELECT d.name, d.manager_phone, COUNT(vr.id) as report_count
        FROM departments d
        LEFT JOIN questions q ON d.id = q.department_id
        LEFT JOIN violation_reports vr ON q.id = vr.question_id
        GROUP BY d.id, d.name, d.manager_phone
        ORDER BY report_count DESC
    """)
    manager_violation_stats = c.fetchall()

    # سوالات
    c.execute("""
        SELECT q.id, u.name, u.phone, q.question_text, q.status, q.created_at, q.answered_at, q.reward_amount, d.name
        FROM questions q
        JOIN users u ON q.user_id = u.id
        JOIN departments d ON q.department_id = d.id
        ORDER BY q.created_at DESC
    """)
    questions = c.fetchall()

    c.execute("SELECT id, name, phone FROM users")
    users = c.fetchall()

    c.execute("SELECT id, name, manager_phone, password, active FROM departments")
    departments = c.fetchall()

    c.execute("SELECT base_reward_amount, base_timer_hours FROM admin_settings WHERE id = 1")
    settings = c.fetchone()

    # Get violation admins
    c.execute("SELECT id, username, created_at, active FROM violation_admins ORDER BY created_at DESC")
    violation_admins = c.fetchall()

    conn.close()

    html = '''
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>داشبورد ادمین کل</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');
            
            body { 
                direction: rtl; 
                background: linear-gradient(135deg, #2d3436 0%, #636e72 100%);
                font-family: 'Vazirmatn', sans-serif;
                min-height: 100vh;
                padding: 20px 0;
            }
            
            .dashboard-header {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 30px;
                margin-bottom: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                text-align: center;
            }
            
            .dashboard-header h3 {
                background: linear-gradient(135deg, #2d3436 0%, #636e72 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                font-weight: 700;
                font-size: 2.2rem;
                margin: 0;
            }
            
            .stats-card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border: none;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                margin-bottom: 30px;
                overflow: hidden;
            }
            
            .stats-header {
                background: linear-gradient(135deg, #00b894 0%, #55efc4 100%);
                color: white;
                padding: 20px 25px;
                margin: 0;
                font-weight: 600;
                font-size: 1.2rem;
            }
            
            .stats-list {
                margin: 0;
                border: none;
            }
            
            .stats-item {
                border: none;
                border-bottom: 1px solid #e2e8f0;
                padding: 20px 25px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                transition: all 0.3s ease;
            }
            
            .stats-item:last-child {
                border-bottom: none;
            }
            
            .stats-item:hover {
                background-color: rgba(0, 184, 148, 0.05);
            }
            
            .stats-label {
                font-weight: 500;
                color: #4a5568;
            }
            
            .stats-value {
                font-weight: 700;
                font-size: 1.1rem;
            }
            
            .positive-value {
                color: #00b894;
            }
            
            .negative-value {
                color: #e17055;
            }
            
            .neutral-value {
                color: #636e72;
            }
            
            .feedback-header {
                background: linear-gradient(135deg, #fdcb6e 0%, #f39c12 100%);
                color: white;
                padding: 20px 25px;
                margin: 0;
                font-weight: 600;
                font-size: 1.2rem;
            }
            
            .feedback-item {
                border: none;
                border-bottom: 1px solid #e2e8f0;
                padding: 20px 25px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                transition: all 0.3s ease;
            }
            
            .feedback-item:last-child {
                border-bottom: none;
            }
            
            .feedback-item:hover {
                background-color: rgba(253, 203, 110, 0.05);
            }
            
            @media (max-width: 768px) {
                .container {
                    padding: 10px;
                }
                
                .dashboard-header {
                    padding: 20px;
                }
                
                .dashboard-header h3 {
                    font-size: 1.8rem;
                }
                
                .stats-item, .feedback-item {
                    padding: 15px 20px;
                    flex-direction: column;
                    align-items: start;
                    gap: 5px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="dashboard-header">
                <div class="d-flex justify-content-between align-items-center">
                    <h3><i class="bi bi-gear me-3"></i>داشبورد ادمین کل</h3>
                    <div>
                        <a href="/admin/violations" class="btn btn-outline-warning me-2">
                            <i class="bi bi-exclamation-triangle me-2"></i>مدیریت تخلفات
                        </a>
                        <a href="/admin/logout" class="btn btn-outline-danger">
                            <i class="bi bi-box-arrow-right me-2"></i>خروج
                        </a>
                    </div>
                </div>
            </div>

            <div class="stats-card">
                <h5 class="stats-header"><i class="bi bi-bar-chart me-2"></i>آمار کلی</h5>
                <ul class="list-group stats-list">
                    <li class="stats-item">
                        <span class="stats-label"><i class="bi bi-question-circle me-2"></i>کل سوالات ثبت شده</span>
                        <span class="stats-value neutral-value">{{ total_questions }}</span>
                    </li>
                    <li class="stats-item">
                        <span class="stats-label"><i class="bi bi-check-circle me-2"></i>سوالات پاسخ داده شده</span>
                        <span class="stats-value positive-value">{{ answered_questions }}</span>
                    </li>
                    <li class="stats-item">
                        <span class="stats-label"><i class="bi bi-gift me-2"></i>تعداد پاداش‌ها</span>
                        <span class="stats-value positive-value">{{ total_rewards }}</span>
                    </li>
                    <li class="stats-item">
                        <span class="stats-label"><i class="bi bi-exclamation-triangle me-2"></i>تعداد جریمه‌ها</span>
                        <span class="stats-value negative-value">{{ total_penalties }}</span>
                    </li>
                    <li class="stats-item">
                        <span class="stats-label"><i class="bi bi-currency-dollar me-2"></i>مجموع پاداش</span>
                        <span class="stats-value positive-value">{{ "{:,}".format(sum_rewards) }} تومان</span>
                    </li>
                    <li class="stats-item">
                        <span class="stats-label"><i class="bi bi-dash-circle me-2"></i>مجموع جریمه</span>
                        <span class="stats-value negative-value">{{ "{:,}".format(sum_penalties) }} تومان</span>
                    </li>
                </ul>
            </div>

            <div class="stats-card">
                <h5 class="feedback-header"><i class="bi bi-pie-chart me-2"></i>آمار انتخاب کاربران</h5>
                <ul class="list-group stats-list">
                    <li class="feedback-item">
                        <span class="stats-label"><i class="bi bi-check-circle me-2"></i>درصد حل مشکل</span>
                        <span class="stats-value positive-value">{{ "%.1f"|format(percent_solved) }}%</span>
                    </li>
                    <li class="feedback-item">
                        <span class="stats-label"><i class="bi bi-hourglass-split me-2"></i>در انتظار حل مشکل</span>
                        <span class="stats-value" style="color:#f39c12;">{{ "%.1f"|format(percent_waiting) }}%</span>
                    </li>
                    <li class="feedback-item">
                        <span class="stats-label"><i class="bi bi-x-circle me-2"></i>پایان درخواست</span>
                        <span class="stats-value negative-value">{{ "%.1f"|format(percent_end) }}%</span>
                    </li>
                    <li class="feedback-item">
                        <span class="stats-label"><i class="bi bi-dash-circle me-2"></i>اقدام نشده</span>
                        <span class="stats-value" style="color:#74b9ff;">{{ "%.1f"|format(percent_none) }}%</span>
                    </li>
                </ul>
            </div>

            <div class="stats-card">
                <h5 class="stats-header" style="background: linear-gradient(135deg, #e17055 0%, #d63031 100%);"><i class="bi bi-exclamation-triangle me-2"></i>آمار گزارش‌های تخلف</h5>
                <ul class="list-group stats-list">
                    <li class="stats-item">
                        <span class="stats-label"><i class="bi bi-flag me-2"></i>کل گزارش‌های تخلف</span>
                        <span class="stats-value neutral-value">{{ total_violation_reports }}</span>
                    </li>
                    <li class="stats-item">
                        <span class="stats-label"><i class="bi bi-hourglass-split me-2"></i>در انتظار بررسی</span>
                        <span class="stats-value" style="color:#f39c12;">{{ pending_violation_reports }}</span>
                    </li>
                </ul>
            </div>

            <div class="stats-card">
                <h5 class="stats-header" style="background: linear-gradient(135deg, #fd79a8 0%, #e84393 100%);"><i class="bi bi-people me-2"></i>آمار گزارش‌های تخلف مدیران</h5>
                <div class="table-responsive">
                    <table class="table table-hover" style="font-size: 0.9rem;">
                        <thead style="background: linear-gradient(135deg, #fd79a8 0%, #e84393 100%); color: white;">
                            <tr>
                                <th style="border: none; padding: 12px;">دپارتمان</th>
                                <th style="border: none; padding: 12px;">شماره مدیر</th>
                                <th style="border: none; padding: 12px;">تعداد گزارش‌ها</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for mvs in manager_violation_stats %}
                            <tr style="transition: all 0.3s ease;">
                                <td style="padding: 12px; vertical-align: middle;">{{ mvs[0] }}</td>
                                <td style="padding: 12px; vertical-align: middle;">{{ mvs[1] }}</td>
                                <td style="padding: 12px; vertical-align: middle;">
                                    {% if mvs[2] > 0 %}
                                        <span style="color: #e17055; font-weight: 600;">{{ mvs[2] }}</span>
                                    {% else %}
                                        <span style="color: #00b894;">بدون گزارش</span>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="stats-card">
                <h5 class="stats-header" style="background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);"><i class="bi bi-gear me-2"></i>تنظیمات کلی</h5>
                <div class="p-4">
                    <form method="post">
                        <div class="mb-3">
                            <label class="form-label fw-semibold"><i class="bi bi-currency-dollar me-2"></i>مبلغ پاداش پایه (تومان)</label>
                            <input type="number" name="base_reward" value="{{ settings[0] }}" class="form-control" style="border-radius: 12px; border: 2px solid #e2e8f0; padding: 12px 16px;" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-semibold"><i class="bi bi-clock me-2"></i>زمان پاسخگویی (دقیقه)</label>
                            <input type="number" name="base_minutes" value="{{ (settings[1]*60)|int }}" class="form-control" style="border-radius: 12px; border: 2px solid #e2e8f0; padding: 12px 16px;" required>
                        </div>
                        <button type="submit" class="btn w-100" style="background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%); color: white; border: none; border-radius: 12px; padding: 12px 20px; font-weight: 600; transition: all 0.3s ease;">
                            <i class="bi bi-save me-2"></i>ذخیره تغییرات
                        </button>
                    </form>
                </div>
            </div>

            <div class="stats-card">
                <h5 class="stats-header" style="background: linear-gradient(135deg, #e17055 0%, #d63031 100%);"><i class="bi bi-building-add me-2"></i>افزودن دپارتمان جدید</h5>
                <div class="p-4">
                    <form method="post">
                        <div class="mb-3">
                            <label class="form-label fw-semibold"><i class="bi bi-building me-2"></i>نام دپارتمان</label>
                            <input type="text" name="new_department_name" class="form-control" style="border-radius: 12px; border: 2px solid #e2e8f0; padding: 12px 16px;" placeholder="نام دپارتمان را وارد کنید" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-semibold"><i class="bi bi-phone me-2"></i>شماره مدیر</label>
                            <input type="tel" name="manager_phone" class="form-control" style="border-radius: 12px; border: 2px solid #e2e8f0; padding: 12px 16px;" placeholder="09xxxxxxxxx" pattern="[0-9]{11}" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-semibold"><i class="bi bi-key me-2"></i>رمز عبور دپارتمان</label>
                            <input type="password" name="department_password" class="form-control" style="border-radius: 12px; border: 2px solid #e2e8f0; padding: 12px 16px;" placeholder="رمز عبور برای مدیر" required>
                        </div>
                        <button type="submit" class="btn w-100" style="background: linear-gradient(135deg, #e17055 0%, #d63031 100%); color: white; border: none; border-radius: 12px; padding: 12px 20px; font-weight: 600; transition: all 0.3s ease;">
                            <i class="bi bi-plus-circle me-2"></i>افزودن دپارتمان
                        </button>
                    </form>
                </div>
            </div>

            <div class="stats-card">
                <h5 class="stats-header" style="background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);"><i class="bi bi-building me-2"></i>دپارتمان‌ها</h5>
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead style="background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); color: white;">
                            <tr>
                                <th style="border: none; padding: 15px;">شناسه</th>
                                <th style="border: none; padding: 15px;">نام دپارتمان</th>
                                <th style="border: none; padding: 15px;">شماره مدیر</th>
                                <th style="border: none; padding: 15px;">رمز عبور</th>
                                <th style="border: none; padding: 15px;">وضعیت</th>
                                <th style="border: none; padding: 15px;">عملیات</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for d in departments %}
                            <tr style="transition: all 0.3s ease;">
                                <td style="padding: 15px; vertical-align: middle;"><strong>#{{ d[0] }}</strong></td>
                                <td style="padding: 15px; vertical-align: middle;">{{ d[1] }}</td>
                                <td style="padding: 15px; vertical-align: middle;">{{ d[2] }}</td>
                                <td style="padding: 15px; vertical-align: middle;">
                                    <span class="badge bg-secondary">{{ d[3] }}</span>
                                </td>
                                <td style="padding: 15px; vertical-align: middle;">
                                    {% if d[4] == 1 %}
                                        <span class="badge bg-success">فعال</span>
                                    {% else %}
                                        <span class="badge bg-danger">غیرفعال</span>
                                    {% endif %}
                                </td>
                                <td style="padding: 15px; vertical-align: middle;">
                                    <div class="btn-group" role="group">
                                        <button type="button" class="btn btn-sm btn-outline-primary edit-btn" 
                                                data-department-id="{{ d[0] }}" 
                                                data-department-name="{{ d[1] }}" 
                                                data-manager-phone="{{ d[2] }}" 
                                                data-department-password="{{ d[3] }}"
                                                data-bs-toggle="modal" 
                                                data-bs-target="#editModal">
                                            <i class="bi bi-pencil"></i>
                                        </button>
                                        <form method="post" style="display:inline;">
                                            <input type="hidden" name="toggle_department_id" value="{{ d[0] }}">
                                            <button type="submit" class="btn btn-sm btn-outline-warning">
                                                <i class="bi bi-{{ 'pause' if d[4] == 1 else 'play' }}"></i>
                                            </button>
                                        </form>
                                        <form method="post" style="display:inline;">
                                            <input type="hidden" name="delete_department_id" value="{{ d[0] }}">
                                            <button type="submit" class="btn btn-sm btn-outline-danger" onclick="return confirm('آیا مطمئن هستید؟')">
                                                <i class="bi bi-trash"></i>
                                            </button>
                                        </form>
                                    </div>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="stats-card">
                <h5 class="stats-header" style="background: linear-gradient(135deg, #fd79a8 0%, #e84393 100%);"><i class="bi bi-chat-dots me-2"></i>سوالات</h5>
                <div class="table-responsive">
                    <table class="table table-hover" style="font-size: 0.9rem;">
                        <thead style="background: linear-gradient(135deg, #fd79a8 0%, #e84393 100%); color: white;">
                            <tr>
                                <th style="border: none; padding: 12px;">شناسه</th>
                                <th style="border: none; padding: 12px;">کاربر</th>
                                <th style="border: none; padding: 12px;">شماره</th>
                                <th style="border: none; padding: 12px;">سوال</th>
                                <th style="border: none; padding: 12px;">دپارتمان</th>
                                <th style="border: none; padding: 12px;">وضعیت</th>
                                <th style="border: none; padding: 12px;">ثبت</th>
                                <th style="border: none; padding: 12px;">پاسخ</th>
                                <th style="border: none; padding: 12px;">پاداش/جریمه</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for q in questions %}
                            <tr style="transition: all 0.3s ease;">
                                <td style="padding: 12px; vertical-align: middle;"><strong>#{{ q[0] }}</strong></td>
                                <td style="padding: 12px; vertical-align: middle;">{{ q[1] }}</td>
                                <td style="padding: 12px; vertical-align: middle;">{{ q[2] }}</td>
                                <td style="padding: 12px; vertical-align: middle; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="{{ q[3] }}">{{ q[3] }}</td>
                                <td style="padding: 12px; vertical-align: middle;">{{ q[8] }}</td>
                                <td style="padding: 12px; vertical-align: middle;">
                                    {% if q[4] == 'pending' %}
                                        <span class="badge" style="background: linear-gradient(135deg, #fdcb6e 0%, #f39c12 100%); padding: 6px 12px; border-radius: 12px;">در انتظار</span>
                                    {% elif q[4] == 'answered' %}
                                        <span class="badge" style="background: linear-gradient(135deg, #00b894 0%, #55efc4 100%); padding: 6px 12px; border-radius: 12px;">پاسخ داده شده</span>
                                    {% endif %}
                                </td>
                                <td style="padding: 12px; vertical-align: middle; font-size: 0.8rem;">{{ q[5] }}</td>
                                <td style="padding: 12px; vertical-align: middle; font-size: 0.8rem;">{{ q[6] if q[6] else "-" }}</td>
                                <td style="padding: 12px; vertical-align: middle;">
                                    {% if q[7] != 0 %}
                                        {% if q[7] > 0 %}
                                            <span style="color: #00b894; font-weight: 600;">+{{ "{:,}".format(q[7]) }}</span>
                                        {% else %}
                                            <span style="color: #e17055; font-weight: 600;">{{ "{:,}".format(q[7]) }}</span>
                                        {% endif %}
                                    {% else %}
                                        <span style="color: #636e72;">-</span>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="stats-card">
                <h5 class="stats-header" style="background: linear-gradient(135deg, #e17055 0%, #d63031 100%);"><i class="bi bi-person-plus me-2"></i>ایجاد ادمین تخلفات جدید</h5>
                <div class="p-4">
                    <form method="post">
                        <div class="mb-3">
                            <label class="form-label fw-semibold"><i class="bi bi-person me-2"></i>نام کاربری</label>
                            <input type="text" name="new_violation_admin_username" class="form-control" style="border-radius: 12px; border: 2px solid #e2e8f0; padding: 12px 16px;" placeholder="نام کاربری ادمین تخلفات" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-semibold"><i class="bi bi-key me-2"></i>رمز عبور</label>
                            <input type="password" name="new_violation_admin_password" class="form-control" style="border-radius: 12px; border: 2px solid #e2e8f0; padding: 12px 16px;" placeholder="رمز عبور" required>
                        </div>
                        <button type="submit" class="btn w-100" style="background: linear-gradient(135deg, #e17055 0%, #d63031 100%); color: white; border: none; border-radius: 12px; padding: 12px 20px; font-weight: 600; transition: all 0.3s ease;">
                            <i class="bi bi-plus-circle me-2"></i>ایجاد ادمین تخلفات
                        </button>
                    </form>
                </div>
            </div>

            <div class="stats-card">
                <h5 class="stats-header" style="background: linear-gradient(135deg, #e17055 0%, #d63031 100%);"><i class="bi bi-shield-check me-2"></i>ادمین‌های تخلفات</h5>
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead style="background: linear-gradient(135deg, #e17055 0%, #d63031 100%); color: white;">
                            <tr>
                                <th style="border: none; padding: 15px;">شناسه</th>
                                <th style="border: none; padding: 15px;">نام کاربری</th>
                                <th style="border: none; padding: 15px;">تاریخ ایجاد</th>
                                <th style="border: none; padding: 15px;">وضعیت</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for va in violation_admins %}
                            <tr style="transition: all 0.3s ease;">
                                <td style="padding: 15px; vertical-align: middle;"><strong>#{{ va[0] }}</strong></td>
                                <td style="padding: 15px; vertical-align: middle;">{{ va[1] }}</td>
                                <td style="padding: 15px; vertical-align: middle; font-size: 0.8rem;">{{ va[2] }}</td>
                                <td style="padding: 15px; vertical-align: middle;">
                                    {% if va[3] == 1 %}
                                        <span class="badge bg-success">فعال</span>
                                    {% else %}
                                        <span class="badge bg-danger">غیرفعال</span>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Single Edit Modal -->
            <div class="modal fade" id="editModal" tabindex="-1" aria-labelledby="editModalLabel" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="editModalLabel">ویرایش دپارتمان</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <form method="post" id="editForm">
                            <div class="modal-body">
                                <input type="hidden" name="edit_department_id" id="editDepartmentId">
                                <div class="mb-3">
                                    <label class="form-label">نام دپارتمان</label>
                                    <input type="text" name="edit_department_name" id="editDepartmentName" class="form-control" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">شماره مدیر</label>
                                    <input type="tel" name="edit_manager_phone" id="editManagerPhone" class="form-control" pattern="[0-9]{11}" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">رمز عبور</label>
                                    <input type="password" name="edit_department_password" id="editDepartmentPassword" class="form-control" required>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">لغو</button>
                                <button type="submit" class="btn btn-primary">ذخیره تغییرات</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
        // Handle edit department button clicks
        document.addEventListener('DOMContentLoaded', function() {
            const editButtons = document.querySelectorAll('.edit-btn');
            
            editButtons.forEach(button => {
                button.addEventListener('click', function() {
                    // Get data from button attributes
                    const departmentId = this.getAttribute('data-department-id');
                    const departmentName = this.getAttribute('data-department-name');
                    const managerPhone = this.getAttribute('data-manager-phone');
                    const departmentPassword = this.getAttribute('data-department-password');
                    
                    // Fill modal form
                    document.getElementById('editDepartmentId').value = departmentId;
                    document.getElementById('editDepartmentName').value = departmentName;
                    document.getElementById('editManagerPhone').value = managerPhone;
                    document.getElementById('editDepartmentPassword').value = departmentPassword;
                });
            });
        });
        </script>
    </body>
    </html>
    '''
    return render_template_string(
        html,
        questions=questions,
        users=users,
        departments=departments,
        settings=settings,
        total_questions=total_questions,
        answered_questions=answered_questions,
        total_rewards=total_rewards,
        total_penalties=total_penalties,
        sum_rewards=sum_rewards,
        sum_penalties=sum_penalties,
        percent_solved=percent_solved,
        percent_waiting=percent_waiting,
        percent_end=percent_end,
        percent_none=percent_none,
        total_violation_reports=total_violation_reports,
        pending_violation_reports=pending_violation_reports,
        manager_violation_stats=manager_violation_stats,
        violation_admins=violation_admins
    )

@app.route('/admin/violations', methods=['GET', 'POST'])
@admin_required
def violation_admin_panel():
    conn = sqlite3.connect('system.db')
    c = conn.cursor()
    
    # Get all violation reports with question details
    c.execute("""
        SELECT vr.id, vr.question_id, vr.reported_by_manager_phone, vr.reported_at, 
               vr.status, vr.admin_action, vr.admin_action_at,
               q.question_text, u.name, u.phone, d.name
        FROM violation_reports vr
        JOIN questions q ON vr.question_id = q.id
        JOIN users u ON q.user_id = u.id
        JOIN departments d ON q.department_id = d.id
        ORDER BY vr.reported_at DESC
    """)
    violation_reports = c.fetchall()
    
    conn.close()
    
    html = '''
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>پنل ادمین تخلفات</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');
            
            body { 
                direction: rtl; 
                background: linear-gradient(135deg, #d63031 0%, #e17055 100%);
                font-family: 'Vazirmatn', sans-serif;
                min-height: 100vh;
                padding: 20px 0;
            }
            
            .dashboard-header {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 30px;
                margin-bottom: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                text-align: center;
            }
            
            .dashboard-header h3 {
                background: linear-gradient(135deg, #d63031 0%, #e17055 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                font-weight: 700;
                font-size: 2.2rem;
                margin: 0;
            }
            
            .violation-card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border: none;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                margin-bottom: 30px;
                overflow: hidden;
            }
            
            .violation-header {
                background: linear-gradient(135deg, #d63031 0%, #e17055 100%);
                color: white;
                padding: 20px 25px;
                margin: 0;
                font-weight: 600;
                font-size: 1.2rem;
            }
            
            .table-responsive {
                border-radius: 0;
            }
            
            .table {
                margin: 0;
                font-size: 0.9rem;
            }
            
            .table thead th {
                background: linear-gradient(135deg, #d63031 0%, #e17055 100%);
                color: white;
                border: none;
                padding: 15px 12px;
                font-weight: 600;
            }
            
            .table tbody td {
                padding: 15px 12px;
                vertical-align: middle;
                border-bottom: 1px solid #e2e8f0;
            }
            
            .table tbody tr:hover {
                background-color: rgba(214, 48, 49, 0.05);
            }
            
            .status-pending {
                background: linear-gradient(135deg, #fdcb6e 0%, #f39c12 100%);
                color: white;
                padding: 6px 12px;
                border-radius: 15px;
                font-size: 0.85rem;
                font-weight: 500;
            }
            
            .status-resolved {
                background: linear-gradient(135deg, #00b894 0%, #55efc4 100%);
                color: white;
                padding: 6px 12px;
                border-radius: 15px;
                font-size: 0.85rem;
                font-weight: 500;
            }
            
            .btn-view {
                background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);
                border: none;
                border-radius: 10px;
                padding: 8px 16px;
                color: white;
                font-weight: 500;
                font-size: 0.9rem;
                transition: all 0.3s ease;
                text-decoration: none;
            }
            
            .btn-view:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(108, 92, 231, 0.4);
                color: white;
            }
            
            .nav-buttons {
                text-align: center;
                margin-bottom: 20px;
            }
            
            .nav-btn {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 12px;
                padding: 10px 20px;
                margin: 5px;
                text-decoration: none;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            
            .nav-btn:hover {
                background: rgba(255, 255, 255, 0.3);
                color: white;
                transform: translateY(-2px);
            }
            
            .nav-btn.active {
                background: white;
                color: #d63031;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="dashboard-header">
                <div class="d-flex justify-content-between align-items-center">
                    <h3><i class="bi bi-exclamation-triangle me-3"></i>پنل ادمین تخلفات</h3>
                    <a href="/admin/logout" class="btn btn-outline-danger">
                        <i class="bi bi-box-arrow-right me-2"></i>خروج
                    </a>
                </div>
            </div>
            
            <div class="nav-buttons">
                <a href="/admin/panel" class="nav-btn">
                    <i class="bi bi-speedometer2 me-2"></i>داشبورد اصلی
                </a>
                <a href="/admin/violations" class="nav-btn active">
                    <i class="bi bi-exclamation-triangle me-2"></i>مدیریت تخلفات
                </a>
            </div>
            
            <div class="violation-card">
                <h5 class="violation-header">
                    <i class="bi bi-list-check me-2"></i>لیست گزارش‌های تخلف
                </h5>
                <div class="table-responsive">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>شناسه</th>
                                <th>سوال</th>
                                <th>کاربر</th>
                                <th>دپارتمان</th>
                                <th>گزارش‌دهنده</th>
                                <th>تاریخ گزارش</th>
                                <th>وضعیت</th>
                                <th>اقدام انجام شده</th>
                                <th>عملیات</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for vr in violation_reports %}
                            <tr>
                                <td><strong>#{{ vr[1] }}</strong></td>
                                <td>
                                    <div style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="{{ vr[7] }}">
                                        {{ vr[7] }}
                                    </div>
                                </td>
                                <td>
                                    <div><strong>{{ vr[8] }}</strong></div>
                                    <small class="text-muted">{{ vr[9] }}</small>
                                </td>
                                <td>{{ vr[10] }}</td>
                                <td>{{ vr[2] }}</td>
                                <td style="font-size: 0.8rem;">{{ vr[3] }}</td>
                                <td>
                                    {% if vr[4] == 'pending' %}
                                        <span class="status-pending">در انتظار بررسی</span>
                                    {% else %}
                                        <span class="status-resolved">بررسی شده</span>
                                    {% endif %}
                                </td>
                                <td>
                                    {% if vr[5] %}
                                        <span class="badge bg-info">{{ vr[5] }}</span>
                                        <br><small class="text-muted">{{ vr[6] }}</small>
                                    {% else %}
                                        <span class="text-muted">-</span>
                                    {% endif %}
                                </td>
                                <td>
                                    <a href="/admin/violation/{{ vr[0] }}" class="btn-view">
                                        <i class="bi bi-eye me-1"></i>مشاهده جزئیات
                                    </a>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''
    
    return render_template_string(html, violation_reports=violation_reports)

@app.route('/admin/violation/<int:violation_id>', methods=['GET', 'POST'])
@admin_required
def violation_detail(violation_id):
    conn = sqlite3.connect('system.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        action = request.form['action']
        admin_notes = request.form.get('admin_notes', '').strip()
        current_time = datetime.now()
        
        # Get violation report details
        c.execute("""SELECT vr.question_id, vr.reported_by_manager_phone, q.user_id, d.name
                     FROM violation_reports vr 
                     JOIN questions q ON vr.question_id = q.id
                     JOIN departments d ON q.department_id = d.id
                     WHERE vr.id = ?""", (violation_id,))
        violation_data = c.fetchone()
        
        if not violation_data:
            flash('گزارش تخلف پیدا نشد', 'error')
            return redirect(url_for('violation_admin_panel'))
        
        question_id, manager_phone, user_id, department_name = violation_data
        
        # Get user phone for SMS
        c.execute("SELECT phone FROM users WHERE id = ?", (user_id,))
        user_phone = c.fetchone()[0]
        
        if action == 'solve':
            # Mark question as solved and calculate final reward
            c.execute("SELECT paused_reward FROM questions WHERE id = ?", (question_id,))
            paused_reward = c.fetchone()[0] or 0
            
            c.execute("""UPDATE questions SET 
                         status = 'answered',
                         reward_amount = ?,
                         user_feedback = 'solved',
                         violation_status = 'resolved'
                         WHERE id = ?""", (paused_reward, question_id))
            
            # Update violation report
            c.execute("""UPDATE violation_reports SET 
                         status = 'resolved',
                         admin_action = 'solved',
                         admin_action_at = ?,
                         notes = ?
                         WHERE id = ?""", (current_time, admin_notes, violation_id))
            
            # Send SMS to manager
            sms_base = f"ادمین اقدام به حل سوال شماره {question_id} کرده است. پاداش نهایی محاسبه شد."
            sms_text = f"{sms_base}\n\n📝 یادداشت ادمین: {admin_notes}" if admin_notes else sms_base
            send_sms(manager_phone, sms_text)
            
            flash('سوال به عنوان حل شده علامت‌گذاری شد', 'success')
            
        elif action == 'waiting':
            # Apply waiting logic
            c.execute("""SELECT waiting_count, paused_reward, penalty_multiplier 
                         FROM questions WHERE id = ?""", (question_id,))
            question_data = c.fetchone()
            waiting_count, paused_reward, penalty_multiplier = question_data
            
            waiting_count = (waiting_count or 0) + 1
            if waiting_count == 1:
                new_hours = 72
            else:
                new_hours = 72 / (2 ** (waiting_count - 1))
            
            new_deadline = current_time + timedelta(hours=new_hours)
            new_penalty_multiplier = (penalty_multiplier or 3) + 1
            
            c.execute("""UPDATE questions SET 
                         status = 'pending',
                         user_feedback = 'waiting',
                         fixed_reward = ?,
                         waiting_deadline = ?,
                         waiting_count = ?,
                         penalty_multiplier = ?,
                         violation_status = 'resolved',
                         paused_at = NULL,
                         paused_timer_remaining = NULL,
                         paused_reward = NULL
                         WHERE id = ?""", 
                      (paused_reward, new_deadline.isoformat(), waiting_count, new_penalty_multiplier, question_id))
            
            # Update violation report
            c.execute("""UPDATE violation_reports SET 
                         status = 'resolved',
                         admin_action = 'waiting',
                         admin_action_at = ?,
                         notes = ?
                         WHERE id = ?""", (current_time, admin_notes, violation_id))
            
            # Send SMS to manager
            sms_base = f"ادمین سوال شماره {question_id} را به حالت انتظار تغییر داده است. زمان جدید تمدید شد."
            sms_text = f"{sms_base}\n\n📝 یادداشت ادمین: {admin_notes}" if admin_notes else sms_base
            send_sms(manager_phone, sms_text)
            
            flash('سوال به حالت انتظار تغییر کرد', 'success')
            
        elif action == 'end':
            # End request without reward/penalty
            c.execute("""UPDATE questions SET 
                         status = 'answered',
                         reward_amount = 0,
                         user_feedback = 'end',
                         violation_status = 'resolved'
                         WHERE id = ?""", (question_id,))
            
            # Update violation report
            c.execute("""UPDATE violation_reports SET 
                         status = 'resolved',
                         admin_action = 'end_request',
                         admin_action_at = ?,
                         notes = ?
                         WHERE id = ?""", (current_time, admin_notes, violation_id))
            
            # Send SMS to manager
            sms_base = f"ادمین درخواست سوال شماره {question_id} را بدون پاداش یا جریمه پایان داده است."
            sms_text = f"{sms_base}\n\n📝 یادداشت ادمین: {admin_notes}" if admin_notes else sms_base
            send_sms(manager_phone, sms_text)
            
            flash('درخواست پایان یافت', 'success')
            
        elif action == 'invalid':
            # Resume normal timer and reward calculation from paused state
            c.execute("""SELECT paused_timer_remaining, paused_reward, created_at, timer_hours, fixed_reward, penalty_multiplier
                         FROM questions WHERE id = ?""", (question_id,))
            question_data = c.fetchone()
            if len(question_data) == 5:
                # Backward compatibility if penalty_multiplier doesn't exist
                paused_timer_remaining, paused_reward, created_at_str, timer_hours, fixed_reward = question_data
                penalty_multiplier = 3
            else:
                paused_timer_remaining, paused_reward, created_at_str, timer_hours, fixed_reward, penalty_multiplier = question_data
            
            # Calculate new virtual created_at to resume from paused state
            if paused_timer_remaining is not None and paused_timer_remaining > 0:
                # Calculate new created_at that would give us the paused_timer_remaining
                # new_created_at = current_time - (timer_hours * 3600 - paused_timer_remaining)
                total_seconds = timer_hours * 3600
                elapsed_seconds = total_seconds - paused_timer_remaining
                new_created_at = current_time - timedelta(seconds=elapsed_seconds)
                
                c.execute("""UPDATE questions SET 
                             created_at = ?,
                             fixed_reward = ?,
                             violation_status = 'resolved',
                             paused_at = NULL,
                             paused_timer_remaining = NULL,
                             paused_reward = NULL,
                             penalty_multiplier = ?
                             WHERE id = ?""", 
                          (new_created_at.strftime("%Y-%m-%d %H:%M:%S.%f"), 
                           paused_reward or fixed_reward, 
                           penalty_multiplier or 3, 
                           question_id))
            else:
                # No paused timer, just clear the paused state
                c.execute("""UPDATE questions SET 
                             violation_status = 'resolved',
                             paused_at = NULL,
                             paused_timer_remaining = NULL,
                             paused_reward = NULL,
                             fixed_reward = ?,
                             penalty_multiplier = ?
                             WHERE id = ?""", 
                          (paused_reward or fixed_reward, penalty_multiplier or 3, question_id))
            
            # Update violation report
            c.execute("""UPDATE violation_reports SET 
                         status = 'resolved',
                         admin_action = 'invalid_report',
                         admin_action_at = ?,
                         notes = ?
                         WHERE id = ?""", (current_time, admin_notes, violation_id))
            
            # Send SMS to manager
            sms_base = f"ادمین گزارش تخلف سوال شماره {question_id} را نامعتبر تشخیص داده است. زمان‌بندی عادی ادامه می‌یابد."
            sms_text = f"{sms_base}\n\n📝 یادداشت ادمین: {admin_notes}" if admin_notes else sms_base
            send_sms(manager_phone, sms_text)
            
            flash('گزارش نامعتبر تشخیص داده شد و زمان‌بندی عادی ادامه یافت', 'success')
        
        conn.commit()
        conn.close()
        return redirect(url_for('violation_detail', violation_id=violation_id))
    
    # GET request - show violation details
    c.execute("""
        SELECT vr.id, vr.question_id, vr.reported_by_manager_phone, vr.reported_at, 
               vr.status, vr.admin_action, vr.admin_action_at, vr.notes,
               q.question_text, q.status as question_status, q.created_at,
               u.name, u.phone, d.name, vr.manager_notes
        FROM violation_reports vr
        JOIN questions q ON vr.question_id = q.id
        JOIN users u ON q.user_id = u.id
        JOIN departments d ON q.department_id = d.id
        WHERE vr.id = ?
    """, (violation_id,))
    violation_report = c.fetchone()
    
    if not violation_report:
        flash('گزارش تخلف پیدا نشد', 'error')
        conn.close()
        return redirect(url_for('violation_admin_panel'))
    
    # Get all answers for this violation
    c.execute("""
        SELECT answer_text, answered_at, is_primary_answer
        FROM violation_report_answers
        WHERE violation_report_id = ?
        ORDER BY answered_at ASC
    """, (violation_id,))
    violation_answers = c.fetchall()
    
    conn.close()
    
    html = '''
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>جزئیات گزارش تخلف</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');
            
            body { 
                direction: rtl; 
                background: linear-gradient(135deg, #d63031 0%, #e17055 100%);
                font-family: 'Vazirmatn', sans-serif;
                min-height: 100vh;
                padding: 20px 0;
            }
            
            .detail-card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border: none;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                margin-bottom: 30px;
                overflow: hidden;
            }
            
            .detail-header {
                background: linear-gradient(135deg, #d63031 0%, #e17055 100%);
                color: white;
                padding: 25px;
                font-weight: 600;
                font-size: 1.3rem;
            }
            
            .info-section {
                padding: 25px;
                border-bottom: 1px solid #e2e8f0;
            }
            
            .info-row {
                display: flex;
                justify-content: space-between;
                margin-bottom: 15px;
                padding: 10px 0;
            }
            
            .info-label {
                font-weight: 600;
                color: #4a5568;
                flex: 0 0 30%;
            }
            
            .info-value {
                flex: 1;
                text-align: left;
                color: #2d3748;
            }
            
            .answer-item {
                background: rgba(108, 92, 231, 0.05);
                border: 1px solid rgba(108, 92, 231, 0.2);
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 15px;
                position: relative;
            }
            
            .answer-primary {
                background: rgba(0, 184, 148, 0.05);
                border-color: rgba(0, 184, 148, 0.3);
            }
            
            .answer-additional {
                background: rgba(253, 203, 110, 0.05);
                border-color: rgba(253, 203, 110, 0.3);
            }
            
            .answer-badge {
                position: absolute;
                top: -8px;
                right: 15px;
                padding: 4px 12px;
                border-radius: 15px;
                font-size: 0.8rem;
                font-weight: 600;
            }
            
            .badge-primary {
                background: linear-gradient(135deg, #00b894 0%, #55efc4 100%);
                color: white;
            }
            
            .badge-additional {
                background: linear-gradient(135deg, #fdcb6e 0%, #f39c12 100%);
                color: white;
            }
            
            .action-buttons {
                padding: 25px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
            }
            
            .action-btn {
                border: none;
                border-radius: 12px;
                padding: 15px 20px;
                font-weight: 600;
                font-size: 1rem;
                transition: all 0.3s ease;
                text-decoration: none;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
            }
            
            .btn-solve {
                background: linear-gradient(135deg, #00b894 0%, #55efc4 100%);
                color: white;
            }
            
            .btn-waiting {
                background: linear-gradient(135deg, #fdcb6e 0%, #f39c12 100%);
                color: white;
            }
            
            .btn-end {
                background: linear-gradient(135deg, #e17055 0%, #d63031 100%);
                color: white;
            }
            
            .btn-invalid {
                background: linear-gradient(135deg, #636e72 0%, #2d3436 100%);
                color: white;
            }
            
            .action-btn:hover {
                transform: translateY(-3px);
                box-shadow: 0 6px 20px rgba(0,0,0,0.3);
                color: white;
            }
            
            .nav-buttons {
                text-align: center;
                margin-bottom: 20px;
            }
            
            .nav-btn {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 12px;
                padding: 10px 20px;
                margin: 5px;
                text-decoration: none;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            
            .nav-btn:hover {
                background: rgba(255, 255, 255, 0.3);
                color: white;
                transform: translateY(-2px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="nav-buttons">
                <a href="/admin/violations" class="nav-btn">
                    <i class="bi bi-arrow-right me-2"></i>بازگشت به لیست تخلفات
                </a>
                <a href="/admin/panel" class="nav-btn">
                    <i class="bi bi-speedometer2 me-2"></i>داشبورد اصلی
                </a>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }} alert-dismissible fade show" role="alert">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <div class="detail-card">
                <div class="detail-header">
                    <i class="bi bi-exclamation-triangle me-3"></i>جزئیات گزارش تخلف #{{ violation_report[1] }}
                </div>
                
                <div class="info-section">
                    <div class="info-row">
                        <span class="info-label"><i class="bi bi-question-circle me-2"></i>متن سوال:</span>
                        <span class="info-value">{{ violation_report[8] }}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label"><i class="bi bi-person me-2"></i>کاربر:</span>
                        <span class="info-value">{{ violation_report[11] }} ({{ violation_report[12] }})</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label"><i class="bi bi-building me-2"></i>دپارتمان:</span>
                        <span class="info-value">{{ violation_report[13] }}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label"><i class="bi bi-phone me-2"></i>گزارش‌دهنده:</span>
                        <span class="info-value">{{ violation_report[2] }}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label"><i class="bi bi-calendar me-2"></i>تاریخ گزارش:</span>
                        <span class="info-value">{{ violation_report[3] }}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label"><i class="bi bi-clock me-2"></i>تاریخ ایجاد سوال:</span>
                        <span class="info-value">{{ violation_report[10] }}</span>
                    </div>
                </div>
                
                {% if violation_report[14] %}
                <div class="info-section">
                    <h6 class="mb-3"><i class="bi bi-sticky me-2"></i>یادداشت مدیر:</h6>
                    <div class="p-3" style="background: rgba(240, 147, 251, 0.1); border-radius: 12px; border: 1px solid rgba(240, 147, 251, 0.3); font-weight: 500; line-height: 1.6;">
                        {{ violation_report[14] }}
                    </div>
                </div>
                {% endif %}
                
                {% if violation_answers %}
                <div class="info-section">
                    <h6 class="mb-3"><i class="bi bi-chat-dots me-2"></i>پاسخ‌های مدیر:</h6>
                    {% for answer in violation_answers %}
                    <div class="answer-item {{ 'answer-primary' if answer[2] else 'answer-additional' }}">
                        <div class="answer-badge {{ 'badge-primary' if answer[2] else 'badge-additional' }}">
                            {{ 'پاسخ اولیه' if answer[2] else 'پاسخ اضافی' }}
                        </div>
                        <div class="mt-2 mb-2" style="font-weight: 500;">{{ answer[0] }}</div>
                        <small class="text-muted">
                            <i class="bi bi-clock me-1"></i>{{ answer[1] }}
                        </small>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
                
                {% if violation_report[4] == 'pending' %}
                <div class="info-section">
                    <h6 class="mb-3"><i class="bi bi-chat-text me-2"></i>اقدام ادمین اصلی:</h6>
                    <form method="post">
                        <div class="mb-3">
                            <label class="form-label fw-semibold">یادداشت ادمین (اختیاری):</label>
                            <textarea name="admin_notes" class="form-control" rows="3" 
                                    placeholder="توضیحات، دلیل تصمیم یا راهنمایی برای مدیر..."
                                    style="border-radius: 12px; border: 2px solid #e2e8f0;"></textarea>
                        </div>
                        <div class="action-buttons">
                            <button type="submit" name="action" value="solve" class="action-btn btn-solve" onclick="return confirm('آیا از حل کردن این سوال مطمئن هستید؟')">
                                <i class="bi bi-check-circle"></i>حل مشکل
                            </button>
                            <button type="submit" name="action" value="waiting" class="action-btn btn-waiting" onclick="return confirm('آیا از تمدید زمان این سوال مطمئن هستید؟')">
                                <i class="bi bi-hourglass-split"></i>در انتظار
                            </button>
                            <button type="submit" name="action" value="end" class="action-btn btn-end" onclick="return confirm('آیا از پایان دادن به این درخواست مطمئن هستید؟')">
                                <i class="bi bi-x-circle"></i>پایان درخواست
                            </button>
                            <button type="submit" name="action" value="invalid" class="action-btn btn-invalid" onclick="return confirm('آیا از نامعتبر بودن این گزارش مطمئن هستید؟')">
                                <i class="bi bi-shield-x"></i>گزارش نامعتبر
                            </button>
                        </div>
                    </form>
                </div>
                {% else %}
                <div class="info-section text-center">
                    <div class="alert alert-info">
                        <i class="bi bi-info-circle me-2"></i>
                        این گزارش قبلاً بررسی شده است. 
                        اقدام انجام شده: <strong>{{ violation_report[5] }}</strong>
                        در تاریخ {{ violation_report[6] }}
                    </div>
                </div>
                {% endif %}
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''
    
    return render_template_string(html, violation_report=violation_report, violation_answers=violation_answers)

if __name__ == '__main__':
    app.run(debug=True)
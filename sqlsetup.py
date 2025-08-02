import sqlite3

conn = sqlite3.connect('system.db')
c = conn.cursor()

# جدول کاربران
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT
)
''')

# جدول دپارتمان‌ها
c.execute('''
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    manager_phone TEXT
)
''')

# جدول سوالات
c.execute('''
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    department_id INTEGER,
    question_text TEXT,
    status TEXT,
    created_at DATETIME,
    answered_at DATETIME,
    reward_amount INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(department_id) REFERENCES departments(id)
)
''')

# جدول تنظیمات کلی
c.execute('''
CREATE TABLE IF NOT EXISTS admin_settings (
    id INTEGER PRIMARY KEY,
    base_reward_amount INTEGER,
    base_timer_hours INTEGER,
    penalty_amount INTEGER
)
''')

# مقدار پیش‌فرض برای تنظیمات
c.execute('INSERT OR IGNORE INTO admin_settings (id, base_reward_amount, base_timer_hours, penalty_amount) VALUES (1, 200000, 2, 0)')

conn.commit()
conn.close()

print("✅ دیتابیس ساخته شد")

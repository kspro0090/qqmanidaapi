import sqlite3

conn = sqlite3.connect('system.db')
c = conn.cursor()

# اضافه کردن ستون timer_hours (اگر وجود نداشت)
try:
    c.execute("ALTER TABLE questions ADD COLUMN timer_hours INTEGER DEFAULT 2")
    print("✅ ستون timer_hours اضافه شد.")
except:
    print("ℹ️ ستون timer_hours از قبل وجود دارد.")

# آپدیت سوالات قدیمی به 2 ساعت
c.execute("UPDATE questions SET timer_hours = 2 WHERE timer_hours IS NULL")

conn.commit()
conn.close()

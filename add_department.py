import sqlite3

conn = sqlite3.connect('system.db')
c = conn.cursor()

# مثال: اضافه کردن واحد فروش
c.execute("INSERT INTO departments (name, manager_phone) VALUES (?, ?)", ("واحد فروش", "09121234567"))

# مثال: اضافه کردن واحد پشتیبانی
c.execute("INSERT INTO departments (name, manager_phone) VALUES (?, ?)", ("واحد پشتیبانی", "09129876543"))

conn.commit()
conn.close()

print("واحدها اضافه شدند ✅")

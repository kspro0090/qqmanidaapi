import requests

# 🔐 مشخصات sms.ir
USERNAME = "9195134535"
PASSWORD = "an5zQbIoXsdwiPUxrrMXySa6K3EJhekRrhz3IySVwl6HuSCy"
LINE_NUMBER = "30005675123456"

def send_sms(phone, message):
    url = "https://api.sms.ir/v1/send"
    params = {
        "username": USERNAME,
        "password": PASSWORD,
        "line": LINE_NUMBER,
        "mobile": phone,
        "text": message
    }
    try:
        print(f"🟢 در حال ارسال به {phone}")
        print("🔹 پارامترها:", params)

        response = requests.get(url, params=params)
        print("🔹 کد وضعیت HTTP:", response.status_code)
        print("🔹 متن پاسخ:", response.text)

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == 1:
                print(f"✅ پیامک ارسال شد — شناسه: {result['data']['messageId']}")
            else:
                print(f"❌ خطای API: {result.get('message', 'نامشخص')}")
        else:
            print(f"❌ خطای HTTP: {response.status_code}")
    except Exception as e:
        print(f"❌ خطای شبکه یا سیستم: {e}")

# تست
if __name__ == "__main__":
    # شماره تستی رو اینجا بذار (با 09 شروع کن یا 98)
    phone_number = "09195134535"
    test_message = "این یک پیام تستی از سیستم شماست 🌟"

    send_sms(phone_number, test_message)

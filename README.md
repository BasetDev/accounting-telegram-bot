# 📊 Hesab - ربات حسابداری تلگرام

<div dir="rtl">

# ربات حسابداری کسب‌وکار برای تلگرام

یک ربات حرفه‌ای حسابداری برای کسب‌وکارهای کوچک و متوسط که به شما امکان مدیریت درآمدها، هزینه‌ها، بدهی‌ها، طلب‌ها، مشتریان و گزارش‌های مالی را مستقیماً از طریق تلگرام می‌دهد.

## قابلیت‌های اصلی

- ✅ **ثبت درآمد** - ثبت انواع درآمد با دسته‌بندی و توضیحات
- ✅ **ثبت هزینه** - ثبت انواع هزینه با دسته‌بندی و توضیحات
- ✅ **ثبت بدهی** - ثبت بدهی‌ها با تاریخ سررسید
- ✅ **ثبت طلب** - ثبت مطالبات با تاریخ سررسید
- ✅ **مدیریت مشتریان** - افزودن، ویرایش، حذف و جستجوی مشتریان
- ✅ **داشبورد مالی** - نمایش خلاصه وضعیت مالی
- ✅ **گزارش‌های مالی** - گزارش روزانه، هفتگی، ماهانه و سالانه
- ✅ **خروجی Excel و PDF** - دریافت گزارش‌ها به صورت فایل
- ✅ **پشتیبان‌گیری** - ایجاد و بازیابی پشتیبان از دیتابیس
- ✅ **سیستم جستجو** - جستجو بر اساس نام، تاریخ، مبلغ و دسته‌بندی

## ویژگی‌های فنی

- **زبان:** فارسی (کاملاً راست‌چین)
- **تاریخ:** شمسی (جلالی)
- **منطقه زمانی:** آسیا/تهران (ایران)
- **دیتابیس:** SQLite (با قابلیت ارتقا به PostgreSQL)
- **چارچوب:** aiogram (Telegram Bot API)
- **معماری:** ماژولار و تمیز (Clean Architecture)

</div>

## 📋 فهرست مطالب

1. [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
2. [پیکربندی](#پیکربندی)
3. [اجرا](#اجرا)
4. [ساختار پروژه](#ساختار-پروژه)
5. [API و دیتابیس](#api-و-دیتابیس)
6. [استقرار](#استقرار)
7. [عیب‌یابی](#عیب‌یابی)

---

## نصب و راه‌اندازی

### پیش‌نیازها

- Python 3.13 یا بالاتر
- pip (مدیریت بسته‌های پایتون)
- توکن ربات تلگرام (از @BotFather)

### نصب محلی

```bash
# 1. کلون کردن مخزن
git clone https://github.com/yourusername/hesab.git
cd hesab

# 2. نصب وابستگی‌ها
pip install -r requirements.txt

# 3. تنظیم فایل .env
cp .env.example .env
# فایل .env را ویرایش کرده و توکن ربات را وارد کنید
```

### نصب با Docker

```bash
# ساختイメージ
docker build -t hesab-bot .

# اجرای کانتینر
docker run -d --name hesab-bot \
  -v $(pwd)/data:/app/hesab/data \
  -v $(pwd)/logs:/app/hesab/logs \
  -v $(pwd)/backups:/app/hesab/backups \
  -v $(pwd)/exports:/app/hesab/exports \
  -v $(pwd)/.env:/app/.env \
  hesab-bot
```

یا با Docker Compose:

```yaml
version: '3.8'
services:
  hesab-bot:
    build: .
    volumes:
      - ./data:/app/hesab/data
      - ./logs:/app/hesab/logs
      - ./backups:/app/hesab/backups
      - ./exports:/app/hesab/exports
      - ./.env:/app/.env
    restart: unless-stopped
```

---

## پیکربندی

### فایل `.env`

```ini
# توکن ربات تلگرام (اجباری)
BOT_TOKEN=your_bot_token_here

# شناسه مدیر (اجباری)
ADMIN_ID=123456789

# مسیر دیتابیس (اختیاری)
DATABASE_URL=sqlite:///data/hesab.db

# تنظیمات منطقه زمانی (اختیاری)
TIMEZONE=Asia/Tehran
```

### دریافت توکن ربات

1. در تلگرام به [@BotFather](https://t.me/BotFather) مراجعه کنید
2. دستور `/newbot` را ارسال کنید
3. نام ربات را وارد کنید
4. توکن دریافت شده را در فایل `.env` قرار دهید

### دریافت شناسه مدیر

1. در تلگرام به [@userinfobot](https://t.me/userinfobot) مراجعه کنید
2. دستور `/start` را ارسال کنید
3. شناسه عددی شما نمایش داده می‌شود

---

## اجرا

### اجرای مستقیم

```bash
cd hesab
python main.py
```

### اجرا در پس‌زمینه (Linux)

```bash
nohup python hesab/main.py > hesab.log 2>&1 &
```

### اجرا با systemd

```ini
[Unit]
Description=Hesab Telegram Bot
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/hesab
ExecStart=/usr/bin/python3 /opt/hesab/hesab/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### اجرا با screen

```bash
screen -S hesab
cd hesab
python main.py
# Ctrl+A, D برای خروج از screen
```

---

## ساختار پروژه

```
hesab/
├── hesab/                    # پوشه اصلی پروژه
│   ├── main.py              # نقطه ورود برنامه
│   └── app/                 # ماژول‌های برنامه
│       ├── config.py        # تنظیمات و پیکربندی
│       ├── database/        # لایه دیتابیس
│       │   ├── models.py    # مدل‌های SQLAlchemy
│       │   └── repository.py # لایه دسترسی به داده
│       ├── handlers/        # مدیریت کننده‌های تلگرام
│       │   └── main_handler.py # تمام هندلرهای ربات
│       ├── keyboards/       # کیبوردهای تلگرام
│       │   └── markups.py   # تعریف کیبوردها
│       ├── services/        # سرویس‌های برنامه
│       │   └── export_service.py # خروجی Excel/PDF
│       ├── utils/           # ابزارهای کمکی
│       │   ├── jdatetime_helper.py # تاریخ و زمان شمسی
│       │   ├── messages.py  # متن‌های فارسی
│       │   └── logger.py    # سیستم ثبت وقایع
│       └── middleware/      # میدلورهای ربات
├── data/                    # فایل‌های دیتابیس
├── logs/                    # فایل‌های لاگ
├── backups/                 # پشتیبان‌ها
├── exports/                 # فایل‌های خروجی
├── .env                     # تنظیمات محیطی
├── Dockerfile               # کانتینر Docker
├── requirements.txt         # وابستگی‌ها
└── README.md               # مستندات
```

### توضیح ماژول‌ها

| ماژول | وظیفه |
|-------|--------|
| `config.py` | بارگذاری تنظیمات از `.env` |
| `models.py` | تعریف جداول دیتابیس با SQLAlchemy |
| `repository.py` | عملیات CRUD روی دیتابیس |
| `main_handler.py` | مدیریت پیام‌ها و دستورات تلگرام |
| `markups.py` | ساخت کیبوردهای حرفه‌ای |
| `export_service.py` | ایجاد فایل‌های Excel و PDF |
| `jdatetime_helper.py` | توابع تاریخ و زمان شمسی |
| `messages.py` | ذخیره متن‌های فارسی |
| `logger.py` | ثبت وقایع سیستم |

---

## API و دیتابیس

### مدل‌های اصلی

#### User
- `id` - شناسه یکتا
- `telegram_id` - شناسه تلگرام
- `username` - نام کاربری
- `is_admin` - دسترسی مدیریت
- `is_active` - فعال بودن

#### Transaction
- `id` - شناسه تراکنش
- `user_id` - شناسه کاربر
- `transaction_type` - نوع (درآمد/هزینه/بدهی/طلب)
- `amount` - مبلغ
- `description` - توضیحات
- `category` - دسته‌بندی
- `jalali_date` - تاریخ شمسی
- `due_jalali_date` - تاریخ سررسید
- `is_settled` - وضعیت تسویه

#### Customer
- `id` - شناسه مشتری
- `full_name` - نام کامل
- `phone` - شماره تلفن
- `address` - آدرس
- `total_debt` - مجموع بدهی
- `total_receivable` - مجموع طلب

## استقرار

### Railway

1. پروژه را به GitHub Push کنید
2. در [Railway](https://railway.app) پروژه جدید ایجاد کنید
3. Repository خود را متصل کنید
4. متغیرهای محیطی را تنظیم کنید:
   - `BOT_TOKEN`
   - `ADMIN_ID`
5. Railway به صورت خودکار Dockerfile را تشخیص می‌دهد

### Linux VPS

```bash
# نصب وابستگی‌ها
sudo apt update
sudo apt install -y python3 python3-pip git

# دریافت کد
git clone https://github.com/yourusername/hesab.git
cd hesab

# نصب
pip install -r requirements.txt

# تنظیم .env
nano .env

# راه‌اندازی با systemd
sudo tee /etc/systemd/system/hesab.service <<EOF
[Unit]
Description=Hesab Bot
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(which python3) hesab/main.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable --now hesab
```

---

## عیب‌یابی

### مشکل: توکن نامعتبر
```bash
# بررسی کنید توکن در .env صحیح است
grep BOT_TOKEN .env
# توکن را از @BotFather دوباره دریافت کنید
```

### مشکل: دسترسی به دیتابیس
```bash
# بررسی دایرکتوری data
ls -la data/
# اگر وجود ندارد، ایجاد کنید:
mkdir -p data
```

### مشکل: فونت فارسی در PDF
```bash
# نصب فونت‌های فارسی
sudo apt install fonts-farsi fonts-vazir fonts-noto-arabic
```

### لاگ‌ها
```bash
# مشاهده لاگ‌ها
tail -f logs/hesab.log

# یا با Journalctl (اگر systemd استفاده می‌کنید)
journalctl -u hesab -f
```

---

## توسعه‌دهندگان

### اضافه کردن قابلیت جدید

1. مدل جدید را در `models.py` تعریف کنید
2. Repository مربوطه را در `repository.py` ایجاد کنید
3. هندلر جدید را در `main_handler.py` بنویسید
4. کیبوردهای مورد نیاز را در `markups.py` اضافه کنید

### تست خط فرمان

```bash
# تست اتصال به دیتابیس
python -c "from app.database.models import init_database; engine, Session = init_database(); print('OK')"

# تست تاریخ شمسی
python -c "from app.utils.jdatetime_helper import get_jalali_full; print(get_jalali_full())"
```

---

## مجوز

این پروژه تحت مجوز MIT منتشر شده است.

---

## پشتیبانی

برای گزارش مشکلات یا پیشنهادات:
- ایجاد Issue در GitHub
- تماس با توسعه‌دهنده

---

<div dir="rtl">
ساخته شده با ❤️ برای کسب‌وکارهای ایرانی
</div>
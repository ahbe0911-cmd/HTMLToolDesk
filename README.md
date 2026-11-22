# میزکار ابزارهای HTML – HTMLToolDesk

برنامهٔ ویندوزی **فارسی و راست‌به‌چپ** مبتنی بر **Python + PyQt6 + PyQt6-WebEngine** برای سازمان‌دهی و اجرای فایل‌های محلی HTML.

## امکانات

- سایدبار عمودی و فشرده در سمت راست (پیش‌فرض حدود ۲۵۲ پیکسل)، با کارت‌های رنگی شاد و قاب‌دار، آیکون‌های SVG، جستجوی فارسی، قابلیت تغییر اندازه و جمع‌کردن.
- اضافه‌کردن ابزار، ویرایش عنوان/توضیح/مسیر، حذف از فهرست **بدون حذف فایل اصلی**.
- مرتب‌سازی با کشیدن آیتم‌ها و گزینه‌های راست‌کلیک «بالا/پایین».
- Chromium داخلی با JavaScript، CSS، فایل‌های جانبی محلی و LocalStorage، بدون تب یا پنجره اضافی.
- **شروع سریع و بدون راه‌اندازی خودکار Chromium**؛ WebEngine فقط زمانی ایجاد می‌شود که کاربر روی یک ابزار HTML کلیک کند. حداکثر دو ابزار اخیراً استفاده‌شده در حافظه نگه داشته می‌شوند تا مصرف RAM کنترل شود.
- آیکون‌های SVG برداری برای هر ابزار و نوار ابزار؛ فهرست عمودی و ثابت سمت راست.
- تم روشن/تاریک، خوش‌آمدگویی، نوار ابزار کوتاه با دکمه‌های Reload و بازکردن HTML در مرورگر پیش‌فرض.
- **بزرگ‌نمایی و کوچک‌نمایی HTML** از نوار بالا با دکمه‌های + و − (هر بار ۱۰٪)، کلیک روی درصد برای بازگشت به ۱۰۰٪؛ بازه ۵۰٪ تا ۲۵۰٪. میان‌برها: Ctrl++ / Ctrl+=، Ctrl+-، Ctrl+0. مقدار زوم برای هر ابزار در طول اجرای برنامه مستقل می‌ماند.
- نمایش **تاریخ شمسی امروز** با نام روز و ماه فارسی و ارقام فارسی در نوار بالا؛ تاریخ از ساعت محلی رایانه خوانده شده و در صورت تغییر روز به‌روزرسانی می‌شود.
- صفحه آغازین ساده، بدون بازکردن خودکار HTML، با پیام **«روی ابزار موردنظر در ستون سمت راست کلیک کنید»** و فلش راهنما.
- **بازیابی خودکار داده‌های HTML بعد از بازکردن مجدد برنامه:** پروفایل WebEngine روی دیسک دائمی است و یک نسخه بازیابی جدا برای LocalStorage و SessionStorage هر ابزار در مسیر کاربر ثبت می‌شود. ثبت نسخه تکمیلی هر ۵ ثانیه در زمان استفاده و هنگام بستن پنجره انجام می‌شود؛ تزریق نسخه بازیابی پیش از اجرای اسکریپت HTML صورت می‌گیرد.
- برنامه در ویندوز به صورت **Maximized** اجرا می‌شود (کل فضای قابل استفاده نمایشگر، بدون پوشاندن تسک‌بار).

- ذخیرهٔ اتمیک تنظیمات در `config.json` و پشتیبان‌گیری از تنظیمات خراب.
- **وزیرمتن (Vazirmatn)** در تمام عناصر خود برنامه؛ ساخت ویندوز در صورت غیبت یا خرابی فونت متوقف می‌شود. فایل‌های HTML افزوده‌شده، سبک/فونت CSS خودشان را حفظ می‌کنند.
- نمونهٔ HTML/CSS/JS برای بررسی ذخیره‌شدن داده‌های LocalStorage.

## ساختار پروژه

```text
HTMLToolDesk/
├── main.py
├── requirements.txt
├── HTMLToolDesk.spec
├── build_windows.bat
├── README.md
├── html_tooldesk/
│   ├── __init__.py
│   ├── models.py
│   ├── storage.py
│   ├── paths.py
│   ├── icons.py
│   ├── jalali.py
│   ├── tool_cards.py
│   ├── theme.py
│   ├── dialogs.py
│   └── window.py
├── assets/fonts/
│   ├── README.txt
│   └── Vazirmatn-Regular.ttf        ← پس از دانلود (اختیاری)
├── examples/
│   ├── sample.html
│   ├── styles.css
│   └── app.js
├── tests/test_storage.py
├── tests/test_jalali.py
├── tests/test_gui_smoke.py
├── scripts/download_vazirmatn.ps1
└── .github/workflows/build-windows.yml
```

## اجرای برنامه از سورس (ویندوز)

پیش‌نیاز: **Windows 10/11 64-bit** و **Python 3.12 x64**.

در پوشهٔ پروژه، PowerShell باز کنید:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\download_vazirmatn.ps1
python main.py
```

اگر PowerShell اجازهٔ فعال‌سازی محیط مجازی نداد، دستورات را بدون Activate اجرا کنید:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

برای آزمایش برنامه یک ابزار جدید با مسیر `examples/sample.html` اضافه کنید، یادداشت را ذخیره کنید، برنامه را ببندید و دوباره باز کنید.

## ساخت EXE (ویندوز)

**ساده‌ترین راه:** روی `build_windows.bat` دوبار کلیک کنید. وابستگی‌ها نصب، تست‌ها اجرا، فونت رسمی در صورت دسترسی دانلود و سپس فایل زیر ایجاد می‌شود:

```text
dist\HTMLToolDesk\HTMLToolDesk.exe
```

**راه دستی:** بعد از نصب وابستگی‌ها:

```powershell
python -m PyInstaller --clean --noconfirm HTMLToolDesk.spec
```

این فایل `.spec` سورس فونت و فایل‌های `assets` را بسته‌بندی می‌کند؛ importهای صریح WebEngine باعث می‌شوند PyInstaller hookهای باینری Qt WebEngine و subprocessهای لازم را شناسایی کند. این دستور را **در ویندوز** اجرا کنید؛ خروجی Linux به EXE ویندوز تبدیل نمی‌شود. خروجی جدید از نوع **onedir** است: اجرای آن سریع‌تر از بسته تک‌فایلی است؛ تمام فایل‌های پوشه `HTMLToolDesk` باید کنار فایل EXE باقی بمانند.

اگر برای عیب‌یابی به نسخهٔ پوشه‌ای نیاز دارید:

```powershell
python -m PyInstaller --noconfirm --clean --windowed --onedir --name HTMLToolDesk-debug --add-data "assets:assets" main.py
```

در PyInstaller جدید، جداکنندهٔ `--add-data` دو نقطه (`:`) است، حتی در ویندوز. برای ساخت معمولی، مسیر پیشنهادی **همان `.spec`** است.

## دریافت EXE از GitHub Actions بدون نصب پایتون روی سیستم شما

پروژه را در یک مخزن GitHub آپلود کنید و در تب **Actions**، workflow با نام **Build Windows EXE** را دستی اجرا کنید. بعد از موفقیت، از بخش **Artifacts** بستهٔ **HTMLToolDesk-Fast-Windows** را بگیرید. پس از استخراج ZIP، پوشه `HTMLToolDesk` را کامل نگه دارید و EXE را از درون همان پوشه اجرا کنید. اجرای workflow مستلزم فعال بودن GitHub Actions و دسترسی به مخزن است.

## محل داده‌ها

- `config.json` **همیشه** در مسیر پایدار `%LOCALAPPDATA%\HTMLToolDesk\config.json` ذخیره می‌شود؛ انتخاب ابزارها پس از بستن و بازکردن برنامه حفظ خواهد شد.
- اگر نسخه قبلی فایل `config.json` را کنار EXE ثبت کرده باشد، هنگام راه‌اندازی اول و در صورت نداشتن تنظیمات قبلی در AppData وارد می‌شود.
- داده‌های LocalStorage، کوکی‌ها و IndexedDB که خود WebEngine قادر به نگهداری‌شان است: `%LOCALAPPDATA%\HTMLToolDesk\web_profile` (کش در `web_cache`).
- نسخه بازیابی اضافه برای LocalStorage و SessionStorage: `%LOCALAPPDATA%\HTMLToolDesk\web_snapshots`. برای هر فایل ثبت‌شده یک فایل جدا با نام امن ساخته می‌شود. این نسخه محلی است و هرگز در GitHub قرار نمی‌گیرد.
- فایل HTML و فایل‌های CSS، JS، تصاویر و فونت‌های وابسته به **مکان اصلی خودشان** باقی می‌مانند. برنامه فایل‌های HTML کاربر را کپی نمی‌کند؛ اگر جابه‌جا شوند باید مسیرشان را از «ویرایش» اصلاح کرد.
- LocalStorage وابسته به origin هر فایل است. جابه‌جایی فایل به مسیر متفاوت، ممکن است داده‌های ذخیره‌شدهٔ قبلی آن صفحه را در آدرس جدید در دسترس نگذارد.
- توجه: نسخه بازیابی کمکی فقط **LocalStorage / SessionStorage** را پوشش می‌دهد؛ داده‌های **IndexedDB** به پروفایل پایدار Chromium متکی‌اند. اگر ابزار HTML اطلاعات را صرفاً در حافظه JavaScript نگه دارد و هرگز در مرورگر ذخیره نکند، هیچ برنامه‌ای بدون اصلاح همان HTML نمی‌تواند آن اطلاعات را بعد از بستن حفظ کند.
- برای پیشگیری از حذف تصادفی اطلاعات، پوشه `%LOCALAPPDATA%\HTMLToolDesk` را هنگام ارتقای برنامه پاک نکنید.

## نکات فنی و امنیتی

- HTML کاربر با JavaScript و مجوز دسترسی به فایل‌های محلی اجرا می‌شود. **فقط فایل‌های HTML مورداعتماد را اضافه کنید**. برای اجرای HTML ناشناس باید sandbox/محدودیت‌های دسترسی جداگانه در نظر گرفته شود.
- وب‌سایت‌هایی که به APIهای اختصاصی Chrome، افزونه‌ها، Service Worker یا یک سرور HTTP نیاز دارند، الزاماً با `file://` کار نمی‌کنند؛ برخی به سرور محلی نیاز خواهند داشت.
- مجموعهٔ PyQt6 با مجوزهای GPL/commercial و Qt WebEngine با تعهدات مجوزی خودش عرضه می‌شود؛ برای توزیع بستهٔ تجاری، مجوزها و noticeها را بررسی کنید.
- فونت Vazirmatn از [مخزن رسمی](https://github.com/rastikerdar/vazirmatn) و تحت SIL OFL 1.1 است. در بستهٔ سورس اولیه فونت باینری قرار داده نشده؛ اسکریپت دانلود آن را به مسیر استاندارد اضافه می‌کند.

## تست‌ها

```powershell
python -m unittest discover -s tests -v
```

تست‌ها شامل ماندگاری LocalStorage/SessionStorage در نسخه بازیابی، عدم راه‌اندازی Chromium در شروع و بازدید مجدد از ابزارهای کش‌شده هستند. همچنین `scripts/verify_webengine_persistence.py` در Windows CI دو اجرای مستقل از مرورگر را آزمایش می‌کند. اجرای واقعی روی رایانه کاربر همچنان ضروری است.
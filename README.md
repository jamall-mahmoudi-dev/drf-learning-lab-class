# آزمایشگاه  DRF: Caching، Throttling، Filtering و Pagination

## ۱. معرفی پروژه و هدف آموزشی

این پروژه یک API ساده به نام   Book Catalog API   است که چهار قابلیت تکمیلی Django REST Framework را روی یک endpoint واقعی (  /api/books/  ) نشان می‌دهد:

| مفهوم | ابزار در پروژه |
|---|---|
| Caching | Redis +   cache_page   |
| Throttling |   AnonRateThrottle  ،   UserRateThrottle  ،   ScopedRateThrottle   |
| Filtering / Search / Ordering |   django-filter  ،   SearchFilter  ،   OrderingFilter   |
| Pagination |   PageNumberPagination   (اصلی) و   LimitOffsetPagination   (جایگزین) |

هدف این است که شما هر مفهوم را با   ارسال درخواست واقعی   ببینید، نه فقط کد بخوانید.

## ۲. پیش‌نیازها

- Docker و Docker Compose (نصب Python و PostgreSQL روی سیستم لازم نیست)
- آشنایی با مدل، Serializer، View و ViewSet در Django/DRF
- ابزار   curl   یا مرورگر

## ۳. معماری ساده و نقش سرویس‌ها

  
 مرورگر / curl ──► web (Django + DRF :8000) ──► db (PostgreSQL)  ← داده کتاب‌ها (volume پایدار)
                          │
                          └──────────────────► redis            ← cache پاسخ‌ها + شمارنده Throttling
  

-   web  : اجرای Django. هنگام شروع   migrate   را خودکار اجرا می‌کند.
-   db  : PostgreSQL با volume به نام   postgres_data  ؛ با   down   پاک نمی‌شود.
-   redis  : دو دیتابیس منطقی دارد:   0   برای Throttling،   1   برای cache کتاب‌ها (دلیلش در بخش Caching آمده). ذخیره‌سازی دیسکی عمداً خاموش است چون cache منبع اصلی داده نیست.

## ۴. ساختار فایل‌ها

  
drf-learning-lab/
├── config/               تنظیمات (settings.py، settings_test.py)، urls
├── catalog/              تنها app پروژه
│   ├── models.py         مدل Book
│   ├── serializers.py
│   ├── filters.py        BookFilter + StableOrderingFilter
│   ├── pagination.py     دو کلاس Pagination
│   ├── views.py          ViewSetها + cache + throttle
│   ├── signals.py        invalidation کش
│   ├── permissions.py
│   └── management/commands/seed_books.py
├── tests/                تست‌های pytest
├── docs/INSTRUCTOR_SOLUTIONS.md   پاسخ تمرین‌ها (فقط مدرس)
├── Dockerfile, compose.yaml, requirements.txt
├── .env.example, .gitignore, pytest.ini
└── README.md
  

## ۵. اجرای پروژه از ابتدا تا انتها

  bash
cp .env.example .env            # مقادیر نمونه؛ در صورت نیاز تغییر دهید
docker compose up --build -d    # ساخت و اجرای web, db, redis
docker compose ps               # db و redis باید healthy باشند
  

## ۶. Migration و Seed

  migrate   هنگام بالا آمدن web خودکار اجرا می‌شود. اجرای دستی:

  bash
docker compose exec web python manage.py migrate
  

ساخت داده نمونه (۳۷ کتاب؛ اجرای مجدد تکراری نمی‌سازد) و کاربران آموزشی:

  bash
docker compose exec web python manage.py seed_books --with-users
  

کاربر   student   (عادی) و   admin   (staff) با رمزهای   DEMO_STUDENT_PASSWORD   و   DEMO_ADMIN_PASSWORD   در   .env   ساخته می‌شوند. ژانرهای موجود:   fiction  ،   fantasy  ،   science  ،   history  ،   programming  ،   biography  .

## ۷. Swagger UI

- مستندات: http://localhost:8000/api/docs/
- Schema: http://localhost:8000/api/schema/
- ریشه API: http://localhost:8000/api/
- پنل ادمین: http://localhost:8000/admin/

(Swagger UI برای بارگذاری ظاهر خود از CDN استفاده می‌کند؛ مرورگر باید به اینترنت دسترسی داشته باشد.)

## ۸. Endpointها

| مسیر | متد | توضیح |
|---|---|---|
|   /api/books/   | GET | فهرست (Filter/Search/Order/PageNumber +   کش  ) |
|   /api/books/   | POST | ایجاد (فقط staff) |
|   /api/books/{id}/   | GET / PUT / PATCH / DELETE | جزئیات؛ نوشتن فقط staff |
|   /api/books/search/   | GET | جست‌وجو با سهمیه جدا (  book-search  )، بدون کش |
|   /api/books-offset/   | GET | همان فیلترها با   limit/offset   |
|   /api/admin/clear-books-cache/   | POST | پاک‌کردن کش کتاب‌ها (فقط staff) |

نمونه پاسخ (ساختار؛ مقادیر بسته به داده شما):

  bash
curl -i "http://localhost:8000/api/books/?page_size=2"
  
  json
{
  "count": 37,
  "next": "http://localhost:8000/api/books/?page=2&page_size=2",
  "previous": null,
  "results": [
    {"id": 1, "title": "Fluent Python", "author": "Luciano Ramalho", "genre": "programming",
     "publication_year": 2015, "price": "45.00", "is_available": true, "...": "..."}
  ]
}
  

## ۹. آموزش مفاهیم

### ۹.۱ Caching

  مسئله.   هر بار که فهرست کتاب‌ها درخواست می‌شود، Django دوباره Query می‌زند، Serialize و JSON می‌سازد؛ حتی اگر داده تغییر نکرده باشد.

  راه‌حل.   پاسخ HTTP نهایی را برای مدت   BOOKS_CACHE_TTL   (پیش‌فرض ۶۰ ثانیه) در Redis نگه می‌داریم. درخواست بعدی با همان URL مستقیماً از Redis پاسخ می‌گیرد.

-   Cache چیست؟   ذخیره موقت نتیجه‌ای گران‌قیمت برای استفاده مجدد.
-   Hit و Miss:   Hit یعنی پاسخ در کش بود؛ Miss یعنی نبود و باید ساخته می‌شد (و سپس ذخیره می‌شود).
-   نقش Redis:   حافظه مشترک بین همه پردازش‌ها.   LocMemCache   برای هر پردازش جداست؛ اگر چند worker داشته باشید هرکدام کش مستقل دارند و با ریست‌شدن پردازش خالی می‌شود. Redis بین همه مشترک است.
-   کش پاسخ HTTP در برابر کش داده/Query:   اینجا کل پاسخ نهایی کش می‌شود (سریع‌ترین، چون Serializer و رندر هم حذف می‌شوند، اما ریزدانه نیست). کش نتیجه Query (مثلاً با   cache.get/set   دستی) فقط داده را نگه می‌دارد و Serialize هنوز اجرا می‌شود؛ کنترل ریزتری دارد ولی کد بیشتری می‌خواهد.

  فایل‌ها:     catalog/views.py   (دکوراتور روی   list  )،   config/settings.py   (  CACHES  ،   BOOKS_CACHE_TTL  )،   catalog/signals.py  .

  نکات طراحی:  
-   cache_page   روی متد   list   گذاشته شده نه کل view؛ بنابراین Throttling و Permission   قبل   از کش اجرا می‌شوند و Cache Hit هم از سهمیه کم می‌کند.
- کلید کش شامل URL کامل با Query String است؛ پس   ?genre=science   و   ?genre=fiction   هرگز با هم قاطی نمی‌شوند.   vary_on_headers("Accept")   هم فرمت‌های مختلف پاسخ را جدا می‌کند.
- فهرست عمومی است و داده شخصی ندارد. اگر پاسخی به هویت کاربر وابسته بود باید   vary_on_headers("Authorization")   (یا Cookie) اضافه می‌شد، یا اصلاً کش مشترک استفاده نمی‌شد.
- پاسخ شامل هدر   Cache-Control: max-age   هم می‌شود؛ مرورگر نیز ممکن است تا ۶۰ ثانیه خودش پاسخ را نگه دارد. برای آزمایش از   curl   استفاده کنید.

  Invalidation.   با هر   save()   یا   delete()   روی Book، سیگنال کل کش   books   را پاک می‌کند. ساده است ولی خشن: همه صفحه‌ها بی‌اعتبار می‌شوند. چون   cache.clear()   در Redis کل دیتابیس Redis را خالی می‌کند، کش کتاب‌ها روی دیتابیس ۱ است تا شمارنده Throttling (دیتابیس ۰) پاک نشود. تغییرهایی که سیگنال ندارند (  bulk_create  ،   QuerySet.update  ، SQL مستقیم) کش را پاک   نمی‌کنند  .

  آزمایش (چگونه بفهمیم واقعاً Cache است؟).   تکرار یک درخواست به‌تنهایی اثبات نیست (داده ممکن است همان باشد). اثبات واقعی: داده را «پشت‌ پرده» عوض کنیم و ببینیم پاسخ قدیمی می‌ماند.

  bash
# 1) درخواست اول (Miss) و ثبت X-Generated-At
curl -si "http://localhost:8000/api/books/?search=cosmos" | grep -E "X-Generated-At|price"

# 2) تغییر مستقیم در PostgreSQL (بدون سیگنال Django)
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "UPDATE catalog_book SET price = 99 WHERE title = '"'"'Cosmos'"'"';"'

# 3) دوباره درخواست؛ قیمت قدیمی و همان X-Generated-At یعنی از Redis آمده
curl -si "http://localhost:8000/api/books/?search=cosmos" | grep -E "X-Generated-At|price"

# 4) پاک‌کردن کش (به‌عنوان staff) و درخواست مجدد؛ حالا قیمت 99.00
curl -s -X POST -u admin:<DEMO_ADMIN_PASSWORD> http://localhost:8000/api/admin/clear-books-cache/
curl -s "http://localhost:8000/api/books/?search=cosmos"
  

مشاهده کلیدها در Redis:   docker compose exec redis redis-cli -n 1 keys '*'  

  خروجی مورد انتظار:   در مرحله ۳ قیمت همان مقدار قبلی (  18.00  ) و   X-Generated-At   یکسان است؛ پس از مرحله ۴ قیمت   99.00   می‌شود. (اگر بیش از ۶۰ ثانیه صبر کنید خودش منقضی می‌شود.)

  تمرین‌ها:  
1. *(ساده)* مقدار   BOOKS_CACHE_TTL   را در   .env   به ۵ تغییر دهید، web را restart کنید و با آزمایش بالا نشان دهید کش بعد از ۵ ثانیه منقضی می‌شود.
2. *(متوسط)* یک کتاب را با   POST   (به‌عنوان admin) اضافه کنید. بدون استفاده از clear endpoint، نشان دهید فهرست جدید فوراً دیده می‌شود. سپس توضیح دهید چرا با   bulk_create   این اتفاق نمی‌افتاد و چه راهی برای رفعش دارید.

### ۹.۲ Throttling

  مسئله.   یک کاربر (یا اسکریپت) می‌تواند هزاران درخواست بفرستد و منابع سرور را مصرف کند.

  راه‌حل.   DRF تعداد درخواست هر «هویت» را در بازه زمانی می‌شمارد و پس از عبور از سقف، پاسخ   429 Too Many Requests   می‌دهد.

| کلاس | هویت | کاربرد |
|---|---|---|
|   AnonRateThrottle   | آدرس IP کاربر ناشناس | نرخ   anon   (پیش‌فرض   10/min  ) |
|   UserRateThrottle   | شناسه کاربر لاگین‌شده | نرخ   user   (پیش‌فرض   30/min  ) |
|   ScopedRateThrottle   | هویت +   throttle_scope   | نرخ مخصوص یک endpoint:   book-search   (پیش‌فرض   5/min  ) |

-   تفاوت با Authentication/Permission:   Authentication می‌پرسد «تو کیستی؟»، Permission می‌پرسد «اجازه داری؟»، Throttling می‌پرسد «چند بار و با چه سرعتی؟». یک کاربر مجاز هم ممکن است Throttle شود.
-   پاسخ پس از عبور:     429  . هدر   Retry-After   (ثانیه تا درخواست بعدی) معمولاً وجود دارد، هرجا DRF بتواند زمان انتظار را محاسبه کند.
-   محدودیت:   Throttling داخلی DRF مکانیزم امنیتی دقیق در برابر DoS نیست. شمارنده‌ها در cache ذخیره می‌شوند و تقریبی‌اند (در رقابت چند درخواست هم‌زمان ممکن است چند درخواست اضافه رد شود)، هویت ناشناس بر پایه IP است (پشت proxy،   X-Forwarded-For   و   NUM_PROXIES   مهم می‌شوند؛ تغییر IP آن را دور می‌زند) و درخواست پیش از رسیدن به Django مصرف منابع کرده است. حفاظت واقعی باید در لایه reverse proxy / WAF / API gateway باشد.

  فایل‌ها:     config/settings.py   (  DEFAULT_THROTTLE_CLASSES   و   DEFAULT_THROTTLE_RATES  )،   catalog/views.py   (action با   throttle_scope="book-search"  ).

  آزمایش:  
  bash
# ناشناس: بعد از ۱۰ درخواست در دقیقه، 429 می‌گیرید
for i in $(seq 1 12); do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/books/; done

# جزئیات 429 و Retry-After
curl -si http://localhost:8000/api/books/ | head -n 12

# کاربر لاگین‌شده؛ سقف بالاتر (30/min)
for i in $(seq 1 12); do curl -s -o /dev/null -w "%{http_code}\n" -u student:<DEMO_STUDENT_PASSWORD> http://localhost:8000/api/books/; done

# scope اختصاصی: پس از ۵ درخواست در دقیقه 429
for i in $(seq 1 7); do curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8000/api/books/search/?search=python"; done
  
  خروجی مورد انتظار:   ده بار   200   و سپس   429   برای ناشناس؛ پاسخ   429   بدنه‌ای شبیه   {"detail":"Request was throttled. Expected available in 43 seconds."}   و هدر   Retry-After   دارد. برای کاربر لاگین‌شده هر ۱۲ درخواست   200   است. بین دو آزمایش باید یک دقیقه صبر کنید یا کش پیش‌فرض را خالی کنید:   docker compose exec redis redis-cli -n 0 flushdb  .

> نکته: در Docker، IP همه درخواست‌های ناشناس از سیستم میزبان معمولاً یکسان دیده می‌شود، پس همه در یک سهمیه شریک‌اند.

  تمرین‌ها:  
1. *(ساده)* نرخ   anon   را به   3/min   برسانید و با curl نشان دهید چهارمین درخواست   429   می‌گیرد.
2. *(متوسط)* یک scope به نام   book-write   با نرخ   2/min   برای عملیات نوشتن (POST/PUT/PATCH/DELETE) تعریف کنید طوری که خواندن تحت تأثیر قرار نگیرد، و با curl آزمایش کنید.

### ۹.۳ Filtering، Search و Ordering

  مسئله.   کاربر نمی‌خواهد همه ۳۷ کتاب را ببیند؛ فقط کتاب‌های یک ژانر، بازه قیمت یا کلمه خاص را می‌خواهد.

  راه‌حل.   سه backend برای   /api/books/  :

| Backend | کار | مثال |
|---|---|---|
|   DjangoFilterBackend   | تطبیق دقیق/بازه روی فیلدهای مشخص |   ?genre=science   |
|   SearchFilter   | جست‌وجوی متنی در   title   و   author   |   ?search=python   |
|   OrderingFilter   | مرتب‌سازی با   title  ،   price  ،   publication_year   |   ?ordering=-price   |

  Query Parameter   بخش بعد از   ?   در URL است و با   &   جدا می‌شود. Filtering «کدام رکوردها» را معلوم می‌کند، Search «کدام رکوردها شامل متن» را، و Ordering «به چه ترتیبی» را.

  چرا محدود؟   اجازه فیلتر یا مرتب‌سازی روی هر فیلد، Queryهای سنگین بدون ایندکس و افشای فیلدهای غیرضروری را ممکن می‌کند. به همین دلیل فقط فیلدهای فهرست‌شده مجازند: فیلد نامعتبر در   ordering   نادیده گرفته می‌شود، مقدار نامعتبر   genre   خطای   400   می‌دهد.

  فایل‌ها:     catalog/filters.py  ،   catalog/views.py   (  BookQueryMixin  ). کلاس   StableOrderingFilter   کلید   id   را به ترتیب اضافه می‌کند تا رکوردهای هم‌قیمت بین صفحه‌ها جابه‌جا نشوند.

  آزمایش‌ها:  
  
GET /api/books/?genre=science
GET /api/books/?author=tolkien
GET /api/books/?is_available=true
GET /api/books/?publication_year=2015
GET /api/books/?price_min=10&price_max=15
GET /api/books/?search=python
GET /api/books/?ordering=-price
GET /api/books/?genre=programming&ordering=title
  
  خروجی مورد انتظار:     ?search=python   دقیقاً ۳ کتاب (Fluent Python، Python Crash Course، Python for Data Analysis)؛   ?author=tolkien   دو کتاب؛ در   ?ordering=-price   گران‌ترین کتاب اول می‌آید.

  تمرین‌ها:  
1. *(ساده)* بررسی کنید چه کتابی با   ?ordering=-publication_year   اول می‌آید. سپس   ?ordering=description   را بزنید و توضیح دهید چرا خطا نمی‌گیرید.
2. *(متوسط)* فیلترهای   year_min   و   year_max   (بازه سال انتشار) را به   BookFilter   اضافه کنید و با   ?year_min=2000&year_max=2015   آزمایش کنید.

### ۹.۴ Pagination

  مسئله.   برگرداندن هزاران رکورد در یک درخواست، پاسخ را سنگین، کند و پرمصرف می‌کند (Query، حافظه، Serialize و پهنای باند).

  راه‌حل.  
-   روش اصلی (پیش‌فرض):     PageNumberPagination   با اندازه صفحه ۱۰، حداکثر ۵۰:   ?page=2&page_size=5  
-   روش جایگزین:     LimitOffsetPagination   روی   /api/books-offset/  :   ?limit=5&offset=10  

تفاوت: Page Number مفهوم «شماره صفحه» دارد و برای رابط‌های صفحه‌بندی‌شده مناسب است؛ Limit/Offset کنترل دقیق‌تری برای «از کجا چند تا» می‌دهد. در هر دو، offset بزرگ روی جدول‌های بسیار بزرگ هزینه دارد (دیتابیس باید ردیف‌های قبلی را رد کند).   Pagination با Filtering فرق دارد:   Filtering تعیین می‌کند *کدام* رکوردها در نتیجه‌اند، Pagination فقط *چه تکه‌ای* از همان نتیجه را بدهد.

رفتار مقادیر نامعتبر:   page_size   بیش از ۵۰ به ۵۰ کاهش می‌یابد؛   page_size   صفر، منفی یا غیرعددی به اندازه پیش‌فرض (۱۰) برمی‌گردد؛   page   خارج از محدوده   404   می‌دهد.

  فایل‌ها:     catalog/pagination.py  ،   config/settings.py   (  DEFAULT_PAGINATION_CLASS  )،   catalog/views.py  .

  آزمایش‌ها:  
  
GET /api/books/?page=1
GET /api/books/?page=2
GET /api/books/?page=1&page_size=5
GET /api/books/?page_size=1000        ← حداکثر ۵۰
GET /api/books/?page_size=abc         ← اندازه پیش‌فرض
GET /api/books-offset/?limit=5&offset=0
GET /api/books-offset/?limit=5&offset=5
  
  خروجی مورد انتظار:   کلیدهای   count  ،   next  ،   previous   و   results  ؛ برای ۳۷ کتاب با اندازه ۱۰، چهار صفحه وجود دارد و صفحه چهارم ۷ نتیجه و   next   برابر   null   دارد.

  تمرین‌ها:  
1. *(ساده)* اندازه پیش‌فرض صفحه را به ۵ و سقف را به ۲۰ تغییر دهید و با   ?page_size=100   بررسی کنید.
2. *(متوسط)* یک   CursorPagination   روی یک endpoint جدید (مرتب‌شده بر   created_at  ) اضافه کنید و خروجی آن را با دو روش دیگر مقایسه کنید.

## ۱۰. آزمایش ترکیبی چهار مفهوم

  
GET /api/books/?genre=programming&search=python&ordering=-price&page=2&page_size=2
  

ابتدا فیلتر ژانر، سپس جست‌وجو، سپس مرتب‌سازی و در نهایت صفحه‌بندی اعمال می‌شود. با داده نمونه ۳ کتاب Python داریم؛ صفحه دوم با اندازه ۲ فقط یک نتیجه (Python Crash Course) و   next = null   دارد. این URL با Query String کامل کش می‌شود. همین درخواست را دوباره بفرستید و   X-Generated-At   را مقایسه کنید؛ سپس با یک ژانر دیگر Miss جدید می‌گیرید. بیش از سقف Throttling بفرستید تا   429   ببینید (حتی اگر پاسخ از کش بیاید).

## ۱۱. اجرای تست‌ها

  bash
docker compose run --rm web pytest
  

تست‌ها از cache محلی (بدون Redis) و تنظیمات   config/settings_test.py   استفاده می‌کنند، پیش از هر تست کش را خالی می‌کنند و ساعت Throttling را شبیه‌سازی می‌کنند (بدون sleep). PostgreSQL فقط برای دیتابیس تست لازم است و Compose آن را خودکار بالا می‌آورد. Cache Hit با   شمارش Queryها   اثبات می‌شود (درخواست دوم صفر Query دارد)، نه صرفاً مقایسه دو پاسخ.

## ۱۲. مشکلات رایج

| مشکل | علت و راه‌حل |
|---|---|
|   env file .env not found   |   cp .env.example .env   را اجرا نکرده‌اید |
|   KeyError: DJANGO_SECRET_KEY   | متغیر در   .env   نیست یا   env_file   اعمال نشده |
| خطای اتصال به PostgreSQL |   docker compose ps   را ببینید؛ db باید healthy باشد. اگر رمز   .env   را بعد از اولین اجرا عوض کردید، volume قدیمی رمز قدیمی را نگه می‌دارد:   docker compose down -v   (داده پاک می‌شود) |
| خطای اتصال به Redis | سرویس redis و مقدار   REDIS_URL   /   REDIS_BOOKS_URL   را بررسی کنید (میزبان باید   redis   باشد، نه   localhost  ) |
| همیشه   429   می‌گیرم | IP ناشناس همه درخواست‌ها یکی است؛ یک دقیقه صبر کنید یا   redis-cli -n 0 flushdb   |
| تغییر داده دیده نمی‌شود | کش هنوز معتبر است؛ TTL را صبر کنید یا clear endpoint را بزنید (به بخش Invalidation نگاه کنید) |
| پورت ۸۰۰۰ اشغال است | پورت در   compose.yaml   را تغییر دهید |
| Swagger بدون ظاهر باز می‌شود | مرورگر به CDN دسترسی ندارد |

## ۱۳. دستورات مهم Docker Compose

| دستور | کار |
|---|---|
|   docker compose up --build -d   | ساخت و اجرا |
|   docker compose ps   | وضعیت سرویس‌ها |
|   docker compose logs -f web   | لاگ Django |
|   docker compose exec web python manage.py seed_books --with-users   | داده نمونه |
|   docker compose exec web python manage.py migrate   | اجرای migration |
|   docker compose run --rm web pytest   | اجرای تست‌ها |
|   docker compose exec redis redis-cli -n 1 keys '*'   | دیدن کلیدهای کش کتاب‌ها |
|   docker compose down   | توقف (داده PostgreSQL می‌ماند) |
|   docker compose down -v   | توقف و حذف داده‌ها |

## ۱۴. تمرین‌های ترکیبی پیشنهادی

1. نموداری بکشید که مسیر یک درخواست   GET /api/books/?genre=science   را از Throttling تا Redis و دیتابیس نشان دهد (Hit و Miss).
2. یک endpoint فقط‌خواندنی   /api/books/stats/   بنویسید که تعداد کتاب‌ها به تفکیک ژانر را بدهد، سپس تصمیم بگیرید کش شود یا نه و دلیل بیاورید.

پاسخ تمرین‌های بخش ۹ در   docs/INSTRUCTOR_SOLUTIONS.md   (ویژه مدرس) است.

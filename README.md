# جنگو | آزمایشگاه DRF

### Caching، Throttling، Filtering و Pagination

این پروژه یک API ساده به نام **Book Catalog API** است که چهار قابلیت مهم Django REST Framework را روی endpoint واقعی `/api/books/` پیاده‌سازی می‌کند. هدفم این است که هر قابلیت را با ارسال درخواست واقعی بررسی کنم و فقط به خواندن کد اکتفا نکنم.

## فهرست مطالب

- [معرفی پروژه](#معرفی-پروژه)
- [پیش‌نیازها](#پیشنیازها)
- [معماری پروژه](#معماری-پروژه)
- [ساختار فایل‌ها](#ساختار-فایلها)
- [راه‌اندازی پروژه](#راهاندازی-پروژه)
- [داده‌های نمونه](#دادههای-نمونه)
- [مستندات API](#مستندات-api)
- [Endpointها](#endpointها)
- [مفاهیم اصلی](#مفاهیم-اصلی)
  - [Caching](#1-caching)
  - [Throttling](#2-throttling)
  - [Filtering، Search و Ordering](#3-filtering-search-و-ordering)
  - [Pagination](#4-pagination)
- [آزمایش ترکیبی](#آزمایش-ترکیبی)
- [اجرای تست‌ها](#اجرای-تستها)
- [مشکلات رایج](#مشکلات-رایج)
- [دستورات کاربردی Docker Compose](#دستورات-کاربردی-docker-compose)
- [تمرین‌های پیشنهادی](#تمرینهای-پیشنهادی)

## معرفی پروژه

در این پروژه چهار قابلیت زیر را بررسی می‌کنم:

| قابلیت | ابزار استفاده‌شده |
|---|---|
| Caching | Redis و `cache_page` |
| Throttling | `AnonRateThrottle`، `UserRateThrottle` و `ScopedRateThrottle` |
| Filtering، Search و Ordering | `django-filter`، `SearchFilter` و `OrderingFilter` |
| Pagination | `PageNumberPagination` و `LimitOffsetPagination` |

## پیش‌نیازها

- Docker و Docker Compose
- آشنایی اولیه با Model، Serializer، View و ViewSet در Django و DRF
- ابزار `curl` یا مرورگر

نیازی نیست Python یا PostgreSQL را مستقیماً روی سیستم نصب کنم؛ سرویس‌ها داخل Docker اجرا می‌شوند.

## معماری پروژه

```text
مرورگر یا curl
      |
      v
web (Django + DRF :8000)
      |                 \
      v                  v
db (PostgreSQL)         redis
داده‌های کتاب‌ها        کش پاسخ‌ها و شمارنده‌های Throttling
```

- **web:** اجرای Django؛ دستور `migrate` هنگام شروع سرویس به‌صورت خودکار اجرا می‌شود.
- **db:** پایگاه داده PostgreSQL با volume به نام `postgres_data`؛ با `docker compose down` داده‌ها حذف نمی‌شوند.
- **redis:** از دیتابیس منطقی `0` برای Throttling و دیتابیس `1` برای کش کتاب‌ها استفاده می‌شود. ذخیره‌سازی دائمی Redis غیرفعال است، چون کش منبع اصلی داده نیست.

## ساختار فایل‌ها

```text
drf-learning-lab/
├── config/
│   ├── settings.py
│   ├── settings_test.py
│   └── urls.py
├── catalog/
│   ├── models.py
│   ├── serializers.py
│   ├── filters.py
│   ├── pagination.py
│   ├── views.py
│   ├── signals.py
│   ├── permissions.py
│   └── management/commands/seed_books.py
├── tests/
├── docs/INSTRUCTOR_SOLUTIONS.md
├── Dockerfile
├── compose.yaml
├── requirements.txt
├── .env.example
├── .gitignore
├── pytest.ini
└── README.md
```

## راه‌اندازی پروژه

دستورها را از پوشه اصلی پروژه اجرا می‌کنم:

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
```

در خروجی `docker compose ps` وضعیت سرویس‌ها را بررسی می‌کنم. سرویس‌های دیتابیس و Redis باید سالم باشند.

## داده‌های نمونه

دستور `migrate` هنگام بالا آمدن سرویس `web` اجرا می‌شود. اگر لازم باشد، می‌توانم آن را دستی هم اجرا کنم:

```bash
docker compose exec web python manage.py migrate
```

برای ساخت داده‌های نمونه و کاربران آموزشی:

```bash
docker compose exec web python manage.py seed_books --with-users
```

این دستور ۳۷ کتاب نمونه می‌سازد و در اجرای مجدد، داده‌های تکراری ایجاد نمی‌کند. کاربرهای `student` و `admin` نیز با رمزهای تنظیم‌شده در متغیرهای `DEMO_STUDENT_PASSWORD` و `DEMO_ADMIN_PASSWORD` داخل فایل `.env` ساخته می‌شوند.

ژانرهای موجود عبارت‌اند از: `fiction`، `fantasy`، `science`، `history`، `programming` و `biography`.

> فایل `.env` را با رمزهای واقعی در مخزن عمومی GitHub قرار ندهید.

## مستندات API

پس از اجرای پروژه، آدرس‌های زیر در دسترس‌اند:

- Swagger UI: <http://localhost:8000/api/docs/>
- Schema: <http://localhost:8000/api/schema/>
- ریشه API: <http://localhost:8000/api/>
- پنل مدیریت: <http://localhost:8000/admin/>

**نکته:** Swagger UI برای بارگذاری ظاهر خود از CDN استفاده می‌کند؛ بنابراین مرورگر باید به اینترنت دسترسی داشته باشد.

## Endpointها

| مسیر | متد | کاربرد |
|---|---|---|
| `/api/books/` | `GET` | دریافت فهرست کتاب‌ها همراه با فیلتر، جست‌وجو، مرتب‌سازی، صفحه‌بندی و کش |
| `/api/books/` | `POST` | ایجاد کتاب؛ فقط برای کاربر staff |
| `/api/books/{id}/` | `GET` | دریافت جزئیات یک کتاب |
| `/api/books/{id}/` | `PUT`، `PATCH`، `DELETE` | ویرایش یا حذف کتاب؛ فقط برای کاربر staff |
| `/api/books/search/` | `GET` | جست‌وجو با سهمیه Throttling جداگانه و بدون کش |
| `/api/books-offset/` | `GET` | فهرست کتاب‌ها با روش `limit/offset` |
| `/api/admin/clear-books-cache/` | `POST` | پاک‌کردن کش کتاب‌ها؛ فقط برای کاربر staff |

نمونه درخواست:

```bash
curl -i "http://localhost:8000/api/books/?page_size=2"
```

پاسخ صفحه‌بندی‌شده، ساختاری شبیه نمونه زیر دارد؛ مقدارها با توجه به داده‌های موجود ممکن است فرق کنند:

```json
{
  "count": 37,
  "next": "http://localhost:8000/api/books/?page=2&page_size=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Fluent Python",
      "author": "Luciano Ramalho",
      "genre": "programming",
      "publication_year": 2015,
      "price": "45.00",
      "is_available": true
    }
  ]
}
```

## مفاهیم اصلی

### 1. Caching

#### مشکل و راه‌حل

بدون کش، در هر درخواست فهرست کتاب‌ها، Django دوباره از دیتابیس Query می‌گیرد، داده‌ها را Serialize می‌کند و پاسخ JSON را می‌سازد. در این پروژه، پاسخ نهایی HTTP برای مدت `BOOKS_CACHE_TTL` (به‌صورت پیش‌فرض ۶۰ ثانیه) در Redis ذخیره می‌شود تا درخواست‌های مشابه بتوانند از همان پاسخ استفاده کنند.

- **Cache Hit:** پاسخ موردنظر از قبل در کش وجود دارد.
- **Cache Miss:** پاسخ در کش نیست؛ بنابراین باید ساخته و ذخیره شود.
- **چرا Redis؟** کش بین پردازش‌های مختلف مشترک است. در مقابل، `LocMemCache` برای هر پردازش جداست.
- **کش پاسخ در برابر کش Query:** اینجا کل پاسخ HTTP کش می‌شود؛ بنابراین در Cache Hit، ساخت پاسخ و Serialize دوباره انجام نمی‌شود. کش‌کردن داده یا نتیجه Query کنترل بیشتری می‌دهد، اما معمولاً به کدنویسی بیشتری نیاز دارد.

**فایل‌های مرتبط:** `catalog/views.py`، `config/settings.py` و `catalog/signals.py`.

#### نکات طراحی

- `cache_page` روی متد `list` قرار گرفته است، نه کل View؛ در نتیجه Permission و Throttling پیش از رسیدن به کش بررسی می‌شوند و Cache Hit هم از سهمیه درخواست کم می‌کند.
- کلید کش، URL کامل و Query String را در نظر می‌گیرد؛ بنابراین درخواست‌های `?genre=science` و `?genre=fiction` کش جداگانه دارند. هدر `Accept` نیز در تفکیک پاسخ‌ها لحاظ می‌شود.
- فهرست کتاب‌ها عمومی است و اطلاعات شخصی ندارد. اگر پاسخ به هویت کاربر وابسته باشد، باید کش را با دقت بیشتری تنظیم کرد یا از کش مشترک استفاده نکرد.
- پاسخ هدر `Cache-Control: max-age` نیز دارد؛ پس ممکن است مرورگر هم پاسخ را تا پایان این زمان نگه دارد.

#### پاک‌سازی کش (Invalidation)

با هر `save()` یا `delete()` روی مدل `Book`، سیگنال پروژه کل کش کتاب‌ها را پاک می‌کند. این روش ساده است، اما همه صفحه‌های کش‌شده را بی‌اعتبار می‌کند.

کش کتاب‌ها در دیتابیس شماره `1` از Redis قرار دارد تا پاک‌سازی آن، شمارنده‌های Throttling در دیتابیس شماره `0` را حذف نکند. عملیات‌هایی مانند `bulk_create`، `QuerySet.update` یا اجرای SQL مستقیم سیگنال‌های معمول مدل را اجرا نمی‌کنند؛ بنابراین لزوماً کش را پاک نمی‌کنند.

#### آزمایش کش

ابتدا یک درخواست می‌فرستم و زمان تولید پاسخ و قیمت کتاب را بررسی می‌کنم:

```bash
curl -si "http://localhost:8000/api/books/?search=cosmos" | grep -E "X-Generated-At|price"
```

سپس قیمت کتاب را مستقیماً در PostgreSQL تغییر می‌دهم؛ این تغییر از مسیر مدل Django عبور نمی‌کند و سیگنال را اجرا نمی‌کند:

```bash
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "UPDATE catalog_book SET price = 99 WHERE title = '"'"'Cosmos'"'"';"'
```

دوباره همان درخواست را می‌فرستم:

```bash
curl -si "http://localhost:8000/api/books/?search=cosmos" | grep -E "X-Generated-At|price"
```

اگر کش هنوز معتبر باشد، پاسخ قبلی و همان `X-Generated-At` را می‌بینم. برای پاک‌کردن کش، با کاربر staff درخواست می‌فرستم:

```bash
curl -s -X POST -u "admin:<DEMO_ADMIN_PASSWORD>" \
  "http://localhost:8000/api/admin/clear-books-cache/"
```

حالا با درخواست دوباره باید قیمت به‌روز را ببینم:

```bash
curl -s "http://localhost:8000/api/books/?search=cosmos"
```

برای مشاهده کلیدهای کش کتاب‌ها در Redis:

```bash
docker compose exec redis redis-cli -n 1 keys '*'
```

**تمرین‌ها**

1. مقدار `BOOKS_CACHE_TTL` را در `.env` روی ۵ ثانیه قرار دهید، سرویس `web` را restart کنید و بررسی کنید کش پس از این مدت منقضی می‌شود.
2. یک کتاب را با `POST` و کاربر admin اضافه کنید و بررسی کنید که آیا کش به‌طور خودکار پاک می‌شود. سپس توضیح دهید چرا `bulk_create` رفتار متفاوتی دارد و چگونه می‌توان آن را مدیریت کرد.

### 2. Throttling

#### مشکل و راه‌حل

Throttling تعداد درخواست‌های یک هویت را در بازه زمانی مشخص محدود می‌کند. وقتی از سقف تعیین‌شده عبور شود، DRF معمولاً پاسخ `429 Too Many Requests` می‌دهد.

| کلاس | مبنای شمارش | نرخ پیش‌فرض این پروژه |
|---|---|---|
| `AnonRateThrottle` | IP کاربر ناشناس | `10/min` |
| `UserRateThrottle` | شناسه کاربر واردشده | `30/min` |
| `ScopedRateThrottle` | هویت کاربر و `throttle_scope` | `book-search`: `5/min` |

تفاوت سه مفهوم مهم:

- **Authentication:** مشخص می‌کند کاربر کیست.
- **Permission:** مشخص می‌کند کاربر اجازه انجام عملیات را دارد یا نه.
- **Throttling:** مشخص می‌کند کاربر با چه نرخی می‌تواند درخواست بفرستد.

پس حتی کاربری که اجازه دسترسی دارد ممکن است به‌دلیل عبور از سقف درخواست محدود شود.

در پاسخ `429` معمولاً هدر `Retry-After` تعداد ثانیه‌های انتظار را نشان می‌دهد. با این حال، Throttling داخلی DRF به‌تنهایی راهکار امنیتی کامل برای مقابله با DoS نیست؛ شمارنده‌ها تقریبی‌اند و برای محافظت جدی‌تر باید از لایه‌هایی مانند reverse proxy، WAF یا API gateway نیز استفاده کرد.

**فایل‌های مرتبط:** `config/settings.py` و `catalog/views.py`.

#### آزمایش Throttling

درخواست‌های ناشناس به فهرست کتاب‌ها:

```bash
for i in $(seq 1 12); do
  curl -s -o /dev/null -w "%{http_code}\n" \
    "http://localhost:8000/api/books/"
done
```

بررسی جزئیات پاسخ:

```bash
curl -si "http://localhost:8000/api/books/" | head -n 12
```

آزمایش با کاربر واردشده:

```bash
for i in $(seq 1 12); do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -u "student:<DEMO_STUDENT_PASSWORD>" \
    "http://localhost:8000/api/books/"
done
```

آزمایش سهمیه اختصاصی جست‌وجو:

```bash
for i in $(seq 1 7); do
  curl -s -o /dev/null -w "%{http_code}\n" \
    "http://localhost:8000/api/books/search/?search=python"
done
```

با تنظیمات پیش‌فرض، درخواست‌های ناشناس پس از عبور از سقف `10/min` و درخواست‌های جست‌وجو پس از عبور از سقف `5/min` محدود می‌شوند. برای آزمایش مجدد، ممکن است لازم باشد تا پایان بازه محدودیت صبر کنید یا شمارنده‌های Throttling را پاک کنید:

```bash
docker compose exec redis redis-cli -n 0 flushdb
```

> در Docker ممکن است درخواست‌های ناشناس از یک IP مشترک دیده شوند و همگی از یک سهمیه استفاده کنند.

**تمرین‌ها**

1. نرخ `anon` را به `3/min` تغییر دهید و بررسی کنید درخواست چهارم چه پاسخی می‌گیرد.
2. یک scope به نام `book-write` با نرخ `2/min` برای عملیات نوشتن تعریف کنید تا درخواست‌های خواندن تحت تأثیر قرار نگیرند.

### 3. Filtering، Search و Ordering

این قابلیت‌ها کمک می‌کنند به‌جای دریافت همه کتاب‌ها، فقط نتایج موردنیاز را درخواست کنم.

| Backend | کاربرد | نمونه |
|---|---|---|
| `DjangoFilterBackend` | فیلتر دقیق یا بازه‌ای | `?genre=science` |
| `SearchFilter` | جست‌وجو در عنوان و نویسنده | `?search=python` |
| `OrderingFilter` | مرتب‌سازی بر اساس فیلدهای مجاز | `?ordering=-price` |

پارامترهای Query در بخشی از URL قرار می‌گیرند که پس از `?` می‌آید و با `&` از هم جدا می‌شوند. فیلتر مشخص می‌کند کدام رکوردها در نتیجه باشند؛ جست‌وجو رکوردهای دارای متن موردنظر را پیدا می‌کند؛ و مرتب‌سازی ترتیب نمایش نتایج را تعیین می‌کند.

در این پروژه فیلتر و مرتب‌سازی به فیلدهای مشخص محدود شده‌اند تا Queryهای نامناسب و دسترسی غیرضروری به فیلدها کمتر شود. کلاس `StableOrderingFilter` نیز `id` را به ترتیب اضافه می‌کند تا رکوردهایی با مقدار مرتب‌سازی یکسان، بین صفحه‌ها کمتر جابه‌جا شوند.

**فایل‌های مرتبط:** `catalog/filters.py` و `catalog/views.py`.

#### نمونه درخواست‌ها

```text
GET /api/books/?genre=science
GET /api/books/?author=tolkien
GET /api/books/?is_available=true
GET /api/books/?publication_year=2015
GET /api/books/?price_min=10&price_max=15
GET /api/books/?search=python
GET /api/books/?ordering=-price
GET /api/books/?genre=programming&ordering=title
```

با داده‌های نمونه این پروژه، جست‌وجوی `?search=python` باید سه کتاب مرتبط با Python را پیدا کند و `?ordering=-price` کتاب گران‌تر را در ابتدای فهرست قرار دهد.

**تمرین‌ها**

1. بررسی کنید `?ordering=-publication_year` کدام کتاب را اول می‌آورد. سپس `?ordering=description` را امتحان کنید و رفتار API را توضیح دهید.
2. فیلترهای `year_min` و `year_max` را به `BookFilter` اضافه کنید و با `?year_min=2000&year_max=2015` آزمایش کنید.

### 4. Pagination

برگرداندن تعداد زیادی رکورد در یک درخواست می‌تواند پاسخ را سنگین و کند کند. Pagination نتایج را به بخش‌های کوچک‌تر تقسیم می‌کند.

این پروژه دو روش دارد:

- **روش اصلی:** `PageNumberPagination` با اندازه پیش‌فرض ۱۰ و حداکثر ۵۰ رکورد در هر صفحه.
- **روش جایگزین:** `LimitOffsetPagination` روی مسیر `/api/books-offset/`.

نمونه‌ها:

```text
/api/books/?page=2&page_size=5
/api/books-offset/?limit=5&offset=10
```

`PageNumberPagination` با شماره صفحه کار می‌کند؛ در مقابل، `LimitOffsetPagination` مشخص می‌کند از کدام موقعیت، چند رکورد برگردد. در جدول‌های بزرگ، مقدار بالای offset می‌تواند پرهزینه باشد، چون دیتابیس باید ردیف‌های قبلی را رد کند.

Pagination با Filtering فرق دارد: فیلتر مشخص می‌کند کدام رکوردها در نتیجه باشند و صفحه‌بندی مشخص می‌کند چه بخشی از همان نتایج برگردد.

رفتار مقدارهای نامعتبر در تنظیمات این پروژه:

- `page_size` بزرگ‌تر از ۵۰ به ۵۰ محدود می‌شود.
- `page_size` صفر، منفی یا غیرعددی به اندازه پیش‌فرض برمی‌گردد.
- شماره صفحه خارج از محدوده پاسخ `404` می‌دهد.

**فایل‌های مرتبط:** `catalog/pagination.py`، `config/settings.py` و `catalog/views.py`.

#### نمونه درخواست‌ها

```text
GET /api/books/?page=1
GET /api/books/?page=2
GET /api/books/?page=1&page_size=5
GET /api/books/?page_size=1000
GET /api/books/?page_size=abc
GET /api/books-offset/?limit=5&offset=0
GET /api/books-offset/?limit=5&offset=5
```

پاسخ معمولاً کلیدهای `count`، `next`، `previous` و `results` را دارد. برای ۳۷ کتاب با اندازه صفحه ۱۰، چهار صفحه داریم و صفحه آخر ۷ نتیجه خواهد داشت.

**تمرین‌ها**

1. اندازه پیش‌فرض صفحه را به ۵ و سقف را به ۲۰ تغییر دهید و با `?page_size=100` نتیجه را بررسی کنید.
2. یک endpoint جدید با `CursorPagination` و ترتیب `created_at` بسازید و آن را با دو روش دیگر مقایسه کنید.

## آزمایش ترکیبی

در این درخواست، فیلتر ژانر، جست‌وجو، مرتب‌سازی و صفحه‌بندی را با هم استفاده می‌کنم:

```text
GET /api/books/?genre=programming&search=python&ordering=-price&page=2&page_size=2
```

فیلتر، جست‌وجو و مرتب‌سازی روی مجموعه نتایج اعمال می‌شوند و در پایان صفحه‌بندی بخش موردنظر را برمی‌گرداند. چون URL کامل در کش لحاظ می‌شود، تغییر Query String باعث می‌شود درخواست متفاوتی داشته باشیم. با ارسال دوباره همان درخواست می‌توانم هدر `X-Generated-At` را بررسی کنم. حتی اگر پاسخ از کش بیاید، Throttling همچنان اعمال می‌شود.

## اجرای تست‌ها

برای اجرای تست‌ها:

```bash
docker compose run --rm web pytest
```

طبق ساختار پروژه، تست‌ها از تنظیمات `config/settings_test.py` استفاده می‌کنند و برای بررسی کش، تعداد Queryها را می‌سنجند؛ صرفاً یکسان بودن دو پاسخ برای اثبات Cache Hit کافی نیست.

## مشکلات رایج

| مشکل | علت یا راه‌حل |
|---|---|
| `env file .env not found` | ابتدا `cp .env.example .env` را اجرا کنید. |
| `KeyError: DJANGO_SECRET_KEY` | متغیر مربوطه را در `.env` بررسی کنید. |
| خطای اتصال به PostgreSQL | با `docker compose ps` وضعیت `db` را بررسی کنید؛ سرویس باید سالم باشد. |
| رمز PostgreSQL پس از تغییر `.env` همچنان قدیمی است | volume ممکن است اطلاعات قبلی را نگه داشته باشد. `docker compose down -v` داده‌ها را حذف می‌کند؛ فقط در صورت اطمینان اجرا کنید. |
| خطای اتصال به Redis | سرویس Redis و متغیرهای `REDIS_URL` و `REDIS_BOOKS_URL` را بررسی کنید؛ نام میزبان در Docker معمولاً `redis` است، نه `localhost`. |
| همیشه پاسخ `429` می‌گیرم | سهمیه Throttling ممکن است پر شده باشد؛ کمی صبر کنید یا شمارنده‌های دیتابیس `0` را پاک کنید. |
| تغییر کتاب‌ها نمایش داده نمی‌شود | کش ممکن است هنوز معتبر باشد؛ منتظر پایان TTL بمانید یا endpoint پاک‌کردن کش را اجرا کنید. |
| پورت ۸۰۰۰ اشغال است | پورت نگاشت‌شده در `compose.yaml` را تغییر دهید. |
| Swagger بدون ظاهر نمایش داده می‌شود | دسترسی مرورگر به CDN را بررسی کنید. |

## دستورات کاربردی Docker Compose

| دستور | کاربرد |
|---|---|
| `docker compose up --build -d` | ساخت و اجرای سرویس‌ها |
| `docker compose ps` | مشاهده وضعیت سرویس‌ها |
| `docker compose logs -f web` | مشاهده لاگ Django |
| `docker compose exec web python manage.py seed_books --with-users` | ساخت داده‌های نمونه و کاربران آموزشی |
| `docker compose exec web python manage.py migrate` | اجرای migrationها |
| `docker compose run --rm web pytest` | اجرای تست‌ها |
| `docker compose exec redis redis-cli -n 1 keys '*'` | مشاهده کلیدهای کش کتاب‌ها |
| `docker compose down` | توقف سرویس‌ها؛ داده PostgreSQL باقی می‌ماند |
| `docker compose down -v` | توقف سرویس‌ها و حذف volumeها و داده‌های ذخیره‌شده |

## تمرین‌های پیشنهادی

1. مسیر یک درخواست `GET /api/books/?genre=science` را از Throttling تا Redis و دیتابیس رسم کنید و تفاوت Cache Hit و Cache Miss را نشان دهید.
2. یک endpoint فقط‌خواندنی به نام `/api/books/stats/` بسازید که تعداد کتاب‌ها را به تفکیک ژانر نمایش دهد. سپس بررسی کنید آیا کش‌کردن این پاسخ مناسب است یا نه و دلیل خود را بنویسید.

پاسخ تمرین‌های بخش‌های آموزشی در فایل `docs/INSTRUCTOR_SOLUTIONS.md` قرار دارد و مخصوص مدرس است.

# پاسخ تمرین‌ها (ویژه مدرس — به دانشجویان داده نشود)

## Caching
**۱ (ساده).** در `.env`: `BOOKS_CACHE_TTL=5` و `docker compose up -d --force-recreate web`. دو درخواست پشت‌سرهم `X-Generated-At` یکسان دارند؛ پس از ۶ ثانیه مقدار جدید می‌شود. (TTL هنگام import در دکوراتور خوانده می‌شود، پس restart لازم است.)

**۲ (متوسط).** `POST` به‌عنوان admin، `save()` را صدا می‌زند و `post_save` کش را پاک می‌کند؛ فهرست بعدی جدید است. در `bulk_create` سیگنال اجرا نمی‌شود، پس کش قدیمی می‌ماند. راه‌حل: بعد از `bulk_create` صریحاً `caches["books"].clear()` یا استفاده از clear endpoint؛ یا سیاست دیگری مثل شماره نسخه در کلید کش.

## Throttling
**۱ (ساده).** در `.env`: `THROTTLE_RATE_ANON=3/min` و ساخت مجدد web. چهارمین درخواست در دقیقه `429` با `Retry-After` می‌دهد.

**۲ (متوسط).** در `settings.py` نرخ `"book-write": "2/min"` اضافه شود. در `BookViewSet`:
```python
def get_throttles(self):
    if self.action in ("create", "update", "partial_update", "destroy"):
        self.throttle_scope = "book-write"
        return [ScopedRateThrottle()]
    return super().get_throttles()
```
خواندن همچنان تحت anon/user است. (توجه: برای این کار باید `ScopedRateThrottle` import شود، که در `views.py` موجود است.)

## Filtering
**۱ (ساده).** `publication_year` از قبل در `ordering_fields` هست؛ `?ordering=-publication_year` جدیدترین کتاب (Two Scoops of Django، ۲۰۲۰) را اول می‌آورد. `description` در `ordering_fields` نیست و DRF فیلد نامعتبر ordering را بی‌صدا نادیده می‌گیرد؛ ترتیب پیش‌فرض (`id`) اعمال می‌شود.

**۲ (متوسط).** در `BookFilter`:
```python
year_min = filters.NumberFilter(field_name="publication_year", lookup_expr="gte")
year_max = filters.NumberFilter(field_name="publication_year", lookup_expr="lte")
```
آزمایش: `/api/books/?year_min=2000&year_max=2015` فقط کتاب‌های ۲۰۰۰ تا ۲۰۱۵.

## Pagination
**۱ (ساده).** در `pagination.py`: `page_size = 5` و `max_page_size = 20`. `?page_size=100` فقط ۲۰ نتیجه می‌دهد.

**۲ (متوسط).** نمونه:
```python
class NewestFirstCursor(CursorPagination):
    page_size = 10
    ordering = "-created_at"
```
یک ViewSet فقط‌خواندنی با `pagination_class = NewestFirstCursor` (و بدون `OrderingFilter`، چون Cursor ترتیب را خودش مدیریت می‌کند). تفاوت: پاسخ `count` ندارد و فقط `next`/`previous` دارد؛ در offsetهای بزرگ کارآمدتر است ولی پرش به صفحه دلخواه ندارد.

## تمرین‌های ترکیبی
**۱.** نمودار باید ترتیب را نشان دهد: Throttle → Permission → `list` کش‌شده (Hit: برگشت از Redis؛ Miss: Filter → Paginate → Serialize → ذخیره در Redis).

**۲.** هر دو پاسخ با دلیل پذیرفته است؛ پاسخ پیشنهادی: کش شود (داده خلاصه و گران نسبت به تغییر)، با همان سیاست invalidation سیگنال‌ها.

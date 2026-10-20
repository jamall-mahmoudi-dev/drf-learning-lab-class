"""
سیاست invalidation: با هر ایجاد/ویرایش/حذف Book، کل cache «books» پاک می‌شود.
ساده و قابل توضیح است؛ هزینه‌اش این است که هر تغییر همه صفحه‌های کش‌شده را بی‌اعتبار می‌کند.

محدودیت: bulk_create / QuerySet.update / SQL مستقیم، سیگنال post_save تولید نمی‌کنند
و کش را پاک نمی‌کنند (در README به‌عنوان آزمایش نشان داده شده است).
"""
from django.conf import settings
from django.core.cache import caches
from django.db.models.signals import post_delete, post_save

from .models import Book


def clear_books_cache(**kwargs):
    caches[settings.BOOKS_CACHE_ALIAS].clear()


post_save.connect(clear_books_cache, sender=Book, dispatch_uid="books_cache_save")
post_delete.connect(clear_books_cache, sender=Book, dispatch_uid="books_cache_delete")

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from catalog.models import Book

# (title, author, genre, year, price, is_available)
BOOKS = [
    ("Fluent Python", "Luciano Ramalho", "programming", 2015, "45.00", True),
    ("Python Crash Course", "Eric Matthes", "programming", 2015, "38.50", True),
    ("Python for Data Analysis", "Wes McKinney", "programming", 2012, "48.00", True),
    ("Two Scoops of Django", "Daniel Roy Greenfeld", "programming", 2020, "42.00", True),
    ("Clean Code", "Robert C. Martin", "programming", 2008, "39.99", False),
    ("The Pragmatic Programmer", "Andrew Hunt", "programming", 1999, "44.00", True),
    ("Designing Data-Intensive Applications", "Martin Kleppmann", "programming", 2017, "55.00", True),
    ("Cosmos", "Carl Sagan", "science", 1980, "18.00", True),
    ("A Brief History of Time", "Stephen Hawking", "science", 1988, "15.50", True),
    ("The Selfish Gene", "Richard Dawkins", "science", 1976, "14.00", False),
    ("Silent Spring", "Rachel Carson", "science", 1962, "12.50", True),
    ("The Structure of Scientific Revolutions", "Thomas Kuhn", "science", 1962, "20.00", False),
    ("Astrophysics for People in a Hurry", "Neil deGrasse Tyson", "science", 2017, "13.00", True),
    ("1984", "George Orwell", "fiction", 1949, "10.00", True),
    ("Brave New World", "Aldous Huxley", "fiction", 1932, "11.00", True),
    ("To Kill a Mockingbird", "Harper Lee", "fiction", 1960, "12.00", False),
    ("The Great Gatsby", "F. Scott Fitzgerald", "fiction", 1925, "9.50", True),
    ("One Hundred Years of Solitude", "Gabriel García Márquez", "fiction", 1967, "16.00", True),
    ("Beloved", "Toni Morrison", "fiction", 1987, "14.50", False),
    ("The Hobbit", "J.R.R. Tolkien", "fantasy", 1937, "13.50", True),
    ("The Fellowship of the Ring", "J.R.R. Tolkien", "fantasy", 1954, "15.00", True),
    ("A Wizard of Earthsea", "Ursula K. Le Guin", "fantasy", 1968, "11.50", True),
    ("The Name of the Wind", "Patrick Rothfuss", "fantasy", 2007, "17.00", False),
    ("American Gods", "Neil Gaiman", "fantasy", 2001, "16.50", True),
    ("Mistborn: The Final Empire", "Brandon Sanderson", "fantasy", 2006, "15.75", True),
    ("Sapiens", "Yuval Noah Harari", "history", 2011, "22.00", True),
    ("Guns, Germs, and Steel", "Jared Diamond", "history", 1997, "19.00", True),
    ("The Silk Roads", "Peter Frankopan", "history", 2015, "21.50", False),
    ("SPQR", "Mary Beard", "history", 2015, "20.50", True),
    ("The Guns of August", "Barbara Tuchman", "history", 1962, "17.50", True),
    ("A People's History of the United States", "Howard Zinn", "history", 1980, "18.50", False),
    ("Steve Jobs", "Walter Isaacson", "biography", 2011, "25.00", True),
    ("Long Walk to Freedom", "Nelson Mandela", "biography", 1994, "19.50", True),
    ("The Diary of a Young Girl", "Anne Frank", "biography", 1947, "10.50", True),
    ("Einstein: His Life and Universe", "Walter Isaacson", "biography", 2007, "24.00", False),
    ("Educated", "Tara Westover", "biography", 2018, "16.00", True),
    ("Born a Crime", "Trevor Noah", "biography", 2016, "15.00", True),
]


class Command(BaseCommand):
    help = "داده‌های نمونه کتاب را idempotent ایجاد می‌کند (اجرای مجدد، تکرار نمی‌سازد)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--with-users",
            action="store_true",
            help="کاربران آموزشی student و admin را با رمزهای DEMO_*_PASSWORD از .env بساز.",
        )

    def handle(self, *args, **options):
        created = 0
        for title, author, genre, year, price, available in BOOKS:
            _, was_created = Book.objects.update_or_create(
                title=title,
                author=author,
                defaults={
                    "genre": genre,
                    "publication_year": year,
                    "price": price,
                    "is_available": available,
                    "description": f"{title} by {author} ({year}).",
                },
            )
            created += was_created
        self.stdout.write(self.style.SUCCESS(
            f"Books: {created} created, {len(BOOKS) - created} updated, total {Book.objects.count()}."
        ))
        if options["with_users"]:
            self._seed_users()

    def _seed_users(self):
        User = get_user_model()
        for username, env_name, staff in (
            ("student", "DEMO_STUDENT_PASSWORD", False),
            ("admin", "DEMO_ADMIN_PASSWORD", True),
        ):
            password = os.environ.get(env_name)
            if not password:
                self.stdout.write(self.style.WARNING(f"{env_name} is not set; skipping user '{username}'."))
                continue
            user, _ = User.objects.get_or_create(username=username)
            user.is_staff = staff
            user.is_superuser = staff
            user.set_password(password)
            user.save()
            self.stdout.write(f"User '{username}' ready (staff={staff}).")

"""
Seeds the 'about_sections' and 'news_posts' tables from their respective CSV
files in this folder. Safe to re-run: it creates the tables if they don't
exist yet, then replaces their contents with whatever is currently in the CSVs.

Office addresses / contact no. / email / social links are NOT handled here -
those live in the existing 'site_settings' table (managed on the admin side),
and are read directly by db_handler.get_site_settings().

To update the About Us / News page content later, just edit:
    - about_us_content.csv
    - news_posts.csv
and re-run this script:
    python database/seed_site_content.py
"""
import csv
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db_handler import get_db_connection

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS about_sections (
    id SERIAL PRIMARY KEY,
    sort_order INTEGER NOT NULL DEFAULT 0,
    title TEXT,
    content TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS news_posts (
    id SERIAL PRIMARY KEY,
    sort_order INTEGER NOT NULL DEFAULT 0,
    title TEXT NOT NULL,
    author TEXT,
    post_date DATE,
    tags TEXT,
    image TEXT,
    content TEXT NOT NULL
);
"""


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_date_or_none(value):
    value = (value or "").strip()
    return value if value else None


def seed_about_sections(cursor, csv_filepath):
    with open(csv_filepath, mode="r", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    cursor.execute("TRUNCATE TABLE about_sections RESTART IDENTITY;")
    for row in rows:
        cursor.execute(
            """
            INSERT INTO about_sections (sort_order, title, content)
            VALUES (%s, %s, %s);
            """,
            (_to_int(row.get("sort_order")), row.get("title", "").strip(), row.get("content", "").strip())
        )
    print(f"  about_sections: seeded {len(rows)} section(s)")


def seed_news_posts(cursor, csv_filepath):
    with open(csv_filepath, mode="r", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    cursor.execute("TRUNCATE TABLE news_posts RESTART IDENTITY;")
    for row in rows:
        cursor.execute(
            """
            INSERT INTO news_posts (sort_order, title, author, post_date, tags, image, content)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """,
            (
                _to_int(row.get("sort_order")),
                row.get("title", "").strip(),
                row.get("author", "").strip(),
                _to_date_or_none(row.get("post_date")),
                row.get("tags", "").strip(),
                row.get("image", "").strip(),
                row.get("content", "").strip(),
            )
        )
    print(f"  news_posts: seeded {len(rows)} post(s)")


def run():
    conn = get_db_connection()
    cursor = conn.cursor()

    print("Ensuring tables exist...")
    cursor.execute(CREATE_TABLES_SQL)

    print("Seeding about_sections from about_us_content.csv...")
    seed_about_sections(cursor, os.path.join(CURRENT_DIR, "about_us_content.csv"))

    print("Seeding news_posts from news_posts.csv...")
    seed_news_posts(cursor, os.path.join(CURRENT_DIR, "news_posts.csv"))

    conn.commit()
    cursor.close()
    conn.close()
    print("\nDone. About Us and News/Blog pages will now read from these tables.")
    print("(Office addresses / contact info / social links come from your existing site_settings table.)")


if __name__ == "__main__":
    run()
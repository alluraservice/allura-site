"""
Applies database/migrations/2026_10_15_data_update.sql to the configured database
(local allura_db, or DATABASE_URL on Render).

    python -m database.apply_data_update        (run from the project root)

It first applies the schema upgrade (new columns, reference-number trigger), then the data update.
"""
import os

from database.admin_schema import ensure_admin_schema
from database.dbconnect import getdblocation

SQL_FILE = os.path.join(os.path.dirname(__file__), 'migrations', '2026_10_15_data_update.sql')


def main():
    print("Applying schema upgrade…")
    ensure_admin_schema()
    with open(SQL_FILE, encoding='utf-8') as f:
        sql = f.read()
    db = getdblocation()
    try:
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) FROM inquiries;")
        before = cur.fetchone()[0]
        cur.execute(sql)
        db.commit()
        cur.execute("SELECT COUNT(*) FROM inquiries;")
        after = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM items WHERE COALESCE(is_featured, FALSE);")
        featured = cur.fetchone()[0]
        print(f"Done. Inquiries: {before} → {after} (+{after - before}). Featured items now: {featured}.")
    finally:
        db.close()


if __name__ == '__main__':
    main()

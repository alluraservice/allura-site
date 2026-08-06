import pandas as pd
import psycopg2
from sqlalchemy import create_engine

# Verified PostgreSQL Credentials
DB_CONFIG = {
    "dbname": "allura_db",
    "user": "postgres",
    "password": "admin",
    "host": "localhost",
    "port": 5432,
}

# SQLAlchemy engine for Pandas integration
DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
engine = create_engine(DATABASE_URL)


def get_db_connection():
    return psycopg2.connect(
        dbname=DB_CONFIG["dbname"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        host=DB_CONFIG["host"],
        port=str(DB_CONFIG["port"])
    )


def fetch_data_df(query: str, params=None) -> pd.DataFrame:
    """Executes a SELECT query and returns the results as a Pandas DataFrame."""
    try:
        df = pd.read_sql_query(query, con=engine, params=params)
        return df
    except Exception as e:
        print(f"[DB ERROR] Read failed: {e}")
        return pd.DataFrame()


def execute_query(query: str, params=None) -> int:
    """Executes INSERT, UPDATE, or DELETE SQL statements safely."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.rowcount
    except Exception as e:
        print(f"[DB ERROR] Write failed: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()


# ==============================================================================
# CATEGORY RETRIEVAL FUNCTIONS
# ==============================================================================

def get_categories_by_type(item_type: str) -> list:
    """
    Fetches distinct category names for Header Dropdowns based on item type ('Product' or 'Service').
    Returns a sorted list of unique category strings.
    """
    query = """
        SELECT DISTINCT c.name AS category
        FROM categories c
        JOIN types t ON c.type_id = t.id
        WHERE LOWER(t.name) = LOWER(%s) AND c.name IS NOT NULL AND c.name != ''
        ORDER BY c.name ASC;
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (item_type,))
            rows = cursor.fetchall()
            
            categories = [row[0] for row in rows]
            print(f"[DEBUG] Fetching type='{item_type}' -> Found {len(categories)} categories: {categories}")
            
            return categories
    except Exception as e:
        print(f"[DB ERROR] Failed to fetch categories for type '{item_type}': {e}")
        return []
    finally:
        conn.close()


def get_category_cards_by_type(item_type: str) -> list:
    """
    Fetches category metadata (slug/id, title, image_path) for Carousel Cards 
    in product_categories.py and service_categories.py based on item type ('Product' or 'Service').
    """
    query = """
        SELECT 
            c.id,
            c.name,
            LOWER(REPLACE(REPLACE(c.name, ' ', '-'), '/', '-')) AS slug,
            c.image_path
        FROM categories c
        JOIN types t ON c.type_id = t.id
        WHERE LOWER(t.name) = LOWER(%s) AND c.name IS NOT NULL AND c.name != ''
        ORDER BY c.id ASC;
    """
    df = fetch_data_df(query, params=(item_type,))
    
    if df.empty:
        return []
    
    default_img = (
        "/assets/icons/service_icon.svg" 
        if item_type.lower() == "service" 
        else "/assets/icons/product_icon.svg"
    )

    categories = []
    for _, row in df.iterrows():
        img_val = row.get("image_path")
        
        if pd.notna(img_val) and str(img_val).strip() != "":
            image_src = str(img_val).strip()
        else:
            image_src = default_img

        categories.append({
            "id": row.get("slug") or str(row.get("id")),
            "title": row.get("name"),
            "img": image_src
        })
    
    return categories


def get_about_sections() -> list:
    """
    Fetches editable About Us page sections (title + body content) in display order.
    Content is stored as Markdown so bullet lists / bold text render correctly.
    Populate/edit via database/about_us_content.csv + seed_site_content.py.
    """
    query = "SELECT title, content FROM about_sections ORDER BY sort_order ASC, id ASC;"
    df = fetch_data_df(query)
    if df.empty:
        return []
    return df.to_dict('records')


def get_news_posts() -> list:
    """
    Fetches editable News/Blog posts in display order.
    Populate/edit via database/news_posts.csv + seed_site_content.py.
    """
    query = """
        SELECT title, author, post_date, tags, image, content
        FROM news_posts
        ORDER BY sort_order ASC, post_date DESC NULLS LAST, id DESC;
    """
    df = fetch_data_df(query)
    if df.empty:
        return []

    df['post_date'] = df['post_date'].apply(lambda d: d.strftime('%b %d, %Y') if pd.notna(d) else '')
    df['image'] = df['image'].apply(lambda x: x if pd.notna(x) and str(x).strip() != '' else '/assets/pictures/cover_photo.jpg')
    return df.to_dict('records')


def _extract_social_url(raw_value):
    """facebook_link is stored as jsonb; handles it being null, a plain string,
    or an object like {"url": "..."}. linkedin_link is plain text so this also
    just passes plain strings through unchanged."""
    if raw_value is None:
        return None
    if isinstance(raw_value, dict):
        return raw_value.get('url') or raw_value.get('link') or None
    text = str(raw_value).strip()
    if not text or text.lower() == 'null':
        return None
    return text


def get_site_settings() -> dict:
    """
    Fetches the single-row 'site_settings' table: contact email/phone, main +
    satellite office addresses, and Facebook/LinkedIn links. Used by the Contact
    Info sidebar and embedded maps on About Us / Contact Us, and the social icon
    row on About Us / News / Contact Us.
    This is admin-managed (not CSV-seeded) since it already existed as a live table.
    """
    query = """
        SELECT contact_email, contact_phone, main_office_address,
               satellite_office_address, facebook_link, linkedin_link
        FROM site_settings
        LIMIT 1;
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()
            if not row:
                return {}
            (contact_email, contact_phone, main_office_address,
             satellite_office_address, facebook_link, linkedin_link) = row
            return {
                "contact_email": contact_email,
                "contact_phone": contact_phone,
                "main_office_address": main_office_address,
                "satellite_office_address": satellite_office_address,
                "facebook_url": _extract_social_url(facebook_link),
                "linkedin_url": _extract_social_url(linkedin_link),
            }
    except Exception as e:
        print(f"[DB ERROR] Failed to fetch site_settings: {e}")
        return {}
    finally:
        conn.close()


def get_category_by_slug_or_id(cat_identifier: str) -> dict:
    """
    Fetches single category info (name, description, id) to populate cat_info/category_info 
    on product_list.py or service_list.py.
    """
    query = """
        SELECT 
            c.id,
            c.name,
            NULL AS description,
            LOWER(REPLACE(REPLACE(c.name, ' ', '-'), '/', '-')) AS slug
        FROM categories c
        WHERE CAST(c.id AS TEXT) = %s 
           OR LOWER(REPLACE(REPLACE(c.name, ' ', '-'), '/', '-')) = LOWER(%s)
           OR LOWER(c.name) = LOWER(%s)
        LIMIT 1;
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (str(cat_identifier), str(cat_identifier), str(cat_identifier)))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "slug": row[3]
                }
        return None
    except Exception as e:
        print(f"[DB ERROR] Failed to fetch category for identifier '{cat_identifier}': {e}")
        return None
    finally:
        conn.close()
"""
Idempotent schema upgrade for the admin pages (inbox, accounts, my account, analytics, password reset).

Every step is safe to repeat, so this runs on every app start (index.py calls ensure_admin_schema()).
After the schema steps, ONE_TIME_UPDATES (data changes) are applied once per database.
Each step runs and commits on its own: if one fails (e.g. an older PostgreSQL), the rest still apply
and the error is printed.
"""
from database.dbconnect import getdblocation

ADMIN_SCHEMA_STEPS = [
    # ---------- Inquiries: inbox organisation fields ----------
    """
    ALTER TABLE inquiries ADD COLUMN IF NOT EXISTS source             VARCHAR(40)  DEFAULT 'Contact Us';
    ALTER TABLE inquiries ADD COLUMN IF NOT EXISTS source_detail      TEXT;
    ALTER TABLE inquiries ADD COLUMN IF NOT EXISTS reference_no       VARCHAR(24);
    ALTER TABLE inquiries ADD COLUMN IF NOT EXISTS priority           VARCHAR(10)  DEFAULT 'Normal';
    ALTER TABLE inquiries ADD COLUMN IF NOT EXISTS is_read            BOOLEAN      DEFAULT FALSE;
    ALTER TABLE inquiries ADD COLUMN IF NOT EXISTS is_starred         BOOLEAN      DEFAULT FALSE;
    ALTER TABLE inquiries ADD COLUMN IF NOT EXISTS is_archived        BOOLEAN      DEFAULT FALSE;
    ALTER TABLE inquiries ADD COLUMN IF NOT EXISTS assigned_to        INTEGER;
    ALTER TABLE inquiries ADD COLUMN IF NOT EXISTS labels             TEXT         DEFAULT '';
    ALTER TABLE inquiries ADD COLUMN IF NOT EXISTS updated_at         TIMESTAMP    DEFAULT NOW();
    ALTER TABLE inquiries ADD COLUMN IF NOT EXISTS first_response_at  TIMESTAMP;
    ALTER TABLE inquiries ADD COLUMN IF NOT EXISTS resolved_at        TIMESTAMP;
    """,

    # ---------- Inquiry channels: one name per website form ----------
    #   Product Page = "Contact Sales" on a product · Service Page = Services page form · Contact Us = Contact Us page
    """
    UPDATE inquiries SET source = 'Product Page' WHERE source IN ('Product Quote', 'Product', 'Contact Sales');
    UPDATE inquiries SET source = 'Service Page' WHERE source IN ('Service Inquiry', 'Service', 'Services');
    UPDATE inquiries SET source = 'Contact Us'   WHERE source IS NULL OR source = '';
    """,

    # ---------- Reference numbers: ALR-YYMM-00042, given to every inquiry automatically ----------
    """
    CREATE OR REPLACE FUNCTION allura_set_inquiry_ref() RETURNS trigger AS $fn$
    BEGIN
        IF NEW.reference_no IS NULL OR NEW.reference_no = '' THEN
            NEW.reference_no := 'ALR-' || to_char(COALESCE(NEW.created_at, NOW()), 'YYMM') || '-' || lpad(NEW.id::text, 5, '0');
        END IF;
        RETURN NEW;
    END
    $fn$ LANGUAGE plpgsql;
    """,
    """
    DO $do$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_inquiry_reference_no') THEN
            CREATE TRIGGER trg_inquiry_reference_no BEFORE INSERT ON inquiries
                FOR EACH ROW EXECUTE FUNCTION allura_set_inquiry_ref();
        END IF;
    END
    $do$;
    """,
    """
    UPDATE inquiries
       SET reference_no = 'ALR-' || to_char(COALESCE(created_at, NOW()), 'YYMM') || '-' || lpad(id::text, 5, '0')
     WHERE reference_no IS NULL OR reference_no = '';
    CREATE UNIQUE INDEX IF NOT EXISTS idx_inquiries_reference_no ON inquiries(reference_no);
    """,

    # ---------- Conversation thread: replies sent + internal notes ----------
    """
    CREATE TABLE IF NOT EXISTS inquiry_messages (
        id          SERIAL PRIMARY KEY,
        inquiry_id  INTEGER NOT NULL REFERENCES inquiries(id) ON DELETE CASCADE,
        kind        VARCHAR(12) NOT NULL,           -- 'reply' | 'note' | 'event'
        author      TEXT,
        author_email TEXT,
        subject     TEXT,
        body        TEXT NOT NULL,
        sent_ok     BOOLEAN DEFAULT TRUE,
        created_at  TIMESTAMP DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_inquiry_messages_inquiry ON inquiry_messages(inquiry_id);
    """,

    # ---------- Accounts: login credentials, profile and account-management powers ----------
    """
    ALTER TABLE accounts ADD COLUMN IF NOT EXISTS personal_email        TEXT;
    ALTER TABLE accounts ADD COLUMN IF NOT EXISTS contact_number        TEXT;
    ALTER TABLE accounts ADD COLUMN IF NOT EXISTS password_hash         TEXT;
    ALTER TABLE accounts ADD COLUMN IF NOT EXISTS must_change_password  BOOLEAN   DEFAULT FALSE;
    ALTER TABLE accounts ADD COLUMN IF NOT EXISTS password_changed_at   TIMESTAMP;
    ALTER TABLE accounts ADD COLUMN IF NOT EXISTS last_login            TIMESTAMP;
    ALTER TABLE accounts ADD COLUMN IF NOT EXISTS can_manage_accounts   BOOLEAN   DEFAULT FALSE;   -- add / edit / delete accounts
    ALTER TABLE accounts ADD COLUMN IF NOT EXISTS can_grant_access      BOOLEAN   DEFAULT FALSE;   -- give / remove these two powers
    """,
    # Someone must always hold the "grant access" power. On first run it goes to the System Administrators
    # (or, if there are none, the oldest active account). After that, admins manage it on the Accounts page.
    """
    UPDATE accounts SET can_manage_accounts = TRUE, can_grant_access = TRUE
     WHERE role = 'System Administrator' AND COALESCE(status, 'Active') = 'Active'
       AND NOT EXISTS (SELECT 1 FROM accounts WHERE can_grant_access);
    UPDATE accounts SET can_manage_accounts = TRUE, can_grant_access = TRUE
     WHERE id = (SELECT MIN(id) FROM accounts WHERE COALESCE(status, 'Active') = 'Active')
       AND NOT EXISTS (SELECT 1 FROM accounts WHERE can_grant_access);
    """,

    # ---------- Forgot password: one-time reset links ----------
    """
    CREATE TABLE IF NOT EXISTS password_resets (
        id          SERIAL PRIMARY KEY,
        account_id  INTEGER NOT NULL,
        token_hash  TEXT NOT NULL UNIQUE,      -- only a SHA-256 of the emailed token is stored
        sent_to     TEXT,
        expires_at  TIMESTAMP NOT NULL,
        used_at     TIMESTAMP,
        created_at  TIMESTAMP DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_password_resets_account ON password_resets(account_id);
    """,

    # ---------- Uploaded photos (stored in the database so they survive redeploys) ----------
    """
    CREATE TABLE IF NOT EXISTS uploaded_images (
        id          SERIAL PRIMARY KEY,
        filename    TEXT,
        mime_type   TEXT NOT NULL,
        data        BYTEA NOT NULL,
        width       INTEGER,
        height      INTEGER,
        size_bytes  INTEGER,
        created_at  TIMESTAMP DEFAULT NOW()
    );
    """,
]


# ---------------------------------------------------------------------
# One-time data updates. Each runs ONCE per database (local or live), the first time the app starts
# after it's added here, and is then recorded in the schema_migrations table so it never repeats.
# This lets the live database be updated just by deploying, without logging into the database.
# To add a new one later: append ("a_new_unique_name", """ SQL """) to this list.
# ---------------------------------------------------------------------
ONE_TIME_UPDATES = [
    ("2026_10_15_unfeature_items_and_add_supplies_clinic_products", """
UPDATE items SET is_featured = FALSE WHERE COALESCE(is_featured, FALSE);

DO $$
DECLARE
    cat_clinic   INTEGER;
    cat_supplies INTEGER;
    mod_imaging  INTEGER;
    mod_infect   INTEGER;
    mod_monitor  INTEGER;
    mod_radprot  INTEGER;
    no_photo     CONSTANT TEXT := '/assets/icons/product_icon.svg';
BEGIN
    -- 1. Find the two existing product categories
    SELECT id INTO cat_clinic   FROM categories WHERE name ILIKE '%clinic%' ORDER BY id LIMIT 1;
    SELECT id INTO cat_supplies FROM categories WHERE name ILIKE '%suppl%'  ORDER BY id LIMIT 1;
    IF cat_clinic IS NULL OR cat_supplies IS NULL THEN
        RAISE EXCEPTION 'Could not find the "Clinic Equipment" and/or "Supplies" category. Check the names in the categories table.';
    END IF;

    -- 2. Sub-groups (modalities): reuse if a same-named one already exists in that category
    SELECT id INTO mod_imaging FROM modalities WHERE category_id = cat_supplies AND LOWER(name) = 'imaging consumables';
    IF mod_imaging IS NULL THEN
        INSERT INTO modalities (name, description, image_url, category_id)
        VALUES ('Imaging Consumables',
                'Films, cassettes, contrast media and injector syringes used every day in radiology departments.',
                'assets/pictures/products/supplies/supplies_cover.png', cat_supplies)
        RETURNING id INTO mod_imaging;
    END IF;

    SELECT id INTO mod_infect FROM modalities WHERE category_id = cat_supplies AND LOWER(name) = 'infection control';
    IF mod_infect IS NULL THEN
        INSERT INTO modalities (name, description, image_url, category_id)
        VALUES ('Infection Control',
                'Sanitizing products that help keep patient areas, clinics and waiting rooms clean.',
                'assets/pictures/products/supplies/supplies_cover.png', cat_supplies)
        RETURNING id INTO mod_infect;
    END IF;

    SELECT id INTO mod_monitor FROM modalities WHERE category_id = cat_clinic AND LOWER(name) = 'patient monitoring accessories';
    IF mod_monitor IS NULL THEN
        INSERT INTO modalities (name, description, image_url, category_id)
        VALUES ('Patient Monitoring Accessories',
                'Cables, sensors, probes and cuffs that connect patients to bedside and transport monitors.',
                'assets/pictures/products/clinic_equipment/clinic_equipment_cover.webp', cat_clinic)
        RETURNING id INTO mod_monitor;
    END IF;

    SELECT id INTO mod_radprot FROM modalities WHERE category_id = cat_clinic AND LOWER(name) = 'radiation protection';
    IF mod_radprot IS NULL THEN
        INSERT INTO modalities (name, description, image_url, category_id)
        VALUES ('Radiation Protection',
                'Lead shielding that protects patients and staff during X-ray, CT and fluoroscopy procedures.',
                'assets/pictures/products/clinic_equipment/clinic_equipment_cover.webp', cat_clinic)
        RETURNING id INTO mod_radprot;
    END IF;

    -- 3. Items (skipped if an item with the same name already exists)
    INSERT INTO items (modality_id, name, image_url, is_active, is_featured, description)
    SELECT v.modality_id, v.name, no_photo, TRUE, FALSE, v.description
    FROM (VALUES
        (mod_imaging, 'Medical Dry Imaging Film',
         'Dry laser imaging film for printing diagnostic images from X-ray, mammography, CT and MRI systems. '
         'Produces sharp, consistent prints without wet chemical processing, and is available in standard sizes for '
         'general radiography and mammography.'),
        (mod_imaging, 'X-Ray Cassette',
         'Radiographic cassette fitted with an intensifying screen, which converts X-rays into light to expose the film '
         'at a lower radiation dose. Available in common film sizes for general radiography.'),
        (mod_imaging, 'Contrast Media',
         'Radiocontrast agents that make blood vessels, organs and tissues stand out on X-ray, CT and angiography '
         'images, helping clinicians see structures that would otherwise be hard to distinguish.'),
        (mod_imaging, 'Contrast Injector Syringe',
         'Syringes for power injectors that deliver contrast media at a controlled rate and volume during CT, MRI and '
         'angiography procedures.'),
        (mod_infect, 'Hand and Air Sanitizer',
         'Sanitizers made from 100% plant extract, for hands and for treating the air in clinics, waiting areas and '
         'patient rooms. Available in a range of product lines and sizes.'),
        (mod_monitor, 'ECG Lead Wire and Trunk Cable',
         'ECG lead wires and trunk cables that connect electrodes to the patient monitor or ECG machine, available in '
         'configurations for common monitor brands.'),
        (mod_monitor, 'SpO2 Sensor',
         'SpO2 probes and extension cables for continuous pulse oximetry, measuring blood oxygen saturation and pulse '
         'rate.'),
        (mod_monitor, 'NIBP Cuff',
         'Blood pressure cuffs for non-invasive blood pressure (NIBP) monitoring, available in neonatal, child, adult '
         'and large adult sizes.'),
        (mod_monitor, 'Temperature Probe',
         'Skin and body-cavity temperature probes for continuous patient temperature monitoring.'),
        (mod_monitor, 'EEG Lead Wire',
         'EEG lead wires that connect scalp electrodes to the EEG machine for recording brain activity.'),
        (mod_monitor, 'IBP Cable',
         'Interface cables for invasive blood pressure (IBP) monitoring, connecting the pressure transducer to the '
         'patient monitor.'),
        (mod_radprot, 'Radiation Lead Shield',
         'Lead protective wear and shields, such as aprons, thyroid collars and gonad shields, that reduce radiation '
         'exposure for patients and staff during imaging procedures.')
    ) AS v(modality_id, name, description)
    WHERE NOT EXISTS (SELECT 1 FROM items i WHERE LOWER(i.name) = LOWER(v.name));
END
$$;
"""),
]


def _apply_one_time_updates(db):
    cur = db.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS schema_migrations (
                       name TEXT PRIMARY KEY, applied_at TIMESTAMP DEFAULT NOW());""")
    db.commit()
    for name, sql in ONE_TIME_UPDATES:
        cur.execute("SELECT 1 FROM schema_migrations WHERE name = %s;", (name,))
        if cur.fetchone():
            continue
        try:
            cur.execute(sql)
            cur.execute("INSERT INTO schema_migrations (name) VALUES (%s);", (name,))
            db.commit()
            print(f"[admin_schema] Applied one-time update: {name}")
        except Exception as e:
            db.rollback()
            print(f"[admin_schema] One-time update {name} failed (will retry next start): {e}")
    cur.close()


def ensure_admin_schema():
    """Applies every step. Never raises: a failing step is printed and the app keeps running."""
    ok = True
    db = None
    try:
        db = getdblocation()
    except Exception as e:
        print(f"[admin_schema] Could not connect to the database: {e}")
        return False
    try:
        for i, step in enumerate(ADMIN_SCHEMA_STEPS, start=1):
            try:
                cur = db.cursor()
                cur.execute(step)
                db.commit()
                cur.close()
            except Exception as e:
                db.rollback()
                ok = False
                print(f"[admin_schema] Step {i} failed: {e}")
        _apply_one_time_updates(db)
        return ok
    finally:
        db.close()

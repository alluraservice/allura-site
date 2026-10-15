"""
Idempotent schema upgrade for the admin pages (inbox, accounts, my account, analytics, password reset).

Every step is safe to repeat, so this runs on every app start (index.py calls ensure_admin_schema()).
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
        return ok
    finally:
        db.close()

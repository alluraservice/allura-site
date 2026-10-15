from database.dbconnect import getdblocation


def get_categories_by_type(type_name):
    """Fetches categories linked to a specific type name (e.g., Product or Service)"""
    db = getdblocation()
    cur = db.cursor()
    query = """
        SELECT c.id, c.name, c.description, c.image_url
        FROM categories c
        JOIN types t ON c.type_id = t.id
        WHERE LOWER(t.name) = LOWER(%s);
    """
    cur.execute(query, (type_name,))
    columns = [desc[0] for desc in cur.description]
    results = [dict(zip(columns, row)) for row in cur.fetchall()]
    db.close()
    return results


def get_modalities_by_category(category_id):
    """Fetches modalities linked to a specific category ID"""
    db = getdblocation()
    cur = db.cursor()
    query = """
        SELECT id, name, description, image_url, category_id
        FROM modalities
        WHERE category_id = %s;
    """
    cur.execute(query, (category_id,))
    columns = [desc[0] for desc in cur.description]
    results = [dict(zip(columns, row)) for row in cur.fetchall()]
    db.close()
    return results


def get_items_by_modality(modality_id, include_hidden=False):
    """Fetches items linked to a specific modality ID (hidden items only when include_hidden=True)"""
    db = getdblocation()
    cur = db.cursor()
    query = f"""
        SELECT id, modality_id, name, image_url, is_active, is_featured, description
        FROM items
        WHERE modality_id = %s {'' if include_hidden else 'AND COALESCE(is_active, TRUE)'}
        ORDER BY name;
    """
    cur.execute(query, (modality_id,))
    columns = [desc[0] for desc in cur.description]
    results = [dict(zip(columns, row)) for row in cur.fetchall()]
    db.close()
    return results


def get_modalities():
    """Fetches all modalities for homepage carousels or general views"""
    db = getdblocation()
    cur = db.cursor()
    cur.execute("SELECT id, name, description, image_url, category_id FROM modalities;")
    columns = [desc[0] for desc in cur.description]
    results = [dict(zip(columns, row)) for row in cur.fetchall()]
    db.close()
    return results


def get_categories_with_types():
    """Fetches product categories (excluding services) and nests their modalities for the sidebar."""
    db = getdblocation()
    cur = db.cursor()
    query = """
        SELECT
            c.id AS category_id,
            c.name AS category_name,
            COALESCE(
                json_agg(
                    json_build_object('id', m.id, 'name', m.name)
                ) FILTER (WHERE m.id IS NOT NULL), '[]'
            ) AS types
        FROM categories c
        JOIN types t ON c.type_id = t.id
        LEFT JOIN modalities m ON c.id = m.category_id
        WHERE LOWER(t.name) NOT LIKE '%service%'
        GROUP BY c.id, c.name
        ORDER BY c.id;
    """
    cur.execute(query)
    rows = cur.fetchall()
    categories = [{"id": row[0], "name": row[1], "types": row[2]} for row in rows]
    cur.close()
    db.close()
    return categories


def get_all_items(include_hidden=False):
    """Fetches all active items across all modalities and categories (hidden ones only for the admin)"""
    db = getdblocation()
    cur = db.cursor()
    query = f"""
        SELECT id, modality_id, name, image_url, is_active, is_featured, description
        FROM items
        {'' if include_hidden else 'WHERE COALESCE(is_active, TRUE)'}
        ORDER BY name;
    """
    cur.execute(query)
    columns = [desc[0] for desc in cur.description]
    results = [dict(zip(columns, row)) for row in cur.fetchall()]
    db.close()
    return results


def get_items_by_category(category_id, include_hidden=False):
    """Fetches all items linked to modalities belonging to a specific category ID"""
    db = getdblocation()
    cur = db.cursor()
    query = f"""
        SELECT i.id, i.modality_id, i.name, i.image_url, i.is_active, i.is_featured, i.description
        FROM items i
        JOIN modalities m ON i.modality_id = m.id
        WHERE m.category_id = %s {'' if include_hidden else 'AND COALESCE(i.is_active, TRUE)'}
        ORDER BY i.name;
    """
    cur.execute(query, (category_id,))
    columns = [desc[0] for desc in cur.description]
    results = [dict(zip(columns, row)) for row in cur.fetchall()]
    db.close()
    return results


def get_item_by_id(item_id):
    """Fetches a single product/item by its ID, joining category and modality names."""
    db = getdblocation()
    if not db:
        return None
    try:
        cur = db.cursor()
        query = """
            SELECT i.id, i.name, i.description, i.image_url, c.name AS category_name, m.name AS modality_name,
                   i.modality_id, m.category_id, COALESCE(i.is_active, TRUE), COALESCE(i.is_featured, FALSE)
            FROM items i
            LEFT JOIN modalities m ON i.modality_id = m.id
            LEFT JOIN categories c ON m.category_id = c.id
            WHERE i.id = %s;
        """
        cur.execute(query, (item_id,))
        row = cur.fetchone()
        if row:
            return {
                "id": row[0], "name": row[1], "description": row[2], "image_url": row[3],
                "category_name": row[4] or "Products", "modality_name": row[5] or "General",
                "modality_id": row[6], "category_id": row[7], "is_active": row[8], "is_featured": row[9],
            }
        return None
    except Exception as e:
        print(f"Error fetching item by id ({item_id}): {e}")
        return None
    finally:
        db.close()


def get_modality_id_by_name(modality_name):
    """Helper to fetch modality ID based on its name string"""
    db = getdblocation()
    if not db:
        return None
    try:
        cur = db.cursor()
        cur.execute("SELECT id FROM modalities WHERE LOWER(name) = LOWER(%s);", (modality_name,))
        row = cur.fetchone()
        cur.close()
        return row[0] if row else None
    except Exception as e:
        print(f"Error fetching modality ID: {e}")
        return None
    finally:
        db.close()


# =====================================================================
#  Shared query helper
# =====================================================================
import re
import unicodedata
from datetime import datetime, timedelta

_DEFAULTS = {'all': [], 'one': None, 'scalar': None, 'none': False}


def _run(sql, params=None, fetch='all', commit=False):
    """Runs one statement and returns dict rows / one dict / a scalar / True. Never raises."""
    db = None
    try:
        db = getdblocation()
        cur = db.cursor()
        cur.execute(sql, params or ())
        result = True
        if fetch == 'all':
            cols = [d[0] for d in cur.description]
            result = [dict(zip(cols, r)) for r in cur.fetchall()]
        elif fetch == 'one':
            row = cur.fetchone()
            result = dict(zip([d[0] for d in cur.description], row)) if row else None
        elif fetch == 'scalar':
            row = cur.fetchone()
            result = row[0] if row else None
        if commit:
            db.commit()
        cur.close()
        return result
    except Exception as e:
        print(f"[db] {e}\n     SQL: {' '.join(sql.split())[:200]}")
        if db:
            db.rollback()
        return _DEFAULTS[fetch]
    finally:
        if db:
            db.close()


# =====================================================================
#  Inquiries
# =====================================================================
INQUIRY_STATUSES = ['New', 'Urgent', 'In Progress', 'Resolved']
INQUIRY_PRIORITIES = ['High', 'Normal', 'Low']
# Which website form the inquiry came from
SOURCE_PRODUCT, SOURCE_SERVICE, SOURCE_CONTACT = 'Product Page', 'Service Page', 'Contact Us'
INQUIRY_SOURCES = [SOURCE_PRODUCT, SOURCE_SERVICE, SOURCE_CONTACT]
SOURCE_DESCRIPTIONS = {
    SOURCE_PRODUCT: "“Contact Sales” on a product page",
    SOURCE_SERVICE: "Service inquiry form on the Services page",
    SOURCE_CONTACT: "Inquiry form on the Contact Us page",
}
INQUIRY_LABELS = ['Quotation Sent', 'Follow-up', 'Site Visit', 'Demo Request',
                  'Service Contract', 'Warranty', 'Government / Bidding']


def create_inquiry(customer_name, address, contact_person, department, phone, email, machine_inquiry, remarks,
                   source=SOURCE_CONTACT, source_detail=None):
    """
    Saves a customer inquiry from one of the website forms.
    Returns {'id': ..., 'reference_no': 'ALR-2610-00042'} or None.
    The reference number is set by the database trigger (see admin_schema.py).
    """
    return _run("""
        INSERT INTO inquiries (customer_name, address, contact_person, department, phone, email,
                               machine_inquiry, remarks, status, source, source_detail, priority, is_read)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'New', %s, %s, 'Normal', FALSE)
        RETURNING id, reference_no;
    """, [customer_name, address, contact_person, department, phone, email, machine_inquiry, remarks,
          source if source in INQUIRY_SOURCES else SOURCE_CONTACT, source_detail], fetch='one', commit=True)


def insert_inquiry(customer_name, address, contact_person, department, phone, email, machine_inquiry, remarks,
                   source=SOURCE_CONTACT):
    """Older name kept for compatibility. Prefer create_inquiry(), which returns the reference number."""
    return bool(create_inquiry(customer_name, address, contact_person, department, phone, email,
                               machine_inquiry, remarks, source))


def get_all_inquiries(status_filter=None):
    """Fetches all inquiries, with optional filtering by status tag"""
    if status_filter and status_filter.lower() != 'all':
        return _run("""SELECT id, reference_no, customer_name, email, phone, machine_inquiry, status, source, created_at
                       FROM inquiries WHERE LOWER(status) = LOWER(%s) ORDER BY created_at DESC;""", [status_filter])
    return _run("""SELECT id, reference_no, customer_name, email, phone, machine_inquiry, status, source, created_at
                   FROM inquiries ORDER BY created_at DESC;""")


def get_inquiry_by_id(inquiry_id):
    """Fetches full details of a specific inquiry"""
    return _run("""SELECT id, reference_no, customer_name, address, contact_person, department, phone, email,
                          machine_inquiry, remarks, status, source, source_detail, created_at
                   FROM inquiries WHERE id = %s;""", [inquiry_id], fetch='one')


def update_inquiry_status(inquiry_id, new_status):
    """Updates the status tag of an inquiry (e.g. New -> In Progress -> Resolved)"""
    return update_inquiry_fields(inquiry_id, status=new_status)


CATEGORY_CASE_SQL = """
    CASE
        WHEN LOWER(machine_inquiry) LIKE '%%ultrasound%%' OR LOWER(machine_inquiry) LIKE '%%affiniti%%'
             OR LOWER(machine_inquiry) LIKE '%%epiq%%' OR LOWER(machine_inquiry) LIKE '%%lumify%%' THEN 'Ultrasound'
        WHEN LOWER(machine_inquiry) LIKE '%%c-arm%%' OR LOWER(machine_inquiry) LIKE '%%zenition%%' THEN 'C-Arm'
        WHEN LOWER(machine_inquiry) LIKE '%%x-ray%%' OR LOWER(machine_inquiry) LIKE '%%xray%%'
             OR LOWER(machine_inquiry) LIKE '%%digieye%%' OR LOWER(machine_inquiry) LIKE '%%mobieye%%' THEN 'X-Ray'
        WHEN LOWER(machine_inquiry) LIKE '%%cath%%' OR LOWER(machine_inquiry) LIKE '%%azurion%%' THEN 'Cath Lab'
        WHEN LOWER(machine_inquiry) LIKE '%%mri%%' THEN 'MRI'
        WHEN LOWER(machine_inquiry) LIKE '%%ct %%' OR LOWER(machine_inquiry) LIKE '%%ct scan%%'
             OR LOWER(machine_inquiry) LIKE '%%incisive%%' THEN 'CT Scan'
        WHEN LOWER(machine_inquiry) LIKE '%%mammo%%' THEN 'Mammography'
        WHEN LOWER(machine_inquiry) LIKE '%%ups%%' OR LOWER(machine_inquiry) LIKE '%%power%%'
             OR LOWER(machine_inquiry) LIKE '%%electrical%%' THEN 'Power & Electrical'
        WHEN LOWER(machine_inquiry) LIKE '%%repair%%' OR LOWER(machine_inquiry) LIKE '%%maintenance%%'
             OR LOWER(machine_inquiry) LIKE '%%install%%' OR LOWER(machine_inquiry) LIKE '%%service%%' THEN 'Equipment Service'
        ELSE 'Other / Supplies'
    END
"""


def get_analytics_summary():
    """High-level KPI metrics (legacy helper)"""
    row = _run("""
        SELECT COUNT(*) AS total_inquiries,
               COUNT(*) FILTER (WHERE LOWER(status) = 'urgent') AS urgent_count,
               COUNT(*) FILTER (WHERE LOWER(status) = 'resolved') AS resolved_count,
               (SELECT COUNT(*) FROM items) AS total_items
        FROM inquiries;
    """, fetch='one') or {}
    return {k: int(row.get(k) or 0) for k in ('total_inquiries', 'urgent_count', 'resolved_count', 'total_items')}


def get_inquiries_by_modality_stats():
    """Aggregates inquiries by equipment category (legacy helper)"""
    rows = _run(f"SELECT {CATEGORY_CASE_SQL} AS modality, COUNT(*) AS count FROM inquiries GROUP BY 1 ORDER BY count DESC;")
    return [{"modality": r['modality'], "count": r['count']} for r in rows]


def get_top_inquiring_institutions(limit=5):
    """Top hospital clients by inquiry volume (legacy helper)"""
    return _run("""
        SELECT customer_name, COUNT(*) AS inquiry_count, MAX(created_at) AS last_inquiry
        FROM inquiries GROUP BY customer_name ORDER BY inquiry_count DESC LIMIT %s;
    """, [limit])


_PERIOD_SQL = {
    'today': "i.created_at >= date_trunc('day', NOW())",
    '7d': "i.created_at >= NOW() - INTERVAL '7 days'",
    '30d': "i.created_at >= NOW() - INTERVAL '30 days'",
    '90d': "i.created_at >= NOW() - INTERVAL '90 days'",
    'year': "i.created_at >= date_trunc('year', NOW())",
}

_SORT_SQL = {
    'newest': "i.created_at DESC",
    'oldest': "i.created_at ASC",
    'updated': "COALESCE(i.updated_at, i.created_at) DESC",
    'customer': "LOWER(i.customer_name) ASC, i.created_at DESC",
    'priority': "CASE i.priority WHEN 'High' THEN 0 WHEN 'Normal' THEN 1 ELSE 2 END, i.created_at DESC",
    'status': "CASE i.status WHEN 'Urgent' THEN 0 WHEN 'New' THEN 1 WHEN 'In Progress' THEN 2 ELSE 3 END, i.created_at DESC",
}

_NOT_ARCHIVED = "COALESCE(i.is_archived, FALSE) = FALSE"


def _folder_clause(folder, me_id):
    if folder == 'unread':
        return f"{_NOT_ARCHIVED} AND COALESCE(i.is_read, FALSE) = FALSE", []
    if folder == 'starred':
        return "COALESCE(i.is_starred, FALSE) = TRUE", []
    if folder == 'mine':
        return f"{_NOT_ARCHIVED} AND i.assigned_to = %s", [me_id or -1]
    if folder == 'archived':
        return "COALESCE(i.is_archived, FALSE) = TRUE", []
    if folder in INQUIRY_STATUSES:
        return f"{_NOT_ARCHIVED} AND i.status = %s", [folder]
    if folder and folder.startswith('source:'):
        return f"{_NOT_ARCHIVED} AND COALESCE(i.source, 'Contact Us') = %s", [folder[7:]]
    if folder and folder.startswith('label:'):
        return "(',' || COALESCE(i.labels, '') || ',') ILIKE %s", [f"%,{folder[6:]},%"]
    return _NOT_ARCHIVED, []   # inbox


def search_inquiries(folder='inbox', search=None, source=None, priority=None, assignee=None,
                     period=None, sort='newest', me_id=None, limit=500):
    """Inbox list query. All filters are optional. Search also matches the reference number."""
    where, params = _folder_clause(folder, me_id)
    where = [where]

    if search and search.strip():
        term = f"%{search.strip()}%"
        where.append("""(i.customer_name ILIKE %s OR i.email ILIKE %s OR i.contact_person ILIKE %s
                         OR i.machine_inquiry ILIKE %s OR i.remarks ILIKE %s OR i.phone ILIKE %s
                         OR i.department ILIKE %s OR i.reference_no ILIKE %s OR i.source_detail ILIKE %s)""")
        params += [term] * 9
    if source:
        where.append("COALESCE(i.source, 'Contact Us') = %s")
        params.append(source)
    if priority:
        where.append("i.priority = %s")
        params.append(priority)
    if assignee == 'unassigned':
        where.append("i.assigned_to IS NULL")
    elif assignee:
        where.append("i.assigned_to = %s")
        params.append(int(assignee))
    if period in _PERIOD_SQL:
        where.append(_PERIOD_SQL[period])

    sql = f"""
        SELECT i.id, i.reference_no, i.customer_name, i.contact_person, i.email, i.phone, i.machine_inquiry, i.remarks,
               i.status, COALESCE(i.priority, 'Normal') AS priority, COALESCE(i.source, 'Contact Us') AS source,
               i.source_detail,
               COALESCE(i.is_read, FALSE) AS is_read, COALESCE(i.is_starred, FALSE) AS is_starred,
               COALESCE(i.is_archived, FALSE) AS is_archived, i.assigned_to, a.name AS assignee_name,
               COALESCE(i.labels, '') AS labels, i.created_at, i.updated_at,
               (SELECT COUNT(*) FROM inquiry_messages m WHERE m.inquiry_id = i.id AND m.kind = 'reply') AS reply_count,
               (SELECT COUNT(*) FROM inquiry_messages m WHERE m.inquiry_id = i.id AND m.kind = 'note') AS note_count
        FROM inquiries i
        LEFT JOIN accounts a ON a.id = i.assigned_to
        WHERE {' AND '.join(where)}
        ORDER BY {_SORT_SQL.get(sort, _SORT_SQL['newest'])}
        LIMIT {int(limit)};
    """
    return _run(sql, params)


def get_inquiry_folder_counts(me_id=None):
    row = _run(f"""
        SELECT
            COUNT(*) FILTER (WHERE {_NOT_ARCHIVED} AND COALESCE(i.is_read, FALSE) = FALSE) AS inbox,
            COUNT(*) FILTER (WHERE {_NOT_ARCHIVED} AND COALESCE(i.is_read, FALSE) = FALSE) AS unread,
            COUNT(*) FILTER (WHERE COALESCE(i.is_starred, FALSE)) AS starred,
            COUNT(*) FILTER (WHERE {_NOT_ARCHIVED} AND i.assigned_to = %s AND i.status <> 'Resolved') AS mine,
            COUNT(*) FILTER (WHERE {_NOT_ARCHIVED} AND i.status = 'New') AS "New",
            COUNT(*) FILTER (WHERE {_NOT_ARCHIVED} AND i.status = 'Urgent') AS "Urgent",
            COUNT(*) FILTER (WHERE {_NOT_ARCHIVED} AND i.status = 'In Progress') AS "In Progress",
            COUNT(*) FILTER (WHERE {_NOT_ARCHIVED} AND i.status = 'Resolved') AS "Resolved",
            COUNT(*) FILTER (WHERE {_NOT_ARCHIVED} AND COALESCE(i.source, 'Contact Us') = 'Product Page') AS "source:Product Page",
            COUNT(*) FILTER (WHERE {_NOT_ARCHIVED} AND COALESCE(i.source, 'Contact Us') = 'Service Page') AS "source:Service Page",
            COUNT(*) FILTER (WHERE {_NOT_ARCHIVED} AND COALESCE(i.source, 'Contact Us') = 'Contact Us') AS "source:Contact Us",
            COUNT(*) FILTER (WHERE COALESCE(i.is_archived, FALSE)) AS archived
        FROM inquiries i;
    """, [me_id or -1], fetch='one') or {}
    return {k: int(v or 0) for k, v in row.items()}


def get_inquiry_detail(inquiry_id):
    return _run("""
        SELECT i.*, COALESCE(i.priority, 'Normal') AS priority_v, COALESCE(i.source, 'Contact Us') AS source_v,
               a.name AS assignee_name, a.email AS assignee_email
        FROM inquiries i LEFT JOIN accounts a ON a.id = i.assigned_to
        WHERE i.id = %s;
    """, [inquiry_id], fetch='one')


def get_inquiry_messages(inquiry_id):
    return _run("""
        SELECT id, kind, author, author_email, subject, body, sent_ok, created_at
        FROM inquiry_messages WHERE inquiry_id = %s ORDER BY created_at ASC, id ASC;
    """, [inquiry_id])


def get_inquiries_by_ids(ids):
    if not ids:
        return []
    return _run("""
        SELECT i.reference_no, i.id, i.created_at, i.customer_name, i.contact_person, i.department, i.address,
               i.email, i.phone, i.source, i.source_detail, i.status, i.priority, a.name AS assigned_to, i.labels,
               i.machine_inquiry, i.remarks, i.first_response_at, i.resolved_at
        FROM inquiries i LEFT JOIN accounts a ON a.id = i.assigned_to
        WHERE i.id = ANY(%s) ORDER BY i.created_at DESC;
    """, [list(ids)])


_UPDATABLE = {'status', 'priority', 'assigned_to', 'labels', 'is_read', 'is_starred', 'is_archived'}


def bulk_update_inquiries(ids, **fields):
    """Updates whitelisted fields on one or more inquiries. Keeps resolved_at in sync with status."""
    ids = [int(i) for i in (ids or [])]
    fields = {k: v for k, v in fields.items() if k in _UPDATABLE}
    if not ids or not fields:
        return False
    sets, params = [], []
    for k, v in fields.items():
        sets.append(f"{k} = %s")
        params.append(v)
    if 'status' in fields:
        sets.append("resolved_at = COALESCE(resolved_at, NOW())" if fields['status'] == 'Resolved' else "resolved_at = NULL")
    if set(fields) & {'status', 'priority', 'assigned_to', 'labels'}:
        sets.append("updated_at = NOW()")
    params.append(ids)
    return _run(f"UPDATE inquiries SET {', '.join(sets)} WHERE id = ANY(%s);", params, fetch='none', commit=True)


def update_inquiry_fields(inquiry_id, **fields):
    return bulk_update_inquiries([inquiry_id], **fields)


def add_inquiry_message(inquiry_id, kind, body, author=None, author_email=None, subject=None, sent_ok=True):
    """kind: 'reply' (email sent to client), 'note' (internal), 'event' (activity log line)."""
    ok = _run("""
        INSERT INTO inquiry_messages (inquiry_id, kind, author, author_email, subject, body, sent_ok)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
    """, [inquiry_id, kind, author, author_email, subject, body, sent_ok], fetch='none', commit=True)
    if ok and kind == 'reply' and sent_ok:
        _run("UPDATE inquiries SET first_response_at = COALESCE(first_response_at, NOW()), updated_at = NOW() WHERE id = %s;",
             [inquiry_id], fetch='none', commit=True)
    elif ok and kind == 'note':
        _run("UPDATE inquiries SET updated_at = NOW() WHERE id = %s;", [inquiry_id], fetch='none', commit=True)
    return ok


# =====================================================================
#  Accounts, permissions & authentication
# =====================================================================
ACCOUNT_ROLES = ['System Administrator', 'Operations Director', 'Systems Consultant', 'Project Manager']

_ACCOUNT_COLS = """id, name, email, personal_email, contact_number, role, status, created_at,
                   last_login, must_change_password, password_changed_at,
                   COALESCE(can_manage_accounts, FALSE) AS can_manage_accounts,
                   COALESCE(can_grant_access, FALSE) AS can_grant_access"""


def get_all_accounts():
    """Fetches all registered admin/staff user accounts"""
    return _run(f"SELECT {_ACCOUNT_COLS} FROM accounts ORDER BY id ASC;")


def get_account_by_id(account_id):
    return _run(f"SELECT {_ACCOUNT_COLS}, password_hash FROM accounts WHERE id = %s;", [account_id], fetch='one')


def get_account_by_email(email):
    if not email:
        return None
    return _run(f"SELECT {_ACCOUNT_COLS}, password_hash FROM accounts WHERE LOWER(email) = LOWER(%s) ORDER BY id LIMIT 1;",
                [email.strip()], fetch='one')


def allura_email_exists(email, exclude_id=None):
    n = _run("SELECT COUNT(*) FROM accounts WHERE LOWER(email) = LOWER(%s) AND id <> %s;",
             [email.strip(), exclude_id or -1], fetch='scalar')
    return bool(n)


def suggest_allura_email(full_name, domain='alluraenterpriseph.com'):
    """'Juan Dela Cruz' -> juan.delacruz@domain (adds 2, 3... if taken)."""
    if not full_name or not full_name.strip():
        return ''
    ascii_name = unicodedata.normalize('NFKD', full_name).encode('ascii', 'ignore').decode().lower()
    parts = [p for p in (re.sub(r'[^a-z0-9]', '', p) for p in ascii_name.split()) if p]
    if not parts:
        return ''
    local = parts[0] if len(parts) == 1 else f"{parts[0]}.{''.join(parts[1:])}"
    candidate, n = f"{local}@{domain}", 2
    while allura_email_exists(candidate):
        candidate = f"{local}{n}@{domain}"
        n += 1
    return candidate


def create_account(name, email, personal_email, contact_number, role, status, password_hash,
                   can_manage_accounts=False, can_grant_access=False):
    """Creates a login-enabled account flagged to change its temporary password. Returns the new id or None."""
    return _run("""
        INSERT INTO accounts (name, email, personal_email, contact_number, role, status, password_hash,
                              must_change_password, password_changed_at, can_manage_accounts, can_grant_access)
        VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, NOW(), %s, %s) RETURNING id;
    """, [name, email.strip().lower(), personal_email, contact_number, role, status, password_hash,
          bool(can_manage_accounts), bool(can_grant_access)], fetch='scalar', commit=True)


def update_account_admin_fields(account_id, role, status, personal_email=None, contact_number=None):
    return _run("""
        UPDATE accounts SET role = %s, status = %s,
               personal_email = COALESCE(%s, personal_email), contact_number = COALESCE(%s, contact_number)
        WHERE id = %s;
    """, [role, status, personal_email, contact_number, account_id], fetch='none', commit=True)


def set_account_permissions(account_id, can_manage_accounts, can_grant_access):
    return _run("UPDATE accounts SET can_manage_accounts = %s, can_grant_access = %s WHERE id = %s;",
                [bool(can_manage_accounts), bool(can_grant_access), account_id], fetch='none', commit=True)


def count_access_granters(exclude_id=None):
    """Active accounts that can give/remove account powers (there must always be at least one)."""
    return int(_run("""SELECT COUNT(*) FROM accounts WHERE COALESCE(can_grant_access, FALSE)
                       AND COALESCE(status, 'Active') = 'Active' AND id <> %s;""",
                    [exclude_id or -1], fetch='scalar') or 0)


def delete_account(account_id):
    """Removes an account. Their inquiries become unassigned; the legacy admin_users login is removed too."""
    acc = get_account_by_id(account_id)
    if not acc:
        return False
    _run("UPDATE inquiries SET assigned_to = NULL WHERE assigned_to = %s;", [account_id], fetch='none', commit=True)
    _run("DELETE FROM password_resets WHERE account_id = %s;", [account_id], fetch='none', commit=True)
    # Without this, authenticate() would re-create the account from the old table on their next login
    _run("DELETE FROM admin_users WHERE LOWER(email) = LOWER(%s);", [acc['email']], fetch='none', commit=True)
    return _run("DELETE FROM accounts WHERE id = %s;", [account_id], fetch='none', commit=True)


def update_account_profile(account_id, name, personal_email, contact_number):
    return _run("UPDATE accounts SET name = %s, personal_email = %s, contact_number = %s WHERE id = %s;",
                [name, personal_email, contact_number, account_id], fetch='none', commit=True)


def set_account_password(account_id, password_hash, must_change=False):
    ok = _run("""
        UPDATE accounts SET password_hash = %s, must_change_password = %s, password_changed_at = NOW()
        WHERE id = %s;
    """, [password_hash, must_change, account_id], fetch='none', commit=True)
    # Keep the legacy login table in sync so old logins can't use a stale password
    acc = get_account_by_id(account_id)
    if ok and acc:
        _run("UPDATE admin_users SET password_hash = %s WHERE LOWER(email) = LOWER(%s);",
             [password_hash, acc['email']], fetch='none', commit=True)
    return ok


def record_login(account_id):
    _run("UPDATE accounts SET last_login = NOW() WHERE id = %s;", [account_id], fetch='none', commit=True)


def authenticate(email, password):
    """
    Returns (account_dict, error_message).
    Checks `accounts` first; falls back to the legacy `admin_users` table and copies that
    login into `accounts` so every admin ends up managed in one place.
    """
    from utils.security import check_password  # local import keeps db_handler importable without bcrypt

    email = (email or '').strip()
    acc = get_account_by_email(email)
    if acc and acc.get('password_hash'):
        if not check_password(password, acc['password_hash']):
            return None, "Incorrect email or password."
        if (acc.get('status') or 'Active') != 'Active':
            return None, "This account is inactive. Please contact an administrator."
        record_login(acc['id'])
        return acc, None

    legacy = _run("SELECT email, password_hash, first_name FROM admin_users WHERE LOWER(email) = LOWER(%s);",
                  [email], fetch='one')
    if not legacy or not check_password(password, legacy.get('password_hash')):
        return None, "Incorrect email or password."

    if acc:   # account row exists but had no password yet
        _run("UPDATE accounts SET password_hash = %s WHERE id = %s;", [legacy['password_hash'], acc['id']],
             fetch='none', commit=True)
        if (acc.get('status') or 'Active') != 'Active':
            return None, "This account is inactive. Please contact an administrator."
    else:
        _run("""INSERT INTO accounts (name, email, role, status, password_hash, must_change_password)
                VALUES (%s, %s, 'System Administrator', 'Active', %s, FALSE);""",
             [legacy.get('first_name') or email.split('@')[0], legacy['email'], legacy['password_hash']],
             fetch='none', commit=True)
    acc = get_account_by_email(email)
    if acc:
        record_login(acc['id'])
    return acc, None


# ---------------------------------------------------------------------
# Forgot password (one-time reset links)
# ---------------------------------------------------------------------
def find_account_for_recovery(email):
    """Active account whose login email OR personal email matches."""
    if not email:
        return None
    return _run(f"""
        SELECT {_ACCOUNT_COLS} FROM accounts
        WHERE (LOWER(email) = LOWER(%s) OR LOWER(COALESCE(personal_email, '')) = LOWER(%s))
          AND COALESCE(status, 'Active') = 'Active'
        ORDER BY (LOWER(email) = LOWER(%s)) DESC, id LIMIT 1;
    """, [email.strip()] * 3, fetch='one')


def create_password_reset(account_id, token_hash, sent_to, minutes=60):
    # Older links for this account stop working as soon as a new one is requested
    _run("UPDATE password_resets SET used_at = NOW() WHERE account_id = %s AND used_at IS NULL;",
         [account_id], fetch='none', commit=True)
    return _run("""INSERT INTO password_resets (account_id, token_hash, sent_to, expires_at)
                   VALUES (%s, %s, %s, NOW() + (%s || ' minutes')::interval);""",
                [account_id, token_hash, sent_to, str(int(minutes))], fetch='none', commit=True)


def get_valid_password_reset(token_hash):
    return _run("""
        SELECT r.id, r.account_id, r.expires_at, a.name, a.email, a.personal_email
        FROM password_resets r JOIN accounts a ON a.id = r.account_id
        WHERE r.token_hash = %s AND r.used_at IS NULL AND r.expires_at > NOW()
          AND COALESCE(a.status, 'Active') = 'Active';
    """, [token_hash], fetch='one')


def mark_password_reset_used(reset_id):
    return _run("UPDATE password_resets SET used_at = NOW() WHERE id = %s;", [reset_id], fetch='none', commit=True)


# =====================================================================
#  Analytics report
# =====================================================================
PERIOD_LABELS = {
    '7d': 'Last 7 days', '30d': 'Last 30 days', 'month': 'This month',
    'quarter': 'This quarter', 'year': 'This year', 'all': 'All time',
}


def period_bounds(period, now=None):
    """Returns (start, end, prev_start, prev_end, comparison_label). start=None means all time."""
    now = now or datetime.now()
    end = now
    if period == '7d':
        start = now - timedelta(days=7); prev = (start - timedelta(days=7), start); lbl = 'vs previous 7 days'
    elif period == '30d':
        start = now - timedelta(days=30); prev = (start - timedelta(days=30), start); lbl = 'vs previous 30 days'
    elif period == 'month':
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        p_start = (start - timedelta(days=1)).replace(day=1)
        prev = (p_start, start); lbl = 'vs last month'
    elif period == 'quarter':
        q_month = 3 * ((now.month - 1) // 3) + 1
        start = now.replace(month=q_month, day=1, hour=0, minute=0, second=0, microsecond=0)
        pm = q_month - 3
        p_start = start.replace(year=start.year - 1, month=pm + 12) if pm < 1 else start.replace(month=pm)
        prev = (p_start, start); lbl = 'vs last quarter'
    elif period == 'year':
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        prev = (start.replace(year=start.year - 1), start); lbl = 'vs last year'
    else:
        return None, end, None, None, ''
    return start, end, prev[0], prev[1], lbl


def get_analytics_report(period='30d'):
    start, end, prev_start, prev_end, cmp_label = period_bounds(period)
    if start is None:
        win, wp = "TRUE", []
        first = _run("SELECT MIN(created_at) FROM inquiries;", fetch='scalar')
        start_for_series = first or datetime.now() - timedelta(days=30)
    else:
        win, wp = "i.created_at >= %s AND i.created_at < %s", [start, end]
        start_for_series = start

    span_days = max(1, (end - start_for_series).days)
    granularity = 'day' if span_days <= 45 else ('week' if span_days <= 200 else 'month')

    kpi = _run(f"""
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE i.status = 'New') AS new_count,
               COUNT(*) FILTER (WHERE i.status = 'Urgent') AS urgent,
               COUNT(*) FILTER (WHERE i.status = 'In Progress') AS in_progress,
               COUNT(*) FILTER (WHERE i.status = 'Resolved') AS resolved,
               COUNT(*) FILTER (WHERE i.status <> 'Resolved' AND i.assigned_to IS NULL) AS unassigned_open,
               COUNT(*) FILTER (WHERE COALESCE(i.priority,'Normal') = 'High') AS high_priority,
               COUNT(DISTINCT LOWER(i.customer_name)) AS institutions,
               PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (i.first_response_at - i.created_at)) / 3600.0)
                   FILTER (WHERE i.first_response_at IS NOT NULL) AS median_response_hrs,
               COUNT(*) FILTER (WHERE i.first_response_at IS NOT NULL) AS responded,
               AVG(EXTRACT(EPOCH FROM (i.resolved_at - i.created_at)) / 86400.0)
                   FILTER (WHERE i.resolved_at IS NOT NULL) AS avg_resolve_days
        FROM inquiries i WHERE {win};
    """, wp, fetch='one') or {}

    prev_total = None
    if prev_start is not None:
        prev_total = _run("SELECT COUNT(*) FROM inquiries i WHERE i.created_at >= %s AND i.created_at < %s;",
                          [prev_start, prev_end], fetch='scalar') or 0

    open_now = _run("SELECT COUNT(*) FROM inquiries WHERE status <> 'Resolved' AND COALESCE(is_archived, FALSE) = FALSE;",
                    fetch='scalar') or 0
    oldest_open_days = _run("""SELECT EXTRACT(DAY FROM NOW() - MIN(created_at)) FROM inquiries
                               WHERE status <> 'Resolved' AND COALESCE(is_archived, FALSE) = FALSE;""", fetch='scalar')

    series = _run(f"""
        SELECT date_trunc('{granularity}', i.created_at) AS bucket,
               COUNT(*) AS received,
               COUNT(*) FILTER (WHERE i.status = 'Resolved') AS resolved
        FROM inquiries i WHERE {win}
        GROUP BY bucket ORDER BY bucket;
    """, wp)

    categories = _run(f"""
        SELECT {CATEGORY_CASE_SQL} AS category, COUNT(*) AS count
        FROM inquiries i WHERE {win} GROUP BY category ORDER BY count DESC;
    """, wp)

    sources = _run(f"""
        SELECT COALESCE(i.source, 'Contact Us') AS source, COUNT(*) AS count
        FROM inquiries i WHERE {win} GROUP BY 1 ORDER BY count DESC;
    """, wp)

    top_clients = _run(f"""
        SELECT MIN(i.customer_name) AS customer_name, COUNT(*) AS inquiry_count,
               COUNT(*) FILTER (WHERE i.status <> 'Resolved') AS open_count, MAX(i.created_at) AS last_inquiry
        FROM inquiries i WHERE {win}
        GROUP BY LOWER(TRIM(i.customer_name)) ORDER BY inquiry_count DESC, last_inquiry DESC LIMIT 6;
    """, wp)

    workload = _run(f"""
        SELECT a.name,
               COUNT(i.id) AS assigned,
               COUNT(i.id) FILTER (WHERE i.status <> 'Resolved') AS open,
               COUNT(i.id) FILTER (WHERE i.status = 'Resolved') AS resolved,
               (SELECT COUNT(*) FROM inquiry_messages m
                 WHERE m.kind = 'reply' AND LOWER(m.author_email) = LOWER(a.email)
                 {"AND m.created_at >= %s AND m.created_at < %s" if start else ""}) AS replies
        FROM accounts a
        LEFT JOIN inquiries i ON i.assigned_to = a.id AND {win}
        WHERE a.status = 'Active'
        GROUP BY a.id, a.name, a.email
        HAVING COUNT(i.id) > 0
            OR (SELECT COUNT(*) FROM inquiry_messages m WHERE m.kind = 'reply' AND LOWER(m.author_email) = LOWER(a.email)) > 0
        ORDER BY assigned DESC, a.name LIMIT 6;
    """, ([start, end] if start else []) + wp)

    catalog_items = _run("SELECT COUNT(*) FROM items WHERE COALESCE(is_active, TRUE);", fetch='scalar') or 0
    active_accounts = _run("SELECT COUNT(*) FROM accounts WHERE status = 'Active';", fetch='scalar') or 0

    return {
        'period': period, 'period_label': PERIOD_LABELS.get(period, 'All time'), 'compare_label': cmp_label,
        'start': start, 'end': end, 'granularity': granularity,
        'kpi': {k: (float(v) if isinstance(v, (int, float)) or hasattr(v, 'as_integer_ratio') else v)
                for k, v in kpi.items()} if kpi else {},
        'prev_total': prev_total, 'open_now': open_now,
        'oldest_open_days': int(oldest_open_days) if oldest_open_days is not None else None,
        'series': series, 'categories': categories, 'sources': sources,
        'top_clients': top_clients, 'workload': workload,
        'catalog_items': catalog_items, 'active_accounts': active_accounts,
    }


# =====================================================================
#  Items (admin) + uploaded photos
# =====================================================================
DEFAULT_ITEM_IMAGE = '/assets/icons/product_icon.svg'


def save_uploaded_image(filename, mime_type, data, width=None, height=None):
    """Stores a photo in the database and returns its id (served at /media/<id>)."""
    import psycopg2
    return _run("""
        INSERT INTO uploaded_images (filename, mime_type, data, width, height, size_bytes)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;
    """, [filename, mime_type, psycopg2.Binary(data), width, height, len(data)], fetch='scalar', commit=True)


def get_uploaded_image(image_id):
    return _run("SELECT id, mime_type, data FROM uploaded_images WHERE id = %s;", [image_id], fetch='one')


def _media_id(image_url):
    s = str(image_url or '').strip().lstrip('/')
    if s.startswith('media/'):
        try:
            return int(s.split('/', 1)[1].split('?')[0])
        except ValueError:
            return None
    return None


def delete_image_if_unused(image_url):
    """Removes an uploaded photo when no item points at it any more (old files in /assets are left alone)."""
    mid = _media_id(image_url)
    if not mid:
        return
    in_use = _run("SELECT COUNT(*) FROM items WHERE TRIM(LEADING '/' FROM image_url) = %s;",
                  [f"media/{mid}"], fetch='scalar')
    if not in_use:
        _run("DELETE FROM uploaded_images WHERE id = %s;", [mid], fetch='none', commit=True)


def create_item(name, modality_id, description, image_url, is_active=True, is_featured=False):
    return _run("""
        INSERT INTO items (name, modality_id, description, image_url, is_active, is_featured)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;
    """, [name, modality_id, description, image_url or DEFAULT_ITEM_IMAGE, is_active, is_featured],
        fetch='scalar', commit=True)


def insert_item(name, modality_id, description, image_url):
    """Older name kept for compatibility. Prefer create_item()."""
    return bool(create_item(name, modality_id, description, image_url))


def update_item(item_id, name, modality_id, description, image_url):
    """Older name kept for compatibility. Prefer update_item_full()."""
    return _run("UPDATE items SET name = %s, modality_id = %s, description = %s, image_url = %s WHERE id = %s;",
                [name, modality_id, description, image_url, item_id], fetch='none', commit=True)


def update_item_full(item_id, name, modality_id, description, image_url, is_active=True, is_featured=False):
    old = get_item_by_id(item_id)
    ok = _run("""
        UPDATE items SET name = %s, modality_id = %s, description = %s, image_url = %s,
                         is_active = %s, is_featured = %s
        WHERE id = %s;
    """, [name, modality_id, description, image_url or DEFAULT_ITEM_IMAGE, is_active, is_featured, item_id],
        fetch='none', commit=True)
    if ok and old and old.get('image_url') != (image_url or DEFAULT_ITEM_IMAGE):
        delete_image_if_unused(old.get('image_url'))
    return ok


def set_item_active(item_id, active):
    return _run("UPDATE items SET is_active = %s WHERE id = %s;", [bool(active), item_id], fetch='none', commit=True)


def delete_item(item_id):
    old = get_item_by_id(item_id)
    ok = _run("DELETE FROM items WHERE id = %s;", [item_id], fetch='none', commit=True)
    if ok and old:
        delete_image_if_unused(old.get('image_url'))
    return ok


def get_item_counts():
    return _run("""
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE COALESCE(is_active, TRUE)) AS visible,
               COUNT(*) FILTER (WHERE NOT COALESCE(is_active, TRUE)) AS hidden,
               COUNT(*) FILTER (WHERE COALESCE(is_featured, FALSE)) AS featured
        FROM items;
    """, fetch='one') or {'total': 0, 'visible': 0, 'hidden': 0, 'featured': 0}

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


def get_items_by_modality(modality_id):
    """Fetches items linked to a specific modality ID"""
    db = getdblocation()
    cur = db.cursor()
    query = """
        SELECT id, modality_id, name, image_url, is_active, is_featured, description 
        FROM items 
        WHERE modality_id = %s;
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
    
    categories = []
    for row in rows:
        categories.append({
            "id": row[0],
            "name": row[1],
            "types": row[2]
        })
        
    cur.close()
    db.close()
    return categories


def get_all_items():
    """Fetches all active items across all modalities and categories"""
    db = getdblocation()
    cur = db.cursor()
    query = """
        SELECT id, modality_id, name, image_url, is_active, is_featured, description 
        FROM items;
    """
    cur.execute(query)
    columns = [desc[0] for desc in cur.description]
    results = [dict(zip(columns, row)) for row in cur.fetchall()]
    db.close()
    return results


def get_items_by_category(category_id):
    """Fetches all items linked to modalities belonging to a specific category ID"""
    db = getdblocation()
    cur = db.cursor()
    query = """
        SELECT i.id, i.modality_id, i.name, i.image_url, i.is_active, i.is_featured, i.description 
        FROM items i
        JOIN modalities m ON i.modality_id = m.id
        WHERE m.category_id = %s;
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
            SELECT 
                i.id,
                i.name,
                i.description,
                i.image_url,
                c.name AS category_name,
                m.name AS modality_name
            FROM items i
            LEFT JOIN modalities m ON i.modality_id = m.id
            LEFT JOIN categories c ON m.category_id = c.id
            WHERE i.id = %s;
        """
        cur.execute(query, (item_id,))
        row = cur.fetchone()

        if row:
            return {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "image_url": row[3],
                "category_name": row[4] or "Products",
                "modality_name": row[5] or "General"
            }
        return None
    except Exception as e:
        print(f"Error fetching item by id ({item_id}): {e}")
        return None
    finally:
        db.close()
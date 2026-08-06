import csv
import os
import sys

# Ensure Python can locate db_handler when running from either root or database/
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db_handler import get_db_connection


def seed_database_from_csv(csv_filepath):
    conn = get_db_connection()
    cursor = conn.cursor()

    with open(csv_filepath, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        
        # Skip the header row: item_name, type, category, Complete?, is_active, short_desc, long_desc
        next(reader, None)
        
        success_count = 0
        for row in reader:
            # Requires at least 7 columns based on your current CSV layout
            if not row or len(row) < 7:
                continue
            
            item_name = row[0].strip()
            type_name = row[1].strip()
            category_name = row[2].strip()
            
            short_desc = row[5].strip() if len(row) > 5 and row[5].strip() else None
            long_desc = row[6].strip() if len(row) > 6 and row[6].strip() else None

            # Get category_id by matching category name and type name
            select_cat_query = """
                SELECT c.id 
                FROM categories c
                JOIN types t ON c.type_id = t.id
                WHERE LOWER(c.name) = LOWER(%s) AND LOWER(t.name) = LOWER(%s);
            """
            cursor.execute(select_cat_query, (category_name, type_name))
            cat_result = cursor.fetchone()

            if cat_result:
                category_id = cat_result[0]
                
                # Check if item already exists in this category
                check_item_query = "SELECT id FROM items WHERE category_id = %s AND LOWER(name) = LOWER(%s);"
                cursor.execute(check_item_query, (category_id, item_name))
                existing_item = cursor.fetchone()

                if existing_item:
                    # Update descriptions for the existing item
                    update_query = """
                        UPDATE items 
                        SET short_description = %s, long_description = %s
                        WHERE id = %s;
                    """
                    cursor.execute(update_query, (short_desc, long_desc, existing_item[0]))
                else:
                    # Insert new item if it doesn't exist yet
                    insert_query = """
                        INSERT INTO items (category_id, name, short_description, long_description)
                        VALUES (%s, %s, %s, %s);
                    """
                    cursor.execute(insert_query, (category_id, item_name, short_desc, long_desc))
                
                success_count += 1
            else:
                print(f"[WARNING] Could not find category '{category_name}' under type '{type_name}'")

    conn.commit()
    cursor.close()
    conn.close()
    print(f"\n Successfully updated/seeded {success_count} items with long & short descriptions!")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    default_csv_path = os.path.join(current_dir, "items_import.csv")
    
    seed_database_from_csv(default_csv_path)
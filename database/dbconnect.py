import os
import psycopg2
import pandas as pd

def getdblocation():
    # Render sets DATABASE_URL in Environment Variables
    db_url = os.environ.get('DATABASE_URL')
    
    if db_url:
        # Production (Render)
        db = psycopg2.connect(db_url, sslmode='require')
    else:
        # Local Development Fallback
        db = psycopg2.connect(
            host='localhost', 
            database='allura_db', 
            user='postgres', 
            port=5432, 
            password='admin'
        )
    return db

def modifyDB(sql, values):
    db = getdblocation()
    cursor = db.cursor()
    cursor.execute(sql, values)
    db.commit()
    db.close()

def getDataFromDB(sql, values, dfcolumns):
    db = getdblocation()
    cur = db.cursor()
    cur.execute(sql, values)
    rows = pd.DataFrame(cur.fetchall(), columns=dfcolumns)
    db.close()
    return rows
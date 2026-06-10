import sqlite3, os
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wildlife_rescue.db')

def get_conn():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

def init_db():
    c = get_conn()
    c.execute('''CREATE TABLE IF NOT EXISTS rescue_cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        species TEXT, location TEXT,
        description TEXT, image_path TEXT,
        latitude REAL, longitude REAL,
        injury_score REAL DEFAULT 0,
        text_score REAL DEFAULT 0,
        species_score REAL DEFAULT 0,
        time_score REAL DEFAULT 0,
        priority_score REAL DEFAULT 0,
        priority_level TEXT DEFAULT 'LOW',
        attended INTEGER DEFAULT 0,
        injured_since TEXT DEFAULT NULL,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    # Auto-migrate existing databases
    for col, dflt in [('attended', 'INTEGER DEFAULT 0'), ('injured_since', 'TEXT DEFAULT NULL')]:
        try:
            c.execute(f'ALTER TABLE rescue_cases ADD COLUMN {col} {dflt}')
        except Exception:
            pass
    c.commit(); c.close()

def insert_case(d):
    c = get_conn()
    cur = c.execute('''INSERT INTO rescue_cases
        (species,location,description,image_path,latitude,longitude,
         injury_score,text_score,species_score,time_score,priority_score,priority_level,injured_since)
        VALUES(:species,:location,:description,:image_path,:latitude,:longitude,
               :injury_score,:text_score,:species_score,:time_score,:priority_score,:priority_level,:injured_since)''', d)
    cid = cur.lastrowid; c.commit(); c.close(); return cid

def get_all_cases():
    c = get_conn()
    rows = [dict(r) for r in c.execute(
        'SELECT * FROM rescue_cases ORDER BY priority_score DESC').fetchall()]
    c.close(); return rows

def update_attended(case_id, attended):
    c = get_conn()
    c.execute('UPDATE rescue_cases SET attended=? WHERE id=?', (1 if attended else 0, case_id))
    c.commit(); c.close()

def get_rescue_counts():
    c = get_conn()
    total    = c.execute('SELECT COUNT(*) FROM rescue_cases').fetchone()[0]
    attended = c.execute('SELECT COUNT(*) FROM rescue_cases WHERE attended=1').fetchone()[0]
    c.close()
    return {'total': total, 'attended': attended}

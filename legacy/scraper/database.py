import sqlite3
import threading
from datetime import datetime
from scraper.logger import logger

_thread_local = threading.local()

def get_connection(db_path):
    if not hasattr(_thread_local, 'conn'):
        _thread_local.conn = sqlite3.connect(db_path, check_same_thread=False)
    return _thread_local.conn

def init_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professionals (
            rpps TEXT PRIMARY KEY,
            name TEXT,
            profession TEXT,
            organization TEXT,
            address TEXT,
            phone TEXT,
            email TEXT,
            finess TEXT,
            siret TEXT,
            situation_data TEXT,
            dossier_data TEXT,
            diplomes_data TEXT,
            personne_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {db_path}")

def upsert_professional(db_path, data):
    if not data.get('rpps'):
        return
    
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO professionals (
            rpps, name, profession, organization, address, phone, email,
            finess, siret, situation_data, dossier_data, diplomes_data,
            personne_data, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(rpps) DO UPDATE SET
            name=COALESCE(excluded.name, name),
            profession=COALESCE(excluded.profession, profession),
            organization=COALESCE(excluded.organization, organization),
            address=COALESCE(excluded.address, address),
            phone=COALESCE(excluded.phone, phone),
            email=COALESCE(excluded.email, email),
            finess=COALESCE(excluded.finess, finess),
            siret=COALESCE(excluded.siret, siret),
            situation_data=COALESCE(excluded.situation_data, situation_data),
            dossier_data=COALESCE(excluded.dossier_data, dossier_data),
            diplomes_data=COALESCE(excluded.diplomes_data, diplomes_data),
            personne_data=COALESCE(excluded.personne_data, personne_data),
            updated_at=excluded.updated_at
    """, (
        data.get('rpps'),
        data.get('name'),
        data.get('profession'),
        data.get('organization'),
        data.get('address'),
        data.get('phone'),
        data.get('email'),
        data.get('finess'),
        data.get('siret'),
        data.get('situation_data'),
        data.get('dossier_data'),
        data.get('diplomes_data'),
        data.get('personne_data'),
        now
    ))
    
    conn.commit()


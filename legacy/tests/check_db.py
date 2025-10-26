#!/usr/bin/env python3
"""Check database content"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
from scraper.logger import logger

def check_database(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute('SELECT COUNT(*) FROM professionals')
    total = cur.fetchone()[0]
    logger.info(f"Total records in {db_path}: {total}")
    
    cur.execute('''SELECT rpps, name, profession, organization, phone, 
                   situation_data IS NOT NULL, dossier_data IS NOT NULL, 
                   diplomes_data IS NOT NULL, personne_data IS NOT NULL 
                   FROM professionals LIMIT 10''')
    rows = cur.fetchall()
    
    logger.info("\nSample records:")
    logger.info("RPPS | Name | Profession | Org | Phone | Sit | Dos | Dip | Per")
    logger.info("-" * 100)
    for row in rows:
        logger.info(f"{row[0]} | {row[1][:20]:20} | {row[2][:15]:15} | {row[3][:15]:15} | {row[4][:12]:12} | {row[5]} | {row[6]} | {row[7]} | {row[8]}")
    
    cur.execute('SELECT COUNT(*) FROM professionals WHERE situation_data IS NOT NULL')
    with_situation = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM professionals WHERE dossier_data IS NOT NULL')
    with_dossier = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM professionals WHERE diplomes_data IS NOT NULL')
    with_diplomes = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM professionals WHERE personne_data IS NOT NULL')
    with_personne = cur.fetchone()[0]
    
    logger.info(f"\nData completeness:")
    logger.info(f"  With situation data: {with_situation}/{total}")
    logger.info(f"  With dossier data: {with_dossier}/{total}")
    logger.info(f"  With diplomes data: {with_diplomes}/{total}")
    logger.info(f"  With personne data: {with_personne}/{total}")
    
    cur.execute('SELECT dossier_data FROM professionals WHERE dossier_data IS NOT NULL LIMIT 1')
    sample_data = cur.fetchone()
    if sample_data and sample_data[0]:
        logger.info(f"\nSample dossier data length: {len(sample_data[0])} bytes")
        logger.info(f"Contains 'EXERCICE PROFESSIONNEL': {'EXERCICE PROFESSIONNEL' in sample_data[0]}")
    
    conn.close()

if __name__ == '__main__':
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'db/test_3_pages.db'
    check_database(db_path)


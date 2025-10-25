#!/usr/bin/env python3
"""Test with letter 'a' which has richer data"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
from scraper.database import init_database
from scraper.worker import process_prefix
from scraper.logger import logger

def test():
    db_path = "db/test_letter_a.db"
    
    logger.info("=== Testing with letter 'a' (only 5 doctors) ===")
    logger.info(f"Database: {db_path}")
    
    init_database(db_path)
    
    seen_prefixes = set()
    seen_prefixes.add('a')
    
    from scraper.worker import submit_search_prefix, parse_search_results
    from scraper.session import create_session
    from scraper.database import upsert_professional
    
    session = create_session()
    response = submit_search_prefix(session, 'a')
    
    if response:
        cards = parse_search_results(response.text)
        logger.info(f"Found {len(cards)} cards, processing first 5...")
        
        for i, card in enumerate(cards[:5]):
            logger.info(f"\nProcessing {i+1}/5: {card.get('name')}")
            logger.info(f"  RPPS: {card.get('rpps')}")
            logger.info(f"  Profession: {card.get('profession')}")
            logger.info(f"  Organization: {card.get('organization')}")
            logger.info(f"  Address: {card.get('address')}")
            logger.info(f"  Phone: {card.get('phone')}")
            
            upsert_professional(db_path, card)
            
            if card.get('_ids'):
                from scraper.worker import fetch_doctor_details
                details = fetch_doctor_details(session, card['_ids'])
                
                detail_update = {
                    'rpps': card['rpps'],
                    'situation_data': details.get('situation_data'),
                    'dossier_data': details.get('dossier_data'),
                    'diplomes_data': details.get('diplomes_data'),
                    'personne_data': details.get('personne_data')
                }
                upsert_professional(db_path, detail_update)
                logger.info(f"  Detail tabs: {sum([1 for v in details.values() if v])}/4")
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('SELECT rpps, name, profession, organization, address, phone FROM professionals')
    rows = cur.fetchall()
    
    logger.info("\n=== Database Contents ===")
    for r in rows:
        logger.info(f"{r[0]} | {r[1]} | {r[2]} | {r[3][:40] if r[3] else ''} | {r[4][:30] if r[4] else ''} | {r[5]}")
    
    conn.close()

if __name__ == '__main__':
    test()


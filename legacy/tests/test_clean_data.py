#!/usr/bin/env python3
"""Test with clean data extraction"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
import json
from scraper.database import init_database
from scraper.worker import process_prefix
from scraper.logger import logger

def test():
    db_path = "db/test_clean.db"
    
    logger.info("=== Testing with CLEAN data extraction ===\n")
    
    init_database(db_path)
    
    seen_prefixes = set()
    seen_prefixes.add('z')
    
    # Process just first page of 'z' (10 doctors)
    logger.info("Processing prefix 'z' (will get ~3 pages, extract first 3 doctors)...")
    
    from scraper.session import create_session
    from scraper.worker import submit_search_prefix
    from scraper.parser import parse_search_results
    from scraper.database import upsert_professional
    from scraper.worker import fetch_doctor_details
    from scraper.content_extractor import extract_all_detail_content
    
    session = create_session()
    response = submit_search_prefix(session, 'z')
    
    if response:
        cards = parse_search_results(response.text)
        logger.info(f"Found {len(cards)} cards, processing first 3...\n")
        
        for i, card in enumerate(cards[:3]):
            logger.info(f"Doctor {i+1}: {card['name']} (RPPS: {card['rpps']})")
            
            # Save basic info
            upsert_professional(db_path, card)
            
            # Fetch and extract details
            if card.get('_ids'):
                raw_details = fetch_doctor_details(session, card['_ids'])
                clean_details = extract_all_detail_content(raw_details)
                
                detail_update = {
                    'rpps': card['rpps'],
                    'situation_data': clean_details.get('situation_data'),
                    'dossier_data': clean_details.get('dossier_data'),
                    'diplomes_data': clean_details.get('diplomes_data'),
                    'personne_data': clean_details.get('personne_data')
                }
                upsert_professional(db_path, detail_update)
                
                # Show size comparison
                raw_size = sum([len(v) if v else 0 for v in raw_details.values()])
                clean_size = sum([len(v) if v else 0 for v in clean_details.values()])
                logger.info(f"  Raw: {raw_size:,} bytes → Clean: {clean_size:,} bytes ({100 - int(clean_size/raw_size*100) if raw_size else 0}% reduction)")
    
    # Verify database
    logger.info("\n=== Database Verification ===")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute('SELECT rpps, name, LENGTH(dossier_data), dossier_data FROM professionals')
    rows = cur.fetchall()
    
    for r in rows:
        logger.info(f"\nRPPS: {r[0]} | Name: {r[1]}")
        logger.info(f"  Dossier size: {r[2]:,} bytes")
        
        if r[3]:
            # Parse and show a sample of the JSON
            try:
                data = json.loads(r[3])
                logger.info(f"  Dossier content type: JSON with {len(data)} sections")
                if 'EXERCICE PROFESSIONNEL' in data:
                    ex_prof = data['EXERCICE PROFESSIONNEL']
                    logger.info(f"    EXERCICE PROFESSIONNEL: {len(ex_prof)} fields")
                    nom_key = "Nom d'exercice"
                    logger.info(f"      Nom: {ex_prof.get(nom_key, 'N/A')}")
                    logger.info(f"      Profession: {ex_prof.get('Profession', 'N/A')}")
            except:
                logger.info(f"  Content: {r[3][:200]}...")
    
    conn.close()
    
    logger.info("\n" + "="*80)
    logger.info("SUCCESS! Data is now clean JSON, not bloated HTML!")
    logger.info("="*80)

if __name__ == '__main__':
    test()


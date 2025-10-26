#!/usr/bin/env python3
"""Test complete workflow for ONE doctor and save all data to files"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
from scraper.database import init_database, upsert_professional
from scraper.worker import submit_search_prefix, fetch_doctor_details
from scraper.parser import parse_search_results
from scraper.session import create_session
from scraper.logger import logger

def test_one_doctor():
    db_path = "db/test_one_doctor.db"
    
    logger.info("=== Testing COMPLETE workflow for ONE doctor ===\n")
    
    init_database(db_path)
    session = create_session()
    
    # Search for 'a'
    logger.info("Step 1: Searching for 'a'...")
    response = submit_search_prefix(session, 'a')
    
    # Get first doctor with organization/address (card 2 - FEVRE CATHERINE)
    cards = parse_search_results(response.text)
    doctor = cards[1]  # Second card has full data
    
    logger.info(f"\nStep 2: Selected doctor: {doctor['name']} (RPPS: {doctor['rpps']})")
    logger.info(f"  Profession: {doctor['profession']}")
    logger.info(f"  Organization: {doctor['organization']}")
    logger.info(f"  Address: {doctor['address']}")
    logger.info(f"  Phone: {doctor['phone']}")
    
    # Save basic info
    logger.info("\nStep 3: Saving basic info to database...")
    upsert_professional(db_path, doctor)
    
    # Fetch details
    logger.info("\nStep 4: Fetching ALL 4 detail tabs...")
    details = fetch_doctor_details(session, doctor['_ids'])
    
    logger.info(f"  Situation: {'OK' if details['situation_data'] else 'FAILED'} ({len(details['situation_data']) if details['situation_data'] else 0:,} bytes)")
    logger.info(f"  Dossier: {'OK' if details['dossier_data'] else 'FAILED'} ({len(details['dossier_data']) if details['dossier_data'] else 0:,} bytes)")
    logger.info(f"  Diplomes: {'OK' if details['diplomes_data'] else 'FAILED'} ({len(details['diplomes_data']) if details['diplomes_data'] else 0:,} bytes)")
    logger.info(f"  Personne: {'OK' if details['personne_data'] else 'FAILED'} ({len(details['personne_data']) if details['personne_data'] else 0:,} bytes)")
    
    # Save details
    logger.info("\nStep 5: Saving detail tabs to database...")
    detail_update = {
        'rpps': doctor['rpps'],
        'situation_data': details.get('situation_data'),
        'dossier_data': details.get('dossier_data'),
        'diplomes_data': details.get('diplomes_data'),
        'personne_data': details.get('personne_data')
    }
    upsert_professional(db_path, detail_update)
    
    # Verify from database
    logger.info("\nStep 6: Verifying data from database...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('SELECT * FROM professionals WHERE rpps=?', (doctor['rpps'],))
    row = cur.fetchone()
    
    if row:
        logger.info(f"  Name: {row[1]}")
        logger.info(f"  Profession: {row[2]}")
        logger.info(f"  Organization: {row[3]}")
        logger.info(f"  Address: {row[4]}")
        logger.info(f"  Phone: {row[5]}")
        logger.info(f"  Situation data: {len(row[9]) if row[9] else 0:,} bytes")
        logger.info(f"  Dossier data: {len(row[10]) if row[10] else 0:,} bytes")
        logger.info(f"  Diplomes data: {len(row[11]) if row[11] else 0:,} bytes")
        logger.info(f"  Personne data: {len(row[12]) if row[12] else 0:,} bytes")
    
    conn.close()
    
    # Save all tabs to HTML files
    logger.info("\nStep 7: Saving all tabs to HTML files for manual verification...")
    if details['situation_data']:
        with open('tests/captured_situation.html', 'w', encoding='utf-8') as f:
            f.write(details['situation_data'])
        logger.info("  Saved: tests/captured_situation.html")
    
    if details['dossier_data']:
        with open('tests/captured_dossier.html', 'w', encoding='utf-8') as f:
            f.write(details['dossier_data'])
        logger.info("  Saved: tests/captured_dossier.html")
    
    if details['diplomes_data']:
        with open('tests/captured_diplomes.html', 'w', encoding='utf-8') as f:
            f.write(details['diplomes_data'])
        logger.info("  Saved: tests/captured_diplomes.html")
    
    if details['personne_data']:
        with open('tests/captured_personne.html', 'w', encoding='utf-8') as f:
            f.write(details['personne_data'])
        logger.info("  Saved: tests/captured_personne.html")
    
    logger.info("\n" + "="*80)
    logger.info("SUCCESS! Open the HTML files above to see the full captured data!")
    logger.info("The '...' in your database viewer is just display truncation of large TEXT fields.")
    logger.info("="*80)

if __name__ == '__main__':
    test_one_doctor()


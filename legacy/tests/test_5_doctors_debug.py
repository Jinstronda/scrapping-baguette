#!/usr/bin/env python3
"""Test 5 doctors with detailed debugging"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
from scraper.database import init_database, upsert_professional
from scraper.worker import submit_search_prefix, fetch_doctor_details
from scraper.parser import parse_search_results
from scraper.session import create_session
from scraper.content_extractor import extract_all_detail_content

db_path = "db/test_5_doctors.db"
init_database(db_path)

session = create_session()
response = submit_search_prefix(session, 'a')
cards = parse_search_results(response.text)

print(f"Processing 5 doctors...\n")

for i, card in enumerate(cards[:5]):
    print(f"\n{'='*80}")
    print(f"DOCTOR {i+1}: {card['name']} (RPPS: {card['rpps']})")
    print(f"{'='*80}")
    
    # Save basic info
    upsert_professional(db_path, card)
    print(f"  ✓ Basic info saved")
    
    # Fetch raw HTML
    print(f"  Fetching detail tabs...")
    raw_details = fetch_doctor_details(session, card['_ids'])
    
    print(f"  Raw sizes:")
    for key, val in raw_details.items():
        size = len(val) if val else 0
        has_content = "YES" if val and len(val) > 10000 else "NO"
        print(f"    {key:20}: {size:,} bytes - {has_content}")
    
    # Extract
    print(f"  Extracting...")
    clean_details = extract_all_detail_content(raw_details)
    
    print(f"  Extracted sizes:")
    for key, val in clean_details.items():
        size = len(val) if val else 0
        print(f"    {key:20}: {size:,} bytes")
        if val and size > 10:
            print(f"      Content preview: {val[:100]}")
    
    # Save to DB
    detail_update = {
        'rpps': card['rpps'],
        'situation_data': clean_details.get('situation_data'),
        'dossier_data': clean_details.get('dossier_data'),
        'diplomes_data': clean_details.get('diplomes_data'),
        'personne_data': clean_details.get('personne_data')
    }
    upsert_professional(db_path, detail_update)
    print(f"  ✓ Saved to database")

print(f"\n{'='*80}")
print("VERIFYING DATABASE")
print(f"{'='*80}")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute('SELECT rpps, name, LENGTH(situation_data), LENGTH(dossier_data), LENGTH(diplomes_data), LENGTH(personne_data) FROM professionals')
rows = cur.fetchall()

for r in rows:
    print(f"\n{r[1]} (RPPS: {r[0]})")
    print(f"  Sit: {r[2]} | Dos: {r[3]} | Dip: {r[4]} | Per: {r[5]}")

conn.close()

print(f"\nDatabase: {db_path}")


#!/usr/bin/env python3
"""Test 10 doctors single-threaded"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
from scraper.database import init_database, upsert_professional
from scraper.worker import submit_search_prefix, fetch_doctor_details
from scraper.parser import parse_search_results
from scraper.session import create_session
from scraper.content_extractor import extract_all_detail_content

db_path = "db/test_10_single.db"

print("Testing 10 doctors (single-threaded)...")

init_database(db_path)
session = create_session()

response = submit_search_prefix(session, 'a')
cards = parse_search_results(response.text)

print(f"Found {len(cards)} doctors, processing all 10...\n")

for i, doctor in enumerate(cards, 1):
    print(f"{i}/10: {doctor['name'][:30]:30} | Org: {bool(doctor.get('organization'))} | Addr: {bool(doctor.get('address'))} | Phone: {bool(doctor.get('phone'))}")
    
    upsert_professional(db_path, doctor)
    
    if doctor.get('_ids'):
        raw_details = fetch_doctor_details(session, doctor['_ids'])
        clean_details = extract_all_detail_content(raw_details)
        
        detail_update = {
            'rpps': doctor['rpps'],
            'situation_data': clean_details.get('situation_data'),
            'dossier_data': clean_details.get('dossier_data'),
            'diplomes_data': clean_details.get('diplomes_data'),
            'personne_data': clean_details.get('personne_data')
        }
        upsert_professional(db_path, detail_update)

# Verify
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM professionals')
total = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM professionals WHERE organization IS NOT NULL AND organization != ""')
with_org = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM professionals WHERE LENGTH(dossier_data) > 100')
with_dossier = cur.fetchone()[0]

print(f"\n{'='*80}")
print(f"RESULTS:")
print(f"  Total: {total}")
print(f"  With organization: {with_org}/{total}")
print(f"  With dossier data (>100): {with_dossier}/{total}")
print(f"  Database: {db_path}")

if with_org > 5 and with_dossier > 5:
    print("\n✓ SUCCESS!")
else:
    print("\n✗ FAILED")

conn.close()
print(f"={'='*80}")


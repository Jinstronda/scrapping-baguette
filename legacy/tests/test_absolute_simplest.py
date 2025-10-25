#!/usr/bin/env python3
"""Absolute simplest test - ONE doctor, show everything"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
from scraper.database import init_database, upsert_professional
from scraper.worker import submit_search_prefix, fetch_doctor_details
from scraper.parser import parse_search_results
from scraper.session import create_session
from scraper.content_extractor import extract_all_detail_content

db_path = "db/ONE_DOCTOR.db"

print("="*80)
print("SIMPLEST POSSIBLE TEST - 1 DOCTOR")
print("="*80)

init_database(db_path)
session = create_session()

print("\n1. Searching for 'a'...")
response = submit_search_prefix(session, 'a')

if not response:
    print("FAILED: No search response")
    sys.exit(1)

print(f"   OK: Got response {response.status_code}")

print("\n2. Parsing results...")
cards = parse_search_results(response.text)
print(f"   OK: Found {len(cards)} doctors")

# Pick card 2 (FEVRE CATHERINE) - we know this one has full data
doctor = cards[1]

print(f"\n3. Doctor: {doctor['name']}")
print(f"   RPPS: {doctor['rpps']}")
print(f"   Profession: {doctor['profession']}")
print(f"   Organization: {doctor.get('organization', 'N/A')}")
print(f"   Address: {doctor.get('address', 'N/A')}")
print(f"   Phone: {doctor.get('phone', 'N/A')}")

print("\n4. Saving basic info...")
upsert_professional(db_path, doctor)
print("   OK: Basic info saved")

print("\n5. Fetching detail tabs...")
raw_details = fetch_doctor_details(session, doctor['_ids'])

print(f"   Raw HTML sizes:")
print(f"     Situation: {len(raw_details['situation_data']) if raw_details['situation_data'] else 0:,} bytes")
print(f"     Dossier: {len(raw_details['dossier_data']) if raw_details['dossier_data'] else 0:,} bytes")
print(f"     Diplomes: {len(raw_details['diplomes_data']) if raw_details['diplomes_data'] else 0:,} bytes")
print(f"     Personne: {len(raw_details['personne_data']) if raw_details['personne_data'] else 0:,} bytes")

# Save raw HTML for inspection
if raw_details['dossier_data']:
    with open('tests/ONE_DOCTOR_dossier_raw.html', 'w', encoding='utf-8') as f:
        f.write(raw_details['dossier_data'])
    print(f"\n   Saved raw dossier to: tests/ONE_DOCTOR_dossier_raw.html")

print("\n6. Extracting clean JSON...")
clean_details = extract_all_detail_content(raw_details)

print(f"   Clean JSON sizes:")
print(f"     Situation: {len(clean_details['situation_data']) if clean_details['situation_data'] else 0:,} bytes")
print(f"     Dossier: {len(clean_details['dossier_data']) if clean_details['dossier_data'] else 0:,} bytes")
print(f"     Diplomes: {len(clean_details['diplomes_data']) if clean_details['diplomes_data'] else 0:,} bytes")
print(f"     Personne: {len(clean_details['personne_data']) if clean_details['personne_data'] else 0:,} bytes")

if clean_details['dossier_data']:
    print(f"\n   Dossier JSON preview:")
    print(f"   {clean_details['dossier_data'][:200]}...")

print("\n7. Saving to database...")
detail_update = {
    'rpps': doctor['rpps'],
    'situation_data': clean_details.get('situation_data'),
    'dossier_data': clean_details.get('dossier_data'),
    'diplomes_data': clean_details.get('diplomes_data'),
    'personne_data': clean_details.get('personne_data')
}
upsert_professional(db_path, detail_update)
print("   OK: Details saved")

print("\n8. Verifying from database...")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute('SELECT rpps, name, profession, organization, address, phone, LENGTH(situation_data), LENGTH(dossier_data), LENGTH(diplomes_data), LENGTH(personne_data) FROM professionals')
row = cur.fetchone()

if row:
    print(f"\n   VERIFICATION SUCCESS:")
    print(f"     Name: {row[1]}")
    print(f"     Profession: {row[2]}")
    print(f"     Organization: {row[3] if row[3] else '(none)'}")
    print(f"     Address: {row[4][:50] if row[4] else '(none)'}")
    print(f"     Phone: {row[5] if row[5] else '(none)'}")
    print(f"     Situation: {row[6]} bytes")
    print(f"     Dossier: {row[7]} bytes")
    print(f"     Diplomes: {row[8]} bytes")
    print(f"     Personne: {row[9]} bytes")

conn.close()

print("\n" + "="*80)
if row and row[6] > 100 and row[7] > 100:
    print("SUCCESS! All data captured correctly!")
else:
    print("FAILED! Detail data not extracted properly")
print("="*80)


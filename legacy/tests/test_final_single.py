#!/usr/bin/env python3
"""Final test - single threaded to verify everything works"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
from scraper.database import init_database
from scraper.worker import process_prefix

db_path = "db/final_test.db"

print("="*80)
print("FINAL VERIFICATION TEST - Single Threaded")
print("="*80)

init_database(db_path)

seen = set()
seen.add('a')

print("\nProcessing prefix 'a' (first 30 doctors - 3 pages)...")
process_prefix('a', db_path, seen)

print("\n" + "="*80)
print("VERIFYING DATABASE")
print("="*80)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Check totals
cur.execute('SELECT COUNT(*) FROM professionals')
total = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM professionals WHERE address IS NOT NULL AND address != ""')
with_address = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM professionals WHERE phone IS NOT NULL AND phone != ""')
with_phone = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM professionals WHERE LENGTH(dossier_data) > 100')
with_dossier = cur.fetchone()[0]

print(f"\nTotal doctors: {total}")
print(f"With address: {with_address}")
print(f"With phone: {with_phone}")
print(f"With dossier data (>100 bytes): {with_dossier}")

# Show samples
print("\n" + "-"*80)
print("SAMPLE DOCTORS:")
print("-"*80)

cur.execute('''SELECT rpps, name, profession, organization, address, phone, 
               LENGTH(situation_data), LENGTH(dossier_data) 
               FROM professionals LIMIT 10''')

rows = cur.fetchall()

for r in rows:
    print(f"\n{r[1]} (RPPS: {r[0]})")
    print(f"  Profession: {r[2]}")
    print(f"  Organization: {r[3] if r[3] else '(none)'}")
    print(f"  Address: {r[4][:50] if r[4] else '(none)'}")
    print(f"  Phone: {r[5] if r[5] else '(none)'}")
    print(f"  Detail data: Sit={r[6] if r[6] else 0} | Dos={r[7] if r[7] else 0}")

conn.close()

print("\n" + "="*80)
print(f"DATABASE: {db_path}")
print("="*80)


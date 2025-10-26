#!/usr/bin/env python3
"""Test single-threaded scraper with 100 doctors"""

import time
import sqlite3
from scraper.main import main

# Delete old database
import os
db_path = 'db/single_thread_100.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Deleted old database: {db_path}")

print("\n" + "="*80)
print("RUNNING SINGLE-THREADED SCRAPER - 100 DOCTORS")
print("="*80)

start_time = time.time()

# Run with 1 thread, limit to 10 pages of 'a' prefix = ~100 doctors
import sys
sys.argv = ['main.py', '--threads', '1', '--db', db_path]

main()

elapsed = time.time() - start_time

print("\n" + "="*80)
print(f"COMPLETED IN: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
print("="*80)

# Check results
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute('SELECT COUNT(*) FROM professionals')
total = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM professionals WHERE address IS NOT NULL')
with_address = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM professionals WHERE situation_data IS NOT NULL')
with_situation = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM professionals WHERE dossier_data IS NOT NULL')
with_dossier = c.fetchone()[0]

conn.close()

print(f"\nResults:")
print(f"  Total doctors: {total}")
print(f"  With address: {with_address}")
print(f"  With situation data: {with_situation}")
print(f"  With dossier data: {with_dossier}")
print(f"\nRate: {total/elapsed:.2f} doctors/second")
print("="*80)


#!/usr/bin/env python3
"""Time single-threaded scraper for 100 doctors"""

import sys
import os
import time
import sqlite3

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.database import init_database
from scraper.coordinator import run_scraper

# Setup
db_path = 'db/single_100_timed.db'
if os.path.exists(db_path):
    os.remove(db_path)

print("\n" + "="*80)
print("SINGLE-THREADED SCRAPER - TIMING TEST FOR ~100 DOCTORS")
print("="*80)
print("Configuration: 1 thread, fastest speed (min delays)")
print("Target: First prefix only (will get ~100 doctors)")
print("="*80 + "\n")

# Initialize
init_database(db_path)

# Temporarily modify config for speed
from scraper import config
original_min = config.MIN_DELAY_SECONDS
original_max = config.MAX_DELAY_SECONDS
config.MIN_DELAY_SECONDS = 0.05  # Super fast
config.MAX_DELAY_SECONDS = 0.1

# Modify coordinator to only process 'a' prefix
import string
from scraper.coordinator import WorkQueue

original_init = WorkQueue.__init__

def limited_init(self):
    import queue
    import threading
    self.queue = queue.Queue()
    self.lock = threading.Lock()
    self.seen_prefixes = set()
    # Only add 'a' prefix
    self.queue.put('a')
    self.seen_prefixes.add('a')

WorkQueue.__init__ = limited_init

start_time = time.time()

try:
    run_scraper(1, db_path)
except KeyboardInterrupt:
    print("\n\nInterrupted by user")

elapsed = time.time() - start_time

# Restore
config.MIN_DELAY_SECONDS = original_min
config.MAX_DELAY_SECONDS = original_max
WorkQueue.__init__ = original_init

print("\n" + "="*80)
print(f"COMPLETED IN: {elapsed:.1f} seconds ({elapsed/60:.2f} minutes)")
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

c.execute('SELECT COUNT(*) FROM professionals WHERE diplomes_data IS NOT NULL')
with_diplomes = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM professionals WHERE personne_data IS NOT NULL')
with_personne = c.fetchone()[0]

conn.close()

print(f"\nResults:")
print(f"  Total doctors: {total}")
print(f"  With address: {with_address}")
print(f"  With situation: {with_situation}")
print(f"  With dossier: {with_dossier}")
print(f"  With diplomes: {with_diplomes}")
print(f"  With personne: {with_personne}")
print(f"\n  Rate: {total/elapsed:.2f} doctors/second")
print(f"  Rate: {total/(elapsed/60):.1f} doctors/minute")
print(f"  Estimated for 100k doctors: {(100000/total)*elapsed/3600:.1f} hours")
print("="*80)


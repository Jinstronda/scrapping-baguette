#!/usr/bin/env python3
"""Test Scrapy scraper with single prefix to verify contact info preservation"""

import subprocess
import sys
import sqlite3
import os

print("="*80)
print("TESTING SCRAPY SCRAPER - SINGLE PREFIX 'a'")
print("="*80)

# Clean up old test database
test_db = 'scrapy_scraper/db/test_scrapy.db'
if os.path.exists(test_db):
    os.remove(test_db)
    print(f"\nRemoved old test database: {test_db}")

# Create db directory if needed
os.makedirs('scrapy_scraper/db', exist_ok=True)

print("\nRunning Scrapy with prefix 'a' and 3 pages max...")
print("This will test if contact info (address, phone, email) is preserved\n")

# Run scrapy with test settings
result = subprocess.run(
    [
        'scrapy', 'crawl', 'health_professionals',
        '-s', 'LOG_LEVEL=INFO',
        '-s', f'DATABASE_PATH={test_db}',
        '-s', 'CLOSESPIDER_PAGECOUNT=30',  # Limit pages for testing
    ],
    cwd='scrapy_scraper',
    capture_output=True,
    text=True
)

if result.returncode != 0:
    print(f"\nScraping failed with code {result.returncode}")
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    sys.exit(result.returncode)

print("\n" + "="*80)
print("CHECKING DATA QUALITY")
print("="*80)

# Check database
conn = sqlite3.connect(test_db)
cursor = conn.cursor()

# Total records
cursor.execute("SELECT COUNT(*) FROM professionals")
total = cursor.fetchone()[0]
print(f"\n✓ Total records: {total}")

# Records with contact info
cursor.execute("SELECT COUNT(*) FROM professionals WHERE address IS NOT NULL AND LENGTH(address) > 0")
with_address = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM professionals WHERE phone IS NOT NULL AND LENGTH(phone) > 0")
with_phone = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM professionals WHERE email IS NOT NULL AND LENGTH(email) > 0")
with_email = cursor.fetchone()[0]

# Records with detail tabs
cursor.execute("SELECT COUNT(*) FROM professionals WHERE situation_data IS NOT NULL")
with_situation = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM professionals WHERE dossier_data IS NOT NULL")
with_dossier = cursor.fetchone()[0]

print(f"\n📊 Contact Information:")
print(f"  - With address: {with_address}/{total} ({100*with_address//total if total > 0 else 0}%)")
print(f"  - With phone:   {with_phone}/{total} ({100*with_phone//total if total > 0 else 0}%)")
print(f"  - With email:   {with_email}/{total} ({100*with_email//total if total > 0 else 0}%)")

print(f"\n📋 Detail Tabs:")
print(f"  - Situation data: {with_situation}/{total} ({100*with_situation//total if total > 0 else 0}%)")
print(f"  - Dossier data:   {with_dossier}/{total} ({100*with_dossier//total if total > 0 else 0}%)")

# Sample records
print(f"\n📝 Sample Records:")
cursor.execute("SELECT rpps, name, profession, address, phone, email FROM professionals LIMIT 5")
for row in cursor.fetchall():
    rpps, name, prof, addr, phone, email = row
    print(f"\n  {name} (RPPS: {rpps})")
    print(f"    Profession: {prof}")
    print(f"    Address: {addr if addr else '❌ MISSING'}")
    print(f"    Phone: {phone if phone else '❌ MISSING'}")
    print(f"    Email: {email if email else '❌ MISSING'}")

conn.close()

print("\n" + "="*80)
if with_address > 0:
    print("✅ SUCCESS: Contact information preserved!")
else:
    print("❌ FAILED: Contact information lost!")
    sys.exit(1)

print("="*80)
print(f"\nDatabase saved at: {test_db}")
print("\nTo view all data:")
print(f"  sqlite3 {test_db} 'SELECT * FROM professionals'")
print("="*80)

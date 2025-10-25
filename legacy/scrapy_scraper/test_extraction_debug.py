#!/usr/bin/env python3
"""Test extraction on existing data"""

import sys
sys.path.insert(0, '..')

import sqlite3
from scraper.content_extractor import (
    extract_situation_content,
    extract_dossier_content,
    extract_diplomes_content,
    extract_personne_content
)

print("="*80)
print("TESTING EXTRACTION ON SAVED DATA")
print("="*80)

# Get one doctor from database
conn = sqlite3.connect('db/scrapy_health_professionals.db')
c = conn.cursor()

c.execute('''
    SELECT rpps, name, situation_data, dossier_data, diplomes_data, personne_data
    FROM professionals
    LIMIT 1
''')

row = c.fetchone()
rpps, name, sit_data, dos_data, dip_data, per_data = row

print(f"\nDoctor: {name} (RPPS: {rpps})")
print(f"\nSituation data length: {len(sit_data) if sit_data else 0} bytes")
print(f"Dossier data length: {len(dos_data) if dos_data else 0} bytes")
print(f"Diplomes data length: {len(dip_data) if dip_data else 0} bytes")
print(f"Personne data length: {len(per_data) if per_data else 0} bytes")

if sit_data:
    print(f"\nSituation content preview:")
    print(sit_data[:500])
    print("...")

if dos_data:
    print(f"\nDossier content preview:")
    print(dos_data[:500])
    print("...")

if dip_data:
    print(f"\nDiplomes content preview:")
    print(dip_data[:500])
    print("...")

if per_data:
    print(f"\nPersonne content preview:")
    print(per_data[:500])
    print("...")

# Now let's check the actual pipeline
print("\n" + "="*80)
print("CHECKING PIPELINE")
print("="*80)

from pipelines import DataCleanerPipeline
from items import ProfessionalItem

# Simulate what happens in the pipeline
print("\nLet's trace through the pipeline logic...")
print("The pipeline expects HTML in *_html fields and converts to *_data JSON")
print("So the issue is: are we receiving HTML or already-converted JSON?")

# Check what's actually in the database raw
c.execute("SELECT situation_data FROM professionals WHERE rpps=?", (rpps,))
raw_data = c.fetchone()[0]
print(f"\nRaw situation_data type: {type(raw_data)}")
print(f"Raw situation_data first 200 chars: {raw_data[:200] if raw_data else 'None'}")

conn.close()

print("\n" + "="*80)
print("The data shows '{}' which means extract_*_content() is returning empty JSON")
print("This suggests the HTML structure doesn't match what the extractor expects")
print("="*80)


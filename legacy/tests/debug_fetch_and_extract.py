#!/usr/bin/env python3
"""Debug what we're actually fetching and extracting"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.session import create_session
from scraper.worker import submit_search_prefix, fetch_doctor_details
from scraper.parser import parse_search_results
from scraper.content_extractor import extract_all_detail_content

session = create_session()

print("Searching for 'a'...")
response = submit_search_prefix(session, 'a')

cards = parse_search_results(response.text)
print(f"Found {len(cards)} cards\n")

# Test first doctor
doctor = cards[0]  # BRYSSENS ALISON
print(f"Testing: {doctor['name']} (RPPS: {doctor['rpps']})")

print("\nFetching raw HTML...")
raw_details = fetch_doctor_details(session, doctor['_ids'])

print(f"\nRaw HTML sizes:")
print(f"  Situation: {len(raw_details['situation_data']) if raw_details['situation_data'] else 0:,} bytes")
print(f"  Dossier: {len(raw_details['dossier_data']) if raw_details['dossier_data'] else 0:,} bytes")
print(f"  Diplomes: {len(raw_details['diplomes_data']) if raw_details['diplomes_data'] else 0:,} bytes")
print(f"  Personne: {len(raw_details['personne_data']) if raw_details['personne_data'] else 0:,} bytes")

# Check if they contain actual data
if raw_details['situation_data']:
    has_activite = 'ACTIVIT' in raw_details['situation_data']
    has_structure = 'STRUCTURE' in raw_details['situation_data']
    print(f"\nSituation HTML contains:")
    print(f"  ACTIVITÉ: {has_activite}")
    print(f"  STRUCTURE: {has_structure}")
    
    # Save to file
    with open('tests/debug_situation_raw.html', 'w', encoding='utf-8') as f:
        f.write(raw_details['situation_data'])
    print(f"  Saved to: tests/debug_situation_raw.html")

if raw_details['dossier_data']:
    has_exercice = 'EXERCICE PROFESSIONNEL' in raw_details['dossier_data']
    print(f"\nDossier HTML contains:")
    print(f"  EXERCICE PROFESSIONNEL: {has_exercice}")

print("\nExtracting...")
clean_details = extract_all_detail_content(raw_details)

print(f"\nExtracted JSON sizes:")
print(f"  Situation: {len(clean_details['situation_data']) if clean_details['situation_data'] else 0:,} bytes")
print(f"  Dossier: {len(clean_details['dossier_data']) if clean_details['dossier_data'] else 0:,} bytes")
print(f"  Diplomes: {len(clean_details['diplomes_data']) if clean_details['diplomes_data'] else 0:,} bytes")
print(f"  Personne: {len(clean_details['personne_data']) if clean_details['personne_data'] else 0:,} bytes")

print(f"\nExtracted content:")
for key, val in clean_details.items():
    if val:
        print(f"\n{key}:")
        print(val[:300] if len(val) > 300 else val)


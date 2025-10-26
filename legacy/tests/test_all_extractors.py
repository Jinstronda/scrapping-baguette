#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.content_extractor import extract_situation_content, extract_dossier_content, extract_diplomes_content, extract_personne_content

# Load all tabs
with open('tests/captured_situation.html', 'r', encoding='utf-8') as f:
    sit_html = f.read()

with open('tests/captured_dossier.html', 'r', encoding='utf-8') as f:
    dos_html = f.read()

with open('tests/captured_diplomes.html', 'r', encoding='utf-8') as f:
    dip_html = f.read()

with open('tests/captured_personne.html', 'r', encoding='utf-8') as f:
    per_html = f.read()

print("="*100)
print("TESTING ALL EXTRACTORS")
print("="*100)

# Test Situation
sit_json = extract_situation_content(sit_html)
print(f"\nSITUATION: {len(sit_html):,} bytes -> {len(sit_json):,} bytes")
print("Content:")
print(sit_json[:800])

# Test Dossier
dos_json = extract_dossier_content(dos_html)
print(f"\n{'='*100}")
print(f"DOSSIER: {len(dos_html):,} bytes -> {len(dos_json):,} bytes")
print("Content:")
print(dos_json[:500])

# Test Diplomes
dip_json = extract_diplomes_content(dip_html)
print(f"\n{'='*100}")
print(f"DIPLOMES: {len(dip_html):,} bytes -> {len(dip_json):,} bytes")
print("Content:")
print(dip_json)

# Test Personne
per_json = extract_personne_content(per_html)
print(f"\n{'='*100}")
print(f"PERSONNE: {len(per_html):,} bytes -> {len(per_json):,} bytes")
print("Content:")
print(per_json[:800])

print(f"\n{'='*100}")
print("SUMMARY")
print(f"{'='*100}")
total_before = len(sit_html) + len(dos_html) + len(dip_html) + len(per_html)
total_after = len(sit_json) + len(dos_json) + len(dip_json) + len(per_json)
print(f"Total before: {total_before:,} bytes")
print(f"Total after: {total_after:,} bytes")
print(f"Reduction: {100 - int(total_after/total_before*100)}%")


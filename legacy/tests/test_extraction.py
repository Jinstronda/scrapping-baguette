#!/usr/bin/env python3
"""Test the content extractor"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.content_extractor import extract_dossier_content, extract_diplomes_content

# Load the captured HTML
with open('tests/captured_dossier.html', 'r', encoding='utf-8') as f:
    dossier_html = f.read()

with open('tests/captured_diplomes.html', 'r', encoding='utf-8') as f:
    diplomes_html = f.read()

print("BEFORE EXTRACTION:")
print(f"  Dossier HTML: {len(dossier_html):,} bytes")
print(f"  Diplomes HTML: {len(diplomes_html):,} bytes")

# Extract clean content
dossier_json = extract_dossier_content(dossier_html)
diplomes_json = extract_diplomes_content(diplomes_html)

print("\nAFTER EXTRACTION (JSON):")
print(f"  Dossier JSON: {len(dossier_json):,} bytes")
print(f"  Diplomes JSON: {len(diplomes_json):,} bytes")

print("\nDossier Content (first 500 chars):")
print(dossier_json[:500])

print("\nDiplomes Content:")
print(diplomes_json)

# Save the clean JSON
with open('tests/clean_dossier.json', 'w', encoding='utf-8') as f:
    f.write(dossier_json)

with open('tests/clean_diplomes.json', 'w', encoding='utf-8') as f:
    f.write(diplomes_json)

print("\nSaved clean JSON to:")
print("  tests/clean_dossier.json")
print("  tests/clean_diplomes.json")


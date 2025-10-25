#!/usr/bin/env python3
"""Debug the content extractor to see why it's returning empty"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.content_extractor import extract_dossier_content, extract_situation_content, extract_personne_content
from bs4 import BeautifulSoup

# Load captured HTML files
with open('tests/captured_dossier.html', 'r', encoding='utf-8') as f:
    dossier_html = f.read()

with open('tests/captured_situation.html', 'r', encoding='utf-8') as f:
    situation_html = f.read()

with open('tests/captured_personne.html', 'r', encoding='utf-8') as f:
    personne_html = f.read()

print("="*100)
print("DEBUGGING CONTENT EXTRACTION")
print("="*100)

# Check what divs exist
soup = BeautifulSoup(dossier_html, 'html.parser')

print("\n1. Looking for content divs in Dossier HTML:")
content_divs = soup.find_all('div', class_='contenu_dossier_pro_details')
print(f"   Found {len(content_divs)} div.contenu_dossier_pro_details")

content_divs2 = soup.find_all('div', class_=lambda x: x and 'contenu' in x.lower() if x else False)
print(f"   Found {len(content_divs2)} divs with 'contenu' in class")

# Look for the actual content area
details_divs = soup.find_all('div', class_='details')
print(f"   Found {len(details_divs)} div.details")

blocs = soup.find_all('div', class_='blocs_details')
print(f"   Found {len(blocs)} div.blocs_details")

# Find h2 headers
h2s = soup.find_all('h2')
print(f"\n2. Found {len(h2s)} h2 headers:")
for h2 in h2s[:5]:
    print(f"   - {h2.get_text(strip=True)}")

# Find tables
tables = soup.find_all('table')
print(f"\n3. Found {len(tables)} tables")

# Find label spans
labels = soup.find_all('span', class_=lambda x: x and 'label' in x.lower() if x else False)
print(f"\n4. Found {len(labels)} label spans")
for label in labels[:5]:
    text = label.get_text(strip=True)
    if text:
        print(f"   - {text[:50]}")

print("\n" + "="*100)
print("Testing extraction...")
print("="*100)

dossier_json = extract_dossier_content(dossier_html)
print(f"\nDossier extracted: {len(dossier_json)} bytes")
print(dossier_json[:500])

print("\n" + "="*100)


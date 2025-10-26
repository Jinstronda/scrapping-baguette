#!/usr/bin/env python3
"""Write proper extractors based on actual HTML structure"""

from bs4 import BeautifulSoup
import json

# Load all captured tabs
with open('tests/captured_situation.html', 'r', encoding='utf-8') as f:
    sit_html = f.read()

with open('tests/captured_dossier.html', 'r', encoding='utf-8') as f:
    dos_html = f.read()

with open('tests/captured_diplomes.html', 'r', encoding='utf-8') as f:
    dip_html = f.read()

with open('tests/captured_personne.html', 'r', encoding='utf-8') as f:
    per_html = f.read()

print("Analyzing HTML structure...")

for name, html in [('Situation', sit_html), ('Dossier', dos_html), ('Diplomes', dip_html), ('Personne', per_html)]:
    print(f"\n{'='*80}")
    print(f"{name} TAB")
    print(f"{'='*80}")
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all h2 headers (section titles)
    h2s = soup.find_all('h2')
    print(f"H2 headers found: {len(h2s)}")
    for h2 in h2s[:10]:
        print(f"  - {h2.get_text(strip=True)}")
    
    # Find all generic divs that might contain the data
    generics = soup.find_all('generic')
    print(f"\nGeneric tags: {len(generics)}")
    
    # Check for text content keywords
    if 'ACTIVITÉ' in html or 'ACTIVIT' in html:
        print("✓ Contains ACTIVITÉ")
    if 'EXERCICE PROFESSIONNEL' in html:
        print("✓ Contains EXERCICE PROFESSIONNEL")
    if 'DIPLÔMES' in html or 'DIPLOM' in html:
        print("✓ Contains DIPLÔMES")
    if 'ÉTAT-CIVIL' in html or 'TAT-CIVIL' in html:
        print("✓ Contains ÉTAT-CIVIL")
    
    # Look for the actual content - it's in <generic> tags with text!
    generics_with_text = [g for g in generics if g.get_text(strip=True) and len(g.get_text(strip=True)) > 10]
    print(f"\nGenerics with substantial text: {len(generics_with_text)}")

print("\n" + "="*80)
print("CONCLUSION: The data is in <generic> tags, not <div> tags!")
print("Need to extract from <generic> elements with Playwright/browser view, not raw HTML <div>")
print("="*80)


#!/usr/bin/env python3
"""Test if URL params work vs form body"""

import sys
sys.path.insert(0, '..')

import requests
from bs4 import BeautifulSoup
import re

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
})

print("="*80)
print("TEST: URL PARAMS VS FORM BODY")
print("="*80)

# Step 1: Home
print("\n1. Getting home page...")
home = session.get('https://annuaire.sante.fr/web/site-pro')
soup = BeautifulSoup(home.text, 'html.parser')
form = soup.find('form', attrs={'name': 'fmRecherche'})
p_auth = ''
if form:
    action = form.get('action', '')
    match = re.search(r'p_auth=([^&]+)', action)
    if match:
        p_auth = match.group(1)
print(f"   p_auth: {p_auth}")

# Step 2: Search (form body is correct here)
print("\n2. Searching...")
search_data = {
    'p_p_id': 'rechercheportlet_INSTANCE_blk14HrIzEMS',
    'p_p_lifecycle': '1',
    'p_p_state': 'normal',
    'p_p_mode': 'view',
    '_rechercheportlet_INSTANCE_blk14HrIzEMS_javax.portlet.action': 'rechercheAction',
    'p_auth': p_auth,
    '_rechercheportlet_INSTANCE_blk14HrIzEMS_texttofind': 'a',
    '_rechercheportlet_INSTANCE_blk14HrIzEMS_adresse': '',
    '_rechercheportlet_INSTANCE_blk14HrIzEMS_cordonneesGeo': '',
    '_rechercheportlet_INSTANCE_blk14HrIzEMS_integralite': 'active_only',
    '_rechercheportlet_INSTANCE_blk14HrIzEMS_typeRecherche': 'textLibre'
}
search = session.post('https://annuaire.sante.fr/web/site-pro/home', data=search_data)
soup = BeautifulSoup(search.text, 'html.parser')
cards = soup.find_all('div', class_='contenant_resultat')
print(f"   Found {len(cards)} doctors")

# Get first doctor
first_card = cards[0]
nom_prenom = first_card.find('div', class_='nom_prenom')
link = nom_prenom.find('a', href=True)
name = link.get_text(strip=True)
print(f"   Doctor: {name}")

from urllib.parse import urlparse, parse_qs
parsed = urlparse(link['href'])
params = parse_qs(parsed.query)
ids = {}
for key, value in params.items():
    ids[key] = value[0] if value else ''
rpps = ids.get('_mapportlet_idRpps', '')
print(f"   RPPS: {rpps}")

# Step 3: Open detail popup - TEST URL PARAMS
print("\n3. Opening detail popup with URL params...")
detail_params = {
    'p_p_id': 'mapportlet',
    'p_p_lifecycle': '1',
    'p_p_state': 'normal',
    'p_p_mode': 'view',
    '_mapportlet_javax.portlet.action': 'DetailsPPAction',
    '_mapportlet_idSituExe': ids.get('_mapportlet_idSituExe', ''),
    '_mapportlet_idExePro': ids.get('_mapportlet_idExePro', ''),
    '_mapportlet_resultatIndex': ids.get('_mapportlet_resultatIndex', ''),
    '_mapportlet_idRpps': rpps,
    '_mapportlet_siteId': ids.get('_mapportlet_siteId', ''),
    '_mapportlet_coordonneesId': ids.get('_mapportlet_coordonneesId', ''),
    '_mapportlet_etatPP': ids.get('_mapportlet_etatPP', 'OUVERT'),
    'p_auth': p_auth
}
detail = session.post('https://annuaire.sante.fr/web/site-pro/recherche/resultats', params=detail_params, data='')
print(f"   Status: {detail.status_code}")
print(f"   Response length: {len(detail.text)}")

# Step 4: Navigate to situation tab - TEST URL PARAMS
print("\n4. Navigating to situation tab with URL params...")
situation_params = {
    'p_p_id': 'mapportlet',
    'p_p_lifecycle': '1',
    'p_p_state': 'normal',
    'p_p_mode': 'view',
    '_mapportlet_javax.portlet.action': 'infoDetailPP',
    '_mapportlet_idSituExePourDetail': ids.get('_mapportlet_idSituExe', ''),
    '_mapportlet_idNat': '8' + rpps,
    '_mapportlet_idExeProPourDetail': ids.get('_mapportlet_idExePro', ''),
    '_mapportlet_coordonneIdPourDetail': ids.get('_mapportlet_coordonneesId', ''),
    '_mapportlet_resultatIndex': ids.get('_mapportlet_resultatIndex', ''),
    '_mapportlet_idRpps': rpps,
    '_mapportlet_etat': ids.get('_mapportlet_etatPP', 'OUVERT'),
    '_mapportlet_siteIdPourDetail': ids.get('_mapportlet_siteId', ''),
    'p_auth': p_auth
}
situation = session.post('https://annuaire.sante.fr/web/site-pro/recherche/resultats', params=situation_params, data='')
print(f"   Status: {situation.status_code}")
print(f"   Response length: {len(situation.text)}")

# Check content
soup = BeautifulSoup(situation.text, 'html.parser')
h2s = soup.find_all('h2')
h3s = soup.find_all('h3')
print(f"   H2 headers: {len(h2s)}")
print(f"   H3 headers: {len(h3s)}")
if h3s:
    print("   First 5 H3s:")
    for h3 in h3s[:5]:
        print(f"     - {h3.get_text(strip=True)}")

# Save for inspection
with open('test_requests_situation.html', 'w', encoding='utf-8') as f:
    f.write(situation.text)
print(f"\n   Saved to: test_requests_situation.html")

print("\n" + "="*80)
print("If H3 count > 0, then URL params work!")
print("If H3 count = 0, then the original scraper is also broken.")
print("="*80)


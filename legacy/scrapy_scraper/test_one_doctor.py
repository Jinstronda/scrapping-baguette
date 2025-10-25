#!/usr/bin/env python3
"""Test single doctor with debugging"""

import sys
sys.path.insert(0, '..')

from scrapy.http import HtmlResponse
from spiders.health_spider import HealthSpider
from bs4 import BeautifulSoup
import requests

# Test with a known doctor
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
})

print("="*80)
print("SINGLE DOCTOR TEST WITH DEBUGGING")
print("="*80)

# Step 1: Get home page and p_auth
print("\n1. Getting home page...")
home_response = session.get('https://annuaire.sante.fr/web/site-pro')
soup = BeautifulSoup(home_response.text, 'html.parser')
form = soup.find('form', attrs={'name': 'fmRecherche'})
import re
p_auth = ''
if form:
    action = form.get('action', '')
    match = re.search(r'p_auth=([^&]+)', action)
    if match:
        p_auth = match.group(1)
print(f"   p_auth: {p_auth}")

# Step 2: Search for 'a'
print("\n2. Searching for 'a'...")
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
search_response = session.post('https://annuaire.sante.fr/web/site-pro/home', data=search_data)
soup = BeautifulSoup(search_response.text, 'html.parser')
cards = soup.find_all('div', class_='contenant_resultat')
print(f"   Found {len(cards)} doctors")

# Get first doctor
first_card = cards[0]
nom_prenom = first_card.find('div', class_='nom_prenom')
link = nom_prenom.find('a', href=True)
name = link.get_text(strip=True)
print(f"   Testing with: {name}")

# Extract IDs
from urllib.parse import urlparse, parse_qs
parsed = urlparse(link['href'])
params = parse_qs(parsed.query)
ids = {}
for key, value in params.items():
    ids[key] = value[0] if value else ''

rpps = ids.get('_mapportlet_idRpps', '')
print(f"   RPPS: {rpps}")

# Step 3: Open doctor detail popup
print("\n3. Opening doctor detail (DetailsPPAction)...")
detail_data = {
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
detail_response = session.post('https://annuaire.sante.fr/web/site-pro/recherche/resultats', data=detail_data)
print(f"   Status: {detail_response.status_code}")

# Step 4: Navigate to full detail page (infoDetailPP)
print("\n4. Navigating to full detail page (infoDetailPP)...")
info_data = {
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
info_response = session.post('https://annuaire.sante.fr/web/site-pro/recherche/resultats', data=info_data)
print(f"   Status: {info_response.status_code}")
print(f"   Response length: {len(info_response.text)} bytes")

# Save the situation HTML
with open('debug_situation.html', 'w', encoding='utf-8') as f:
    f.write(info_response.text)
print(f"   Saved to: debug_situation.html")

# Check what's in it
soup = BeautifulSoup(info_response.text, 'html.parser')
situation_div = soup.find('div', class_=lambda x: x and 'contenu_situation' in x if x else False)
print(f"   Found situation div: {situation_div is not None}")
if situation_div:
    print(f"   Situation div length: {len(str(situation_div))} bytes")

# Step 5: Fetch Dossier tab
print("\n5. Fetching Dossier tab...")
dossier_data = {
    'p_p_id': 'resultatsportlet',
    'p_p_lifecycle': '1',
    'p_p_state': 'normal',
    'p_p_mode': 'view',
    '_resultatsportlet_javax.portlet.action': 'detailsPPDossierPro',
    '_resultatsportlet_idNat': '8' + rpps,
    '_resultatsportlet_resultatIndex': ids.get('_mapportlet_resultatIndex', ''),
    '_resultatsportlet_idRpps': rpps,
    '_resultatsportlet_siteId': ids.get('_mapportlet_siteId', ''),
    '_resultatsportlet_coordonneId': ids.get('_mapportlet_coordonneesId', ''),
    '_resultatsportlet_etat': ids.get('_mapportlet_etatPP', 'OUVERT'),
    'p_auth': p_auth,
    '_resultatsportlet_idExePro': ids.get('_mapportlet_idExePro', '')
}
dossier_response = session.post('https://annuaire.sante.fr/web/site-pro/information-detaillees', data=dossier_data)
print(f"   Status: {dossier_response.status_code}")
print(f"   Response length: {len(dossier_response.text)} bytes")

with open('debug_dossier.html', 'w', encoding='utf-8') as f:
    f.write(dossier_response.text)
print(f"   Saved to: debug_dossier.html")

# Check what's in it
soup = BeautifulSoup(dossier_response.text, 'html.parser')
dossier_div = soup.find('div', class_=lambda x: x and 'contenu_dossier' in x if x else False)
print(f"   Found dossier div: {dossier_div is not None}")
if dossier_div:
    print(f"   Dossier div length: {len(str(dossier_div))} bytes")

# Now test extraction
print("\n6. Testing extraction...")
from scraper.content_extractor import extract_situation_content, extract_dossier_content

situation_json = extract_situation_content(info_response.text)
print(f"   Situation JSON length: {len(situation_json)} bytes")
print(f"   Situation content: {situation_json[:200]}...")

dossier_json = extract_dossier_content(dossier_response.text)
print(f"   Dossier JSON length: {len(dossier_json)} bytes")
print(f"   Dossier content: {dossier_json[:200]}...")

print("\n" + "="*80)
print("Check debug_situation.html and debug_dossier.html to see what's received")
print("="*80)


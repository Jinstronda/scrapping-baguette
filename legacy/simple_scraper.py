#!/usr/bin/env python3
"""
Simple, working scraper using requests.Session() - the pattern we KNOW works.
No Scrapy, no complex threading - just sequential scraping that works.
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import sqlite3
import time
from legacy.scraper.content_extractor import (
    extract_situation_content,
    extract_dossier_content,
    extract_diplomes_content,
    extract_personne_content
)

def create_database():
    """Create SQLite database"""
    conn = sqlite3.connect('db/simple_scraper.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS professionals (
            rpps TEXT PRIMARY KEY,
            name TEXT,
            profession TEXT,
            organization TEXT,
            address TEXT,
            phone TEXT,
            email TEXT,
            finess TEXT,
            siret TEXT,
            situation_data TEXT,
            dossier_data TEXT,
            diplomes_data TEXT,
            personne_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_doctor(data):
    """Save doctor to database"""
    conn = sqlite3.connect('db/simple_scraper.db')
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO professionals
        (rpps, name, profession, organization, address, phone, email,
         situation_data, dossier_data, diplomes_data, personne_data, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (
        data['rpps'],
        data.get('name'),
        data.get('profession'),
        data.get('organization'),
        data.get('address'),
        data.get('phone'),
        data.get('email'),
        data.get('situation_data', '{}'),
        data.get('dossier_data', '{}'),
        data.get('diplomes_data', '{}'),
        data.get('personne_data', '{}')
    ))
    conn.commit()
    conn.close()

def scrape_one_doctor(session, card, p_auth):
    """Scrape one doctor - returns dict with all data"""
    # Extract basic info from card
    nom_prenom = card.find('div', class_='nom_prenom')
    if not nom_prenom:
        return None
    
    link = nom_prenom.find('a', href=True)
    if not link:
        return None
    
    name = link.get_text(strip=True)
    
    # Extract IDs from URL
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(link['href'])
    params = parse_qs(parsed.query)
    ids = {k: v[0] if v else '' for k, v in params.items()}
    rpps = ids.get('_mapportlet_idRpps', '')
    
    if not rpps:
        return None
    
    # print(f"  Processing: {name} (RPPS: {rpps})")  # Comment out to reduce noise
    
    # Basic fields
    data = {
        'rpps': rpps,
        'name': name
    }
    
    # Profession
    profession_divs = card.find_all('div', class_='profession')
    if profession_divs:
        texts = [p.get_text(strip=True) for p in profession_divs if p.get_text(strip=True)]
        if texts:
            data['profession'] = texts[0]
        if len(texts) > 1:
            data['organization'] = ' | '.join(texts[1:])
    
    # Address
    address_div = card.find('div', class_='adresse')
    if address_div:
        data['address'] = address_div.get_text(' ', strip=True)
    
    # Phone
    tel_div = card.find('div', class_='tel')
    if tel_div:
        data['phone'] = tel_div.get_text(strip=True)
    
    # Email
    email_div = card.find('div', class_='mssante')
    if email_div:
        data['email'] = email_div.get_text(strip=True)
    
    # Fetch details
    try:
        # Step 1: Open detail popup
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
        detail = session.post('https://annuaire.sante.fr/web/site-pro/recherche/resultats', 
                            params=detail_params, data='', timeout=30)
        time.sleep(0.5)  # Delay after opening detail
        
        # Step 2: Navigate to situation tab
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
        situation = session.post('https://annuaire.sante.fr/web/site-pro/recherche/resultats',
                                params=situation_params, data='', timeout=30)
        data['situation_data'] = extract_situation_content(situation.text)
        time.sleep(0.5)  # Delay between tabs
        
        # Step 3: Fetch other tabs
        base_params = {
            'p_p_id': 'resultatsportlet',
            'p_p_lifecycle': '1',
            'p_p_state': 'normal',
            'p_p_mode': 'view',
            '_resultatsportlet_idNat': '8' + rpps,
            '_resultatsportlet_resultatIndex': ids.get('_mapportlet_resultatIndex', ''),
            '_resultatsportlet_idRpps': rpps,
            '_resultatsportlet_siteId': ids.get('_mapportlet_siteId', ''),
            '_resultatsportlet_coordonneId': ids.get('_mapportlet_coordonneesId', ''),
            '_resultatsportlet_etat': ids.get('_mapportlet_etatPP', 'OUVERT'),
            'p_auth': p_auth,
            '_resultatsportlet_idExePro': ids.get('_mapportlet_idExePro', '')
        }
        
        # Dossier
        dossier_params = base_params.copy()
        dossier_params['_resultatsportlet_javax.portlet.action'] = 'detailsPPDossierPro'
        dossier = session.post('https://annuaire.sante.fr/web/site-pro/information-detaillees',
                              params=dossier_params, data='', timeout=30)
        data['dossier_data'] = extract_dossier_content(dossier.text)
        time.sleep(0.5)  # Delay between tabs
        
        # Diplomes
        diplomes_params = base_params.copy()
        diplomes_params['_resultatsportlet_javax.portlet.action'] = 'detailsPPDiplomes'
        diplomes = session.post('https://annuaire.sante.fr/web/site-pro/information-detaillees',
                               params=diplomes_params, data='', timeout=30)
        data['diplomes_data'] = extract_diplomes_content(diplomes.text)
        time.sleep(0.5)  # Delay between tabs
        
        # Personne
        personne_params = base_params.copy()
        personne_params['_resultatsportlet_javax.portlet.action'] = 'detailsPPPersonne'
        personne = session.post('https://annuaire.sante.fr/web/site-pro/information-detaillees',
                               params=personne_params, data='', timeout=30)
        data['personne_data'] = extract_personne_content(personne.text)
        
    except Exception as e:
        print(f"    ERROR fetching details: {e}")
    
    return data

def main():
    """Main scraper"""
    print("="*80)
    print("SIMPLE WORKING SCRAPER - USING REQUESTS.SESSION()")
    print("="*80)
    
    # Create database
    create_database()
    
    # Create session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    })
    
    # Get p_auth
    print("\n1. Getting p_auth...")
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
    
    # Search for 'a'
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
    search = session.post('https://annuaire.sante.fr/web/site-pro/home', data=search_data)
    soup = BeautifulSoup(search.text, 'html.parser')
    cards = soup.find_all('div', class_='contenant_resultat')
    print(f"   Found {len(cards)} doctors on page 1")
    
    # CRITICAL: Collect ALL cards from ALL pages FIRST, THEN scrape details
    # This prevents session from being flagged during pagination
    print("\n3. Collecting cards from all pages...")
    all_cards = []
    page = 1
    max_pages = 10
    
    # Collect cards from first page
    all_cards.extend(cards)
    print(f"   Page {page}: {len(cards)} cards")
    
    # Quickly paginate through remaining pages
    for page in range(2, max_pages + 1):
        pagination_params = {
            'p_p_id': 'resultatportlet',
            'p_p_lifecycle': '0',
            'p_p_state': 'normal',
            'p_p_mode': 'view',
            '_resultatportlet_delta': '10',
            '_resultatportlet_resetCur': 'false',
            '_resultatportlet_cur': str(page)
        }
        pagination_headers = {
            'Referer': 'https://annuaire.sante.fr/web/site-pro/recherche/resultats',
            'Upgrade-Insecure-Requests': '1'
        }
        page_response = session.get('https://annuaire.sante.fr/web/site-pro/recherche/resultats', 
                                   params=pagination_params, headers=pagination_headers, timeout=30)
        
        if page_response.status_code != 200:
            print(f"   Page {page}: Failed (HTTP {page_response.status_code})")
            break
        
        soup = BeautifulSoup(page_response.text, 'html.parser')
        page_cards = soup.find_all('div', class_='contenant_resultat')
        
        if not page_cards:
            print(f"   Page {page}: No more results")
            break
        
        all_cards.extend(page_cards)
        print(f"   Page {page}: {len(page_cards)} cards")
        time.sleep(0.2)  # Small delay between pagination requests
    
    print(f"\n   Total cards collected: {len(all_cards)}")
    
    # NOW scrape details for collected cards
    print("\n4. Scraping details for collected doctors (target: 100)...")
    count = 0
    target = min(100, len(all_cards))
    
    for card in all_cards[:target]:
        doctor_data = scrape_one_doctor(session, card, p_auth)
        if doctor_data:
            save_doctor(doctor_data)
            count += 1
            print(f"    [{count}/{target}] [OK] Saved: {doctor_data['name']}")
            # Longer delay to avoid triggering anti-scraping
            time.sleep(1.0)
    
    print(f"\n{'='*80}")
    print(f"DONE! Scraped {count} doctors successfully")
    print(f"Database: db/simple_scraper.db")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()


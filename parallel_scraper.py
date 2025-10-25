#!/usr/bin/env python3
"""
Parallel scraper using multiprocessing to scrape multiple prefixes simultaneously.
Each process runs an independent session with its own prefix.

SOTA Approach:
- Multiprocessing (not threading) to avoid GIL and session conflicts
- Each process gets unique search prefixes
- Independent sessions prevent anti-scraping triggers
- Shared SQLite database with proper locking
- Progress tracking with tqdm
"""

import multiprocessing as mp
from multiprocessing import Pool, Manager
import time
import requests
from bs4 import BeautifulSoup
import re
import sqlite3
from functools import partial
import sys

# Import from our working scraper
from legacy.scraper.content_extractor import (
    extract_situation_content,
    extract_dossier_content,
    extract_diplomes_content,
    extract_personne_content
)


def create_database():
    """Create SQLite database with proper threading support"""
    conn = sqlite3.connect('db/health_professionals.db', check_same_thread=False)
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
            search_prefix TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def save_doctor(data, db_path='db/health_professionals.db'):
    """Thread-safe database save with proper locking"""
    conn = sqlite3.connect(db_path, timeout=30.0)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO professionals
        (rpps, name, profession, organization, address, phone, email,
         situation_data, dossier_data, diplomes_data, personne_data, 
         search_prefix, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
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
        data.get('personne_data', '{}'),
        data.get('prefix', '')
    ))
    conn.commit()
    conn.close()


def scrape_one_doctor(session, card, p_auth, prefix):
    """Scrape one doctor (same as simple_scraper.py)"""
    nom_prenom = card.find('div', class_='nom_prenom')
    if not nom_prenom:
        return None
    
    link = nom_prenom.find('a', href=True)
    if not link:
        return None
    
    name = link.get_text(strip=True)
    
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(link['href'])
    params = parse_qs(parsed.query)
    ids = {k: v[0] if v else '' for k, v in params.items()}
    rpps = ids.get('_mapportlet_idRpps', '')
    
    if not rpps:
        return None
    
    data = {'rpps': rpps, 'name': name, 'prefix': prefix}
    
    # Basic fields
    profession_divs = card.find_all('div', class_='profession')
    if profession_divs:
        texts = [p.get_text(strip=True) for p in profession_divs if p.get_text(strip=True)]
        if texts:
            data['profession'] = texts[0]
        if len(texts) > 1:
            data['organization'] = ' | '.join(texts[1:])
    
    address_div = card.find('div', class_='adresse')
    if address_div:
        data['address'] = address_div.get_text(' ', strip=True)
    
    tel_div = card.find('div', class_='tel')
    if tel_div:
        data['phone'] = tel_div.get_text(strip=True)
    
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
        time.sleep(0.5)
        
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
        time.sleep(0.5)
        
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
        time.sleep(0.5)
        
        # Diplomes
        diplomes_params = base_params.copy()
        diplomes_params['_resultatsportlet_javax.portlet.action'] = 'detailsPPDiplomes'
        diplomes = session.post('https://annuaire.sante.fr/web/site-pro/information-detaillees',
                               params=diplomes_params, data='', timeout=30)
        data['diplomes_data'] = extract_diplomes_content(diplomes.text)
        time.sleep(0.5)
        
        # Personne
        personne_params = base_params.copy()
        personne_params['_resultatsportlet_javax.portlet.action'] = 'detailsPPPersonne'
        personne = session.post('https://annuaire.sante.fr/web/site-pro/information-detaillees',
                               params=personne_params, data='', timeout=30)
        data['personne_data'] = extract_personne_content(personne.text)
        
    except Exception as e:
        print(f"    ERROR fetching details for {name}: {e}")
    
    return data


def scrape_prefix(prefix, progress_queue=None):
    """
    Scrape all doctors for a given search prefix.
    This runs in its own process with its own session.
    """
    process_id = mp.current_process().name
    
    try:
        # Create session
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        })
        
        # Get p_auth
        home = session.get('https://annuaire.sante.fr/web/site-pro', timeout=30)
        soup = BeautifulSoup(home.text, 'html.parser')
        form = soup.find('form', attrs={'name': 'fmRecherche'})
        p_auth = ''
        if form:
            action = form.get('action', '')
            match = re.search(r'p_auth=([^&]+)', action)
            if match:
                p_auth = match.group(1)
        
        if not p_auth:
            print(f"[{process_id}] Prefix '{prefix}': Failed to get p_auth")
            return {'prefix': prefix, 'count': 0, 'error': 'No p_auth'}
        
        # Search
        search_data = {
            'p_p_id': 'rechercheportlet_INSTANCE_blk14HrIzEMS',
            'p_p_lifecycle': '1',
            'p_p_state': 'normal',
            'p_p_mode': 'view',
            '_rechercheportlet_INSTANCE_blk14HrIzEMS_javax.portlet.action': 'rechercheAction',
            'p_auth': p_auth,
            '_rechercheportlet_INSTANCE_blk14HrIzEMS_texttofind': prefix,
            '_rechercheportlet_INSTANCE_blk14HrIzEMS_adresse': '',
            '_rechercheportlet_INSTANCE_blk14HrIzEMS_cordonneesGeo': '',
            '_rechercheportlet_INSTANCE_blk14HrIzEMS_integralite': 'active_only',
            '_rechercheportlet_INSTANCE_blk14HrIzEMS_typeRecherche': 'textLibre'
        }
        search = session.post('https://annuaire.sante.fr/web/site-pro/home', data=search_data, timeout=30)
        soup = BeautifulSoup(search.text, 'html.parser')
        cards = soup.find_all('div', class_='contenant_resultat')
        
        # Collect ALL cards from pagination FIRST
        all_cards = list(cards)
        max_pages = 10
        
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
                break
            
            soup = BeautifulSoup(page_response.text, 'html.parser')
            page_cards = soup.find_all('div', class_='contenant_resultat')
            
            if not page_cards:
                break
            
            all_cards.extend(page_cards)
            time.sleep(0.2)
        
        print(f"[{process_id}] Prefix '{prefix}': Collected {len(all_cards)} cards")
        
        # NOW scrape details
        count = 0
        for card in all_cards:
            doctor_data = scrape_one_doctor(session, card, p_auth, prefix)
            if doctor_data:
                save_doctor(doctor_data)
                count += 1
                if progress_queue:
                    progress_queue.put({'prefix': prefix, 'doctor': doctor_data['name']})
                time.sleep(1.0)  # Critical delay
        
        return {'prefix': prefix, 'count': count, 'total_cards': len(all_cards)}
        
    except Exception as e:
        print(f"[{process_id}] Prefix '{prefix}': ERROR - {e}")
        return {'prefix': prefix, 'count': 0, 'error': str(e)}


def main():
    """Main parallel scraper with progress tracking"""
    print("="*80)
    print("PARALLEL SCRAPER - Multiple Processes, Multiple Prefixes")
    print("="*80)
    
    # Create database
    create_database()
    
    # Define search prefixes (start with single letters)
    # You can expand this to aa, ab, ac, etc. for more coverage
    prefixes = list('abcdefghij')  # First 10 letters for testing
    num_workers = min(4, len(prefixes))  # Max 4 concurrent processes
    
    print(f"\n1. Configuration:")
    print(f"   Prefixes to scrape: {', '.join(prefixes)}")
    print(f"   Concurrent workers: {num_workers}")
    print(f"   Database: db/health_professionals.db")
    
    print(f"\n2. Starting parallel scraping...")
    start_time = time.time()
    
    # Create manager for progress tracking
    with Manager() as manager:
        progress_queue = manager.Queue()
        
        # Create pool and run
        with Pool(processes=num_workers) as pool:
            # Start async results
            scrape_with_queue = partial(scrape_prefix, progress_queue=progress_queue)
            result = pool.map_async(scrape_with_queue, prefixes)
            
            # Monitor progress
            completed_prefixes = 0
            while not result.ready():
                try:
                    msg = progress_queue.get(timeout=1)
                    print(f"   [{msg['prefix']}] Saved: {msg['doctor']}")
                except:
                    pass
            
            # Get final results
            results = result.get()
    
    elapsed = time.time() - start_time
    
    # Summary
    print(f"\n{'='*80}")
    print("SCRAPING COMPLETE")
    print(f"{'='*80}")
    print(f"\nResults by prefix:")
    total_doctors = 0
    for res in results:
        prefix = res['prefix']
        count = res['count']
        total_cards = res.get('total_cards', 0)
        error = res.get('error', '')
        total_doctors += count
        status = f"✓ {count}/{total_cards} doctors" if not error else f"✗ Error: {error}"
        print(f"  {prefix:3s}: {status}")
    
    print(f"\n  Total: {total_doctors} doctors scraped")
    print(f"  Time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print(f"  Speed: {total_doctors/elapsed:.2f} doctors/second")
    print(f"\nDatabase: db/health_professionals.db")
    print(f"{'='*80}")


if __name__ == '__main__':
    # Required for Windows multiprocessing
    mp.freeze_support()
    main()


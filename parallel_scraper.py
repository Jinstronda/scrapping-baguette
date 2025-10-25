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
- Comprehensive logging and metrics tracking
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
import os
import json
from datetime import datetime
from pathlib import Path

# Import configuration
import config

# Import smart expansion
from smart_expansion import smart_scrape

# Import from our working scraper
from legacy.scraper.content_extractor import (
    extract_situation_content,
    extract_dossier_content,
    extract_diplomes_content,
    extract_personne_content
)


def create_database():
    """Create SQLite database with proper threading support"""
    # Ensure db directory exists
    Path('db').mkdir(exist_ok=True)
    conn = sqlite3.connect(config.DATABASE_PATH, check_same_thread=False)
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


def save_doctor(data, db_path=None):
    """Thread-safe database save with proper locking"""
    if db_path is None:
        db_path = config.DATABASE_PATH
    conn = sqlite3.connect(db_path, timeout=config.DB_TIMEOUT)
    c = conn.cursor()
    
    # Check if doctor already exists
    c.execute('SELECT rpps FROM professionals WHERE rpps = ?', (data['rpps'],))
    is_duplicate = c.fetchone() is not None
    
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
    
    return is_duplicate


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
                            params=detail_params, data='', timeout=config.REQUEST_TIMEOUT)
        time.sleep(config.DELAY_BETWEEN_TABS)
        
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
                                params=situation_params, data='', timeout=config.REQUEST_TIMEOUT)
        data['situation_data'] = extract_situation_content(situation.text)
        time.sleep(config.DELAY_BETWEEN_TABS)
        
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
                              params=dossier_params, data='', timeout=config.REQUEST_TIMEOUT)
        data['dossier_data'] = extract_dossier_content(dossier.text)
        time.sleep(config.DELAY_BETWEEN_TABS)
        
        # Diplomes
        diplomes_params = base_params.copy()
        diplomes_params['_resultatsportlet_javax.portlet.action'] = 'detailsPPDiplomes'
        diplomes = session.post('https://annuaire.sante.fr/web/site-pro/information-detaillees',
                               params=diplomes_params, data='', timeout=config.REQUEST_TIMEOUT)
        data['diplomes_data'] = extract_diplomes_content(diplomes.text)
        time.sleep(config.DELAY_BETWEEN_TABS)
        
        # Personne
        personne_params = base_params.copy()
        personne_params['_resultatsportlet_javax.portlet.action'] = 'detailsPPPersonne'
        personne = session.post('https://annuaire.sante.fr/web/site-pro/information-detaillees',
                               params=personne_params, data='', timeout=config.REQUEST_TIMEOUT)
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
            time.sleep(config.DELAY_BETWEEN_PAGES)
        
        pages_scraped = (len(all_cards) + 9) // 10  # Round up to get page count
        print(f"[{process_id}] Prefix '{prefix}': ✓ Collected {len(all_cards)} cards from {pages_scraped} pages")
        print(f"[{process_id}] Prefix '{prefix}': Starting detail scraping...")
        
        # NOW scrape details
        count = 0
        duplicates = 0
        details_complete = 0
        
        for idx, card in enumerate(all_cards, 1):
            doctor_data = scrape_one_doctor(session, card, p_auth, prefix)
            if doctor_data:
                is_duplicate = save_doctor(doctor_data)
                count += 1
                
                # Check if details were successfully scraped
                has_details = (
                    len(doctor_data.get('situation_data', '{}')) > 10 and
                    len(doctor_data.get('dossier_data', '{}')) > 10 and
                    len(doctor_data.get('diplomes_data', '{}')) > 10 and
                    len(doctor_data.get('personne_data', '{}')) > 10
                )
                
                if has_details:
                    details_complete += 1
                
                if is_duplicate:
                    duplicates += 1
                
                # Enhanced logging
                status_parts = []
                if is_duplicate:
                    status_parts.append("DUPLICATE")
                if has_details:
                    status_parts.append("DETAILS ✓")
                else:
                    status_parts.append("BASIC ONLY")
                
                status = f"[{', '.join(status_parts)}]" if status_parts else ""
                
                if progress_queue:
                    progress_queue.put({
                        'prefix': prefix, 
                        'doctor': doctor_data['name'],
                        'status': status,
                        'idx': idx,
                        'total': len(all_cards)
                    })
                
                time.sleep(config.DELAY_BETWEEN_DOCTORS)  # Critical delay
                
            # Check if we hit the limit
            if config.MAX_DOCTORS_PER_PREFIX > 0 and count >= config.MAX_DOCTORS_PER_PREFIX:
                print(f"[{process_id}] Prefix '{prefix}': Reached max doctors limit ({config.MAX_DOCTORS_PER_PREFIX})")
                break
        
        # Summary log
        print(f"[{process_id}] Prefix '{prefix}': ✓ FINISHED - {count} doctors ({details_complete} with full details, {duplicates} duplicates)")
        
        return {
            'prefix': prefix, 
            'count': count, 
            'total_cards': len(all_cards),
            'details_complete': details_complete,
            'duplicates': duplicates
        }
        
    except Exception as e:
        print(f"[{process_id}] Prefix '{prefix}': ERROR - {e}")
        return {'prefix': prefix, 'count': 0, 'error': str(e)}


def main():
    """Main parallel scraper with progress tracking"""
    # Setup logging
    if config.ENABLE_FILE_LOGGING:
        Path(config.LOGS_DIR).mkdir(exist_ok=True)
        
        if config.AUTO_LOG_FILENAME:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"scrape_{timestamp}_{config.NUM_WORKERS}workers.log"
        else:
            log_filename = f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        log_path = Path(config.LOGS_DIR) / log_filename
        log_file = open(log_path, 'w', encoding='utf-8')
    else:
        log_file = None
    
    def log(message):
        """Log to console and file"""
        print(message)
        if log_file:
            log_file.write(message + '\n')
            log_file.flush()
    
    log("="*80)
    log("PARALLEL SCRAPER - Multiple Processes, Multiple Prefixes")
    log("="*80)
    
    # Create database
    create_database()
    
    # Use config values
    prefixes = config.PREFIXES
    num_workers = min(config.NUM_WORKERS, len(prefixes))
    
    log(f"\n1. Configuration:")
    log(f"   Prefixes to scrape: {', '.join(prefixes)}")
    log(f"   Concurrent workers: {num_workers}")
    log(f"   Database: {config.DATABASE_PATH}")
    log(f"   Max doctors per prefix: {config.MAX_DOCTORS_PER_PREFIX if config.MAX_DOCTORS_PER_PREFIX > 0 else 'Unlimited'}")
    log(f"   Delay between doctors: {config.DELAY_BETWEEN_DOCTORS}s")
    log(f"   Log file: {log_path if config.ENABLE_FILE_LOGGING else 'Console only'}")
    
    log(f"   Smart expansion: {'ENABLED' if config.SMART_EXPANSION else 'DISABLED'}")
    log(f"\n2. Starting parallel scraping...")
    start_time = time.time()
    
    # Create manager for progress tracking
    with Manager() as manager:
        progress_queue = manager.Queue()
        
        # Monitor progress in background
        import threading
        stop_monitoring = threading.Event()
        
        def monitor_progress():
            while not stop_monitoring.is_set():
                try:
                    msg = progress_queue.get(timeout=1)
                    doctor_name = msg['doctor']
                    status = msg.get('status', '')
                    idx = msg.get('idx', '')
                    total = msg.get('total', '')
                    progress = f"({idx}/{total})" if idx and total else ""
                    log(f"   [{msg['prefix']}] {progress} {doctor_name} {status}")
                except:
                    pass
        
        monitor_thread = threading.Thread(target=monitor_progress, daemon=True)
        monitor_thread.start()
        
        # Choose scraping mode
        if config.SMART_EXPANSION:
            log("   Mode: SMART EXPANSION (will auto-expand prefixes that hit limits)")
            results = smart_scrape(scrape_prefix, prefixes, num_workers, progress_queue)
        else:
            log("   Mode: FIXED PREFIXES (no expansion)")
            with Pool(processes=num_workers) as pool:
                scrape_with_queue = partial(scrape_prefix, progress_queue=progress_queue)
                results = pool.map(scrape_with_queue, prefixes)
        
        stop_monitoring.set()
        monitor_thread.join(timeout=2)
    
    elapsed = time.time() - start_time
    
    # Calculate metrics
    log(f"\n{'='*80}")
    log("SCRAPING COMPLETE")
    log(f"{'='*80}")
    log(f"\nResults by prefix:")
    total_doctors = 0
    total_details = 0
    total_duplicates = 0
    failed_prefixes = []
    
    for res in results:
        prefix = res['prefix']
        count = res['count']
        total_cards = res.get('total_cards', 0)
        details = res.get('details_complete', 0)
        duplicates = res.get('duplicates', 0)
        error = res.get('error', '')
        total_doctors += count
        total_details += details
        total_duplicates += duplicates
        
        if error:
            status = f"✗ Error: {error}"
            failed_prefixes.append({'prefix': prefix, 'error': error})
        else:
            status = f"✓ {count}/{total_cards} doctors ({details} full details, {duplicates} dups)"
        log(f"  {prefix:3s}: {status}")
    
    success_rate = (len(prefixes) - len(failed_prefixes)) / len(prefixes) * 100 if prefixes else 0
    detail_completion_rate = (total_details / total_doctors * 100) if total_doctors > 0 else 0
    
    log(f"\n  Total: {total_doctors} doctors scraped")
    log(f"  Full details: {total_details}/{total_doctors} ({detail_completion_rate:.1f}%)")
    log(f"  Duplicates: {total_duplicates}")
    log(f"  Failed prefixes: {len(failed_prefixes)}/{len(prefixes)}")
    log(f"  Success rate: {success_rate:.1f}%")
    log(f"  Time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    log(f"  Speed: {total_doctors/elapsed:.2f} doctors/second")
    log(f"\nDatabase: {config.DATABASE_PATH}")
    log(f"{'='*80}")
    
    # Save metrics to JSON
    if config.TRACK_METRICS:
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'config': {
                'num_workers': num_workers,
                'prefixes': prefixes,
                'max_doctors_per_prefix': config.MAX_DOCTORS_PER_PREFIX,
                'delay_between_doctors': config.DELAY_BETWEEN_DOCTORS,
                'delay_between_tabs': config.DELAY_BETWEEN_TABS,
                'delay_between_pages': config.DELAY_BETWEEN_PAGES
            },
            'results': {
                'total_doctors': total_doctors,
                'total_details_complete': total_details,
                'detail_completion_rate': detail_completion_rate,
                'total_duplicates': total_duplicates,
                'failed_prefixes': len(failed_prefixes),
                'success_rate': success_rate,
                'elapsed_seconds': elapsed,
                'doctors_per_second': total_doctors / elapsed if elapsed > 0 else 0
            },
            'by_prefix': [
                {
                    'prefix': r['prefix'],
                    'count': r['count'],
                    'total_cards': r.get('total_cards', 0),
                    'details_complete': r.get('details_complete', 0),
                    'duplicates': r.get('duplicates', 0),
                    'error': r.get('error', None)
                }
                for r in results
            ],
            'failed_prefixes': failed_prefixes if config.SAVE_FAILED_DOCTORS else []
        }
        
        metrics_filename = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{num_workers}workers.json"
        metrics_path = Path(config.LOGS_DIR) / metrics_filename
        with open(metrics_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)
        log(f"\nMetrics saved to: {metrics_path}")
    
    if log_file:
        log_file.close()


if __name__ == '__main__':
    # Required for Windows multiprocessing
    mp.freeze_support()
    main()


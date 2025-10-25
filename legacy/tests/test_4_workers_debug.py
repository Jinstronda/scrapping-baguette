#!/usr/bin/env python3
"""Test 4 workers, 8 doctors each = 32 total with detailed logging"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import threading
import queue
import time
import sqlite3
from scraper.database import init_database, upsert_professional
from scraper.worker import submit_search_prefix, fetch_doctor_details
from scraper.parser import parse_search_results
from scraper.session import create_session
from scraper.content_extractor import extract_all_detail_content
from scraper.logger import logger

lock = threading.Lock()
total_doctors = 0
processed_doctors = 0

def worker_thread(worker_id, doctor_queue, db_path):
    """Worker that processes assigned doctors"""
    session = create_session()
    
    logger.info(f"Worker {worker_id} started")
    
    while True:
        try:
            doctor = doctor_queue.get(timeout=1)
            if doctor is None:
                break
            
            logger.info(f"Worker {worker_id} processing: {doctor['name']} (RPPS: {doctor['rpps']})")
            logger.info(f"  Basic fields: org={bool(doctor.get('organization'))}, addr={bool(doctor.get('address'))}, phone={bool(doctor.get('phone'))}")
            
            # Save basic info
            upsert_professional(db_path, doctor)
            
            # Fetch details
            if doctor.get('_ids'):
                raw_details = fetch_doctor_details(session, doctor['_ids'])
                
                # Log raw sizes
                raw_sizes = {k: len(v) if v else 0 for k, v in raw_details.items()}
                logger.info(f"  Raw fetched: sit={raw_sizes['situation_data']}, dos={raw_sizes['dossier_data']}, dip={raw_sizes['diplomes_data']}, per={raw_sizes['personne_data']}")
                
                # Save first response for debugging
                if worker_id == 0 and processed_doctors == 0:
                    with open(f'tests/worker0_dossier.html', 'w', encoding='utf-8') as f:
                        f.write(raw_details['dossier_data'] if raw_details['dossier_data'] else '')
                    logger.info(f"  Saved worker 0 first dossier to tests/worker0_dossier.html")
                
                # Extract clean
                clean_details = extract_all_detail_content(raw_details)
                
                # Log clean sizes
                clean_sizes = {k: len(v) if v else 0 for k, v in clean_details.items()}
                logger.info(f"  Clean extracted: sit={clean_sizes['situation_data']}, dos={clean_sizes['dossier_data']}, dip={clean_sizes['diplomes_data']}, per={clean_sizes['personne_data']}")
                
                detail_update = {
                    'rpps': doctor['rpps'],
                    'situation_data': clean_details.get('situation_data'),
                    'dossier_data': clean_details.get('dossier_data'),
                    'diplomes_data': clean_details.get('diplomes_data'),
                    'personne_data': clean_details.get('personne_data')
                }
                upsert_professional(db_path, detail_update)
                logger.info(f"  Worker {worker_id} completed {doctor['name']}")
            
            doctor_queue.task_done()
            
        except queue.Empty:
            break
        except Exception as e:
            logger.error(f"Worker {worker_id} error: {e}")
            doctor_queue.task_done()
    
    logger.info(f"Worker {worker_id} finished")

def main():
    global total_doctors
    
    db_path = "db/test_4_workers.db"
    
    logger.info("="*80)
    logger.info("4-WORKER TEST - 32 doctors (8 per worker)")
    logger.info("="*80)
    
    init_database(db_path)
    
    # Fetch 32 doctors
    logger.info("Fetching 32 doctors from letter 'a'...")
    session = create_session()
    response = submit_search_prefix(session, 'a')
    
    doctors = parse_search_results(response.text)
    
    # Get more pages
    from scraper.config import SEARCH_URL
    from scraper.session import get_with_retry
    
    for page in range(2, 4):
        params = {
            'p_p_id': 'resultatportlet',
            'p_p_lifecycle': '0',
            'p_p_state': 'normal',
            'p_p_mode': 'view',
            '_resultatportlet_delta': '10',
            '_resultatportlet_resetCur': 'false',
            '_resultatportlet_cur': str(page)
        }
        
        page_response = get_with_retry(session, SEARCH_URL, params=params, retries=1)
        if page_response and page_response.status_code == 200:
            page_doctors = parse_search_results(page_response.text)
            doctors.extend(page_doctors)
    
    doctors = doctors[:32]
    total_doctors = len(doctors)
    
    logger.info(f"Collected {total_doctors} doctors")
    
    # Log sample of what we collected
    logger.info(f"\nSample of collected doctors:")
    for i, doc in enumerate(doctors[:3]):
        logger.info(f"  {i+1}. {doc['name']} - Org: {doc.get('organization', 'N/A')} - Phone: {doc.get('phone', 'N/A')}")
    
    # Queue
    doctor_queue = queue.Queue()
    for doc in doctors:
        doctor_queue.put(doc)
    
    logger.info(f"\nStarting 4 workers...")
    
    # Start workers
    threads = []
    for i in range(4):
        thread = threading.Thread(target=worker_thread, args=(i, doctor_queue, db_path))
        thread.start()
        threads.append(thread)
    
    # Wait
    start_time = time.time()
    for thread in threads:
        thread.join()
    
    elapsed = time.time() - start_time
    
    logger.info("="*80)
    logger.info(f"TEST COMPLETE in {elapsed:.1f} seconds")
    logger.info("="*80)
    
    # Verify database
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute('SELECT COUNT(*) FROM professionals')
    total = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM professionals WHERE address IS NOT NULL AND address != ""')
    with_addr = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM professionals WHERE phone IS NOT NULL AND phone != ""')
    with_phone = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM professionals WHERE organization IS NOT NULL AND organization != ""')
    with_org = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM professionals WHERE LENGTH(dossier_data) > 100')
    with_dossier = cur.fetchone()[0]
    
    logger.info(f"\nDATA QUALITY:")
    logger.info(f"  Total records: {total}")
    logger.info(f"  With address: {with_addr}")
    logger.info(f"  With phone: {with_phone}")
    logger.info(f"  With organization: {with_org}")
    logger.info(f"  With dossier data (>100 bytes): {with_dossier}")
    
    # Show samples
    cur.execute('''SELECT rpps, name, organization, address, phone, 
                   LENGTH(dossier_data) 
                   FROM professionals LIMIT 5''')
    
    logger.info(f"\nSAMPLE RECORDS:")
    for r in cur.fetchall():
        logger.info(f"  {r[1]}")
        logger.info(f"    Org: {r[2][:40] if r[2] else '(none)'}")
        logger.info(f"    Addr: {r[3][:40] if r[3] else '(none)'}")
        logger.info(f"    Phone: {r[4] if r[4] else '(none)'}")
        logger.info(f"    Dossier: {r[5] if r[5] else 0} bytes")
    
    conn.close()
    
    logger.info(f"\nDatabase: {db_path}")
    logger.info("="*80)

if __name__ == '__main__':
    main()


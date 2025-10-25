#!/usr/bin/env python3
"""Test 4 workers with 10 doctors each = 40 total"""

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

def worker_thread(worker_id, doctor_queue, db_path):
    session = create_session()
    logger.info(f"Worker {worker_id} started")
    
    while True:
        try:
            doctor = doctor_queue.get(timeout=1)
            if doctor is None:
                break
            
            logger.info(f"W{worker_id}: {doctor['name'][:20]:20} | Org={bool(doctor.get('organization'))} Addr={bool(doctor.get('address'))} Phone={bool(doctor.get('phone'))}")
            
            upsert_professional(db_path, doctor)
            
            if doctor.get('_ids'):
                raw_details = fetch_doctor_details(session, doctor['_ids'])
                clean_details = extract_all_detail_content(raw_details)
                
                detail_update = {
                    'rpps': doctor['rpps'],
                    'situation_data': clean_details.get('situation_data'),
                    'dossier_data': clean_details.get('dossier_data'),
                    'diplomes_data': clean_details.get('diplomes_data'),
                    'personne_data': clean_details.get('personne_data')
                }
                upsert_professional(db_path, detail_update)
            
            doctor_queue.task_done()
            
        except queue.Empty:
            break
        except Exception as e:
            logger.error(f"Worker {worker_id} error: {e}")
            doctor_queue.task_done()
    
    logger.info(f"Worker {worker_id} finished")

def main():
    db_path = "db/test_4_workers_final.db"
    
    logger.info("="*80)
    logger.info("4-WORKER TEST - 40 doctors")
    logger.info("="*80)
    
    init_database(db_path)
    
    # Fetch 40 doctors
    logger.info("Fetching doctors...")
    session = create_session()
    response = submit_search_prefix(session, 'a')
    
    doctors = parse_search_results(response.text)
    
    from scraper.config import SEARCH_URL
    from scraper.session import get_with_retry
    
    for page in range(2, 5):
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
    
    doctors = doctors[:40]
    logger.info(f"Collected {len(doctors)} doctors")
    
    # Queue
    doctor_queue = queue.Queue()
    for doc in doctors:
        doctor_queue.put(doc)
    
    logger.info("Starting 4 workers...")
    
    # Start workers
    threads = []
    start_time = time.time()
    
    for i in range(4):
        thread = threading.Thread(target=worker_thread, args=(i, doctor_queue, db_path))
        thread.start()
        threads.append(thread)
        time.sleep(0.5)  # Stagger worker starts to avoid overwhelming server
    
    for thread in threads:
        thread.join()
    
    elapsed = time.time() - start_time
    
    logger.info("="*80)
    logger.info(f"TEST COMPLETE in {elapsed:.1f}s")
    logger.info("="*80)
    
    # Verify
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute('SELECT COUNT(*) FROM professionals')
    total = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM professionals WHERE organization IS NOT NULL AND organization != ""')
    with_org = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM professionals WHERE phone IS NOT NULL AND phone != ""')
    with_phone = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM professionals WHERE LENGTH(dossier_data) > 100')
    with_dossier = cur.fetchone()[0]
    
    logger.info(f"\nRESULTS:")
    logger.info(f"  Total: {total}")
    logger.info(f"  With organization: {with_org}/{total}")
    logger.info(f"  With phone: {with_phone}/{total}")
    logger.info(f"  With dossier (>100 bytes): {with_dossier}/{total}")
    
    if with_org > 20 and with_dossier > 30:
        logger.info("\n✓ SUCCESS! 4 workers working correctly")
    else:
        logger.info("\n✗ FAILED - Detail extraction issue")
    
    logger.info(f"\nDatabase: {db_path}")
    logger.info("="*80)
    
    conn.close()

if __name__ == '__main__':
    main()


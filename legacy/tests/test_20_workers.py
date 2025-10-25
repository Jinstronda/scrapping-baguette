#!/usr/bin/env python3
"""Test with 20 workers scraping doctors"""

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

# Global counters
lock = threading.Lock()
total_doctors = 0
processed_doctors = 0
failed_doctors = 0
worker_status = {}

def update_progress(worker_id, status, doctor_name=""):
    global processed_doctors, failed_doctors, worker_status
    
    with lock:
        worker_status[worker_id] = f"{status}: {doctor_name}"
        if status == "DONE":
            processed_doctors += 1
        elif status == "FAILED":
            failed_doctors += 1

def print_progress():
    with lock:
        print("\033[2J\033[H", end="")
        print("="*80)
        print(f"20-WORKER TEST - Scraping {total_doctors} doctors")
        print("="*80)
        print(f"Progress: {processed_doctors}/{total_doctors} | Failed: {failed_doctors}")
        print(f"Active: {sum([1 for s in worker_status.values() if 'WORKING' in s or 'FETCH' in s])}/20")
        print("-"*80)
        
        # Show workers in 2 rows of 10
        for i in range(0, 20, 10):
            row = []
            for j in range(10):
                wid = i + j
                status = worker_status.get(wid, "IDLE")
                if "DONE" in status:
                    row.append("#")
                elif "WORK" in status or "FETCH" in status:
                    row.append("*")
                elif "FAIL" in status:
                    row.append("X")
                else:
                    row.append(".")
            print(f"W{i:2}-{i+9:2}: {' '.join(row)}")
        
        print("-"*80)
        print("# = Done  * = Working  . = Waiting  X = Failed")
        print("="*80)

def worker_thread(worker_id, doctor_queue, db_path):
    session = create_session()
    
    while True:
        try:
            doctor = doctor_queue.get(timeout=1)
            if doctor is None:
                break
            
            try:
                update_progress(worker_id, "WORKING", doctor['name'][:20])
                
                # Save basic
                upsert_professional(db_path, doctor)
                
                # Fetch details
                if doctor.get('_ids'):
                    update_progress(worker_id, "FETCHING", doctor['name'][:20])
                    
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
                
                update_progress(worker_id, "DONE", doctor['name'][:20])
            except Exception as e:
                logger.error(f"Worker {worker_id} error on {doctor.get('name', 'unknown')}: {e}")
                update_progress(worker_id, "FAILED", str(e)[:20])
            
            doctor_queue.task_done()
            
        except queue.Empty:
            break
        except Exception as e:
            logger.error(f"Worker {worker_id} queue error: {e}")
            break

def main():
    global total_doctors
    
    db_path = "db/test_20_workers.db"
    
    logger.info("Initializing...")
    init_database(db_path)
    
    logger.info("Fetching 40 doctors (20 workers x 2 doctors each)...")
    session = create_session()
    response = submit_search_prefix(session, 'a')
    
    doctors = parse_search_results(response.text)
    
    # Get more pages to reach 40
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
    total_doctors = len(doctors)
    logger.info(f"Collected {total_doctors} doctors")
    
    # Queue
    doctor_queue = queue.Queue()
    for doc in doctors:
        doctor_queue.put(doc)
    
    # Init status
    for i in range(20):
        worker_status[i] = "IDLE"
    
    logger.info("Starting 20 workers...")
    
    # Start workers
    threads = []
    for i in range(20):
        thread = threading.Thread(target=worker_thread, args=(i, doctor_queue, db_path))
        thread.daemon = True
        thread.start()
        threads.append(thread)
    
    # Progress monitor
    start_time = time.time()
    while processed_doctors + failed_doctors < total_doctors:
        print_progress()
        time.sleep(0.5)
    
    doctor_queue.join()
    print_progress()
    
    elapsed = time.time() - start_time
    
    print(f"\n{'='*80}")
    print("TEST COMPLETE!")
    print(f"{'='*80}")
    print(f"Time: {elapsed:.1f}s")
    print(f"Processed: {processed_doctors}/{total_doctors}")
    print(f"Failed: {failed_doctors}")
    print(f"Database: {db_path}")
    
    # Verify
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute('SELECT COUNT(*) FROM professionals WHERE LENGTH(dossier_data) > 100')
    with_data = cur.fetchone()[0]
    
    cur.execute('SELECT AVG(LENGTH(situation_data)), AVG(LENGTH(dossier_data)), AVG(LENGTH(diplomes_data)), AVG(LENGTH(personne_data)) FROM professionals WHERE dossier_data IS NOT NULL')
    avg = cur.fetchone()
    
    print(f"\nData Quality:")
    print(f"  Doctors with complete data: {with_data}/{total_doctors} ({int(with_data/total_doctors*100)}%)")
    if avg and avg[0]:
        print(f"  Avg sizes: Sit={int(avg[0])} | Dos={int(avg[1])} | Dip={int(avg[2])} | Per={int(avg[3])}")
    
    conn.close()
    print(f"{'='*80}")

if __name__ == '__main__':
    main()


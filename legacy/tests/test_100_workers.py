#!/usr/bin/env python3
"""Test with 100 workers scraping 200 doctors total"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import threading
import queue
import time
from scraper.database import init_database, upsert_professional
from scraper.worker import submit_search_prefix, fetch_doctor_details
from scraper.parser import parse_search_results
from scraper.session import create_session
from scraper.content_extractor import extract_all_detail_content
from scraper.logger import logger

# Global counters for progress
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
    """Print progress bar for all workers"""
    with lock:
        print("\033[2J\033[H", end="")  # Clear screen
        print("="*100)
        print(f"100-WORKER SCRAPER TEST - Target: 200 doctors")
        print("="*100)
        print(f"Progress: {processed_doctors}/{total_doctors} completed | {failed_doctors} failed")
        print(f"Active workers: {sum([1 for s in worker_status.values() if 'WORKING' in s or 'FETCHING' in s])}/100")
        print("-"*100)
        
        # Show worker status in grid
        for i in range(0, 100, 10):
            row = []
            for j in range(10):
                worker_id = i + j
                status = worker_status.get(worker_id, "IDLE")
                if "DONE" in status:
                    row.append("#")
                elif "WORK" in status or "FETCH" in status:
                    row.append("*")
                elif "FAIL" in status:
                    row.append("X")
                else:
                    row.append(".")
            print(f"Workers {i:2}-{i+9:2}: {' '.join(row)}")
        
        print("-"*100)
        print("# = Done  * = Working  . = Waiting  X = Failed")
        print("="*100)

def worker_thread(worker_id, doctor_queue, db_path):
    """Worker that processes assigned doctors"""
    session = create_session()
    
    while True:
        try:
            doctor = doctor_queue.get(timeout=1)
            if doctor is None:
                break
            
            update_progress(worker_id, "WORKING", doctor['name'])
            
            # Save basic info
            upsert_professional(db_path, doctor)
            
            # Fetch details
            if doctor.get('_ids'):
                update_progress(worker_id, "FETCHING", doctor['name'])
                
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
            
            update_progress(worker_id, "DONE", doctor['name'])
            doctor_queue.task_done()
            
        except queue.Empty:
            break
        except Exception as e:
            update_progress(worker_id, "FAILED", str(e)[:20])
            doctor_queue.task_done()

def main():
    global total_doctors
    
    db_path = "db/test_100_workers.db"
    
    logger.info("Initializing database...")
    init_database(db_path)
    
    logger.info("Fetching 200 doctors from letter 'a'...")
    session = create_session()
    response = submit_search_prefix(session, 'a')
    
    # Get first page (10 doctors)
    doctors = parse_search_results(response.text)
    
    # Get more pages to reach ~200 doctors
    from scraper.config import SEARCH_URL
    from scraper.session import get_with_retry
    
    for page in range(2, 21):  # Pages 2-20 = 190 more doctors
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
            
            if len(doctors) >= 200:
                doctors = doctors[:200]
                break
    
    total_doctors = len(doctors)
    logger.info(f"Collected {total_doctors} doctors to process")
    
    # Create work queue
    doctor_queue = queue.Queue()
    for doctor in doctors:
        doctor_queue.put(doctor)
    
    # Initialize worker status
    for i in range(100):
        worker_status[i] = "IDLE"
    
    logger.info("Starting 100 workers...")
    
    # Start workers
    threads = []
    for i in range(100):
        thread = threading.Thread(target=worker_thread, args=(i, doctor_queue, db_path))
        thread.daemon = True
        thread.start()
        threads.append(thread)
    
    # Progress monitor
    start_time = time.time()
    while processed_doctors + failed_doctors < total_doctors:
        print_progress()
        time.sleep(0.5)
    
    # Wait for completion
    doctor_queue.join()
    
    # Final progress
    print_progress()
    
    elapsed = time.time() - start_time
    
    print(f"\n{'='*100}")
    print(f"TEST COMPLETE!")
    print(f"{'='*100}")
    print(f"Total time: {elapsed:.1f} seconds")
    print(f"Doctors processed: {processed_doctors}/{total_doctors}")
    print(f"Failed: {failed_doctors}")
    print(f"Database: {db_path}")
    print(f"{'='*100}")

if __name__ == '__main__':
    main()


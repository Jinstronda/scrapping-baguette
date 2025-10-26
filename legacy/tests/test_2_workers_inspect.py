#!/usr/bin/env python3
"""Test 2 workers and inspect what they receive"""

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

def worker_thread(worker_id, doctor_queue, db_path):
    session = create_session()
    logger.info(f"Worker {worker_id} STARTED")
    
    doctor_count = 0
    
    while True:
        try:
            doctor = doctor_queue.get(timeout=1)
            if doctor is None:
                break
            
            doctor_count += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"Worker {worker_id} | Doctor {doctor_count}: {doctor['name']}")
            logger.info(f"  RPPS: {doctor['rpps']}")
            logger.info(f"  Org: {doctor.get('organization', 'N/A')}")
            logger.info(f"  Addr: {doctor.get('address', 'N/A')[:40] if doctor.get('address') else 'N/A'}")
            logger.info(f"  Phone: {doctor.get('phone', 'N/A')}")
            
            # Save basic
            upsert_professional(db_path, doctor)
            
            # Fetch details
            if doctor.get('_ids'):
                logger.info(f"\n  Fetching detail tabs...")
                raw_details = fetch_doctor_details(session, doctor['_ids'])
                
                # Show what we got
                logger.info(f"  RAW HTML received:")
                logger.info(f"    Situation: {len(raw_details['situation_data']) if raw_details['situation_data'] else 0:,} bytes")
                logger.info(f"    Dossier: {len(raw_details['dossier_data']) if raw_details['dossier_data'] else 0:,} bytes")
                logger.info(f"    Diplomes: {len(raw_details['diplomes_data']) if raw_details['diplomes_data'] else 0:,} bytes")
                logger.info(f"    Personne: {len(raw_details['personne_data']) if raw_details['personne_data'] else 0:,} bytes")
                
                # Check if it contains actual data
                if raw_details['dossier_data']:
                    has_exercice = 'EXERCICE PROFESSIONNEL' in raw_details['dossier_data']
                    has_content_div = 'contenu_dossier' in raw_details['dossier_data']
                    logger.info(f"  Dossier checks:")
                    logger.info(f"    Contains 'EXERCICE PROFESSIONNEL': {has_exercice}")
                    logger.info(f"    Contains 'contenu_dossier': {has_content_div}")
                    
                    # Save for inspection
                    with open(f'tests/worker{worker_id}_doctor{doctor_count}_dossier.html', 'w', encoding='utf-8') as f:
                        f.write(raw_details['dossier_data'])
                    logger.info(f"    Saved to: tests/worker{worker_id}_doctor{doctor_count}_dossier.html")
                
                # Extract
                logger.info(f"\n  Extracting clean JSON...")
                clean_details = extract_all_detail_content(raw_details)
                
                logger.info(f"  CLEAN JSON extracted:")
                logger.info(f"    Situation: {len(clean_details['situation_data']) if clean_details['situation_data'] else 0:,} bytes")
                logger.info(f"    Dossier: {len(clean_details['dossier_data']) if clean_details['dossier_data'] else 0:,} bytes")
                logger.info(f"    Diplomes: {len(clean_details['diplomes_data']) if clean_details['diplomes_data'] else 0:,} bytes")
                logger.info(f"    Personne: {len(clean_details['personne_data']) if clean_details['personne_data'] else 0:,} bytes")
                
                # Save
                detail_update = {
                    'rpps': doctor['rpps'],
                    'situation_data': clean_details.get('situation_data'),
                    'dossier_data': clean_details.get('dossier_data'),
                    'diplomes_data': clean_details.get('diplomes_data'),
                    'personne_data': clean_details.get('personne_data')
                }
                upsert_professional(db_path, detail_update)
                logger.info(f"  Saved to database")
            
            doctor_queue.task_done()
            
        except queue.Empty:
            break
        except Exception as e:
            logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
            doctor_queue.task_done()
    
    logger.info(f"\nWorker {worker_id} FINISHED (processed {doctor_count} doctors)")

def main():
    db_path = "db/test_2_workers.db"
    
    logger.info("="*80)
    logger.info("2-WORKER INSPECTION TEST")
    logger.info("="*80)
    
    init_database(db_path)
    
    # Fetch 10 doctors
    logger.info("\nFetching 10 doctors...")
    session = create_session()
    response = submit_search_prefix(session, 'a')
    
    doctors = parse_search_results(response.text)[:10]
    logger.info(f"Collected {len(doctors)} doctors\n")
    
    # Queue
    doctor_queue = queue.Queue()
    for doc in doctors:
        doctor_queue.put(doc)
    
    logger.info("Starting 2 workers (staggered by 1 second)...\n")
    
    # Start workers
    threads = []
    for i in range(2):
        thread = threading.Thread(target=worker_thread, args=(i, doctor_queue, db_path))
        thread.start()
        threads.append(thread)
        time.sleep(1)  # Stagger starts
    
    for thread in threads:
        thread.join()
    
    logger.info("\n" + "="*80)
    logger.info("TEST COMPLETE")
    logger.info("="*80)
    logger.info(f"\nDatabase: {db_path}")
    logger.info("Check the saved HTML files in tests/ to see what each worker received")
    logger.info("="*80)

if __name__ == '__main__':
    main()


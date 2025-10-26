#!/usr/bin/env python3
"""Test script for single-letter scraping"""

import sqlite3
from scraper.database import init_database
from scraper.coordinator import run_scraper
from scraper.logger import logger

def test_single_letter():
    """Test scraping with single thread on letter 'z' (small dataset)"""
    db_path = "test_scraper.db"
    
    logger.info("=== Starting single-letter test ===")
    logger.info(f"Database: {db_path}")
    logger.info("This will scrape only letter 'z' as a test")
    
    init_database(db_path)
    
    from scraper.coordinator import WorkQueue, worker_thread
    work_queue = WorkQueue()
    
    work_queue.queue.queue.clear()
    work_queue.seen_prefixes.clear()
    work_queue.queue.put('z')
    work_queue.seen_prefixes.add('z')
    
    worker_thread(work_queue, db_path, 0)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM professionals")
    count = cursor.fetchone()[0]
    
    cursor.execute("SELECT rpps, name, profession FROM professionals LIMIT 5")
    samples = cursor.fetchall()
    
    conn.close()
    
    logger.info("=== Test Results ===")
    logger.info(f"Total records: {count}")
    logger.info("Sample records:")
    for rpps, name, profession in samples:
        logger.info(f"  {rpps} - {name} - {profession}")
    
    if count > 0:
        logger.info("✓ Test PASSED - Data was successfully scraped")
    else:
        logger.warning("✗ Test FAILED - No data was scraped")
    
    return count > 0

if __name__ == '__main__':
    test_single_letter()


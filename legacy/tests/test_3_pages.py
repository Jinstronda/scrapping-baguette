#!/usr/bin/env python3
"""Test script for 3 pages with single worker"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
from scraper.database import init_database
from scraper.worker import process_prefix
from scraper.logger import logger
from scraper.config import DB_PATH

def test_3_pages():
    db_path = "db/test_3_pages.db"
    
    logger.info("=== Testing 3 pages with single worker ===")
    logger.info(f"Database: {db_path}")
    logger.info("Testing with letter 'z'")
    
    init_database(db_path)
    
    seen_prefixes = set()
    seen_prefixes.add('z')
    
    logger.info("Starting to process prefix 'z'")
    sub_prefixes = process_prefix('z', db_path, seen_prefixes)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM professionals")
    count = cursor.fetchone()[0]
    
    cursor.execute("SELECT rpps, name, profession, organization FROM professionals LIMIT 10")
    samples = cursor.fetchall()
    
    conn.close()
    
    logger.info("=== Test Results ===")
    logger.info(f"Total records: {count}")
    logger.info(f"Sub-prefixes generated: {sub_prefixes}")
    logger.info("Sample records:")
    for rpps, name, profession, org in samples:
        logger.info(f"  {rpps} - {name} - {profession} - {org}")
    
    if count > 0:
        logger.info("✓ Test PASSED - Data was successfully scraped")
    else:
        logger.warning("✗ Test FAILED - No data was scraped")
    
    return count > 0

if __name__ == '__main__':
    test_3_pages()


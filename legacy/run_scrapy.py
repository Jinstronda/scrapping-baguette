#!/usr/bin/env python3
"""Run the Scrapy spider"""

import subprocess
import sys

print("="*80)
print("RUNNING SCRAPY HEALTH PROFESSIONAL SCRAPER")
print("="*80)
print("\nThis uses Scrapy's built-in concurrency with cookiejar per doctor")
print("to solve the session conflict issues from multi-threaded requests.\n")

# Run scrapy
result = subprocess.run(
    ['scrapy', 'crawl', 'health_professionals', '-s', 'LOG_LEVEL=INFO'],
    cwd='scrapy_scraper',
    capture_output=False
)

if result.returncode == 0:
    print("\n" + "="*80)
    print("SCRAPING COMPLETE")
    print("="*80)
    print("\nDatabase: scrapy_scraper/db/scrapy_health_professionals.db")
    print("\nView data:")
    print("  python view_data.py scrapy_scraper/db/scrapy_health_professionals.db")
    print("="*80)
else:
    print(f"\nScraping failed with code {result.returncode}")
    sys.exit(result.returncode)


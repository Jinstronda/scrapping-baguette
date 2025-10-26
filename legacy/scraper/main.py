import argparse
from scraper.config import NUM_THREADS, DB_PATH
from scraper.database import init_database
from scraper.coordinator import run_scraper
from scraper.logger import logger

def main():
    parser = argparse.ArgumentParser(description='Health Professional Scraper')
    parser.add_argument('--threads', type=int, default=NUM_THREADS,
                       help=f'Number of worker threads (default: {NUM_THREADS})')
    parser.add_argument('--db', type=str, default=DB_PATH,
                       help=f'Database path (default: {DB_PATH})')
    
    args = parser.parse_args()
    
    logger.info(f"Initializing scraper with {args.threads} threads")
    logger.info(f"Database: {args.db}")
    
    init_database(args.db)
    
    run_scraper(args.threads, args.db)
    
    logger.info("Scraping completed")

if __name__ == '__main__':
    main()


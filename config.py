"""
Configuration file for parallel scraper
Adjust these settings to optimize scraping performance

QUICK START:
1. Test with 4 workers, no expansion: Leave defaults
2. Scale up: Set NUM_WORKERS = 30
3. Full coverage: Set SMART_EXPANSION = True, PREFIXES = list('abcdefghijklmnopqrstuvwxyz')
4. Run: python parallel_scraper.py
5. Check logs/ folder for results

See TESTING_GUIDE.md for detailed testing methodology
"""

# ============================================================================
# WORKER CONFIGURATION
# ============================================================================

# Number of concurrent workers (processes)
# Start with 4, can try up to 30-50
# More workers = faster, but risk of rate limiting
NUM_WORKERS = 30

# ============================================================================
# SCRAPING SCOPE
# ============================================================================

# Search prefixes to scrape
# Examples:
#   - Single letters: list('abcdefghij')
#   - All letters: list('abcdefghijklmnopqrstuvwxyz')
#   - Custom list: ['a', 'b', 'ma', 'me', 'pa']
PREFIXES = list('abcdefghij')  # First 10 letters for testing

# Enable smart prefix expansion
# When True: Automatically expands prefixes that hit pagination limit
# Example: If 'a' gets 100 results (10 pages), expands to 'aa', 'ab', ..., 'az'
SMART_EXPANSION = False  # Set to True for 100% coverage

# Maximum number of doctors to scrape per prefix (0 = unlimited)
# Useful for quick tests
MAX_DOCTORS_PER_PREFIX = 0

# Maximum pages to paginate through (website limit is ~10)
MAX_PAGES = 10

# ============================================================================
# TIMING & DELAYS
# ============================================================================

# Delay between scraping individual doctors (seconds)
# CRITICAL: Too fast will trigger anti-scraping
# Recommended: 0.5 - 2.0 seconds
DELAY_BETWEEN_DOCTORS = 1.0

# Delay between detail tab requests (seconds)
DELAY_BETWEEN_TABS = 0.5

# Delay between pagination requests (seconds)
DELAY_BETWEEN_PAGES = 0.2

# Request timeout (seconds)
REQUEST_TIMEOUT = 30

# ============================================================================
# DATABASE
# ============================================================================

DATABASE_PATH = 'db/health_professionals.db'

# Database connection timeout (seconds)
# Higher = better for high concurrency
DB_TIMEOUT = 30.0

# ============================================================================
# LOGGING
# ============================================================================

# Enable detailed logging to file
ENABLE_FILE_LOGGING = True

# Logs directory
LOGS_DIR = 'logs'

# Log level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL = 'INFO'

# Save failed doctors for retry
SAVE_FAILED_DOCTORS = True

# ============================================================================
# PERFORMANCE TESTING
# ============================================================================

# Auto-generate log filename with worker count
# Format: scrape_YYYYMMDD_HHMMSS_Nworkers.log
AUTO_LOG_FILENAME = True

# Track detailed metrics for performance analysis
TRACK_METRICS = True


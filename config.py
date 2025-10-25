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

# Prefix depth: How many letters in each starting prefix
# Examples:
#   PREFIX_DEPTH = 1  → ['a', 'b', 'c', ...]           (26 prefixes)
#   PREFIX_DEPTH = 2  → ['aa', 'ab', 'ac', ..., 'zz']  (676 prefixes)
#   PREFIX_DEPTH = 3  → ['aaa', 'aab', ..., 'zzz']     (17,576 prefixes)
PREFIX_DEPTH = 2

# How many initial prefixes to generate at PREFIX_DEPTH
# Examples:
#   PREFIX_DEPTH=1, INITIAL_PREFIXES=4   → ['a', 'b', 'c', 'd']
#   PREFIX_DEPTH=1, INITIAL_PREFIXES=26  → ['a' through 'z']
#   PREFIX_DEPTH=2, INITIAL_PREFIXES=10  → ['aa', 'ab', 'ac', ..., 'aj']
#   PREFIX_DEPTH=2, INITIAL_PREFIXES=676 → All 2-letter combos
INITIAL_PREFIXES = 676

# Or set custom prefixes directly (overrides above if not empty)
# Examples:
#   CUSTOM_PREFIXES = ['ma', 'me', 'pa']  # Specific patterns
#   CUSTOM_PREFIXES = ['aa', 'ab', 'ac']  # Start from 2-letter depth
#   CUSTOM_PREFIXES = []                  # Use PREFIX_DEPTH + INITIAL_PREFIXES
CUSTOM_PREFIXES = []

# Generate prefixes based on config
if CUSTOM_PREFIXES:
    PREFIXES = CUSTOM_PREFIXES
else:
    import string
    import itertools
    # Generate all combinations at PREFIX_DEPTH, take first INITIAL_PREFIXES
    all_combos = [''.join(combo) for combo in itertools.product(string.ascii_lowercase, repeat=PREFIX_DEPTH)]
    PREFIXES = all_combos[:INITIAL_PREFIXES]

# Enable smart prefix expansion
# When True: Automatically expands prefixes that hit pagination limit
# Example: If 'a' gets 100 results (10 pages), expands to 'aa', 'ab', ..., 'az'
SMART_EXPANSION = True  # Set to True for 100% coverage

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


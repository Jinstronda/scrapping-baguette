BOT_NAME = 'health_scraper'
SPIDER_MODULES = ['spiders']
NEWSPIDER_MODULE = 'spiders'

# Concurrency - Faster with better headers
CONCURRENT_REQUESTS = 3
CONCURRENT_REQUESTS_PER_DOMAIN = 3
DOWNLOAD_DELAY = 0.3
RANDOMIZE_DOWNLOAD_DELAY = True

# Auto-throttle
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.3
AUTOTHROTTLE_MAX_DELAY = 2.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 3.0

# Cookies
COOKIES_ENABLED = True
COOKIES_DEBUG = False

# Retry
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429, 403]

# User agent and headers
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'

# Default request headers - mimic real browser
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Cache-Control': 'max-age=0',
}

# Pipelines
ITEM_PIPELINES = {
    'pipelines.DataCleanerPipeline': 100,
    'pipelines.DatabasePipeline': 300,
}

# Database
DATABASE_PATH = 'db/scrapy_health_professionals.db'

# Logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '[%(asctime)s] %(levelname)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'

# Disable telnet console
TELNETCONSOLE_ENABLED = False

# Request fingerprinter
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'


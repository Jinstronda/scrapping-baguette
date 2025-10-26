NUM_THREADS = 4
REQUEST_TIMEOUT = 30
MIN_DELAY_SECONDS = 0.1
MAX_DELAY_SECONDS = 0.3
DB_PATH = "db/health_professionals.db"
RETRY_COUNT = 3
RETRY_DELAY = 2

BASE_URL = "https://annuaire.sante.fr"
SEARCH_URL = f"{BASE_URL}/web/site-pro/recherche/resultats"
INFO_URL = f"{BASE_URL}/web/site-pro/information-detaillees"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "X-PJAX": "true",
    "X-Requested-With": "XMLHttpRequest",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}


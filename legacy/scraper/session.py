import requests
import time
import random
from scraper.config import HEADERS, MIN_DELAY_SECONDS, MAX_DELAY_SECONDS, REQUEST_TIMEOUT

def create_session():
    session = requests.Session()
    session.headers.update(HEADERS)
    return session

def random_delay():
    time.sleep(random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS))

def get_with_retry(session, url, params=None, retries=1):
    for attempt in range(retries + 1):
        try:
            random_delay()
            response = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            return response
        except Exception as e:
            if attempt < retries:
                time.sleep(1)
            elif attempt == retries:
                raise
    return None

def post_with_retry(session, url, params=None, data=None, retries=1):
    for attempt in range(retries + 1):
        try:
            random_delay()
            response = session.post(url, params=params, data=data, timeout=REQUEST_TIMEOUT)
            return response
        except Exception as e:
            if attempt < retries:
                time.sleep(1)
            elif attempt == retries:
                raise
    return None


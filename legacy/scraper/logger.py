import logging
import threading
from datetime import datetime

def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='[T-%(thread)d] %(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

logger = setup_logger()

def log_prefix_start(prefix, page, cards):
    logger.info(f"prefix={prefix} page={page} cards={cards}")

def log_doctor_open(rpps, status):
    logger.info(f"rpps={rpps} open={status}")

def log_tab_fetch(rpps, tab, status):
    logger.info(f"rpps={rpps} tab={tab} status={status}")

def log_upsert(rpps):
    logger.info(f"rpps={rpps} upsert=ok")

def log_error(msg, url=None, status=None):
    if url and status:
        logger.error(f"{msg} url={url} status={status}")
    else:
        logger.error(msg)


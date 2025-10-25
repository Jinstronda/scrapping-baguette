import threading
import queue
import string
import random
from scraper.worker import process_prefix
from scraper.logger import logger

class WorkQueue:
    def __init__(self):
        self.queue = queue.Queue()
        self.lock = threading.Lock()
        self.seen_prefixes = set()
        
        prefixes = list(string.ascii_lowercase)
        random.shuffle(prefixes)
        
        for prefix in prefixes:
            self.queue.put(prefix)
            self.seen_prefixes.add(prefix)
    
    def get_next_prefix(self):
        try:
            return self.queue.get(timeout=1)
        except queue.Empty:
            return None
    
    def add_prefixes(self, prefixes):
        with self.lock:
            for prefix in prefixes:
                if prefix not in self.seen_prefixes:
                    self.queue.put(prefix)
                    self.seen_prefixes.add(prefix)
    
    def task_done(self):
        self.queue.task_done()
    
    def is_empty(self):
        return self.queue.empty()

def worker_thread(work_queue, db_path, thread_id):
    logger.info(f"Worker thread {thread_id} started")
    
    while True:
        prefix = work_queue.get_next_prefix()
        
        if prefix is None:
            if work_queue.is_empty():
                break
            continue
        
        try:
            logger.info(f"Thread {thread_id} processing prefix: {prefix}")
            sub_prefixes = process_prefix(prefix, db_path, work_queue.seen_prefixes)
            
            if sub_prefixes:
                work_queue.add_prefixes(sub_prefixes)
                logger.info(f"Thread {thread_id} added {len(sub_prefixes)} sub-prefixes for {prefix}")
                
        except Exception as e:
            logger.error(f"Thread {thread_id} error processing prefix {prefix}: {e}")
        finally:
            work_queue.task_done()
    
    logger.info(f"Worker thread {thread_id} finished")

def run_scraper(num_threads, db_path):
    work_queue = WorkQueue()
    threads = []
    
    logger.info(f"Starting scraper with {num_threads} threads")
    
    for i in range(num_threads):
        thread = threading.Thread(target=worker_thread, args=(work_queue, db_path, i))
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()
    
    logger.info("All threads completed")


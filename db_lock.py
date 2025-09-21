#!/usr/bin/env python3
"""
Simple database lock mechanism to prevent concurrent access
"""

import os
import time
import fcntl
from contextlib import contextmanager

@contextmanager
def db_lock():
    """Acquire a database lock to prevent concurrent access."""
    lock_file = "geoliga.db.lock"
    lock_fd = None
    
    try:
        # Create lock file
        lock_fd = os.open(lock_file, os.O_CREAT | os.O_WRONLY)
        
        # Try to acquire exclusive lock with timeout
        timeout = 30  # 30 seconds
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except IOError:
                time.sleep(0.1)
        else:
            raise Exception("Database lock timeout - another process is using the database")
        
        yield
        
    finally:
        if lock_fd is not None:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                os.close(lock_fd)
            except:
                pass
            
            # Remove lock file
            try:
                os.unlink(lock_file)
            except:
                pass

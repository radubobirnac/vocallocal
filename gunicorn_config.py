"""
Gunicorn configuration file for VocalLocal
"""
import os
import multiprocessing

# Worker settings
# For paid tier with more resources, we can use better settings
workers = 2  # Keep at 2 for stability
worker_class = 'gthread'  # Use gthread workers for concurrent processing
threads = 4  # Use 4 threads per worker for parallel processing
timeout = 600  # Increased timeout for processing large files (10 minutes)
graceful_timeout = 120  # Allow 2 minutes for graceful shutdown
keepalive = 5

# Server settings
bind = f"0.0.0.0:{os.environ.get('PORT', '5001')}"
worker_tmp_dir = '/tmp'

# Memory management
# Restart workers after processing a certain number of requests to prevent memory leaks
max_requests = 50  # Reduced to restart workers more frequently and free memory
max_requests_jitter = 25  # Add randomness to prevent all workers from restarting at once

# Worker memory management
# These settings help prevent memory issues with large files
worker_connections = 20  # Increased for better concurrency
# threads = 4  # Already set above

# Logging
accesslog = '-'  # Log to stdout
errorlog = '-'   # Log to stderr
loglevel = 'info'

# Limit the maximum request body size (in bytes)
# This helps prevent memory issues with large file uploads
# No limit on request body size - we handle this in the application
# We set MAX_CONTENT_LENGTH to 150MB in the Flask app
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# Preload the application to save memory across workers
preload_app = True

def post_fork(server, worker):
    """
    Called just after a worker has been forked.
    """
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    """
    Called just prior to forking the worker subprocess.
    """
    pass

def pre_exec(server):
    """
    Called just prior to forking off a secondary
    master process during things like config reloading.
    """
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    """
    Called just after the server is started.
    """
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    """
    Called just after a worker exited on SIGINT or SIGQUIT.
    """
    worker.log.info("worker received INT or QUIT signal")

def worker_abort(worker):
    """
    Called when a worker received the SIGABRT signal.
    """
    worker.log.info("worker received ABORT signal")

"""
Gunicorn configuration file for VocalLocal
"""
import os
import multiprocessing

# Worker settings
# For memory-constrained environments like Render's free tier,
# use fewer workers with a longer timeout
workers = 2  # Reduced from default to conserve memory
worker_class = 'sync'  # Use sync workers for better memory management
timeout = 300  # Increased timeout for processing large files (5 minutes)
keepalive = 5

# Server settings
bind = f"0.0.0.0:{os.environ.get('PORT', '5001')}"
worker_tmp_dir = '/tmp'
graceful_timeout = 120

# Memory management
# Restart workers after processing a certain number of requests to prevent memory leaks
max_requests = 100
max_requests_jitter = 50  # Add randomness to prevent all workers from restarting at once

# Logging
accesslog = '-'  # Log to stdout
errorlog = '-'   # Log to stderr
loglevel = 'info'

# Limit the maximum request body size (in bytes)
# This helps prevent memory issues with large file uploads
# 30MB limit (adjust as needed)
limit_request_line = 0
limit_request_fields = 100
limit_request_field_size = 0

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

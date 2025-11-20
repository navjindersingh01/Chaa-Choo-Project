#!/bin/bash
# Production Gunicorn configuration file
# Save as: gunicorn_config.py

import os
import multiprocessing

# Server socket
bind = "127.0.0.1:5000"
backlog = 2048

# Worker processes
workers = int(os.getenv('WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = os.getenv('WORKER_CLASS', 'sync')
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = int(os.getenv('WORKER_TIMEOUT', 60))
keepalive = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'chaa-choo'

# Server mechanics
daemon = False
pidfile = '/var/run/gunicorn.pid'
umask = 0
user = os.getenv('GUNICORN_USER', 'www-data')
group = os.getenv('GUNICORN_GROUP', 'www-data')
tmp_upload_dir = '/var/tmp'

# Application settings
forwarded_allow_ips = '127.0.0.1'
secure_scheme_headers = {
    'X-FORWARDED_PROTOCOL': 'ssl',
    'X-FORWARDED_PROTO': 'https',
    'X-FORWARDED_SSL': 'on',
}

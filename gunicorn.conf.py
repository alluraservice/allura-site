"""
Gunicorn settings for Render. Gunicorn reads this file automatically when it starts in this folder
(a copy sits in public_site/ too, in case the start command runs from there).

Before this file, the site ran with gunicorn's defaults: one worker that handles one request at a time.
While one visitor's form was being saved, every other request waited, which is why pages looked frozen
after Submit during the UAT (D-01). Threads let one worker serve several requests at once.
Change the numbers with the WEB_CONCURRENCY / GUNICORN_THREADS environment variables on Render.
"""
import os

workers = int(os.environ.get('WEB_CONCURRENCY', '1'))      # 1 fits the 512 MB plan; raise on a bigger plan
threads = int(os.environ.get('GUNICORN_THREADS', '8'))
timeout = 120               # seconds before a stuck request is stopped (default was 30)
graceful_timeout = 30
keepalive = 5

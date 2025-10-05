from main import app, run_scheduler
import threading

# This is the production entrypoint for the application.
# It starts the background monitoring thread and then the web server.

# 1. Start the background scheduler thread
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

# 2. The `app` object will be picked up by Gunicorn
# The Gunicorn command will be `gunicorn run:app`
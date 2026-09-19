"""
Samanvay-AI Standalone CDC Worker Service CLI.

Runs the real-time Change Data Capture worker process listening to PostgreSQL
and streaming row creations and updates to Neo4j.
"""

import sys
import os
import logging
import signal

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.services.cdc_manager import start_cdc_worker

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [Samanvay-CDC] %(message)s"
    )
    print("Starting Samanvay-AI Real-Time Change Data Capture (CDC) Worker...")
    try:
        start_cdc_worker()
    except KeyboardInterrupt:
        print("\nCDC Worker stopped by user.")
        sys.exit(0)

"""
Samanvay-AI Dataset Generation Script CLI Entrypoint.

Executes data generation pipelines and produces:
1. data/catalogs/inventory_catalog.csv (5,000 canonical rows)
2. data/benchmarks/golden_benchmarks.json (150 paired test cases)
3. data/benchmarks/ocr_payloads.json (500 MTC payloads)
"""

import os
import sys

# Add repository root to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.generators.generate_datasets import main

if __name__ == "__main__":
    main()

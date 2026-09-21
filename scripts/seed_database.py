"""
Samanvay-AI Database & Vector Store Seeder.

Seeds PostgreSQL with 5,000 catalog inventory lines from datasets/inventory_catalog.csv,
populates initial Sovereign Audit Ledger entries with cryptographic SHA-256 seals,
and indexes vectors into Qdrant.
"""

import os
import sys
import hashlib
import json
from datetime import datetime, timezone
import pandas as pd

# Add repository root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings
from backend.app.models.base import engine, SessionLocal, init_db
from backend.app.models.tables import InventoryItem, SovereignAuditLedger
from ml.ner.normalizer import DialectNormalizer
from ml.embeddings.vector_encoder import VectorEncoder
from ml.embeddings.qdrant_client import SamanvayQdrantClient


def derive_depot_id(cpse: str, location: str) -> str:
    loc_clean = location.split(",")[0].strip().replace(" ", "_").upper()
    return f"{cpse}_{loc_clean}"


def seed_database():
    print("[INIT] Initializing database tables...")
    init_db()

    csv_path = os.path.join(os.path.dirname(__file__), "..", "datasets", "inventory_catalog.csv")
    if not os.path.exists(csv_path):
        print(f"[ERROR] Catalog file not found at {csv_path}")
        return

    print(f"[READ] Reading catalog from {csv_path}...")
    df = pd.read_csv(csv_path)
    total_rows = len(df)
    print(f"Loaded {total_rows} catalog rows.")

    db = SessionLocal()
    normalizer = DialectNormalizer()

    force_reload = "--force" in sys.argv or "-f" in sys.argv
    try:
        existing_count = db.query(InventoryItem).count()
        if existing_count > 0 and not force_reload:
            print(f"[INFO] Inventory table already contains {existing_count} items. Use --force to reload. Skipping insert.")
        else:
            if existing_count > 0 and force_reload:
                print(f"[FORCE] Truncating {existing_count} existing inventory records for clean authentic re-seed...")
                db.query(InventoryItem).delete()
                db.commit()

            print(f"[SEED] Inserting {total_rows} items into PostgreSQL...")
            items_to_add = []
            
            for idx, row in df.iterrows():
                sku = str(row["sku_code"]).strip()
                cpse = str(row["cpse_name"]).strip().upper()
                location = str(row["depot_location"]).strip()
                desc = str(row["raw_description"]).strip()
                qty = int(row["quantity"])
                unit_cost = float(row["unit_cost_inr"])
                days_idle = int(row["days_idle"])
                depot_id = derive_depot_id(cpse, location)

                # Dialect normalization & metadata extraction
                meta = normalizer.normalize(desc)
                item_type = meta.get("item_type") or "EQUIPMENT"
                size_nb_mm = meta.get("size_nb_mm")
                pressure_class = meta.get("pressure_class")
                metallurgy = str(meta.get("metallurgy") or "")[:60] if meta.get("metallurgy") else None
                facing_end = str(meta.get("facing_end") or "")[:30] if meta.get("facing_end") else None
                item_type = str(item_type)[:60]

                # Enriched procurement fields
                po_no = str(row["po_no"]).strip() if "po_no" in row and pd.notna(row["po_no"]) else None
                heat_no = str(row["heat_no"]).strip() if "heat_no" in row and pd.notna(row["heat_no"]) else None
                standard = str(row["standard"]).strip() if "standard" in row and pd.notna(row["standard"]) else None
                
                for field in ["hsn_code", "gem_category", "mesc_code", "cppp_tender_id"]:
                    if field in row and pd.notna(row[field]):
                        meta[field] = str(row[field]).strip()

                # Determine surplus status
                if days_idle >= 365:
                    status = "SURPLUS_DECLARED"
                    broadcast = True
                elif days_idle >= 180:
                    status = "POTENTIAL_SURPLUS"
                    broadcast = True
                else:
                    status = "TO_BE_CONSUMED"
                    broadcast = False

                item = InventoryItem(
                    sku_code=sku,
                    cpse=cpse,
                    depot_id=depot_id,
                    depot_location=location,
                    po_no=po_no,
                    heat_no=heat_no,
                    description=desc,
                    item_type=item_type,
                    size_nb_mm=size_nb_mm,
                    pressure_class=pressure_class,
                    metallurgy=metallurgy,
                    facing_end=facing_end,
                    standard=standard,
                    quantity=qty,
                    unit_cost_inr=unit_cost,
                    status=status,
                    days_idle=days_idle,
                    is_broadcasted_surplus=broadcast,
                    properties=meta,
                )
                items_to_add.append(item)

                if len(items_to_add) >= 500:
                    db.bulk_save_objects(items_to_add)
                    db.commit()
                    items_to_add = []
                    print(f"  Processed {idx + 1}/{total_rows} items...")

            if items_to_add:
                db.bulk_save_objects(items_to_add)
                db.commit()
                print(f"  Processed {total_rows}/{total_rows} items.")

            print(f"[SUCCESS] Successfully seeded {total_rows} inventory items into PostgreSQL!")

        # ── Seed Genesis Audit Ledger ──────────────────────────────────────────
        audit_count = db.query(SovereignAuditLedger).count()
        if audit_count == 0:
            print("[AUDIT] Initializing Sovereign Cryptographic Audit Ledger...")
            from backend.app.services.audit_service import create_audit_entry

            create_audit_entry(
                db,
                {
                    "log_id": "LOG-GENESIS-00001",
                    "actor_name": "SYSTEM_ARCHITECT",
                    "actor_role": "ADMIN",
                    "action_category": "GOVERNANCE",
                    "action_name": "SYSTEM_INITIALIZATION",
                    "cpse": "MOPNG",
                    "depot": "CENTRAL_REGISTRY",
                    "reference_id": "GENESIS-001",
                    "payload": {
                        "event": "GENESIS_INITIALIZATION",
                        "authority": "MoPNG_BHARATCODEX",
                        "description": "Samanvay-AI Sovereign Air-Gapped Master Ledger Initialized",
                    },
                }
            )

            create_audit_entry(
                db,
                {
                    "log_id": "LOG-IMPORT-00002",
                    "actor_name": "CENTRAL_OFFICER",
                    "actor_role": "INVENTORY_MANAGER",
                    "action_category": "INGESTION",
                    "action_name": "CATALOG_BATCH_IMPORT",
                    "cpse": "MOPNG",
                    "depot": "ALL_DEPOTS",
                    "reference_id": "CATALOG-5000",
                    "payload": {
                        "source_file": "inventory_catalog.csv",
                        "total_records": total_rows,
                        "description": "Initial 5,000 spare parts catalog batch imported",
                    },
                }
            )
            print("[AUDIT] Genesis audit trail sealed with SHA-256 digital blocks.")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Database seeding error: {e}")
        raise
    finally:
        db.close()

    # ── Populate Qdrant Vector Index ──────────────────────────────────────────
    try:
        print("[VECTOR] Populating Qdrant dense vector embeddings (sample batch)...")
        qdrant = SamanvayQdrantClient()
        encoder = VectorEncoder()
        
        sample_df = df.head(100)  # Seed top 100 into Qdrant for immediate search
        batch = []
        for _, row in sample_df.iterrows():
            desc = str(row["raw_description"])
            sku = str(row["sku_code"])
            cpse = str(row["cpse_name"])
            vec = encoder.encode(desc)
            batch.append({
                "sku_code": sku,
                "vector": vec,
                "item_type": str(row.get("item_type", "EQUIPMENT")),
                "payload": {
                    "sku_code": sku,
                    "cpse": cpse,
                    "description": desc,
                }
            })
        qdrant.upsert_items(batch)
        print("[VECTOR] Qdrant vector index seeded successfully with 100 embeddings!")
    except Exception as e:
        print(f"[NOTICE] Qdrant seeding notice: {e}")


if __name__ == "__main__":
    seed_database()

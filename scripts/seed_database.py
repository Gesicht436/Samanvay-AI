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


from sqlalchemy import text


def seed_database():
    print("[INIT] Initializing database tables...")
    init_db()

    # Ensure schema migrations for Indian procurement columns
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE inventory_items ADD COLUMN IF NOT EXISTS indian_standard VARCHAR(100);
            ALTER TABLE inventory_items ADD COLUMN IF NOT EXISTS oil_std_spec VARCHAR(100);
            ALTER TABLE inventory_items ADD COLUMN IF NOT EXISTS oil_material_code VARCHAR(32);
            ALTER TABLE inventory_items ADD COLUMN IF NOT EXISTS gem_category_id VARCHAR(100);
            ALTER TABLE inventory_items ADD COLUMN IF NOT EXISTS gem_product_id VARCHAR(64);
            ALTER TABLE inventory_items ADD COLUMN IF NOT EXISTS cppp_tender_ref VARCHAR(100);
            ALTER TABLE inventory_items ADD COLUMN IF NOT EXISTS make_in_india_class VARCHAR(32) DEFAULT 'Class-I';
            ALTER TABLE inventory_items ADD COLUMN IF NOT EXISTS local_content_percentage NUMERIC(5, 2) DEFAULT 75.0;
            ALTER TABLE inventory_items ADD COLUMN IF NOT EXISTS pressure_rating_bar NUMERIC(8, 2);
            ALTER TABLE inventory_items ADD COLUMN IF NOT EXISTS location_state VARCHAR(64);
        """))
        conn.commit()

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
                indian_standard = str(row["indian_standard"]).strip() if "indian_standard" in row and pd.notna(row["indian_standard"]) else meta.get("indian_standard")
                oil_std_spec = str(row["oil_std_spec"]).strip() if "oil_std_spec" in row and pd.notna(row["oil_std_spec"]) else meta.get("oil_std_spec")
                oil_material_code = str(row["oil_material_code"]).strip() if "oil_material_code" in row and pd.notna(row["oil_material_code"]) else meta.get("oil_material_code")
                gem_category_id = str(row["gem_category_id"]).strip() if "gem_category_id" in row and pd.notna(row["gem_category_id"]) else meta.get("gem_category_id")
                gem_product_id = str(row["gem_product_id"]).strip() if "gem_product_id" in row and pd.notna(row["gem_product_id"]) else None
                cppp_tender_ref = str(row["cppp_tender_ref"]).strip() if "cppp_tender_ref" in row and pd.notna(row["cppp_tender_ref"]) else meta.get("cppp_tender_ref")
                make_in_india_class = str(row["make_in_india_class"]).strip() if "make_in_india_class" in row and pd.notna(row["make_in_india_class"]) else (meta.get("make_in_india_class") or "Class-I")
                local_content_percentage = float(row["local_content_percentage"]) if "local_content_percentage" in row and pd.notna(row["local_content_percentage"]) else 75.0
                pressure_rating_bar = float(row["pressure_rating_bar"]) if "pressure_rating_bar" in row and pd.notna(row["pressure_rating_bar"]) else meta.get("pressure_rating_bar")
                location_state = str(row["location_state"]).strip() if "location_state" in row and pd.notna(row["location_state"]) else None
                
                for field in ["hsn_code", "gem_category", "mesc_code", "cppp_tender_id", "indian_standard", "oil_std_spec", "oil_material_code", "gem_category_id", "cppp_tender_ref", "make_in_india_class"]:
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
                    indian_standard=indian_standard,
                    oil_std_spec=oil_std_spec,
                    oil_material_code=oil_material_code,
                    gem_category_id=gem_category_id,
                    gem_product_id=gem_product_id,
                    cppp_tender_ref=cppp_tender_ref,
                    make_in_india_class=make_in_india_class,
                    local_content_percentage=local_content_percentage,
                    pressure_rating_bar=pressure_rating_bar,
                    location_state=location_state,
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

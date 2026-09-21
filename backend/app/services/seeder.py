"""
Samanvay-AI Automatic Data Seeder Service.

Automatically populates the database and vector engine on startup if empty,
ensuring zero manual intervention is required on fresh volume deployments.
"""

import os
import sys
import logging
import pandas as pd

from backend.app.models.base import SessionLocal, init_db
from backend.app.models.tables import InventoryItem, SovereignAuditLedger
from ml.ner.normalizer import DialectNormalizer

logger = logging.getLogger("samanvay.seeder")


def derive_depot_id(cpse: str, location: str) -> str:
    loc_clean = location.split(",")[0].strip().replace(" ", "_").upper()
    return f"{cpse}_{loc_clean}"


def seed_database_if_empty():
    """
    Checks if PostgreSQL inventory table has records; if empty, loads the 5,000 catalog records.
    """
    init_db()

    db = SessionLocal()
    try:
        count = db.query(InventoryItem).count()
        if count > 0:
            logger.info(f"Inventory table already initialized with {count} items. Skipping auto-seed.")
            return

        csv_candidates = [
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "datasets", "inventory_catalog.csv"),
            "/app/datasets/inventory_catalog.csv",
            "datasets/inventory_catalog.csv",
        ]

        catalog_csv = None
        for path in csv_candidates:
            if os.path.exists(path):
                catalog_csv = path
                break

        if not catalog_csv:
            logger.warning("Auto-seeder: datasets/inventory_catalog.csv not found in search paths.")
            return

        logger.info(f"Auto-seeding 5,000 inventory items from {catalog_csv}...")
        df = pd.read_csv(catalog_csv)
        total_rows = len(df)

        normalizer = DialectNormalizer()
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

            meta = normalizer.normalize(desc)
            item_type = str(meta.get("item_type") or "EQUIPMENT")[:60]
            size_nb_mm = meta.get("size_nb_mm")
            pressure_class = meta.get("pressure_class")
            metallurgy = str(meta.get("metallurgy") or "")[:60] if meta.get("metallurgy") else None
            facing_end = str(meta.get("facing_end") or "")[:30] if meta.get("facing_end") else None

            po_no = str(row["po_no"]).strip() if "po_no" in row and pd.notna(row["po_no"]) else None
            heat_no = str(row["heat_no"]).strip() if "heat_no" in row and pd.notna(row["heat_no"]) else None
            standard = str(row["standard"]).strip() if "standard" in row and pd.notna(row["standard"]) else None

            for field in ["hsn_code", "gem_category", "mesc_code", "cppp_tender_id"]:
                if field in row and pd.notna(row[field]):
                    meta[field] = str(row[field]).strip()

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

        if items_to_add:
            db.bulk_save_objects(items_to_add)
            db.commit()

        logger.info(f"Successfully seeded {total_rows} items into PostgreSQL.")

        # Seed Genesis Audit Entries if missing
        if db.query(SovereignAuditLedger).count() == 0:
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
            logger.info("Genesis SHA-256 Sovereign Audit Trail entry sealed.")

    except Exception as e:
        db.rollback()
        logger.error(f"Error during auto-seed: {e}")
    finally:
        db.close()

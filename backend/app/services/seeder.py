"""
Samanvay-AI Automatic Data Seeder Service.

Automatically populates the database and vector engine on startup if empty,
ensuring zero manual intervention is required on fresh volume deployments.
"""

import os
import sys
import logging
import pandas as pd

from backend.app.contracts.canonical_schema import normalize_catalog_row
from backend.app.models.base import SessionLocal, init_db
from backend.app.models.tables import InventoryItem, SovereignAuditLedger
from machine_learning.ner_tagger import DialectNormalizer

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
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "catalogs", "inventory_catalog.csv"),
            "/app/data/catalogs/inventory_catalog.csv",
            "data/catalogs/inventory_catalog.csv",
        ]

        catalog_csv = None
        for path in csv_candidates:
            if os.path.exists(path):
                catalog_csv = path
                break

        if not catalog_csv:
            logger.warning("Auto-seeder: data/catalogs/inventory_catalog.csv not found in search paths.")
            return

        logger.info(f"Auto-seeding 5,000 inventory items from {catalog_csv}...")
        df = pd.read_csv(catalog_csv)
        total_rows = len(df)

        normalizer = DialectNormalizer()
        items_to_add = []

        for idx, row in df.iterrows():
            norm = normalize_catalog_row(row.to_dict())
            sku = str(norm["sku_code"]).strip()
            cpse = str(norm["cpse"]).strip().upper()
            location = str(norm["depot_location"]).strip()
            desc = str(norm["description"]).strip()
            qty = int(norm["quantity"])
            unit_cost = float(norm["unit_cost_inr"])
            days_idle = int(norm.get("days_idle", 0) or 0)
            depot_id = norm.get("depot_id") or derive_depot_id(cpse, location)

            meta = normalizer.normalize(desc)
            item_type = str(norm.get("item_type") or meta.get("item_type") or "EQUIPMENT")[:60]
            size_nb_mm = norm.get("size_nb_mm") or meta.get("size_nb_mm")
            pressure_class = norm.get("pressure_class") or meta.get("pressure_class")
            metallurgy = str(norm.get("metallurgy") or meta.get("metallurgy") or "")[:60] if (norm.get("metallurgy") or meta.get("metallurgy")) else None
            facing_end = str(norm.get("facing_end") or meta.get("facing_end") or "")[:30] if (norm.get("facing_end") or meta.get("facing_end")) else None

            po_no = str(norm["po_no"]).strip() if norm.get("po_no") and pd.notna(norm["po_no"]) else None
            heat_no = str(norm["heat_no"]).strip() if norm.get("heat_no") and pd.notna(norm["heat_no"]) else None
            standard = str(norm["standard"]).strip() if norm.get("standard") and pd.notna(norm["standard"]) else None
            canonical_id = str(norm["canonical_id"]).strip() if norm.get("canonical_id") and pd.notna(norm["canonical_id"]) else None

            indian_standard = str(norm["indian_standard"]).strip() if norm.get("indian_standard") and pd.notna(norm["indian_standard"]) else meta.get("indian_standard")
            oil_std_spec = str(norm["oil_std_spec"]).strip() if norm.get("oil_std_spec") and pd.notna(norm["oil_std_spec"]) else meta.get("oil_std_spec")
            oil_material_code = str(norm["oil_material_code"]).strip() if norm.get("oil_material_code") and pd.notna(norm["oil_material_code"]) else meta.get("oil_material_code")
            gem_category_id = str(norm["gem_category_id"]).strip() if norm.get("gem_category_id") and pd.notna(norm["gem_category_id"]) else meta.get("gem_category_id")
            gem_product_id = str(norm["gem_product_id"]).strip() if norm.get("gem_product_id") and pd.notna(norm["gem_product_id"]) else None
            cppp_tender_ref = str(norm["cppp_tender_ref"]).strip() if norm.get("cppp_tender_ref") and pd.notna(norm["cppp_tender_ref"]) else meta.get("cppp_tender_ref")
            make_in_india_class = str(norm.get("make_in_india_class") or "Class-I")[:30]
            local_content_percentage = float(norm.get("local_content_percentage") or 75.0)
            pressure_rating_bar = float(norm["pressure_rating_bar"]) if norm.get("pressure_rating_bar") and pd.notna(norm["pressure_rating_bar"]) else None
            location_state = str(norm["location_state"]).strip() if norm.get("location_state") and pd.notna(norm["location_state"]) else None

            props = dict(norm.get("properties", {}))
            props.update(meta)

            status = norm.get("status", "TO_BE_CONSUMED")
            broadcast = bool(norm.get("is_broadcasted_surplus", False))

            item = InventoryItem(
                sku_code=sku,
                canonical_id=canonical_id,
                cpse=cpse,
                depot_id=depot_id,
                depot_location=location,
                po_no=po_no,
                heat_no=heat_no,
                description=desc,
                item_type=item_type,
                size_nb_mm=size_nb_mm,
                pressure_class=pressure_class,
                pressure_rating_bar=pressure_rating_bar,
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
                location_state=location_state,
                quantity=qty,
                unit_cost_inr=unit_cost,
                status=status,
                days_idle=days_idle,
                is_broadcasted_surplus=broadcast,
                properties=props,
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

        # Seed Default Persona Users
        seed_users_if_empty(db)

    except Exception as e:
        db.rollback()
        logger.error(f"Error during auto-seed: {e}")
    finally:
        db.close()


def seed_users_if_empty(db=None):
    """
    Ensures all 25 default seed persona accounts across 7 CPSEs exist in the PostgreSQL users table.

    Purely additive: only missing personas are created. An existing seed account
    is never reactivated, reapproved, re-roled or re-hashed, so seed data is not
    treated as the authority for current administrative account state
    (AUTH-005 Section "Seed/deployment interaction"; frozen invariant that startup
    seeding must not silently undo administrative account-state changes).

    Development/test only. AUTH-006 forbids exposing seed credentials in production;
    startup seeding does not run in a production deployment.
    """
    from backend.app.core.config import settings
    from backend.app.models.tables import User
    from backend.app.core.security import get_password_hash
    from backend.app.schemas.auth import SEED_USERS, DEFAULT_SEED_PASSWORD

    if settings.is_production:
        logger.info("Seed user provisioning skipped: production deployment.")
        return

    close_db = False
    if db is None:
        init_db()
        db = SessionLocal()
        close_db = True

    try:
        hashed = get_password_hash(DEFAULT_SEED_PASSWORD)
        created_count = 0
        for seed_info in SEED_USERS:
            existing = db.query(User).filter(
                (User.username == seed_info.username) | (User.email == seed_info.email)
            ).first()
            if existing:
                # Existing account state is authoritative: never reactivate,
                # reapprove, re-role or re-hash an existing account.
                continue
            user = User(
                username=seed_info.username,
                email=seed_info.email,
                hashed_password=hashed,
                full_name=seed_info.full_name,
                role=seed_info.role,
                cpse=seed_info.cpse,
                depot_id=seed_info.depot_id,
                is_active=True,
                is_approved=True,
            )
            db.add(user)
            try:
                db.commit()
                created_count += 1
            except Exception as inner_e:
                db.rollback()
                logger.warning(f"Skipping seed user {seed_info.username}: {inner_e}")
        logger.info(f"Seed users status: {created_count} created, existing accounts left unchanged.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding default users: {e}")
    finally:
        if close_db:
            db.close()

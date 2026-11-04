"""
Pydantic schemas and models for authentication and Role-Based Access Control (RBAC).
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRole(str, Enum):
    SITE_ENGINEER = "SITE_ENGINEER"
    MATERIALS_MANAGER = "MATERIALS_MANAGER"
    TECHNICAL_AUTHORITY = "TECHNICAL_AUTHORITY"
    CISF_SECURITY = "CISF_SECURITY"
    VIGILANCE_AUDITOR = "VIGILANCE_AUDITOR"
    SUPER_ADMIN = "SUPER_ADMIN"


class UserLogin(BaseModel):
    username: str = Field(..., description="Username or CPSE email identifier")
    password: str = Field(..., description="Plain-text password")


class UserProvisionRequest(BaseModel):
    """SUPER_ADMIN account provisioning payload (AUTH-006 Account Provisioning).

    The role/CPSE/depot are assigned through the authorized server-side
    operation; client-supplied values never establish authorization.
    No session is created for a provisioned account until it is approved.
    """

    username: str = Field(..., min_length=3, max_length=50, description="Unique username identifier")
    password: str = Field(..., min_length=8, description="Plain-text password")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of personnel")
    email: EmailStr = Field(..., description="Official CPSE email address")
    role: UserRole = Field(..., description="Assigned sovereign functional role")
    cpse: str = Field(..., description="CPSE organization code (OIL, IOCL, ONGC, BPCL, HPCL, GAIL, NRL)")
    depot_id: str = Field(..., description="Assigned depot code (e.g. DEPOT-OIL-DLJ)")


class CsrfTokenResponse(BaseModel):
    """Session-bound CSRF token response (AUTH-006 Section 4). Never persisted."""

    csrf_token: str



class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    email: Optional[str] = None
    role: str
    cpse: str
    depot_id: str
    is_active: bool
    is_approved: bool

    model_config = ConfigDict(from_attributes=True)


class SeedUserInfo(BaseModel):
    username: str
    full_name: str
    role: str
    cpse: str
    depot_id: str
    email: str
    description: str


# Canonical list of seed test accounts for one-click testing and demonstration
SEED_USERS = [
    # ── OIL (Oil India Limited - Duliajan) ──────────────────────────────────
    SeedUserInfo(
        username="engineer_oil",
        full_name="Er. Arindam Phukan",
        role="SITE_ENGINEER",
        cpse="OIL",
        depot_id="DEPOT-OIL-DLJ",
        email="arindam.phukan@oilindia.in",
        description="Site Maintenance & Reliability Engineer (Oil India Duliajan)",
    ),
    SeedUserInfo(
        username="stores_oil",
        full_name="Debojit Barua",
        role="MATERIALS_MANAGER",
        cpse="OIL",
        depot_id="DEPOT-OIL-DLJ",
        email="debojit.barua@oilindia.in",
        description="Stores Superintendent & Inventory Manager (Oil India Duliajan)",
    ),
    SeedUserInfo(
        username="cisf_oil",
        full_name="Inspector K. S. Rathore",
        role="CISF_SECURITY",
        cpse="OIL",
        depot_id="DEPOT-OIL-DLJ",
        email="ks.rathore@cisf.gov.in",
        description="CISF Perimeter Security Inspector (Oil India Duliajan Gate)",
    ),

    # ── IOCL (Indian Oil Corporation Limited - Panipat Refinery) ────────────
    SeedUserInfo(
        username="engineer_iocl",
        full_name="Er. Rajesh Sharma",
        role="SITE_ENGINEER",
        cpse="IOCL",
        depot_id="DEPOT-IOCL-PNP",
        email="rajesh.sharma@indianoil.in",
        description="Plant Piping & Mechanical Engineer (IOCL Panipat Refinery)",
    ),
    SeedUserInfo(
        username="stores_iocl",
        full_name="Vikramaditya Rao",
        role="MATERIALS_MANAGER",
        cpse="IOCL",
        depot_id="DEPOT-IOCL-PNP",
        email="vikram.rao@indianoil.in",
        description="Warehouse Depot In-Charge (IOCL Panipat Refinery)",
    ),
    SeedUserInfo(
        username="cisf_iocl",
        full_name="Inspector Devendra Malik",
        role="CISF_SECURITY",
        cpse="IOCL",
        depot_id="DEPOT-IOCL-PNP",
        email="d.malik@cisf.gov.in",
        description="CISF Gate Pass Verification Officer (IOCL Panipat Gate)",
    ),

    # ── ONGC (Oil & Natural Gas Corporation - Uran Gas Plant) ───────────────
    SeedUserInfo(
        username="engineer_ongc",
        full_name="Er. Pradeep Kulkarni",
        role="SITE_ENGINEER",
        cpse="ONGC",
        depot_id="DEPOT-ONGC-URN",
        email="pradeep.kulkarni@ongc.co.in",
        description="Offshore & Processing Engineer (ONGC Uran Gas Processing)",
    ),
    SeedUserInfo(
        username="stores_ongc",
        full_name="Mahesh Tendulkar",
        role="MATERIALS_MANAGER",
        cpse="ONGC",
        depot_id="DEPOT-ONGC-URN",
        email="mahesh.tendulkar@ongc.co.in",
        description="Central Stores Officer (ONGC Uran Terminal)",
    ),
    SeedUserInfo(
        username="cisf_ongc",
        full_name="Inspector S. P. Gaikwad",
        role="CISF_SECURITY",
        cpse="ONGC",
        depot_id="DEPOT-ONGC-URN",
        email="sp.gaikwad@cisf.gov.in",
        description="CISF Security Unit Commander (ONGC Uran Facility)",
    ),

    # ── GAIL (GAIL India Limited - Pata Petrochemical) ──────────────────────
    SeedUserInfo(
        username="engineer_gail",
        full_name="Er. Alok Srivastava",
        role="SITE_ENGINEER",
        cpse="GAIL",
        depot_id="DEPOT-GAIL-PAT",
        email="alok.srivastava@gail.co.in",
        description="Pipeline & Gas Grid Engineer (GAIL Pata Complex)",
    ),
    SeedUserInfo(
        username="stores_gail",
        full_name="Rameshwar Dixit",
        role="MATERIALS_MANAGER",
        cpse="GAIL",
        depot_id="DEPOT-GAIL-PAT",
        email="rameshwar.dixit@gail.co.in",
        description="Depot Materials Superintendent (GAIL Pata Stores)",
    ),
    SeedUserInfo(
        username="cisf_gail",
        full_name="Inspector Harish Tewari",
        role="CISF_SECURITY",
        cpse="GAIL",
        depot_id="DEPOT-GAIL-PAT",
        email="h.tewari@cisf.gov.in",
        description="CISF Out-Gate Dispatch Inspector (GAIL Pata)",
    ),

    # ── BPCL (Bharat Petroleum - Mumbai Mahul Refinery) ─────────────────────
    SeedUserInfo(
        username="engineer_bpcl",
        full_name="Er. Nitin Sawant",
        role="SITE_ENGINEER",
        cpse="BPCL",
        depot_id="DEPOT-BPCL-MUM",
        email="nitin.sawant@bharatpetroleum.in",
        description="Refinery Turnaround Maintenance Engineer (BPCL Mahul)",
    ),
    SeedUserInfo(
        username="stores_bpcl",
        full_name="Sanjay Deshmukh",
        role="MATERIALS_MANAGER",
        cpse="BPCL",
        depot_id="DEPOT-BPCL-MUM",
        email="sanjay.deshmukh@bharatpetroleum.in",
        description="Senior Materials Executive (BPCL Mumbai Refinery)",
    ),
    SeedUserInfo(
        username="cisf_bpcl",
        full_name="Inspector V. B. Jadhav",
        role="CISF_SECURITY",
        cpse="BPCL",
        depot_id="DEPOT-BPCL-MUM",
        email="vb.jadhav@cisf.gov.in",
        description="CISF In-Gate Security Inspector (BPCL Mumbai Refinery)",
    ),

    # ── HPCL (Hindustan Petroleum - Visakh Refinery) ────────────────────────
    SeedUserInfo(
        username="engineer_hpcl",
        full_name="Er. K. V. Ramana",
        role="SITE_ENGINEER",
        cpse="HPCL",
        depot_id="DEPOT-HPCL-VSK",
        email="kv.ramana@hpcl.in",
        description="Process Plant Equipment Specialist (HPCL Visakh Refinery)",
    ),
    SeedUserInfo(
        username="stores_hpcl",
        full_name="B. Satyanarayana",
        role="MATERIALS_MANAGER",
        cpse="HPCL",
        depot_id="DEPOT-HPCL-VSK",
        email="b.satya@hpcl.in",
        description="Depot Stock Ledger In-Charge (HPCL Visakh Stores)",
    ),
    SeedUserInfo(
        username="cisf_hpcl",
        full_name="Inspector Ch. Appa Rao",
        role="CISF_SECURITY",
        cpse="HPCL",
        depot_id="DEPOT-HPCL-VSK",
        email="ch.apparao@cisf.gov.in",
        description="CISF Digital Gate Pass Officer (HPCL Visakh Terminal)",
    ),

    # ── NRL (Numaligarh Refinery Limited - Assam) ───────────────────────────
    SeedUserInfo(
        username="engineer_nrl",
        full_name="Er. Bhaskar Gogoi",
        role="SITE_ENGINEER",
        cpse="NRL",
        depot_id="DEPOT-NRL-NUM",
        email="bhaskar.gogoi@nrl.co.in",
        description="Expansion Project Piping Lead (Numaligarh Refinery)",
    ),
    SeedUserInfo(
        username="stores_nrl",
        full_name="Monojit Saikia",
        role="MATERIALS_MANAGER",
        cpse="NRL",
        depot_id="DEPOT-NRL-NUM",
        email="monojit.saikia@nrl.co.in",
        description="Warehouse & Inventory Controller (NRL Numaligarh)",
    ),
    SeedUserInfo(
        username="cisf_nrl",
        full_name="Inspector T. K. Bora",
        role="CISF_SECURITY",
        cpse="NRL",
        depot_id="DEPOT-NRL-NUM",
        email="tk.bora@cisf.gov.in",
        description="CISF Security Gate Pass Inspector (NRL Main Gate)",
    ),

    # ── Sovereign Central Oversight (MoPNG) ─────────────────────────────────
    SeedUserInfo(
        username="tech_authority",
        full_name="Dr. Ananya Sen",
        role="TECHNICAL_AUTHORITY",
        cpse="OIL",
        depot_id="DEPOT-OIL-DLJ",
        email="ananya.sen@oilindia.in",
        description="Chief Metallurgist & QA-QC Technical Authority (HITL Triage)",
    ),
    SeedUserInfo(
        username="cisf_officer",
        full_name="Inspector K. S. Rathore",
        role="CISF_SECURITY",
        cpse="OIL",
        depot_id="DEPOT-OIL-DLJ",
        email="cisf.officer@cisf.gov.in",
        description="CISF Perimeter Security Inspector (Legacy Alias)",
    ),
    SeedUserInfo(
        username="auditor",
        full_name="Sunil K. Verma",
        role="VIGILANCE_AUDITOR",
        cpse="MoPNG",
        depot_id="CENTRAL",
        email="sunil.verma@mopng.gov.in",
        description="Chief Vigilance Officer & CAG Statutory Auditor (SHA-256 Ledger)",
    ),
    SeedUserInfo(
        username="admin",
        full_name="Samanvay Administrator",
        role="SUPER_ADMIN",
        cpse="MoPNG",
        depot_id="CENTRAL",
        email="admin@samanvay.nic.in",
        description="Sovereign Ministry System Administrator",
    ),
]

DEFAULT_SEED_PASSWORD = "Samanvay@2026"

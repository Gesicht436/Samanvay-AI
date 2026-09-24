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


class UserSignup(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username identifier")
    password: str = Field(..., min_length=6, description="Plain-text password")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of personnel")
    email: EmailStr = Field(..., description="Official CPSE email address")
    role: UserRole = Field(..., description="Assigned sovereign functional role")
    cpse: str = Field(..., description="CPSE organization code (OIL, IOCL, ONGC, BPCL, HPCL, GAIL, NRL)")
    depot_id: str = Field(..., description="Assigned depot code (e.g. DEPOT-OIL-DLJ)")



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


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    sub: str  # username
    role: str
    cpse: str
    depot_id: str
    exp: Optional[int] = None


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
        email="ks.rathore@cisf.gov.in",
        description="CISF Perimeter Security Inspector (Digital Gate Pass Stamping)",
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

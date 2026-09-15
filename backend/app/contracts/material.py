"""
Pydantic v2 Contracts for Samanvay-AI Material Standardization.
Defines extracted physical attributes, item types, facing ends, and canonical master representations.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ItemType(str, Enum):
    FLANGE_WELD_NECK = "FLANGE_WELD_NECK"
    FLANGE_BLIND = "FLANGE_BLIND"
    FLANGE_SLIP_ON = "FLANGE_SLIP_ON"
    GATE_VALVE = "GATE_VALVE"
    BALL_VALVE = "BALL_VALVE"
    GLOBE_VALVE = "GLOBE_VALVE"
    CHECK_VALVE = "CHECK_VALVE"
    PIPE_SEAMLESS = "PIPE_SEAMLESS"
    SPIRAL_WOUND_GASKET = "SPIRAL_WOUND_GASKET"
    STUD_BOLT = "STUD_BOLT"
    PUMP_CENTRIFUGAL = "PUMP_CENTRIFUGAL"
    MECHANICAL_SEAL = "MECHANICAL_SEAL"
    BEARING_ROLLER = "BEARING_ROLLER"
    MOTOR_FLAMEPROOF = "MOTOR_FLAMEPROOF"
    CABLE_ARMOURED = "CABLE_ARMOURED"
    ELBOW_BUTTWELD = "ELBOW_BUTTWELD"
    ACTUATOR_PNEUMATIC = "ACTUATOR_PNEUMATIC"
    FERRULE_FITTING = "FERRULE_FITTING"
    BUTTERFLY_VALVE = "BUTTERFLY_VALVE"
    PLUG_VALVE = "PLUG_VALVE"


class FacingEnd(str, Enum):
    RF = "RF"        # Raised Face
    RTJ = "RTJ"      # Ring Type Joint
    FF = "FF"        # Flat Face
    BW = "BW"        # Butt Weld
    SW = "SW"        # Socket Weld
    THRD = "THRD"    # Threaded


class ExtractedMaterialAttributes(BaseModel):
    """
    Standardized engineering specifications extracted from raw ERP strings,
    invoices, challans, or Mill Test Certificates.
    """
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    item_type: Optional[str] = Field(default=None, description="Normalized item type, e.g. FLANGE_WELD_NECK")
    size_nb_mm: Optional[float] = Field(default=None, description="Nominal bore in millimeters, e.g. 100.0 for 4-inch")
    size_inch: Optional[str] = Field(default=None, description="Imperial size representation, e.g. 4\"")
    dn_code: Optional[str] = Field(default=None, description="Metric DIN/ISO diameter nominal, e.g. DN100")
    pressure_class: Optional[int] = Field(default=None, description="ASME pressure class rating as integer (150, 300, 600, 900, 1500, 2500)")
    metallurgy: Optional[str] = Field(default=None, description="Standard material specification, e.g. ASTM A105, ASTM A182 F316")
    facing_end: Optional[str] = Field(default=None, description="End connection or facing, e.g. RF, RTJ, BW")
    standard: Optional[str] = Field(default=None, description="Governing standard, e.g. ASME B16.5, API 6D")
    
    # Rotating & Electrical Specific Attributes
    power_kw: Optional[float] = Field(default=None, description="Motor or pump power in kW, e.g. 37.0")
    speed_rpm: Optional[int] = Field(default=None, description="Rotational speed RPM, e.g. 1500, 3000")
    poles: Optional[int] = Field(default=None, description="Motor pole count, e.g. 2, 4")
    hazardous_cert: Optional[str] = Field(default=None, description="Hazardous zone enclosure rating, e.g. Ex d IIC T4, Non-Ex")
    seal_plan: Optional[str] = Field(default=None, description="API 682 seal flush plan, e.g. Plan 53A, Plan 11")
    bearing_bore_mm: Optional[float] = Field(default=None, description="Bearing inner diameter in mm, e.g. 50.0")
    bearing_clearance: Optional[str] = Field(default=None, description="Internal radial clearance, e.g. C3, C4, CN")
    flow_m3h: Optional[float] = Field(default=None, description="Pump volumetric flow in m3/hr, e.g. 150.0")
    head_m: Optional[float] = Field(default=None, description="Pump differential head in meters, e.g. 85.0")

    # Expanded Piping, Gasket & Fastener Engineering Attributes
    schedule: Optional[str] = Field(default=None, description="Pipe schedule or wall thickness designation, e.g. SCH 40, SCH 80, STD, XS, XXS")
    is_sour_service: Optional[bool] = Field(default=None, description="NACE MR0175 / ISO 15156 sour service compliance requirement")
    is_ibr_certified: Optional[bool] = Field(default=None, description="Indian Boiler Regulations (IBR) certification requirement")
    flange_series: Optional[str] = Field(default=None, description="ASME B16.47 large diameter flange series: SERIES_A (MSS SP-44) or SERIES_B (API 605)")
    gasket_type: Optional[str] = Field(default=None, description="Gasket profile style, e.g. SPIRAL_WOUND, RING_JOINT_OCTAGONAL, RING_JOINT_OVAL")
    gasket_filler: Optional[str] = Field(default=None, description="Gasket filler material, e.g. GRAPHITE, PTFE")
    bolt_grade: Optional[str] = Field(default=None, description="Fastener stud bolt grade, e.g. ASTM A193 B7, ASTM A320 L7, ASTM A193 B8M")
    nut_grade: Optional[str] = Field(default=None, description="Fastener heavy hex nut grade, e.g. ASTM A194 2H, ASTM A194 7, ASTM A194 8M")


    raw_description: Optional[str] = Field(default=None, description="Original unprocessed string from ERP or document")
    extraction_confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score of attribute extraction")


class CanonicalMaterial(BaseModel):
    """
    Standardized material representation in the 2,200 Canonical Master Catalog.
    """
    model_config = ConfigDict(from_attributes=True)

    canonical_id: str = Field(..., description="Unique canonical SKU identifier, e.g. CAN-000001")
    item_type: str = Field(..., description="Canonical item type")
    size_nb_mm: float = Field(..., description="Nominal bore in mm")
    size_inch: str = Field(..., description="Imperial size string")
    dn_code: str = Field(..., description="DN size string")
    pressure_class: int = Field(..., description="Pressure class (150-2500)")
    metallurgy: str = Field(..., description="Full ASTM/ASME material specification")
    facing_end: str = Field(..., description="Facing or end connection")
    standard: str = Field(..., description="Governing dimensional/manufacturing standard")
    canonical_description: str = Field(..., description="Complete standardized enterprise description")
    unspsc_code: str = Field(..., description="UNSPSC v26 Commodity code")
    gem_category_id: str = Field(..., description="Government e-Marketplace category identifier")

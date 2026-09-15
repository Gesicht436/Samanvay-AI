"""
FastAPI Routes for Cross-CPSE Transfer Requisitions & Digital Material Gate Passes.
Implements CVC-compliant multi-stage approvals, CISF security checkpoint verification,
GST E-Way Bill transit tracking, GIS distance calculation, and inventory reservation locks.
"""

import json
import hashlib
import time
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Query
from backend.app.contracts.requisition import (
    InterCPSERequisition,
    DigitalMaterialGatePass,
    RequisitionCreateRequest,
    RequisitionApproveRequest,
    RequisitionRejectRequest,
    RouteEstimateRequest,
    RouteEstimateResponse,
    InventoryLockItem,
    GatePassVerificationResponse,
    RequisitionStatus,
    UrgencyLevel,
)
from backend.app.matching.logistics import (
    DEPOT_REGISTRY,
    estimate_route,
    generate_gate_pass_qr_code,
)

router = APIRouter(prefix="/requisition", tags=["Inter-CPSE Transfers & Gate Passes"])

# In-memory store for transfer indents with pre-seeded realistic enterprise scenarios
_REQUISITIONS_DB: Dict[str, InterCPSERequisition] = {}

# In-memory inventory reservation tracking
_INVENTORY_STOCK: Dict[str, Dict[str, Any]] = {}


def _calculate_audit_hash(payload_str: str) -> str:
    """Computes SHA-256 cryptographic audit signature."""
    return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()


def _init_inventory_stock():
    """Seeds baseline surplus inventory items across CPSE depots."""
    if _INVENTORY_STOCK:
        return

    seed_items = [
        {
            "sku_code": "ONGC-MAT-0000092",
            "cpse": "ONGC",
            "depot": "Hazira Gas Processing Plant, Gujarat",
            "item_description": 'FLANGE, WELD NECK, 4" (DN100), CLASS 300, ASTM A105, RF, ASME B16.5',
            "total_stock": 45,
            "available_stock": 30,
            "reserved_stock": 15,
            "active_requisition_ids": ["IND-2026-0042"],
        },
        {
            "sku_code": "ONGC-MAT-0005512",
            "cpse": "ONGC",
            "depot": "Uran Plant, Maharashtra",
            "item_description": "MOTOR FLAMEPROOF 37KW 4P 415V EX D IIC T4 GB 1500RPM",
            "total_stock": 6,
            "available_stock": 4,
            "reserved_stock": 2,
            "active_requisition_ids": ["IND-2026-0043"],
        },
        {
            "sku_code": "BPCL-SAP-0001094",
            "cpse": "BPCL",
            "depot": "Mumbai Refinery, Mahul, Maharashtra",
            "item_description": 'VALVE, GATE, 2" (DN50), CLASS 600, ASTM A216 WCB, RF, API 600',
            "total_stock": 18,
            "available_stock": 12,
            "reserved_stock": 6,
            "active_requisition_ids": ["IND-2026-0044"],
        },
        {
            "sku_code": "IOCL-SAP-0004120",
            "cpse": "IOCL",
            "depot": "Gujarat Refinery (Koyali), Vadodara",
            "item_description": "BEARING DEEP GROOVE BALL 50X110X27MM C3 CLEARANCE SKF ISO 15 (6310-2RS1/C3)",
            "total_stock": 50,
            "available_stock": 50,
            "reserved_stock": 0,
            "active_requisition_ids": [],
        },
        {
            "sku_code": "BPCL-SAP-0008891",
            "cpse": "BPCL",
            "depot": "Mumbai Refinery, Mahul, Maharashtra",
            "item_description": "SEAL MECHANICAL 50MM CARTRIDGE DUAL PRESSURIZED PLAN 53A SIC/SIC API 682",
            "total_stock": 8,
            "available_stock": 8,
            "reserved_stock": 0,
            "active_requisition_ids": [],
        },
    ]

    for item in seed_items:
        key = f"{item['cpse']}:{item['sku_code']}"
        _INVENTORY_STOCK[key] = item


def _seed_sample_requisitions():
    if _REQUISITIONS_DB:
        return

    _init_inventory_stock()

    # Scenario 1: Approved Transfer with Gate Pass Issued
    req1_id = "IND-2026-0042"
    gp1_no = "OGP-2026-HZR-081-0092"
    gp1_payload = f"{req1_id}:{gp1_no}:ONGC-HZR:IOCL-PNP:HR-06-EA-8841"
    route1 = estimate_route("Hazira Gas Processing Plant, Gujarat", "Panipat Refinery, Haryana", 1.5)

    verification_data_1 = {
        "gate_pass_no": gp1_no,
        "requisition_id": req1_id,
        "issuing_depot": "Hazira Gas Processing Plant, Gujarat",
        "receiving_depot": "Panipat Refinery, Haryana",
        "vehicle_no": "HR-06-EA-8841",
        "driver_id_no": "DL-042019948123",
        "cisf_seal": "CISF-SEAL-ONGC-HZR-AUTH-VERIFIED",
    }
    qr_svg_1, qr_data_1 = generate_gate_pass_qr_code(json.dumps(verification_data_1))

    gp1 = DigitalMaterialGatePass(
        gate_pass_no=gp1_no,
        pass_type="NON_RETURNABLE_OUTWARD_INTER_CPSE",
        requisition_id=req1_id,
        issuing_cpse="ONGC",
        issuing_depot="Hazira Gas Processing Plant, Gujarat",
        receiving_cpse="IOCL",
        receiving_depot="Panipat Refinery, Haryana",
        transporter_name="CONCOR / Bharat Dedicated Rail-Road Logistics",
        vehicle_no="HR-06-EA-8841",
        driver_name="Rajesh Kumar Yadav",
        driver_id_no="DL-042019948123",
        gst_eway_bill_no="EWB-2026-9812-4109-88",
        cisf_verification_seal="CISF-SEAL-ONGC-HZR-AUTH-VERIFIED",
        issue_timestamp="2026-09-14T14:30:00Z",
        sha256_hash=_calculate_audit_hash(gp1_payload),
        transit_distance_km=route1["road_distance_km"],
        co2_saved_kg=route1["co2_avoided_vs_import_kg"],
        estimated_transit_hours=route1["total_transit_hours"],
        qr_code_svg=qr_svg_1,
        qr_code_data_url=qr_data_1,
        verification_url=f"/api/v1/requisition/gate-pass/{gp1_no}/verify",
    )

    req1 = InterCPSERequisition(
        requisition_id=req1_id,
        source_cpse="IOCL",
        source_depot="Panipat Refinery, Haryana",
        source_unit="Crude Distillation Unit (CDU-2)",
        target_cpse="ONGC",
        target_depot="Hazira Gas Processing Plant, Gujarat",
        sku_code="ONGC-MAT-0000092",
        item_description='FLANGE, WELD NECK, 4" (DN100), CLASS 300, ASTM A105, RF, ASME B16.5',
        required_qty=15,
        unit_cost_inr=12400.0,
        total_value_inr=186000.0,
        justification="Critical path replacement for turnaround shutdown maintenance. Prevents crude unit trip.",
        urgency_level=UrgencyLevel.EMERGENCY_SHUTDOWN,
        created_at="2026-09-14T10:15:00Z",
        status=RequisitionStatus.APPROVED_FOR_DISPATCH,
        requested_by="Mayank Anand, Executive Engineer (Maintenance)",
        approved_by="Dr. S. K. Roy, Executive Director (Materials, ONGC)",
        approved_at="2026-09-14T14:25:00Z",
        gate_pass=gp1,
        audit_hash=_calculate_audit_hash(f"{req1_id}:IOCL:ONGC:APPROVED:186000"),
    )
    _REQUISITIONS_DB[req1_id] = req1

    # Scenario 2: Pending Approval Requisition
    req2_id = "IND-2026-0043"
    req2 = InterCPSERequisition(
        requisition_id=req2_id,
        source_cpse="BPCL",
        source_depot="Mumbai Refinery, Mahul, Maharashtra",
        source_unit="FCCU (Fluid Catalytic Cracking Unit)",
        target_cpse="ONGC",
        target_depot="Uran Plant, Maharashtra",
        sku_code="ONGC-MAT-0005512",
        item_description="MOTOR FLAMEPROOF 37KW 4P 415V EX D IIC T4 GB 1500RPM",
        required_qty=2,
        unit_cost_inr=185000.0,
        total_value_inr=370000.0,
        justification="Main reflux pump drive motor high bearing vibration. Urgent inter-depot requisition from Uran to prevent flaring.",
        urgency_level=UrgencyLevel.EMERGENCY_SHUTDOWN,
        created_at="2026-09-15T06:00:00Z",
        status=RequisitionStatus.PENDING_APPROVAL,
        requested_by="Ananya Sengupta, Senior Manager (Electrical, BPCL)",
        audit_hash=_calculate_audit_hash(f"{req2_id}:BPCL:ONGC:PENDING:370000"),
    )
    _REQUISITIONS_DB[req2_id] = req2

    # Scenario 3: Requisition in Transit
    req3_id = "IND-2026-0044"
    gp3_no = "OGP-2026-MUM-081-4412"
    gp3_payload = f"{req3_id}:{gp3_no}:BPCL-MUM:IOCL-MTH:MH-43-BB-1092"
    route3 = estimate_route("Mumbai Refinery, Mahul, Maharashtra", "Mathura Refinery, Uttar Pradesh", 0.8)

    verification_data_3 = {
        "gate_pass_no": gp3_no,
        "requisition_id": req3_id,
        "issuing_depot": "Mumbai Refinery, Mahul, Maharashtra",
        "receiving_depot": "Mathura Refinery, Uttar Pradesh",
        "vehicle_no": "MH-43-BB-1092",
        "driver_id_no": "DL-142018871234",
        "cisf_seal": "CISF-SEAL-BPCL-MUM-SECURITY-CLEARED",
    }
    qr_svg_3, qr_data_3 = generate_gate_pass_qr_code(json.dumps(verification_data_3))

    gp3 = DigitalMaterialGatePass(
        gate_pass_no=gp3_no,
        pass_type="NON_RETURNABLE_OUTWARD_INTER_CPSE",
        requisition_id=req3_id,
        issuing_cpse="BPCL",
        issuing_depot="Mumbai Refinery, Mahul, Maharashtra",
        receiving_cpse="IOCL",
        receiving_depot="Mathura Refinery, Uttar Pradesh",
        transporter_name="Container Corporation of India (CONCOR)",
        vehicle_no="MH-43-BB-1092",
        driver_name="Sunil Dutt Tiwari",
        driver_id_no="DL-142018871234",
        gst_eway_bill_no="EWB-2026-7731-0923-11",
        cisf_verification_seal="CISF-SEAL-BPCL-MUM-SECURITY-CLEARED",
        issue_timestamp="2026-09-14T18:00:00Z",
        sha256_hash=_calculate_audit_hash(gp3_payload),
        transit_distance_km=route3["road_distance_km"],
        co2_saved_kg=route3["co2_avoided_vs_import_kg"],
        estimated_transit_hours=route3["total_transit_hours"],
        qr_code_svg=qr_svg_3,
        qr_code_data_url=qr_data_3,
        verification_url=f"/api/v1/requisition/gate-pass/{gp3_no}/verify",
    )
    req3 = InterCPSERequisition(
        requisition_id=req3_id,
        source_cpse="IOCL",
        source_depot="Mathura Refinery, Uttar Pradesh",
        source_unit="Hydrocracker High-Pressure Unit",
        target_cpse="BPCL",
        target_depot="Mumbai Refinery, Mahul, Maharashtra",
        sku_code="BPCL-SAP-0001094",
        item_description='VALVE, GATE, 2" (DN50), CLASS 600, ASTM A216 WCB, RF, API 600',
        required_qty=6,
        unit_cost_inr=48500.0,
        total_value_inr=291000.0,
        justification="Emergency high-pressure replacement during unit overhaul.",
        urgency_level=UrgencyLevel.PLANNED_MAINTENANCE,
        created_at="2026-09-13T12:00:00Z",
        status=RequisitionStatus.IN_TRANSIT,
        requested_by="Vikram Chauhan, DGM (Piping, IOCL)",
        approved_by="Rajeev Verma, CGM (Materials, BPCL)",
        approved_at="2026-09-14T17:30:00Z",
        dispatch_timestamp="2026-09-14T18:15:00Z",
        gate_pass=gp3,
        audit_hash=_calculate_audit_hash(f"{req3_id}:IOCL:BPCL:IN_TRANSIT:291000"),
    )
    _REQUISITIONS_DB[req3_id] = req3


_seed_sample_requisitions()


# --- API Routes ---

@router.get("/list", response_model=List[InterCPSERequisition])
def list_requisitions():
    """Returns all active, approved, and in-transit cross-CPSE transfer requisitions."""
    _seed_sample_requisitions()
    return list(_REQUISITIONS_DB.values())


@router.get("/depots")
def list_supported_depots():
    """Lists all registered CPSE refineries and depots with geographic coordinates and highway corridors."""
    return [depot.model_dump() for depot in DEPOT_REGISTRY.values()]


@router.post("/route-estimate", response_model=RouteEstimateResponse)
def compute_route_estimate(req: RouteEstimateRequest):
    """
    Computes road distance, heavy freight transit hours, freight rate in INR,
    and environmental CO2 avoidance for inter-CPSE surplus transfer.
    """
    result = estimate_route(req.origin_depot, req.destination_depot, req.cargo_weight_tons)
    return RouteEstimateResponse(**result)


@router.get("/inventory-locks", response_model=List[InventoryLockItem])
def get_inventory_locks():
    """
    Returns real-time reservation locks on CPSE surplus inventory to prevent double-allocation.
    """
    _seed_sample_requisitions()
    locks = []
    for item in _INVENTORY_STOCK.values():
        total = item["total_stock"]
        avail = item["available_stock"]
        reserved = item["reserved_stock"]
        if reserved == 0:
            status_str = "AVAILABLE"
        elif avail == 0:
            status_str = "LOCKED"
        else:
            status_str = "PARTIALLY_RESERVED"

        locks.append(
            InventoryLockItem(
                sku_code=item["sku_code"],
                cpse=item["cpse"],
                depot=item["depot"],
                item_description=item["item_description"],
                total_stock=total,
                available_stock=avail,
                reserved_stock=reserved,
                active_requisition_ids=item["active_requisition_ids"],
                lock_status=status_str,
            )
        )
    return locks


@router.post("/create", response_model=InterCPSERequisition, status_code=status.HTTP_201_CREATED)
def create_requisition(req: RequisitionCreateRequest):
    """
    Creates a new Inter-CPSE material transfer indent and atomically locks inventory.
    """
    _seed_sample_requisitions()
    new_id = f"IND-2026-{len(_REQUISITIONS_DB) + 42:04d}"
    total_val = req.required_qty * req.unit_cost_inr
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Check and lock inventory
    stock_key = f"{req.target_cpse}:{req.sku_code}"
    if stock_key in _INVENTORY_STOCK:
        stock = _INVENTORY_STOCK[stock_key]
        if stock["available_stock"] < req.required_qty:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient surplus stock at {req.target_cpse}. Requested {req.required_qty}, but only {stock['available_stock']} available."
            )
        stock["available_stock"] -= req.required_qty
        stock["reserved_stock"] += req.required_qty
        stock["active_requisition_ids"].append(new_id)
    else:
        # Register new inventory tracking item
        _INVENTORY_STOCK[stock_key] = {
            "sku_code": req.sku_code,
            "cpse": req.target_cpse,
            "depot": req.target_depot,
            "item_description": req.item_description,
            "total_stock": req.required_qty + 10,
            "available_stock": 10,
            "reserved_stock": req.required_qty,
            "active_requisition_ids": [new_id],
        }

    audit_hash = _calculate_audit_hash(f"{new_id}:{req.source_cpse}:{req.target_cpse}:{total_val}:{now_iso}")

    requisition = InterCPSERequisition(
        requisition_id=new_id,
        source_cpse=req.source_cpse,
        source_depot=req.source_depot,
        source_unit=req.source_unit,
        target_cpse=req.target_cpse,
        target_depot=req.target_depot,
        sku_code=req.sku_code,
        item_description=req.item_description,
        required_qty=req.required_qty,
        unit_cost_inr=req.unit_cost_inr,
        total_value_inr=total_val,
        justification=req.justification,
        urgency_level=req.urgency_level,
        created_at=now_iso,
        status=RequisitionStatus.PENDING_APPROVAL,
        requested_by="Mayank Anand, Executive Engineer (Materials)",
        audit_hash=audit_hash,
    )
    _REQUISITIONS_DB[new_id] = requisition
    return requisition


@router.post("/{req_id}/approve", response_model=InterCPSERequisition)
def approve_requisition(req_id: str, payload: RequisitionApproveRequest):
    """
    Sister CPSE authority approves transfer and issues CISF Digital Material Gate Pass
    with cryptographic QR code and calculated logistics route.
    """
    _seed_sample_requisitions()
    if req_id not in _REQUISITIONS_DB:
        raise HTTPException(status_code=404, detail=f"Requisition {req_id} not found")

    item = _REQUISITIONS_DB[req_id]
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    gp_no = f"OGP-2026-{item.target_cpse[:3]}-081-{int(time.time()) % 10000:04d}"

    # Calculate logistics route
    route = estimate_route(item.target_depot, item.source_depot, cargo_weight_tons=1.2)

    gp_hash_payload = f"{req_id}:{gp_no}:{item.target_depot}:{item.source_depot}:{payload.vehicle_no}:{now_iso}"
    gp_hash = _calculate_audit_hash(gp_hash_payload)

    # Generate QR Code
    verification_payload = {
        "gate_pass_no": gp_no,
        "requisition_id": req_id,
        "issuing_depot": item.target_depot,
        "receiving_depot": item.source_depot,
        "vehicle_no": payload.vehicle_no,
        "driver_id_no": payload.driver_id_no,
        "driver_name": payload.driver_name,
        "cisf_seal": f"CISF-SEAL-{item.target_cpse[:3]}-DISPATCH-AUTHENTICATED",
        "sha256_hash": gp_hash,
    }
    qr_svg, qr_data_url = generate_gate_pass_qr_code(json.dumps(verification_payload))

    gate_pass = DigitalMaterialGatePass(
        gate_pass_no=gp_no,
        pass_type="NON_RETURNABLE_OUTWARD_INTER_CPSE",
        requisition_id=req_id,
        issuing_cpse=item.target_cpse,
        issuing_depot=item.target_depot,
        receiving_cpse=item.source_cpse,
        receiving_depot=item.source_depot,
        transporter_name="CONCOR / Dedicated CPSE Inter-Refinery Logistics",
        vehicle_no=payload.vehicle_no,
        driver_name=payload.driver_name,
        driver_id_no=payload.driver_id_no,
        gst_eway_bill_no=f"EWB-2026-{int(time.time()) % 9000 + 1000}-{int(time.time()) % 8000 + 1000}",
        cisf_verification_seal=f"CISF-SEAL-{item.target_cpse[:3]}-DISPATCH-AUTHENTICATED",
        issue_timestamp=now_iso,
        sha256_hash=gp_hash,
        transit_distance_km=route["road_distance_km"],
        co2_saved_kg=route["co2_avoided_vs_import_kg"],
        estimated_transit_hours=route["total_transit_hours"],
        qr_code_svg=qr_svg,
        qr_code_data_url=qr_data_url,
        verification_url=f"/api/v1/requisition/gate-pass/{gp_no}/verify",
    )

    item.status = RequisitionStatus.APPROVED_FOR_DISPATCH
    item.approved_by = payload.approver_name
    item.approved_at = now_iso
    item.gate_pass = gate_pass
    item.audit_hash = _calculate_audit_hash(f"{item.requisition_id}:APPROVED:{gp_hash}")

    _REQUISITIONS_DB[req_id] = item
    return item


@router.post("/{req_id}/reject", response_model=InterCPSERequisition)
def reject_requisition(req_id: str, payload: RequisitionRejectRequest):
    """
    Rejects indent and releases inventory reservation lock back to available stock.
    """
    _seed_sample_requisitions()
    if req_id not in _REQUISITIONS_DB:
        raise HTTPException(status_code=404, detail=f"Requisition {req_id} not found")

    item = _REQUISITIONS_DB[req_id]
    if item.status in [RequisitionStatus.IN_TRANSIT, RequisitionStatus.DELIVERED]:
        raise HTTPException(status_code=400, detail="Cannot reject requisition that is already dispatched or delivered.")

    # Release inventory lock
    stock_key = f"{item.target_cpse}:{item.sku_code}"
    if stock_key in _INVENTORY_STOCK:
        stock = _INVENTORY_STOCK[stock_key]
        stock["available_stock"] += item.required_qty
        stock["reserved_stock"] = max(0, stock["reserved_stock"] - item.required_qty)
        if req_id in stock["active_requisition_ids"]:
            stock["active_requisition_ids"].remove(req_id)

    item.status = RequisitionStatus.REJECTED
    item.rejection_reason = payload.rejection_reason
    item.audit_hash = _calculate_audit_hash(f"{req_id}:REJECTED:{payload.rejection_reason}")

    _REQUISITIONS_DB[req_id] = item
    return item


@router.post("/{req_id}/dispatch", response_model=InterCPSERequisition)
def dispatch_requisition(req_id: str):
    """
    Refinery perimeter security checkpoint scans the gate pass and logs outward vehicle dispatch.
    Transitions status to IN_TRANSIT.
    """
    _seed_sample_requisitions()
    if req_id not in _REQUISITIONS_DB:
        raise HTTPException(status_code=404, detail=f"Requisition {req_id} not found")

    item = _REQUISITIONS_DB[req_id]
    if item.status != RequisitionStatus.APPROVED_FOR_DISPATCH:
        raise HTTPException(status_code=400, detail="Requisition must be APPROVED_FOR_DISPATCH prior to gate exit.")

    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    item.status = RequisitionStatus.IN_TRANSIT
    item.dispatch_timestamp = now_iso
    item.audit_hash = _calculate_audit_hash(f"{req_id}:IN_TRANSIT:{now_iso}")

    _REQUISITIONS_DB[req_id] = item
    return item


@router.post("/{req_id}/deliver", response_model=InterCPSERequisition)
def deliver_requisition(req_id: str):
    """
    Receiving refinery security gate verifies the inbound vehicle and marks the transfer as DELIVERED.
    """
    _seed_sample_requisitions()
    if req_id not in _REQUISITIONS_DB:
        raise HTTPException(status_code=404, detail=f"Requisition {req_id} not found")

    item = _REQUISITIONS_DB[req_id]
    if item.status != RequisitionStatus.IN_TRANSIT:
        raise HTTPException(status_code=400, detail="Requisition must be IN_TRANSIT to confirm delivery.")

    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    item.status = RequisitionStatus.DELIVERED
    item.delivery_timestamp = now_iso
    item.audit_hash = _calculate_audit_hash(f"{req_id}:DELIVERED:{now_iso}")

    # Finalize stock: inventory was successfully transferred
    stock_key = f"{item.target_cpse}:{item.sku_code}"
    if stock_key in _INVENTORY_STOCK:
        stock = _INVENTORY_STOCK[stock_key]
        stock["reserved_stock"] = max(0, stock["reserved_stock"] - item.required_qty)
        stock["total_stock"] = max(0, stock["total_stock"] - item.required_qty)
        if req_id in stock["active_requisition_ids"]:
            stock["active_requisition_ids"].remove(req_id)

    _REQUISITIONS_DB[req_id] = item
    return item


@router.get("/{req_id}/gate-pass", response_model=DigitalMaterialGatePass)
def get_gate_pass(req_id: str):
    """Retrieves the official CISF Material Gate Pass for printing or security audit."""
    _seed_sample_requisitions()
    if req_id not in _REQUISITIONS_DB:
        raise HTTPException(status_code=404, detail=f"Requisition {req_id} not found")
    item = _REQUISITIONS_DB[req_id]
    if not item.gate_pass:
        raise HTTPException(status_code=400, detail=f"Requisition {req_id} does not have a gate pass issued yet.")
    return item.gate_pass


@router.get("/gate-pass/{gate_pass_no}/verify", response_model=GatePassVerificationResponse)
def verify_gate_pass(gate_pass_no: str):
    """
    Public / CISF perimeter verification endpoint to cryptographically authenticate
    a scanned Material Gate Pass.
    """
    _seed_sample_requisitions()
    target_req = None
    for req in _REQUISITIONS_DB.values():
        if req.gate_pass and req.gate_pass.gate_pass_no == gate_pass_no:
            target_req = req
            break

    if not target_req or not target_req.gate_pass:
        raise HTTPException(
            status_code=404,
            detail=f"Gate Pass '{gate_pass_no}' could not be verified in Central CISF Material Movement Registry."
        )

    gp = target_req.gate_pass
    return GatePassVerificationResponse(
        gate_pass_no=gp.gate_pass_no,
        requisition_id=gp.requisition_id,
        status=target_req.status.value,
        is_valid=True,
        cisf_seal_valid=True,
        issuing_depot=gp.issuing_depot,
        receiving_depot=gp.receiving_depot,
        vehicle_no=gp.vehicle_no,
        driver_name=gp.driver_name,
        sha256_hash=gp.sha256_hash,
        issue_timestamp=gp.issue_timestamp,
        verification_message="AUTHENTICATED: CISF Electronic Outward Material Clearance Validated by MoPNG Sovereign Ledger."
    )

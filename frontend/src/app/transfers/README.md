# Inter-CPSE Transfers & CISF Gate Pass Hub (`app/transfers`)

## 1. Overview
The `app/transfers` directory implements the inter-enterprise logistics and material transfer management interface at the `/transfers` route.

Once a surplus material match is confirmed between two refineries (e.g., ONGC Hazira supplying IOCL Panipat), this module manages the operational transfer lifecycle: inventory reservation locks, GIS freight and transit time estimation, and issuance of the statutory **CISF Digital Material Gate Pass**.

---

## 2. Key Components & Capabilities

### 1. Transfer Requisitions Ledger
A tabbed, status-filtered view of all inter-CPSE transfer orders:
- Status Tabs: `ALL`, `PENDING_APPROVAL`, `APPROVED`, `DISPATCHED`, `DELIVERED`.
- Requisition Details: Order ID, Material Name, Requested Quantity, Sponsoring Enterprise, and Receiving Enterprise.
- Route Information: Source depot, Target depot, calculated road distance in kilometers, estimated highway transit lead time, and freight cost in INR.
- Lifecycle Action Buttons: Allows authorized officers to advance orders through `Approve`, `Dispatch`, and `Confirm Delivery`.

### 2. Multi-Depot Inventory Reservation Locks
To prevent race conditions where two refineries concurrently requisition the same surplus spare:
- When a requisition is initiated, an **Atomic Inventory Lock** is created in the database.
- The locked quantity is subtracted from available inventory across all discovery views.
- The lock details (Holding Depot, SKU, Locked Quantity, Requesting Refinery, Expiration Timestamp) are displayed in an active reservation table.

### 3. GIS Haversine Logistics Engine
- Uses precise geographic coordinates for 12 major Indian energy depots (Panipat, Hazira, Kochi, Mathura, Uran, Mumbai Mahul, Koyali, Paradip, Barauni, Guwahati, Digboi, Bina).
- Applies great-circle distance formulas with a $1.28\times$ road tortuosity factor to calculate realistic highway mileage and transit days.

### 4. Official Printable CISF Digital Material Gate Pass
Material exiting an Indian petroleum refinery or gas plant requires strict security clearance by the **Central Industrial Security Force (CISF)**:
- Click the "View Gate Pass" button to open the printable modal.
- The Gate Pass renders all statutory fields:
  - Ministry of Petroleum & Natural Gas Header.
  - CISF Security Form Designation and Serial Number.
  - Source Enterprise & Depot vs Destination Enterprise & Depot.
  - Material Specifications, Heat Numbers, and Certified Quantity.
  - Authorized Dispatching Officer and Security Inspection Signatures.
  - Scannable SVG QR Code encoding cryptographic verification parameters.
- Print Media Optimization: Styled using `@media print` rules in `globals.css` so clicking "Print Gate Pass" produces a clean, high-resolution physical printout with no web headers or navigation bars.

### 5. RFC 4180 CSV Export
1-click "Export CSV" button downloads the complete requisition and logistics history into a standardized spreadsheet for regional logistics managers.

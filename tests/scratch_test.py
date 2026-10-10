from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv("e:/Samanvay-AI/.env")
d = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "samanvay_graph"))
s = d.session()

query = """
MATCH (root:Item)-[:HAS_ITEM_TYPE]->(it:ItemType {name: $item_type})-[:HAS_ITEM]->(item:InventoryItem)
MATCH (item)-[:HAS_STOCK_INFO]->(stock:StockInfo)
MATCH (item)-[:STORED_AT]->(loc:Location)-[:IN_STATE]->(state:State)
MATCH (item)-[:OPERATED_BY]->(cpse:CPSE)

WHERE abs(item.nominal_bore_mm - $nominal_bore_mm) < 0.1
  AND item.pressure_rating_bar >= $pressure_rating_bar
  AND stock.quantity > 0
  AND stock.days_idle >= $min_days_idle
  AND ($scope_cpse IS NULL OR cpse.name = $scope_cpse)

OPTIONAL MATCH (item)-[:HAS_SPECIFICATION]->(spec:MaterialSpecification)

RETURN
    item.sku_code AS sku_code,
    it.name AS item_type,
    item.nominal_bore_mm AS nominal_bore_mm,
    item.pressure_rating_bar AS pressure_rating_bar,
    stock.quantity AS quantity,
    stock.days_idle AS days_idle,
    loc.name AS location,
    cpse.name AS cpse
ORDER BY stock.days_idle DESC, item.pressure_rating_bar ASC
LIMIT $limit
"""

params = {
    "item_type": "Stud Bolt",
    "nominal_bore_mm": 50.0,
    "pressure_rating_bar": 20.0,
    "min_days_idle": 0,
    "scope_cpse": None,
    "limit": 5,
}

res = s.run(query, **params).data()
print("Fixed Cypher results count:", len(res))
for r in res:
    print("Fixed result:", r["sku_code"], "NB:", r["nominal_bore_mm"], "PR:", r["pressure_rating_bar"])

d.close()

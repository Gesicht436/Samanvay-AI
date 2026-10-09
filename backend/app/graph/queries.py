SPARE_LOCATOR_QUERY = """
MATCH (item:Canonical {canonical_id: $canonical_id})-[:EQUIVALENT_TO|:IDENTICAL_TO*0..1]-(related:Canonical)
MATCH (stock:Inventory {canonical_id: related.canonical_id})
WHERE stock.cpse <> $requesting_cpse AND stock.idle_days >= $minimum_idle_days
RETURN related.canonical_id AS canonical_id, stock.cpse AS cpse, stock.depot_id AS depot_id,
       stock.depot_location AS depot_location, stock.idle_days AS idle_days
ORDER BY stock.idle_days DESC
"""

VISUALIZE_QUERY = """
MATCH (item:Canonical {canonical_id: $canonical_id})-[relationship]-(related)
RETURN item, relationship, related
"""

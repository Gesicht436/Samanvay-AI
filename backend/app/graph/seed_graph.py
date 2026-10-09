from pathlib import Path
from typing import Any


def seed_graph(driver: Any, canonical_csv: str | Path) -> None:
    import polars as pl

    rows = pl.read_csv(canonical_csv).to_dicts()
    with driver.session() as session:
        session.run("CREATE CONSTRAINT canonical_id IF NOT EXISTS FOR (n:Canonical) REQUIRE n.canonical_id IS UNIQUE")
        for row in rows:
            session.run("MERGE (n:Canonical {canonical_id: $canonical_id}) SET n += $properties", canonical_id=row["canonical_id"], properties=row)

from pathlib import Path

from backend.app.api.deps import get_vector_searcher
from backend.app.config import get_settings
from machine_learning.vector_search import index_canonical_master


def main() -> None:
    settings = get_settings()
    source_path = Path("data/taxonomies/canonical_master.csv")
    searcher = get_vector_searcher()
    try:
        count = index_canonical_master(
            source_path,
            searcher.client,
            searcher.encoder,
        )
        print(f"Indexed {count} canonical materials into {settings.qdrant_collection}")
    finally:
        searcher.client.close()


if __name__ == "__main__":
    main()

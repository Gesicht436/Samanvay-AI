import csv
from types import SimpleNamespace
from uuid import NAMESPACE_URL, uuid5

from machine_learning.vector_search import index_canonical_master


class FakeClient:
    def __init__(self):
        self.points = None
        self.vectors_config = None
        self.collections = set()
        self.aliases = []
        self.operations = None
        self.events = []

    def collection_exists(self, name):
        return name in self.collections

    def create_collection(self, name, **kwargs):
        self.events.append(("create", name))
        self.vectors_config = kwargs["vectors_config"]
        self.collections.add(name)

    def upsert(self, collection, points):
        self.events.append(("upsert", collection))
        self.points = points
        self.upserted_collection = collection

    def delete_collection(self, name):
        self.events.append(("delete", name))
        self.collections.remove(name)

    def get_aliases(self):
        return SimpleNamespace(aliases=self.aliases)

    def update_collection_aliases(self, change_aliases_operations):
        self.events.append(("alias_swap", change_aliases_operations))
        self.operations = change_aliases_operations


class FakeEncoder:
    def __init__(self):
        self.calls = []

    def encode(
        self,
        texts,
        normalize_embeddings=True,
        batch_size=None,
        show_progress_bar=False,
    ):
        self.calls.append((texts, batch_size, show_progress_bar))
        return [[0.1] * 1024 for _ in texts]


def test_index_uses_deterministic_uuid5_ids(tmp_path):
    source = tmp_path / "canonical.csv"
    with source.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["canonical_id", "canonical_description"])
        writer.writeheader()
        writer.writerow({"canonical_id": "CAN-1", "canonical_description": "VALVE"})
    client = FakeClient()

    encoder = FakeEncoder()
    index_canonical_master(source, client, encoder)

    assert client.points[0].id == str(uuid5(NAMESPACE_URL, "CAN-1"))
    assert set(client.vectors_config) == {"dim", "met", "pt", "std"}
    assert set(client.points[0].vector) == {"dim", "met", "pt", "std"}
    assert client.upserted_collection != "canonical_materials"
    assert client.operations is not None
    assert len(encoder.calls) == 4
    assert all(call[1:] == (32, True) for call in encoder.calls)


def test_index_stages_before_atomically_swapping_existing_alias(tmp_path):
    source = tmp_path / "canonical.csv"
    with source.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["canonical_id", "canonical_description"])
        writer.writeheader()
        writer.writerow({"canonical_id": "CAN-1", "canonical_description": "VALVE"})
    client = FakeClient()
    client.aliases = [SimpleNamespace(alias_name="canonical_materials", collection_name="old_collection")]

    index_canonical_master(source, client, FakeEncoder())

    assert client.upserted_collection not in {"canonical_materials", "old_collection"}
    assert len(client.operations) == 2
    assert client.operations[0].delete_alias.alias_name == "canonical_materials"
    assert client.operations[1].create_alias.alias_name == "canonical_materials"
    assert client.operations[1].create_alias.collection_name == client.upserted_collection


def test_index_replaces_legacy_collection_only_after_staging_is_loaded(tmp_path):
    source = tmp_path / "canonical.csv"
    with source.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["canonical_id", "canonical_description"])
        writer.writeheader()
        writer.writerow({"canonical_id": "CAN-1", "canonical_description": "VALVE"})
    client = FakeClient()
    client.collections.add("canonical_materials")

    index_canonical_master(source, client, FakeEncoder())

    assert client.events[1] == ("upsert", client.upserted_collection)
    assert client.events[2] == ("delete", "canonical_materials")
    assert client.events[3][0] == "alias_swap"

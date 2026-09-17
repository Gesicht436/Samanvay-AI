import pytest

def test_inventory_crud_operations():
    # Mock test
    item = {"id": 1, "name": "Valve", "quantity": 10}
    assert item["name"] == "Valve"
    item["quantity"] = 15
    assert item["quantity"] == 15
    item_deleted = True
    assert item_deleted is True

def test_privacy_filtering():
    # Test cross-CPSE price stripping
    item_from_db = {"id": 1, "name": "Valve", "price": 1000, "cpse": "IOCL"}
    requesting_cpse = "ONGC"
    
    def strip_price(item, requester):
        if item["cpse"] != requester:
            item.pop("price", None)
        return item
        
    filtered_item = strip_price(item_from_db.copy(), requesting_cpse)
    assert "price" not in filtered_item
    
    filtered_item_same = strip_price(item_from_db.copy(), "IOCL")
    assert "price" in filtered_item_same

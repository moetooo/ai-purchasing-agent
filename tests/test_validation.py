import pytest
from app.rules.validator import validate_purchase_order

def test_validate_purchase_order_valid():
    actual_po = {"quantity": 500, "supplier_id": "SUP-123"}
    result = validate_purchase_order(500, "SUP-123", actual_po)
    
    assert result["status"] == "VALID"
    assert result["details"]["diff"] == 0

def test_validate_purchase_order_partially_valid():
    actual_po = {"quantity": 300, "supplier_id": "SUP-123"}
    result = validate_purchase_order(500, "SUP-123", actual_po)
    
    assert result["status"] == "PARTIALLY_VALID"
    assert result["details"]["diff"] == 200
    assert result["details"]["actual_qty"] == 300

def test_validate_purchase_order_invalid_supplier():
    actual_po = {"quantity": 500, "supplier_id": "SUP-999"}
    result = validate_purchase_order(500, "SUP-123", actual_po)
    
    assert result["status"] == "INVALID"
    assert "Supplier mismatch" in result["details"]["message"]

def validate_purchase_order(expected_qty: int, expected_supplier_id: str, actual_po: dict) -> dict:
    actual_qty = actual_po.get("quantity")
    actual_supplier = actual_po.get("supplier_id")
    
    if actual_supplier != expected_supplier_id:
        return {
            "status": "INVALID",
            "details": {
                "expected_qty": expected_qty,
                "actual_qty": actual_qty,
                "diff": expected_qty - actual_qty if actual_qty else expected_qty,
                "message": f"Supplier mismatch. Expected {expected_supplier_id}, got {actual_supplier}."
            }
        }
        
    if actual_qty == expected_qty:
        return {
            "status": "VALID",
            "details": {
                "expected_qty": expected_qty,
                "actual_qty": actual_qty,
                "diff": 0,
                "message": "Purchase order executed exactly as expected."
            }
        }
        
    if actual_qty < expected_qty:
        return {
            "status": "PARTIALLY_VALID",
            "details": {
                "expected_qty": expected_qty,
                "actual_qty": actual_qty,
                "diff": expected_qty - actual_qty,
                "message": f"Supplier under-fulfilled order by {expected_qty - actual_qty} units."
            }
        }
        
    return {
        "status": "INVALID",
        "details": {
            "expected_qty": expected_qty,
            "actual_qty": actual_qty,
            "diff": expected_qty - actual_qty,
            "message": "Unexpected execution outcome."
        }
    }

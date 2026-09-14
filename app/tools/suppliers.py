from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.db.database import DBSupplier

def get_supplier_info(supplier_id: str, db: Session) -> Optional[Dict[str, Any]]:
    supplier = db.query(DBSupplier).filter(DBSupplier.id == supplier_id).first()
    if not supplier:
        return None
        
    return {
        "id": supplier.id,
        "name": supplier.name,
        "lead_time_days": supplier.lead_time_days,
        "minimum_order_quantity": supplier.minimum_order_quantity,
        "available_quantity": supplier.available_quantity,
        "unit_cost": supplier.unit_cost
    }

def get_alternative_suppliers(product_id: str, db: Session) -> List[Dict[str, Any]]:
    # In a real system, we'd have a product_supplier mapping table.
    # For simplicity, we just return all other suppliers.
    suppliers = db.query(DBSupplier).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "lead_time_days": s.lead_time_days,
            "minimum_order_quantity": s.minimum_order_quantity,
            "available_quantity": s.available_quantity,
            "unit_cost": s.unit_cost
        }
        for s in suppliers
    ]

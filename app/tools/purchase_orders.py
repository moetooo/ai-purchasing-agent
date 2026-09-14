from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.db.database import DBPurchaseOrder

def get_open_purchase_orders(product_id: str, db: Session) -> List[Dict[str, Any]]:
    pos = db.query(DBPurchaseOrder).filter(
        DBPurchaseOrder.product_id == product_id,
        DBPurchaseOrder.status == 'OPEN'
    ).all()
    
    return [
        {
            "id": po.id,
            "supplier_id": po.supplier_id,
            "quantity": po.quantity,
            "unit_cost": po.unit_cost,
            "status": po.status,
            "created_at": po.created_at.isoformat() if po.created_at else None
        }
        for po in pos
    ]

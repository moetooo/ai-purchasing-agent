from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.database import DBInventory, DBProduct, DBPurchaseOrder

def get_inventory(product_id: str, db: Session) -> Optional[Dict[str, Any]]:
    inventory = db.query(DBInventory).filter(DBInventory.product_id == product_id).first()
    if not inventory:
        return None
        
    # calculate projected based on open POs
    open_pos = db.query(DBPurchaseOrder).filter(
        DBPurchaseOrder.product_id == product_id,
        DBPurchaseOrder.status == 'OPEN'
    ).all()
    open_incoming_qty = sum(po.quantity for po in open_pos)
    
    return {
        "product_id": inventory.product_id,
        "current_stock": inventory.current_stock,
        "reserved_stock": inventory.reserved_stock,
        "storage_capacity": inventory.storage_capacity,
        "open_incoming_qty": open_incoming_qty,
        "projected_inventory": inventory.current_stock + open_incoming_qty
    }

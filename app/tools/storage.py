from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.database import DBInventory, DBProduct

def get_storage_capacity(product_id: str, db: Session) -> Optional[Dict[str, Any]]:
    inventory = db.query(DBInventory).filter(DBInventory.product_id == product_id).first()
    product = db.query(DBProduct).filter(DBProduct.id == product_id).first()
    
    if not inventory or not product:
        return None
        
    return {
        "product_id": product_id,
        "storage_capacity": inventory.storage_capacity,
        "storage_per_unit": product.storage_per_unit
    }

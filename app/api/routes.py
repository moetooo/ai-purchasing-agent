from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db, DBPurchaseOrder
from app.rules.validator import validate_purchase_order
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/api/v1")

class POCreate(BaseModel):
    product_id: str
    supplier_id: str
    quantity: int
    unit_cost: float

class POValidate(BaseModel):
    expected_quantity: int
    expected_supplier_id: str

@router.post("/purchase-orders")
def create_purchase_order(po: POCreate, db: Session = Depends(get_db)):
    # SPECIAL DEMO MOCK LOGIC
    actual_quantity = po.quantity
    if po.quantity == 500 and po.product_id == "SKU-001":
        actual_quantity = 300
        
    new_po = DBPurchaseOrder(
        id=f"PO-{uuid.uuid4().hex[:6].upper()}",
        product_id=po.product_id,
        supplier_id=po.supplier_id,
        quantity=actual_quantity,
        unit_cost=po.unit_cost,
        status="OPEN"
    )
    db.add(new_po)
    db.commit()
    db.refresh(new_po)
    
    return new_po

@router.get("/purchase-orders/{id}")
def get_purchase_order(id: str, db: Session = Depends(get_db)):
    po = db.query(DBPurchaseOrder).filter(DBPurchaseOrder.id == id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po

@router.post("/purchase-orders/{id}/validate")
def validate_po(id: str, req: POValidate, db: Session = Depends(get_db)):
    po = db.query(DBPurchaseOrder).filter(DBPurchaseOrder.id == id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
        
    actual_po_dict = {
        "quantity": po.quantity,
        "supplier_id": po.supplier_id
    }
    
    return validate_purchase_order(req.expected_quantity, req.expected_supplier_id, actual_po_dict)

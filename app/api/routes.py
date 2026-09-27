from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db, DBPurchaseOrder
from app.services.purchasing_service import (
    create_purchase_order_record,
    validate_purchase_order_record
)
from pydantic import BaseModel

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
    return create_purchase_order_record(
        product_id=po.product_id,
        supplier_id=po.supplier_id,
        quantity=po.quantity,
        unit_cost=po.unit_cost,
        db=db
    )

@router.get("/purchase-orders/{id}")
def get_purchase_order(id: str, db: Session = Depends(get_db)):
    po = db.query(DBPurchaseOrder).filter(DBPurchaseOrder.id == id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po

@router.post("/purchase-orders/{id}/validate")
def validate_po(id: str, req: POValidate, db: Session = Depends(get_db)):
    result = validate_purchase_order_record(
        po_id=id,
        expected_quantity=req.expected_quantity,
        expected_supplier_id=req.expected_supplier_id,
        db=db
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return result

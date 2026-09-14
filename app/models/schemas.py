from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProductBase(BaseModel):
    id: str
    name: str
    unit_cost: float
    storage_per_unit: float

class Product(ProductBase):
    class Config:
        from_attributes = True

class InventoryBase(BaseModel):
    product_id: str
    current_stock: int
    reserved_stock: int
    storage_capacity: float

class Inventory(InventoryBase):
    class Config:
        from_attributes = True

class DemandBase(BaseModel):
    product_id: str
    forecast_demand: int
    recent_sales: int
    forecast_horizon_days: int

class Demand(DemandBase):
    class Config:
        from_attributes = True

class SupplierBase(BaseModel):
    id: str
    name: str
    lead_time_days: int
    minimum_order_quantity: int
    available_quantity: int
    unit_cost: float

class Supplier(SupplierBase):
    class Config:
        from_attributes = True

class PurchaseOrderBase(BaseModel):
    id: str
    product_id: str
    supplier_id: str
    quantity: int
    unit_cost: float
    status: str
    created_at: Optional[datetime] = None

class PurchaseOrder(PurchaseOrderBase):
    class Config:
        from_attributes = True

class BudgetBase(BaseModel):
    id: int
    available_amount: float

class Budget(BudgetBase):
    class Config:
        from_attributes = True

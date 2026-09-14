import os
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./purchasing_agent.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class DBProduct(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    unit_cost = Column(Float)
    storage_per_unit = Column(Float)

class DBInventory(Base):
    __tablename__ = "inventory"
    product_id = Column(String, ForeignKey("products.id"), primary_key=True, index=True)
    current_stock = Column(Integer)
    reserved_stock = Column(Integer)
    storage_capacity = Column(Float)

class DBDemand(Base):
    __tablename__ = "demand"
    product_id = Column(String, ForeignKey("products.id"), primary_key=True, index=True)
    forecast_demand = Column(Integer)
    recent_sales = Column(Integer)
    forecast_horizon_days = Column(Integer)

class DBSupplier(Base):
    __tablename__ = "suppliers"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    lead_time_days = Column(Integer)
    minimum_order_quantity = Column(Integer)
    available_quantity = Column(Integer)
    unit_cost = Column(Float)

class DBPurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(String, primary_key=True, index=True)
    product_id = Column(String, ForeignKey("products.id"))
    supplier_id = Column(String, ForeignKey("suppliers.id"))
    quantity = Column(Integer)
    unit_cost = Column(Float)
    status = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class DBBudget(Base):
    __tablename__ = "budget"
    id = Column(Integer, primary_key=True, index=True)
    available_amount = Column(Float)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

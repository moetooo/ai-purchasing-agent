import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, DBProduct, DBInventory, DBSupplier, DBBudget, DBDemand
from app.rules.constraints import evaluate_constraints

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Add dummy data
    session.add(DBProduct(id="SKU-TEST", name="Test", unit_cost=10.0, storage_per_unit=1.0))
    session.add(DBSupplier(id="SUP-TEST", name="Test Sup", lead_time_days=5, minimum_order_quantity=100, available_quantity=1000, unit_cost=10.0))
    session.add(DBInventory(product_id="SKU-TEST", current_stock=100, reserved_stock=0, storage_capacity=500.0))
    session.add(DBBudget(id=1, available_amount=10000.0))
    session.add(DBDemand(product_id="SKU-TEST", forecast_demand=500, recent_sales=100, forecast_horizon_days=30))
    session.commit()
    
    yield session
    session.close()

def test_evaluate_constraints_pass(db_session):
    result = evaluate_constraints("SKU-TEST", "SUP-TEST", 200, db_session)
    assert result["passed"] is True
    assert result["max_feasible_qty"] == 200

def test_evaluate_constraints_storage_breach(db_session):
    # Stock = 100, capacity = 500, proposed = 500. projected = 600. max allowed = 400.
    result = evaluate_constraints("SKU-TEST", "SUP-TEST", 500, db_session)
    assert result["passed"] is False
    assert result["max_feasible_qty"] == 400
    assert any("Storage capacity exceeded" in v for v in result["violations"])

def test_evaluate_constraints_budget_breach(db_session):
    # Budget = 10000, cost = 10. proposed = 2000. total cost = 20000
    result = evaluate_constraints("SKU-TEST", "SUP-TEST", 2000, db_session)
    assert result["passed"] is False
    assert any("Budget exceeded" in v for v in result["violations"])

def test_evaluate_constraints_moq_breach(db_session):
    # MOQ = 100, proposed = 50
    result = evaluate_constraints("SKU-TEST", "SUP-TEST", 50, db_session)
    assert result["passed"] is False
    assert result["max_feasible_qty"] == 0
    assert any("Below minimum order quantity" in v for v in result["violations"])

def test_evaluate_constraints_storage_per_unit_zero(db_session):
    product = db_session.query(DBProduct).filter(DBProduct.id == "SKU-TEST").first()
    product.storage_per_unit = 0.0
    db_session.commit()

    result = evaluate_constraints("SKU-TEST", "SUP-TEST", 200, db_session)
    assert result["passed"] is False
    assert result["max_feasible_qty"] == 0
    assert any("Invalid product storage_per_unit" in v for v in result["violations"])

def test_evaluate_constraints_storage_per_unit_negative(db_session):
    product = db_session.query(DBProduct).filter(DBProduct.id == "SKU-TEST").first()
    product.storage_per_unit = -1.5
    db_session.commit()

    result = evaluate_constraints("SKU-TEST", "SUP-TEST", 200, db_session)
    assert result["passed"] is False
    assert result["max_feasible_qty"] == 0
    assert any("Invalid product storage_per_unit" in v for v in result["violations"])

def test_evaluate_constraints_unit_cost_zero(db_session):
    product = db_session.query(DBProduct).filter(DBProduct.id == "SKU-TEST").first()
    product.unit_cost = 0.0
    db_session.commit()

    result = evaluate_constraints("SKU-TEST", "SUP-TEST", 200, db_session)
    assert result["passed"] is False
    assert result["max_feasible_qty"] == 0
    assert any("Invalid product unit_cost" in v for v in result["violations"])

def test_evaluate_constraints_unit_cost_negative(db_session):
    product = db_session.query(DBProduct).filter(DBProduct.id == "SKU-TEST").first()
    product.unit_cost = -10.0
    db_session.commit()

    result = evaluate_constraints("SKU-TEST", "SUP-TEST", 200, db_session)
    assert result["passed"] is False
    assert result["max_feasible_qty"] == 0
    assert any("Invalid product unit_cost" in v for v in result["violations"])


import pytest
import os
from app.services.purchasing_service import run_purchasing_workflow
from app.db.database import SessionLocal
from app.db.seed import seed_database

@pytest.fixture(autouse=True)
def setup_db():
    # Make sure we have the seeded data
    seed_database()

# Note: These tests require an LLM API Key to run since they use Gemini.
# Ensure MODEL_NAME and GOOGLE_API_KEY are set in the environment.

@pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), reason="Requires GOOGLE_API_KEY")
def test_scenario_1_feasible():
    # Rec=300, Storage/Budget/MOQ OK. Expected: ACCEPT
    res = run_purchasing_workflow("SKU-003", "SUP-002", 300, auto_approve=True)
    assert res["decision"] == "ACCEPT"
    assert res["final_qty"] == 300
    assert res["execution_result"] is not None
    assert res["validation_result"]["status"] == "VALID"

@pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), reason="Requires GOOGLE_API_KEY")
def test_scenario_2_storage_breach():
    # SKU-001 Rec=800. Storage permits 500. Expected: MODIFY to 500.
    res = run_purchasing_workflow("SKU-001", "SUP-001", 800, auto_approve=True)
    assert res["decision"] == "MODIFY"
    # Actually, in the demo, PO 500 returns 300 for SKU-001. So final_qty should be 500, but actual PO is 300.
    assert res["final_qty"] == 500
    assert res["execution_result"] is not None
    assert res["validation_result"]["status"] == "PARTIALLY_VALID"

@pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), reason="Requires GOOGLE_API_KEY")
def test_scenario_3_budget_breach():
    # SKU-002 unit_cost=10 (wait, I set to 10 in seed, let's use 2000 units -> $20000 > $10000 budget). Expected: REJECT/MODIFY.
    res = run_purchasing_workflow("SKU-002", "SUP-002", 2000, auto_approve=True)
    assert res["decision"] in ["REJECT", "MODIFY"]
    if res["decision"] == "MODIFY":
        assert res["final_qty"] <= 1000 # 1000 * 10 = 10000
    
@pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), reason="Requires GOOGLE_API_KEY")
def test_scenario_4_supplier_capacity():
    # SKU-004 Rec=500. Supplier SUP-003 has available 250. Expected: MODIFY or INVESTIGATE
    res = run_purchasing_workflow("SKU-004", "SUP-003", 500, auto_approve=True)
    assert res["decision"] in ["INVESTIGATE", "MODIFY"]
    if res["decision"] == "MODIFY":
        assert res["final_qty"] <= 250

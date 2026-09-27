import pytest
from unittest.mock import patch
from app.db.database import SessionLocal, DBPurchaseOrder
from app.db.seed import seed_database
from app.services.purchasing_service import run_purchasing_workflow
from app.agents.purchasing_agent import check_approval_node

@pytest.fixture(autouse=True)
def setup_db():
    seed_database(force_reseed=True)

def test_check_approval_node_only_flags_modify():
    """Verify that only MODIFY requires execution approval; REJECT/INVESTIGATE are non-executing."""
    for decision, expected_approval in [
        ("ACCEPT", False),
        ("MODIFY", True),
        ("REJECT", False),
        ("INVESTIGATE", False),
    ]:
        state = {
            "decision": decision,
            "agent_trace": []
        }
        res = check_approval_node(state)
        assert res["required_approval"] is expected_approval, (
            f"Decision {decision} should have required_approval={expected_approval}"
        )

def test_reject_cannot_create_purchase_order():
    """Verify that a REJECT decision NEVER creates a purchase order, even if final_qty > 0."""
    db = SessionLocal()
    initial_po_count = db.query(DBPurchaseOrder).count()
    db.close()

    mock_state = {
        "recommendation": {"product_id": "SKU-001", "supplier_id": "SUP-001", "recommended_qty": 800},
        "investigation_data": {},
        "constraint_result": {"passed": False, "max_feasible_qty": 0},
        "decision": "REJECT",
        "final_qty": 500,  # simulate potential LLM misbehavior
        "reasoning_summary": "Storage and budget completely exhausted",
        "important_factors": ["Storage breach"],
        "risks": ["Stockout"],
        "required_approval": False,
        "execution_result": None,
        "validation_result": None,
        "agent_trace": []
    }

    with patch("app.services.purchasing_service.purchasing_graph.invoke", return_value=mock_state):
        # Even with auto_approve=True, REJECT must never execute
        res = run_purchasing_workflow("SKU-001", "SUP-001", 800, auto_approve=True)

    assert res["execution_result"] is None
    assert res["validation_result"] is None

    db = SessionLocal()
    final_po_count = db.query(DBPurchaseOrder).count()
    db.close()
    assert final_po_count == initial_po_count, "No PO should be created on REJECT"

def test_investigate_cannot_create_purchase_order():
    """Verify that an INVESTIGATE decision NEVER creates a purchase order."""
    db = SessionLocal()
    initial_po_count = db.query(DBPurchaseOrder).count()
    db.close()

    mock_state = {
        "recommendation": {"product_id": "SKU-004", "supplier_id": "SUP-003", "recommended_qty": 500},
        "investigation_data": {},
        "constraint_result": {"passed": False, "max_feasible_qty": 250},
        "decision": "INVESTIGATE",
        "final_qty": 0,
        "reasoning_summary": "Supplier capacity insufficient; investigate alternate supplier",
        "important_factors": ["Supplier capacity bottleneck"],
        "risks": ["Delayed fulfillment"],
        "required_approval": False,
        "execution_result": None,
        "validation_result": None,
        "agent_trace": []
    }

    with patch("app.services.purchasing_service.purchasing_graph.invoke", return_value=mock_state):
        res = run_purchasing_workflow("SKU-004", "SUP-003", 500, auto_approve=True)

    assert res["execution_result"] is None
    assert res["validation_result"] is None

    db = SessionLocal()
    final_po_count = db.query(DBPurchaseOrder).count()
    db.close()
    assert final_po_count == initial_po_count, "No PO should be created on INVESTIGATE"

def test_modify_blocked_without_explicit_approval():
    """Verify that MODIFY is blocked from execution when auto_approve=False (default)."""
    db = SessionLocal()
    initial_po_count = db.query(DBPurchaseOrder).count()
    db.close()

    mock_state = {
        "recommendation": {"product_id": "SKU-001", "supplier_id": "SUP-001", "recommended_qty": 800},
        "investigation_data": {},
        "constraint_result": {"passed": False, "max_feasible_qty": 500},
        "decision": "MODIFY",
        "final_qty": 500,
        "reasoning_summary": "Storage limited to 500 units",
        "important_factors": ["Storage capacity 500"],
        "risks": ["Potential understock"],
        "required_approval": True,
        "execution_result": None,
        "validation_result": None,
        "agent_trace": []
    }

    with patch("app.services.purchasing_service.purchasing_graph.invoke", return_value=mock_state):
        # Default auto_approve=False
        res = run_purchasing_workflow("SKU-001", "SUP-001", 800)

    assert res["execution_result"] is None
    assert any("Execution Blocked" in step.get("step", "") for step in res["agent_trace"])

    db = SessionLocal()
    final_po_count = db.query(DBPurchaseOrder).count()
    db.close()
    assert final_po_count == initial_po_count, "No PO should be created when approval is pending"

def test_modify_executes_with_explicit_approval():
    """Verify that MODIFY executes when explicit approval (auto_approve=True) is granted."""
    db = SessionLocal()
    initial_po_count = db.query(DBPurchaseOrder).count()
    db.close()

    mock_state = {
        "recommendation": {"product_id": "SKU-001", "supplier_id": "SUP-001", "recommended_qty": 800},
        "investigation_data": {},
        "constraint_result": {"passed": False, "max_feasible_qty": 500},
        "decision": "MODIFY",
        "final_qty": 500,
        "reasoning_summary": "Storage limited to 500 units",
        "important_factors": ["Storage capacity 500"],
        "risks": [],
        "required_approval": True,
        "execution_result": None,
        "validation_result": None,
        "agent_trace": []
    }

    with patch("app.services.purchasing_service.purchasing_graph.invoke", return_value=mock_state):
        res = run_purchasing_workflow("SKU-001", "SUP-001", 800, auto_approve=True)

    assert res["execution_result"] is not None
    assert res["execution_result"]["id"] is not None

    db = SessionLocal()
    final_po_count = db.query(DBPurchaseOrder).count()
    db.close()
    assert final_po_count == initial_po_count + 1, "Exactly one PO should be created after approval"

def test_accept_executes_without_requiring_approval():
    """Verify that ACCEPT executes automatically without requiring human gate."""
    db = SessionLocal()
    initial_po_count = db.query(DBPurchaseOrder).count()
    db.close()

    mock_state = {
        "recommendation": {"product_id": "SKU-003", "supplier_id": "SUP-002", "recommended_qty": 300},
        "investigation_data": {},
        "constraint_result": {"passed": True, "max_feasible_qty": 300},
        "decision": "ACCEPT",
        "final_qty": 300,
        "reasoning_summary": "All constraints satisfied",
        "important_factors": ["Optimal stock"],
        "risks": [],
        "required_approval": False,
        "execution_result": None,
        "validation_result": None,
        "agent_trace": []
    }

    with patch("app.services.purchasing_service.purchasing_graph.invoke", return_value=mock_state):
        # Even with default auto_approve=False, ACCEPT does not require approval
        res = run_purchasing_workflow("SKU-003", "SUP-002", 300, auto_approve=False)

    assert res["execution_result"] is not None
    assert res["execution_result"]["quantity"] == 300
    assert res["validation_result"]["status"] == "VALID"

    db = SessionLocal()
    final_po_count = db.query(DBPurchaseOrder).count()
    db.close()
    assert final_po_count == initial_po_count + 1, "Exactly one PO should be created for ACCEPT"

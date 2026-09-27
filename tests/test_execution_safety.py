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

def test_llm_unsafe_quantity_clamped_to_modify_and_approval_required():
    """Verify that if LLM returns ACCEPT with final_qty > max_feasible_qty,
    it is clamped to max_feasible_qty, converted to MODIFY, and approval is required."""
    from unittest.mock import MagicMock
    from app.agents.purchasing_agent import reason_and_decide_node, AgentDecision

    mock_llm_output = AgentDecision(
        decision="ACCEPT",
        final_qty=1000,
        reasoning_summary="Everything looks fine",
        important_factors=[],
        risks=[]
    )
    
    state = {
        "recommendation": {"product_id": "SKU-001", "supplier_id": "SUP-001", "recommended_qty": 800},
        "investigation_data": {},
        "constraint_result": {"passed": False, "max_feasible_qty": 500},
        "decision": None,
        "final_qty": None,
        "reasoning_summary": None,
        "important_factors": [],
        "risks": [],
        "required_approval": False,
        "execution_result": None,
        "validation_result": None,
        "agent_trace": []
    }
    
    with patch("app.agents.purchasing_agent.ChatGoogleGenerativeAI") as mock_chat:
        mock_instance = MagicMock()
        mock_chat.return_value = mock_instance
        mock_instance.with_fallbacks.return_value = mock_instance
        mock_instance.with_structured_output.return_value.invoke.return_value = mock_llm_output
        
        # Test reason_and_decide_node
        decided_state = reason_and_decide_node(state)
        assert decided_state["decision"] == "MODIFY"
        assert decided_state["final_qty"] == 500
        assert any("Deterministic Safety Clamp" in step.get("step", "") for step in decided_state["agent_trace"])
        
        # Follow through check_approval_node
        approved_state = check_approval_node(decided_state)
        assert approved_state["required_approval"] is True

    # Also verify full workflow execution blocks without explicit approval
    db = SessionLocal()
    initial_po_count = db.query(DBPurchaseOrder).count()
    db.close()

    with patch("app.agents.purchasing_agent.ChatGoogleGenerativeAI") as mock_chat:
        mock_instance = MagicMock()
        mock_chat.return_value = mock_instance
        mock_instance.with_fallbacks.return_value = mock_instance
        mock_instance.with_structured_output.return_value.invoke.return_value = mock_llm_output
        
        # Default auto_approve=False
        res = run_purchasing_workflow("SKU-001", "SUP-001", 800, auto_approve=False)
        assert res["decision"] == "MODIFY"
        assert res["final_qty"] == 500
        assert res["required_approval"] is True
        assert res["execution_result"] is None

    db = SessionLocal()
    final_po_count = db.query(DBPurchaseOrder).count()
    db.close()
    assert final_po_count == initial_po_count, "Unsafe quantity of 1000 was not executed"

def test_llm_unsafe_quantity_clamped_to_reject_when_max_feasible_zero():
    """Verify that if LLM returns ACCEPT with final_qty > 0 when max_feasible_qty == 0,
    it is forced to REJECT and 0 units, and no PO is created."""
    from unittest.mock import MagicMock
    from app.agents.purchasing_agent import reason_and_decide_node, AgentDecision

    mock_llm_output = AgentDecision(
        decision="ACCEPT",
        final_qty=500,
        reasoning_summary="Attempting to purchase despite zero feasibility",
        important_factors=[],
        risks=[]
    )
    
    state = {
        "recommendation": {"product_id": "SKU-001", "supplier_id": "SUP-001", "recommended_qty": 800},
        "investigation_data": {},
        "constraint_result": {"passed": False, "max_feasible_qty": 0},
        "decision": None,
        "final_qty": None,
        "reasoning_summary": None,
        "important_factors": [],
        "risks": [],
        "required_approval": False,
        "execution_result": None,
        "validation_result": None,
        "agent_trace": []
    }
    
    with patch("app.agents.purchasing_agent.ChatGoogleGenerativeAI") as mock_chat:
        mock_instance = MagicMock()
        mock_chat.return_value = mock_instance
        mock_instance.with_fallbacks.return_value = mock_instance
        mock_instance.with_structured_output.return_value.invoke.return_value = mock_llm_output
        
        decided_state = reason_and_decide_node(state)
        assert decided_state["decision"] == "REJECT"
        assert decided_state["final_qty"] == 0
        assert any("Deterministic Safety Clamp" in step.get("step", "") for step in decided_state["agent_trace"])
        
        approved_state = check_approval_node(decided_state)
        assert approved_state["required_approval"] is False

def test_llm_safe_quantity_preserved():
    """Verify that when final_qty <= max_feasible_qty, the LLM decision and quantity are preserved."""
    from unittest.mock import MagicMock
    from app.agents.purchasing_agent import reason_and_decide_node, AgentDecision

    mock_llm_output = AgentDecision(
        decision="ACCEPT",
        final_qty=300,
        reasoning_summary="Within all constraints",
        important_factors=["Budget OK", "Storage OK"],
        risks=[]
    )
    
    state = {
        "recommendation": {"product_id": "SKU-003", "supplier_id": "SUP-002", "recommended_qty": 300},
        "investigation_data": {},
        "constraint_result": {"passed": True, "max_feasible_qty": 300},
        "decision": None,
        "final_qty": None,
        "reasoning_summary": None,
        "important_factors": [],
        "risks": [],
        "required_approval": False,
        "execution_result": None,
        "validation_result": None,
        "agent_trace": []
    }
    
    with patch("app.agents.purchasing_agent.ChatGoogleGenerativeAI") as mock_chat:
        mock_instance = MagicMock()
        mock_chat.return_value = mock_instance
        mock_instance.with_fallbacks.return_value = mock_instance
        mock_instance.with_structured_output.return_value.invoke.return_value = mock_llm_output
        
        decided_state = reason_and_decide_node(state)
        assert decided_state["decision"] == "ACCEPT"
        assert decided_state["final_qty"] == 300
        assert decided_state["reasoning_summary"] == "Within all constraints"
        assert any("Reason and Decide" in step.get("step", "") for step in decided_state["agent_trace"])

def test_default_model_fallback_chain_order(monkeypatch):
    """Verify default fallback chain order when MODEL_NAME is unset."""
    from app.agents.purchasing_agent import get_model_fallback_chain, DEFAULT_MODEL_FALLBACKS
    monkeypatch.delenv("MODEL_NAME", raising=False)
    
    chain = get_model_fallback_chain()
    assert chain == [
        "gemini-flash-latest",
        "gemini-flash-lite-latest",
        "gemini-3.5-flash-lite",
        "gemma-4-31b-it"
    ]
    assert chain == DEFAULT_MODEL_FALLBACKS

def test_model_fallback_chain_with_custom_model(monkeypatch):
    """Verify that an explicit MODEL_NAME becomes first choice, followed by the fallback chain."""
    from app.agents.purchasing_agent import get_model_fallback_chain
    monkeypatch.setenv("MODEL_NAME", "custom-experimental-model")
    
    chain = get_model_fallback_chain()
    assert chain == [
        "custom-experimental-model",
        "gemini-flash-latest",
        "gemini-flash-lite-latest",
        "gemini-3.5-flash-lite",
        "gemma-4-31b-it"
    ]

def test_model_fallback_chain_avoids_duplicates(monkeypatch):
    """Verify that if explicit model is already in fallback list, it is not duplicated."""
    from app.agents.purchasing_agent import get_model_fallback_chain
    monkeypatch.setenv("MODEL_NAME", "gemini-3.5-flash-lite")
    
    chain = get_model_fallback_chain()
    assert chain[0] == "gemini-3.5-flash-lite"
    assert chain.count("gemini-3.5-flash-lite") == 1
    assert chain == [
        "gemini-3.5-flash-lite",
        "gemini-flash-latest",
        "gemini-flash-lite-latest",
        "gemma-4-31b-it"
    ]

def test_reason_and_decide_node_configures_fallbacks(monkeypatch):
    """Verify that reason_and_decide_node configures primary and fallback LLMs from the chain."""
    from unittest.mock import MagicMock
    from app.agents.purchasing_agent import reason_and_decide_node, AgentDecision
    monkeypatch.delenv("MODEL_NAME", raising=False)

    mock_llm_output = AgentDecision(
        decision="ACCEPT",
        final_qty=100,
        reasoning_summary="OK",
        important_factors=[],
        risks=[]
    )
    state = {
        "recommendation": {"product_id": "SKU-001", "supplier_id": "SUP-001", "recommended_qty": 100},
        "investigation_data": {},
        "constraint_result": {"passed": True, "max_feasible_qty": 100},
        "decision": None,
        "final_qty": None,
        "reasoning_summary": None,
        "important_factors": [],
        "risks": [],
        "required_approval": False,
        "execution_result": None,
        "validation_result": None,
        "agent_trace": []
    }

    created_models = []
    with patch("app.agents.purchasing_agent.ChatGoogleGenerativeAI") as mock_chat:
        def fake_chat(**kwargs):
            mock_inst = MagicMock()
            mock_inst.model_name = kwargs.get("model")
            created_models.append(kwargs.get("model"))
            mock_inst.with_fallbacks.return_value = mock_inst
            mock_inst.with_structured_output.return_value.invoke.return_value = mock_llm_output
            return mock_inst

        mock_chat.side_effect = fake_chat
        reason_and_decide_node(state)

        # Primary + 3 fallbacks should be initialized in order
        assert created_models == [
            "gemini-flash-latest",
            "gemini-flash-lite-latest",
            "gemini-3.5-flash-lite",
            "gemma-4-31b-it"
        ]

def test_approval_execution_binds_to_workflow_recommendation():
    """Verify that approval execution strictly binds to state['recommendation'],
    preventing any divergent/stale UI input values from corrupting the purchase order."""
    from app.services.purchasing_service import execute_purchase_action, get_product_unit_cost

    # Workflow state has analyzed and recommended SKU-001 / SUP-001
    workflow_state = {
        "recommendation": {"product_id": "SKU-001", "supplier_id": "SUP-001", "recommended_qty": 800},
        "investigation_data": {},
        "constraint_result": {"passed": False, "max_feasible_qty": 500},
        "decision": "MODIFY",
        "final_qty": 500,
        "reasoning_summary": "Storage limited to 500 units",
        "important_factors": ["Storage capacity"],
        "risks": [],
        "required_approval": True,
        "execution_result": None,
        "validation_result": None,
        "agent_trace": []
    }

    # Simulate divergent sidebar inputs that were modified after agent ran
    stale_sidebar_prod = "SKU-002"
    stale_sidebar_sup = "SUP-002"

    # The safe approval binding logic:
    rec = workflow_state.get("recommendation", {})
    approved_prod = rec.get("product_id")
    approved_sup = rec.get("supplier_id")
    unit_cost = get_product_unit_cost(approved_prod)

    outcome = execute_purchase_action(
        product_id=approved_prod,
        supplier_id=approved_sup,
        quantity=workflow_state["final_qty"],
        unit_cost=unit_cost
    )

    exec_res = outcome["execution_result"]
    val_res = outcome["validation_result"]

    # Verify that the PO was created for the recommended product/supplier, NOT the stale sidebar inputs
    assert exec_res["product_id"] == "SKU-001"
    assert exec_res["product_id"] != stale_sidebar_prod
    assert exec_res["supplier_id"] == "SUP-001"
    assert exec_res["supplier_id"] != stale_sidebar_sup
    assert exec_res["quantity"] == 300  # SKU-001 demo simulated fulfillment
    assert val_res is not None
    assert val_res["status"] == "PARTIALLY_VALID"

def test_run_purchasing_workflow_closes_session_on_exception():
    """Verify that run_purchasing_workflow closes SessionLocal even if graph invocation fails."""
    from unittest.mock import MagicMock
    from app.db.database import SessionLocal as RealSessionLocal

    real_session = RealSessionLocal()
    close_mock = MagicMock(wraps=real_session.close)
    real_session.close = close_mock

    with patch("app.services.purchasing_service.SessionLocal", return_value=real_session):
        with patch("app.services.purchasing_service.purchasing_graph.invoke", side_effect=RuntimeError("LLM invocation error")):
            with pytest.raises(RuntimeError, match="LLM invocation error"):
                run_purchasing_workflow("SKU-001", "SUP-001", 100)

    assert close_mock.called, "SessionLocal.close() must be called in finally block on workflow exception"

def test_investigate_node_closes_session_on_exception():
    """Verify that investigate_node closes SessionLocal even if a tool query fails."""
    from unittest.mock import MagicMock
    from app.agents.purchasing_agent import investigate_node
    from app.db.database import SessionLocal as RealSessionLocal

    real_session = RealSessionLocal()
    close_mock = MagicMock(wraps=real_session.close)
    real_session.close = close_mock

    state = {
        "recommendation": {"product_id": "SKU-001", "supplier_id": "SUP-001", "recommended_qty": 100},
        "agent_trace": []
    }

    with patch("app.agents.purchasing_agent.SessionLocal", return_value=real_session):
        with patch("app.agents.purchasing_agent.get_inventory", side_effect=RuntimeError("DB query failure")):
            with pytest.raises(RuntimeError, match="DB query failure"):
                investigate_node(state)

    assert close_mock.called, "SessionLocal.close() must be called in finally block on investigate_node exception"

def test_evaluate_constraints_node_closes_session_on_exception():
    """Verify that evaluate_constraints_node closes SessionLocal even if evaluation fails."""
    from unittest.mock import MagicMock
    from app.agents.purchasing_agent import evaluate_constraints_node
    from app.db.database import SessionLocal as RealSessionLocal

    real_session = RealSessionLocal()
    close_mock = MagicMock(wraps=real_session.close)
    real_session.close = close_mock

    state = {
        "recommendation": {"product_id": "SKU-001", "supplier_id": "SUP-001", "recommended_qty": 100},
        "agent_trace": []
    }

    with patch("app.agents.purchasing_agent.SessionLocal", return_value=real_session):
        with patch("app.agents.purchasing_agent.evaluate_constraints", side_effect=RuntimeError("Constraint failure")):
            with pytest.raises(RuntimeError, match="Constraint failure"):
                evaluate_constraints_node(state)

    assert close_mock.called, "SessionLocal.close() must be called in finally block on evaluate_constraints_node exception"

def test_service_level_po_creation_and_validation():
    """Verify that PO creation and validation functions work at the service layer without API dependencies."""
    from app.services.purchasing_service import create_purchase_order_record, validate_purchase_order_record
    
    db = SessionLocal()
    try:
        # Create a PO via service-level function
        po = create_purchase_order_record(
            product_id="SKU-003",
            supplier_id="SUP-002",
            quantity=300,
            unit_cost=15.0,
            db=db
        )
        assert po.id is not None
        assert po.id.startswith("PO-")
        assert po.product_id == "SKU-003"
        assert po.quantity == 300
        assert po.status == "OPEN"

        # Validate the PO via service-level function
        val = validate_purchase_order_record(
            po_id=po.id,
            expected_quantity=300,
            expected_supplier_id="SUP-002",
            db=db
        )
        assert val is not None
        assert val["status"] == "VALID"
        assert val["details"]["diff"] == 0

        # Validate non-existent PO returns None
        missing_val = validate_purchase_order_record(
            po_id="PO-NONEXISTENT",
            expected_quantity=100,
            expected_supplier_id="SUP-001",
            db=db
        )
        assert missing_val is None
    finally:
        db.close()

def test_api_routes_delegate_to_service_functions():
    """Verify that FastAPI route handlers delegate to the service layer properly."""
    from app.api.routes import create_purchase_order, validate_po, POCreate, POValidate
    
    db = SessionLocal()
    try:
        po_req = POCreate(
            product_id="SKU-002",
            supplier_id="SUP-002",
            quantity=150,
            unit_cost=10.0
        )
        created_po = create_purchase_order(po=po_req, db=db)
        assert created_po.id is not None
        assert created_po.quantity == 150

        val_req = POValidate(
            expected_quantity=150,
            expected_supplier_id="SUP-002"
        )
        val_res = validate_po(id=created_po.id, req=val_req, db=db)
        assert val_res["status"] == "VALID"
    finally:
        db.close()

def test_agent_decision_schema_valid_decisions():
    """Verify that all four valid decision values are accepted by AgentDecision."""
    from app.agents.purchasing_agent import AgentDecision
    
    for valid_dec in ["ACCEPT", "MODIFY", "REJECT", "INVESTIGATE"]:
        ad = AgentDecision(
            decision=valid_dec,
            final_qty=100,
            reasoning_summary="Valid decision test",
            important_factors=["Factor A"],
            risks=[]
        )
        assert ad.decision == valid_dec
        assert ad.final_qty == 100

def test_agent_decision_schema_rejects_invalid_decision():
    """Verify that any invalid decision string is rejected with ValidationError."""
    from app.agents.purchasing_agent import AgentDecision
    from pydantic import ValidationError
    
    for bad_dec in ["accept", "HOLD", "APPROVE", "CANCEL", ""]:
        with pytest.raises(ValidationError):
            AgentDecision(
                decision=bad_dec,
                final_qty=100,
                reasoning_summary="Invalid decision test",
                important_factors=[],
                risks=[]
            )

def test_agent_decision_schema_rejects_negative_quantity():
    """Verify that negative final_qty is rejected with ValidationError."""
    from app.agents.purchasing_agent import AgentDecision
    from pydantic import ValidationError
    
    for bad_qty in [-1, -50, -999]:
        with pytest.raises(ValidationError):
            AgentDecision(
                decision="ACCEPT",
                final_qty=bad_qty,
                reasoning_summary="Negative quantity test",
                important_factors=[],
                risks=[]
            )

def test_agent_decision_schema_accepts_zero_quantity():
    """Verify that final_qty=0 is accepted by AgentDecision."""
    from app.agents.purchasing_agent import AgentDecision
    
    ad = AgentDecision(
        decision="REJECT",
        final_qty=0,
        reasoning_summary="Zero quantity test",
        important_factors=[],
        risks=[]
    )
    assert ad.final_qty == 0
    assert ad.decision == "REJECT"






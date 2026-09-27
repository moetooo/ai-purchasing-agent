from app.agents.purchasing_agent import purchasing_graph
from app.db.database import SessionLocal, DBProduct
from app.api.routes import create_purchase_order, POCreate, validate_po, POValidate
from datetime import datetime
from app.agents.state import AgentState
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

def get_product_unit_cost(product_id: str, db: Optional[Session] = None) -> float:
    """Retrieve unit cost for a given product from the database."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        product = db.query(DBProduct).filter(DBProduct.id == product_id).first()
        return product.unit_cost if product else 0.0
    finally:
        if close_db:
            db.close()

def execute_purchase_action(
    product_id: str,
    supplier_id: str,
    quantity: int,
    unit_cost: Optional[float] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """Execute purchase order creation and validation.
    
    Centralized execution function that creates the PO and validates
    it against expected values.
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        if unit_cost is None:
            unit_cost = get_product_unit_cost(product_id, db=db)
        po_req = POCreate(
            product_id=product_id,
            supplier_id=supplier_id,
            quantity=quantity,
            unit_cost=unit_cost
        )
        created_po = create_purchase_order(po_req, db)
        execution_result = {
            "id": created_po.id,
            "product_id": created_po.product_id,
            "supplier_id": created_po.supplier_id,
            "quantity": created_po.quantity,
            "status": created_po.status
        }
        
        val_req = POValidate(
            expected_quantity=quantity,
            expected_supplier_id=supplier_id
        )
        val_res = validate_po(created_po.id, val_req, db)
        
        return {
            "execution_result": execution_result,
            "validation_result": val_res
        }
    finally:
        if close_db:
            db.close()

def run_purchasing_workflow(product_id: str, supplier_id: str, recommended_qty: int, auto_approve: bool = False) -> AgentState:
    db = SessionLocal()
    product = db.query(DBProduct).filter(DBProduct.id == product_id).first()
    unit_cost = product.unit_cost if product else 0.0
    
    initial_state = AgentState(
        recommendation={
            "product_id": product_id,
            "supplier_id": supplier_id,
            "recommended_qty": recommended_qty
        },
        investigation_data={},
        constraint_result={},
        decision=None,
        final_qty=None,
        reasoning_summary=None,
        important_factors=[],
        risks=[],
        required_approval=False,
        execution_result=None,
        validation_result=None,
        agent_trace=[{"step": "Start", "timestamp": datetime.now().isoformat(), "detail": "Workflow initialized"}]
    )
    
    final_state = purchasing_graph.invoke(initial_state)
    
    decision = final_state.get("decision")
    final_qty = final_state.get("final_qty", 0) or 0
    req_approval = final_state.get("required_approval", False)
    
    # REJECT and INVESTIGATE must return without creating a PO
    if decision not in ["ACCEPT", "MODIFY"] or final_qty <= 0:
        db.close()
        return final_state
        
    # MODIFY requires explicit approval before execution
    if decision == "MODIFY" and req_approval and not auto_approve:
        final_state["agent_trace"].append({"step": "Execution Blocked", "timestamp": datetime.now().isoformat(), "detail": "Waiting for human approval."})
        db.close()
        return final_state
        
    final_state["agent_trace"].append({"step": "Action Execution", "timestamp": datetime.now().isoformat(), "detail": f"Executing PO for {final_qty} units."})
        
    try:
        exec_outcome = execute_purchase_action(
            product_id=product_id,
            supplier_id=supplier_id,
            quantity=final_qty,
            unit_cost=unit_cost,
            db=db
        )
        final_state["execution_result"] = exec_outcome["execution_result"]
        final_state["validation_result"] = exec_outcome["validation_result"]
        
        final_state["agent_trace"].append({
            "step": "Validation",
            "timestamp": datetime.now().isoformat(),
            "detail": f"Validation status: {exec_outcome['validation_result']['status']}"
        })
    except Exception as e:
        final_state["execution_result"] = {"error": str(e)}
        final_state["agent_trace"].append({
            "step": "Execution Failed",
            "timestamp": datetime.now().isoformat(),
            "detail": str(e)
        })

    db.close()
    return final_state

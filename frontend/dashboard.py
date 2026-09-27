import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Ensure app is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.purchasing_service import (
    run_purchasing_workflow,
    execute_purchase_action,
    get_product_unit_cost
)
from app.db.seed import seed_database

st.set_page_config(page_title="AI Purchasing Agent", layout="wide")

# Seed database on startup
@st.cache_resource
def init_db():
    seed_database()
    return True

init_db()

st.title("AI Purchasing Agent Dashboard")

scenarios = {
    "Scenario 1: Fully Feasible": {"product": "SKU-003", "supplier": "SUP-002", "qty": 300},
    "Scenario 2: Storage Breach": {"product": "SKU-001", "supplier": "SUP-001", "qty": 800},
    "Scenario 3: Budget Breach": {"product": "SKU-002", "supplier": "SUP-002", "qty": 2000},
    "Scenario 4: Supplier Capacity": {"product": "SKU-004", "supplier": "SUP-003", "qty": 500},
    "Scenario 5: Intentional Partial Execution": {"product": "SKU-001", "supplier": "SUP-001", "qty": 800},
}

with st.sidebar:
    st.header("Purchasing Scenario")
    preset = st.selectbox("Select Scenario Preset", list(scenarios.keys()))
    
    st.markdown("---")
    st.subheader("Custom Inputs")
    prod = st.text_input("Product ID", scenarios[preset]["product"])
    sup = st.text_input("Supplier ID", scenarios[preset]["supplier"])
    qty = st.number_input("Recommended Qty", value=scenarios[preset]["qty"])
    
    run_btn = st.button("Run Purchasing Agent", type="primary")

if 'workflow_state' not in st.session_state:
    st.session_state.workflow_state = None

if run_btn:
    with st.spinner("Agent is investigating and reasoning..."):
        if not os.getenv("GOOGLE_API_KEY"):
            st.sidebar.error("Please set GOOGLE_API_KEY environment variable to use the LangGraph agent.")
        else:
            state = run_purchasing_workflow(prod, sup, int(qty), auto_approve=False)
            st.session_state.workflow_state = state

state = st.session_state.workflow_state

if state:
    st.header("1. Agent Investigation Data")
    inv_data = state.get("investigation_data", {})
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("Inventory")
        st.json(inv_data.get("inventory", {}))
        st.subheader("Demand")
        st.json(inv_data.get("demand", {}))
    with c2:
        st.subheader("Supplier")
        st.json(inv_data.get("supplier", {}))
        st.subheader("Open POs")
        st.json(inv_data.get("open_pos", []))
    with c3:
        st.subheader("Budget")
        st.json(inv_data.get("budget", {}))
        st.subheader("Storage")
        st.json(inv_data.get("storage", {}))
        
    st.header("2. Deterministic Constraints")
    const_res = state.get("constraint_result", {})
    passed = const_res.get("passed", False)
    st.metric("Constraint Engine Result", "PASS" if passed else "FAIL", delta_color="normal")
    st.write(f"**Max Feasible Quantity:** {const_res.get('max_feasible_qty')}")
    if const_res.get("violations"):
        for v in const_res["violations"]:
            st.error(f"Violation: {v}")
            
    st.header("3. Agent Decision")
    decision = state.get("decision", "UNKNOWN")
    color = "green" if decision == "ACCEPT" else "orange" if decision == "MODIFY" else "red" if decision == "REJECT" else "blue"
    st.markdown(f"<h3 style='color: {color};'>Decision: {decision}</h3>", unsafe_allow_html=True)
    
    st.metric("Final Approved Qty", state.get("final_qty", 0))
    
    with st.expander("Agent Reasoning Details"):
        st.write(f"**Summary:** {state.get('reasoning_summary')}")
        st.write("**Important Factors:**")
        for f in state.get('important_factors', []):
            st.write(f"- {f}")
        st.write("**Risks:**")
        for r in state.get('risks', []):
            st.write(f"- {r}")
            
    st.header("4. Human Approval Gate")
    if state.get("decision") == "MODIFY" and state.get("required_approval") and not state.get("execution_result") and state.get("final_qty", 0) > 0:
        st.warning("Human Approval Required for Action Execution due to modifications or constraints.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Approve Execution", type="primary"):
                # Run execution via centralized service
                unit_cost = get_product_unit_cost(prod)
                exec_outcome = execute_purchase_action(
                    product_id=prod,
                    supplier_id=sup,
                    quantity=state["final_qty"],
                    unit_cost=unit_cost
                )
                
                state["execution_result"] = exec_outcome["execution_result"]
                state["validation_result"] = exec_outcome["validation_result"]
                po_id = exec_outcome["execution_result"].get("id", "UNKNOWN")
                state["agent_trace"].append({"step": "Approved & Executed", "detail": f"PO Created: {po_id}"})
                st.rerun()
        with col2:
            if st.button("Reject Execution"):
                state["agent_trace"].append({"step": "Rejected", "detail": "User rejected the execution."})
                st.error("Execution Rejected by User.")
                
    st.header("5. Execution & Validation Result")
    if state.get("execution_result"):
        st.success("Execution Complete")
        st.json(state["execution_result"])
        
        val = state.get("validation_result", {})
        if val.get("status") == "VALID":
            st.success("Validation: VALID")
        elif val.get("status") == "PARTIALLY_VALID":
            st.warning(f"Validation: PARTIALLY_VALID - {val.get('details', {}).get('message')}")
        else:
            st.error(f"Validation: INVALID - {val.get('details', {}).get('message')}")
            
        st.json(val)
        
    st.header("6. Execution Trace")
    with st.expander("View Agent Log Trace"):
        st.table(pd.DataFrame(state.get("agent_trace", [])))

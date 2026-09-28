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
    run_purchasing_workflow_stream,
    execute_purchase_action,
    get_product_unit_cost
)
from app.db.seed import seed_database
from app.rules.constraints import format_inr

st.set_page_config(
    page_title="AI Purchasing Agent | Operations Console",
    page_icon="📦",
    layout="wide"
)

# Seed database on startup
@st.cache_resource
def init_db():
    seed_database()
    return True

init_db()

# Predefined procurement scenarios (Scenarios 1-5 preserved for backend & evaluation suite)
scenarios = {
    "Scenario 1 — Fully Feasible": {
        "product": "SKU-003",
        "supplier": "SUP-002",
        "qty": 300,
        "note": "Fully compliant order: storage, budget (₹10,00,000), supplier capacity, and MOQ all satisfied."
    },
    "Scenario 2 — Storage Breach": {
        "product": "SKU-001",
        "supplier": "SUP-001",
        "qty": 800,
        "note": "Warehouse capacity exceeded: deterministic engine clamps to 500 units; triggers human approval & validation."
    },
    "Scenario 3: Budget Breach": {
        "product": "SKU-002",
        "supplier": "SUP-002",
        "qty": 2000,
        "note": "Total purchase cost (₹20,00,000) exceeds remaining purchasing budget (₹10,00,000)."
    },
    "Scenario 4: Supplier Capacity": {
        "product": "SKU-004",
        "supplier": "SUP-003",
        "qty": 500,
        "note": "Supplier only has 250 units available; triggers quantity modification or investigation."
    },
    "Scenario 5: Intentional Partial Execution": {
        "product": "SKU-001",
        "supplier": "SUP-001",
        "qty": 800,
        "note": "Modified to 500; supplier simulates 300 fulfillment to trigger PARTIALLY_VALID post-check."
    },
}

# The user-facing UI exposes ONLY the two primary evaluator demonstration scenarios
ui_scenario_keys = [
    "Scenario 1 — Fully Feasible",
    "Scenario 2 — Storage Breach"
]

# --- SIDEBAR (Secondary Telemetry & Utility Only) ---
with st.sidebar:
    st.subheader("System Telemetry")
    api_ready = bool(os.getenv("GOOGLE_API_KEY"))
    if api_ready:
        st.success("● LLM Engine: Connected")
    else:
        st.error("● LLM Engine: Missing GOOGLE_API_KEY")

    active_model = os.getenv("MODEL_NAME", "gemini-flash-latest")
    st.caption(f"**Primary Model:** `{active_model}`")
    st.caption("**Fallback Chain:** `gemini-flash-lite-latest` → `gemini-3.5-flash-lite` → `gemma-4-31b-it`")
    st.caption("**Database:** SQLite (`purchasing_agent.db`)")
    st.caption("**Currency:** Indian Rupees (₹)")

    st.divider()
    if st.button("🔄 Reset Workspace", use_container_width=True):
        st.session_state.workflow_state = None
        st.session_state.is_running = False
        st.rerun()

# --- HEADER ---
col_head, col_stat = st.columns([4, 1])
with col_head:
    st.markdown("<h1 style='margin: 0; padding: 0;'>AI Purchasing Agent</h1>", unsafe_allow_html=True)
with col_stat:
    state = st.session_state.get("workflow_state")
    if state and state.get("execution_result"):
        st.markdown("<div style='text-align: right; font-weight: 600; color: #10B981; padding-top: 10px;'>● Order Executed</div>", unsafe_allow_html=True)
    elif state and state.get("decision") == "MODIFY" and state.get("required_approval") and not state.get("user_rejected"):
        st.markdown("<div style='text-align: right; font-weight: 600; color: #F59E0B; padding-top: 10px;'>⚠ Approval Required</div>", unsafe_allow_html=True)
    elif state:
        st.markdown("<div style='text-align: right; font-weight: 600; color: #3B82F6; padding-top: 10px;'>● Evaluated</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align: right; font-weight: 600; color: #10B981; padding-top: 10px;'>● Ready</div>", unsafe_allow_html=True)

st.markdown("<hr style='margin: 8px 0 16px 0; border: 0; border-top: 1px solid rgba(128, 128, 128, 0.25);'>", unsafe_allow_html=True)

# --- PURCHASING WORKSPACE ---
st.subheader("PURCHASING WORKSPACE")

preset_key = st.selectbox(
    "Select a scenario",
    ui_scenario_keys,
    index=0,
    help="Select a procurement scenario to populate parameters and evaluate."
)
selected_scenario = scenarios[preset_key]

# Parameter display / override
c_param1, c_param2, c_param3 = st.columns(3)
with c_param1:
    st.metric("Product ID", selected_scenario["product"])
with c_param2:
    st.metric("Supplier ID", selected_scenario["supplier"])
with c_param3:
    st.metric("Requested Quantity", f"{selected_scenario['qty']:,} units")

st.caption(f"**Scenario Context:** {selected_scenario['note']}")

# Optional custom override expander
with st.expander("⚙ Custom Parameters (Advanced)"):
    custom_toggle = st.checkbox("Override scenario defaults", value=False)
    if custom_toggle:
        c_cust1, c_cust2, c_cust3 = st.columns(3)
        active_prod = c_cust1.text_input("Custom Product ID", value=selected_scenario["product"])
        active_sup = c_cust2.text_input("Custom Supplier ID", value=selected_scenario["supplier"])
        active_qty = int(c_cust3.number_input("Custom Quantity", value=selected_scenario["qty"], step=50))
    else:
        active_prod = selected_scenario["product"]
        active_sup = selected_scenario["supplier"]
        active_qty = selected_scenario["qty"]

if not custom_toggle if 'custom_toggle' in locals() else True:
    active_prod = selected_scenario["product"]
    active_sup = selected_scenario["supplier"]
    active_qty = selected_scenario["qty"]

st.write("")
col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    run_btn = st.button("▶ Run Purchasing Agent", type="primary", use_container_width=True)

st.markdown("<hr style='margin: 16px 0; border: 0; border-top: 1px solid rgba(128, 128, 128, 0.25);'>", unsafe_allow_html=True)

# --- RENDERING HELPER FUNCTIONS ---

def render_system_flow(ph, stage_status):
    """Renders the 6-stage horizontal pipeline progress bar into a Streamlit container/placeholder."""
    with ph.container():
        st.subheader("SYSTEM FLOW")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        
        stages = [
            ("Investigation", stage_status.get("investigation", "○ Ready")),
            ("Constraints", stage_status.get("constraints", "○ Ready")),
            ("Agent Decision", stage_status.get("decision", "○ Ready")),
            ("Approval", stage_status.get("approval", "○ Ready")),
            ("Execution", stage_status.get("execution", "○ Ready")),
            ("Validation", stage_status.get("validation", "○ Ready"))
        ]
        
        cols = [c1, c2, c3, c4, c5, c6]
        for col, (name, badge) in zip(cols, stages):
            col.markdown(f"<div style='text-align: center;'><b>{name}</b><br>{badge}</div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 12px 0; border: 0; border-top: 1px solid rgba(128, 128, 128, 0.15);'>", unsafe_allow_html=True)

def render_investigation_section(ph, state):
    """Renders the investigation metrics row immediately after investigation finishes."""
    rec = state.get("recommendation") or {}
    inv_data = state.get("investigation_data") or {}
    inv_stock = (inv_data.get("inventory") or {}).get("current_stock", 0)
    proj_inv = (inv_data.get("inventory") or {}).get("projected_inventory", inv_stock)
    demand_f = (inv_data.get("demand") or {}).get("forecast_demand", 0)
    budget_avail = (inv_data.get("budget") or {}).get("available_amount", 0.0)
    storage_cap = (inv_data.get("storage") or {}).get("storage_capacity", 0)
    storage_per_unit = (inv_data.get("storage") or {}).get("storage_per_unit", 1.0)
    
    with ph.container():
        col_an_title, col_an_badge = st.columns([3, 1])
        with col_an_title:
            st.subheader("PURCHASE ANALYSIS")
            st.caption(f"**Target:** `{rec.get('product_id')}` · **Supplier:** `{rec.get('supplier_id')}` · **Requested:** `{rec.get('recommended_qty', 0):,} units`")
        with col_an_badge:
            decision = state.get("decision")
            if decision:
                dec_color = "#10B981" if decision == "ACCEPT" else "#F59E0B" if decision == "MODIFY" else "#EF4444" if decision == "REJECT" else "#3B82F6"
                st.markdown(
                    f"<div style='background-color: {dec_color}22; border: 1px solid {dec_color}; border-radius: 6px; padding: 10px; text-align: center; margin-top: 5px;'>"
                    f"<span style='color: {dec_color}; font-weight: 700; font-size: 1.1rem;'>DECISION: {decision}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    "<div style='background-color: #3B82F622; border: 1px solid #3B82F6; border-radius: 6px; padding: 10px; text-align: center; margin-top: 5px;'>"
                    "<span style='color: #3B82F6; font-weight: 600;'>STAGE: INVESTIGATION COMPLETE</span>"
                    "</div>",
                    unsafe_allow_html=True
                )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Current Inventory", f"{inv_stock:,} units", delta=f"{proj_inv:,} projected", delta_color="off")
        m2.metric("Forecast Demand", f"{demand_f:,} units")
        m3.metric("Available Budget (₹)", format_inr(budget_avail))
        m4.metric("Storage Capacity", f"{storage_cap:,} units", delta=f"{storage_per_unit} space/unit", delta_color="off")
        st.write("")

def render_constraints_section(ph, state):
    """Renders deterministic constraint checks immediately after evaluation completes."""
    rec = state.get("recommendation") or {}
    rec_qty = rec.get("recommended_qty", 0)
    const_res = state.get("constraint_result") or {}
    violations = const_res.get("violations") or []
    max_feasible = const_res.get("max_feasible_qty", 0)

    budget_ok = not any("budget" in v.lower() for v in violations)
    storage_ok = not any("storage" in v.lower() for v in violations)
    supplier_ok = not any("supplier capacity" in v.lower() or "supplier only has" in v.lower() for v in violations)
    moq_ok = not any("moq" in v.lower() or "minimum order" in v.lower() for v in violations)

    with ph.container():
        st.markdown("#### Operational Constraints Check")
        cc1, cc2, cc3, cc4, cc5 = st.columns([1, 1, 1, 1, 1.2])
        cc1.markdown(f"**Budget (₹):**<br>{'🟢 PASS' if budget_ok else '🔴 FAIL'}", unsafe_allow_html=True)
        cc2.markdown(f"**Storage:**<br>{'🟢 PASS' if storage_ok else '🔴 FAIL'}", unsafe_allow_html=True)
        cc3.markdown(f"**Supplier Stock:**<br>{'🟢 PASS' if supplier_ok else '🔴 FAIL'}", unsafe_allow_html=True)
        cc4.markdown(f"**MOQ Limit:**<br>{'🟢 PASS' if moq_ok else '🔴 FAIL'}", unsafe_allow_html=True)
        cc5.metric(
            "Max Feasible Qty",
            f"{max_feasible:,} units",
            delta=None if const_res.get("passed") else f"-{rec_qty - max_feasible} constrained",
            delta_color="inverse"
        )

        if violations:
            for v in violations:
                st.error(f"⚠ Violation: {v}")
        if const_res.get("warnings"):
            for w in const_res.get("warnings"):
                st.warning(f"ℹ Warning: {w}")
        st.markdown("<hr style='margin: 12px 0; border: 0; border-top: 1px solid rgba(128, 128, 128, 0.15);'>", unsafe_allow_html=True)

def render_decision_loading(ph):
    """Renders clean operational progress while the LLM is reasoning, hiding downstream info."""
    with ph.container():
        st.markdown("#### Agent Decision & Reasoning")
        st.info("◌ **Analyzing purchasing situation with LLM...** (Evaluating constraints, demand context, and operational risks)")

def render_decision_section(ph, state):
    """Renders the structured decision once LLM reasoning has completed."""
    rec = state.get("recommendation") or {}
    rec_qty = rec.get("recommended_qty", 0)
    const_res = state.get("constraint_result") or {}
    max_feasible = const_res.get("max_feasible_qty", 0)
    final_qty = state.get("final_qty", 0)

    with ph.container():
        col_reas1, col_reas2 = st.columns([2, 1])
        with col_reas1:
            st.markdown("#### Agent Decision & Reasoning")
            st.write(f"**Summary:** {state.get('reasoning_summary')}")
            if state.get("important_factors"):
                st.write("**Key Factors Considered:**")
                for factor in state.get("important_factors", []):
                    st.write(f"• {factor}")
            if state.get("risks"):
                st.write("**Identified Risks:**")
                for risk in state.get("risks", []):
                    st.write(f"• {risk}")

        with col_reas2:
            st.markdown("#### Quantity Breakdown")
            st.metric("1. Requested Quantity", f"{rec_qty:,} units")
            st.metric("2. Deterministic Feasible Limit", f"{max_feasible:,} units")
            st.metric("3. Final Approved Quantity", f"{final_qty:,} units")

def render_approval_section(ph, state):
    """Renders the human approval gate when MODIFY is triggered."""
    rec = state.get("recommendation") or {}
    rec_qty = rec.get("recommended_qty", 0)
    final_qty = state.get("final_qty", 0)
    prod_id = rec.get("product_id", "unknown")
    sup_id = rec.get("supplier_id", "unknown")

    # Derive unique, deterministic widget keys from stable workflow state
    key_suffix = f"{prod_id}_{sup_id}_{final_qty}"
    approve_key = f"btn_approve_exec_{key_suffix}"
    reject_key = f"btn_reject_exec_{key_suffix}"

    with ph.container():
        st.markdown("<hr style='margin: 12px 0; border: 0; border-top: 1px solid rgba(128, 128, 128, 0.15);'>", unsafe_allow_html=True)
        st.warning("⚠ **HUMAN APPROVAL REQUIRED**: The agent recommends modifying the order quantity due to hard operational constraints.")

        ap_c1, ap_c2 = st.columns([3, 1])
        with ap_c1:
            st.write(f"The order has been clamped from **{rec_qty:,} units** down to **{final_qty:,} units** to respect operational constraints.")
            st.write(f"Reason: *{state.get('reasoning_summary')}*")
        with ap_c2:
            st.write("")
            if st.button("✔ Approve & Execute", type="primary", use_container_width=True, key=approve_key):
                approved_prod = rec.get("product_id")
                approved_sup = rec.get("supplier_id")
                unit_cost = get_product_unit_cost(approved_prod)
                exec_outcome = execute_purchase_action(
                    product_id=approved_prod,
                    supplier_id=approved_sup,
                    quantity=state["final_qty"],
                    unit_cost=unit_cost
                )
                state["execution_result"] = exec_outcome["execution_result"]
                state["validation_result"] = exec_outcome["validation_result"]
                po_id = exec_outcome["execution_result"].get("id", "UNKNOWN")
                state["agent_trace"].append({"step": "Approved & Executed", "detail": f"PO Created: {po_id}"})
                st.session_state.workflow_state = state
                st.rerun()

            if st.button("✖ Reject Execution", use_container_width=True, key=reject_key):
                state["agent_trace"].append({"step": "Rejected", "detail": "User rejected the execution."})
                state["user_rejected"] = True
                st.session_state.workflow_state = state
                st.rerun()

def render_execution_and_validation(ph, state):
    """Renders the PO execution record and post-action validation comparisons."""
    exec_res = state.get("execution_result") or {}
    val_res = state.get("validation_result") or {}
    val_status = val_res.get("status", "UNKNOWN")
    val_details = val_res.get("details") or {}

    final_qty = state.get("final_qty", 0)
    exp_qty = val_details.get("expected_qty", final_qty)
    act_qty = val_details.get("actual_qty", exec_res.get("quantity", 0))
    diff_qty = val_details.get("diff", exp_qty - act_qty)
    po_id = exec_res.get("id", "UNKNOWN")

    with ph.container():
        st.markdown("<hr style='margin: 12px 0; border: 0; border-top: 1px solid rgba(128, 128, 128, 0.15);'>", unsafe_allow_html=True)
        st.subheader("EXECUTION & POST-ACTION VALIDATION")

        card_ex1, card_ex2 = st.columns(2)
        with card_ex1:
            st.markdown(
                f"<div style='border: 1px solid #10B981; border-radius: 6px; padding: 12px; background-color: #10B98111;'>"
                f"<span style='color: #10B981; font-weight: 700;'>EXECUTION STATUS: CREATED</span><br>"
                f"<b>Purchase Order:</b> <code>{po_id}</code> &nbsp;&nbsp;|&nbsp;&nbsp; <b>Status:</b> <code>{exec_res.get('status')}</code><br>"
                f"<b>Product:</b> <code>{exec_res.get('product_id')}</code> &nbsp;&nbsp;|&nbsp;&nbsp; <b>Supplier:</b> <code>{exec_res.get('supplier_id')}</code>"
                f"</div>",
                unsafe_allow_html=True
            )
        with card_ex2:
            if val_status == "VALID":
                v_border = "#10B981"
                v_msg = "VALID — Purchase order executed exactly as intended."
            elif val_status == "PARTIALLY_VALID":
                v_border = "#F59E0B"
                v_msg = f"PARTIALLY VALID — {val_details.get('message', 'Shortfall detected.')}"
            else:
                v_border = "#EF4444"
                v_msg = f"INVALID — {val_details.get('message', 'Validation error.')}"

            st.markdown(
                f"<div style='border: 1px solid {v_border}; border-radius: 6px; padding: 12px; background-color: {v_border}11;'>"
                f"<span style='color: {v_border}; font-weight: 700;'>VALIDATION RESULT: {val_status}</span><br>"
                f"{v_msg}"
                f"</div>",
                unsafe_allow_html=True
            )

        st.write("")
        vq1, vq2, vq3 = st.columns(3)
        vq1.metric("Expected Order Qty", f"{exp_qty:,} units")
        vq2.metric("Actual Fulfilled Qty", f"{act_qty:,} units")
        if diff_qty > 0:
            vq3.metric("Fulfillment Shortfall", f"{diff_qty:,} units", delta=f"-{diff_qty} shortfall", delta_color="inverse")
        else:
            vq3.metric("Fulfillment Shortfall", "0 units", delta="Complete Match", delta_color="normal")

def render_trace_section(ph, state):
    """Renders the chronological trace and raw JSON tabs in an expander."""
    trace_data = state.get("agent_trace") or []
    with ph.container():
        st.markdown("<hr style='margin: 12px 0; border: 0; border-top: 1px solid rgba(128, 128, 128, 0.15);'>", unsafe_allow_html=True)
        with st.expander("🔍 Operational Trace & Technical Audit Log"):
            st.caption("Chronological execution trace recorded by the LangGraph agent:")
            if trace_data:
                st.table(pd.DataFrame(trace_data))

            st.caption("Raw Technical Payloads:")
            tab_raw1, tab_raw2, tab_raw3 = st.tabs(["Investigation Data", "Execution Result", "Validation Result"])
            with tab_raw1:
                st.json(state.get("investigation_data") or {})
            with tab_raw2:
                st.json(state.get("execution_result") or {})
            with tab_raw3:
                st.json(state.get("validation_result") or {})

# --- MAIN PROGRESSIVE WORKFLOW CONTROLLER ---

# Dynamic Placeholders
flow_ph = st.empty()
analysis_ph = st.empty()
constraints_ph = st.empty()
decision_ph = st.empty()
approval_ph = st.empty()
execution_ph = st.empty()
trace_ph = st.empty()

if run_btn:
    if not os.getenv("GOOGLE_API_KEY"):
        st.error("Please configure the `GOOGLE_API_KEY` environment variable to run the purchasing agent.")
    else:
        st.session_state.workflow_state = None
        
        flow_status = {
            "investigation": "<span style='color:#3B82F6;'>◌ Running</span>",
            "constraints": "○ Pending",
            "decision": "○ Pending",
            "approval": "○ Pending",
            "execution": "○ Pending",
            "validation": "○ Pending"
        }
        render_system_flow(flow_ph, flow_status)

        latest_state = None
        for stage, current_state in run_purchasing_workflow_stream(active_prod, active_sup, int(active_qty), auto_approve=False):
            latest_state = current_state

            if stage == "investigate":
                # Stage 1 Complete!
                flow_status["investigation"] = "<span style='color:#10B981;'>✓ Done</span>"
                flow_status["constraints"] = "<span style='color:#3B82F6;'>◌ Running</span>"
                render_system_flow(flow_ph, flow_status)
                render_investigation_section(analysis_ph, current_state)

            elif stage == "evaluate":
                # Stage 2 Complete!
                const_ok = (current_state.get("constraint_result") or {}).get("passed", False)
                const_badge = "<span style='color:#10B981;'>✓ Pass</span>" if const_ok else "<span style='color:#EF4444;'>⚠ Violations</span>"
                flow_status["constraints"] = const_badge
                flow_status["decision"] = "<span style='color:#3B82F6;'>◌ Running</span>"
                render_system_flow(flow_ph, flow_status)
                render_investigation_section(analysis_ph, current_state)
                render_constraints_section(constraints_ph, current_state)
                render_decision_loading(decision_ph)

            elif stage == "decide":
                # Stage 3 Complete!
                dec = current_state.get("decision", "UNKNOWN")
                dec_color = "#10B981" if dec == "ACCEPT" else "#F59E0B" if dec == "MODIFY" else "#EF4444" if dec == "REJECT" else "#3B82F6"
                flow_status["decision"] = f"<span style='color:{dec_color};font-weight:600;'>{dec}</span>"
                flow_status["approval"] = "<span style='color:#3B82F6;'>◌ Checking</span>"
                render_system_flow(flow_ph, flow_status)
                render_investigation_section(analysis_ph, current_state)
                render_constraints_section(constraints_ph, current_state)
                render_decision_section(decision_ph, current_state)

            elif stage in ["approval", "blocked"]:
                # Stage 4 Complete!
                req_app = current_state.get("required_approval", False)
                dec = current_state.get("decision", "UNKNOWN")
                if not req_app:
                    flow_status["approval"] = "<span style='color:#6B7280;'>— Not Req.</span>"
                    flow_status["execution"] = "<span style='color:#3B82F6;'>◌ Executing</span>" if dec == "ACCEPT" else "<span style='color:#6B7280;'>— Blocked</span>"
                else:
                    flow_status["approval"] = "<span style='color:#F59E0B;font-weight:600;'>⚠ Pending</span>"
                    flow_status["execution"] = "<span style='color:#6B7280;'>— Awaiting</span>"

                render_system_flow(flow_ph, flow_status)
                render_investigation_section(analysis_ph, current_state)
                render_constraints_section(constraints_ph, current_state)
                render_decision_section(decision_ph, current_state)

                if stage == "blocked" and req_app and dec == "MODIFY" and not current_state.get("execution_result"):
                    render_approval_section(approval_ph, current_state)

            elif stage == "execution":
                # Stage 5 Complete!
                flow_status["execution"] = "<span style='color:#10B981;'>✓ Created</span>"
                flow_status["validation"] = "<span style='color:#3B82F6;'>◌ Validating</span>"
                render_system_flow(flow_ph, flow_status)

            elif stage == "validation":
                # Stage 6 Complete!
                val_status = (current_state.get("validation_result") or {}).get("status")
                if val_status == "VALID":
                    val_badge = "<span style='color:#10B981;'>✓ Valid</span>"
                elif val_status == "PARTIALLY_VALID":
                    val_badge = "<span style='color:#F59E0B;'>⚠ Partial</span>"
                elif val_status == "INVALID":
                    val_badge = "<span style='color:#EF4444;'>✖ Invalid</span>"
                else:
                    val_badge = "<span style='color:#6B7280;'>— Pending</span>"

                flow_status["validation"] = val_badge
                render_system_flow(flow_ph, flow_status)
                render_execution_and_validation(execution_ph, current_state)
                render_trace_section(trace_ph, current_state)

        st.session_state.workflow_state = latest_state

# --- STATIC RENDER ON RERUN / RESUME ---
elif st.session_state.get("workflow_state"):
    state = st.session_state.workflow_state
    dec = state.get("decision", "UNKNOWN")
    dec_color = "#10B981" if dec == "ACCEPT" else "#F59E0B" if dec == "MODIFY" else "#EF4444" if dec == "REJECT" else "#3B82F6"
    
    # Compute static flow status badges
    const_ok = (state.get("constraint_result") or {}).get("passed", False)
    const_badge = "<span style='color:#10B981;'>✓ Pass</span>" if const_ok else "<span style='color:#EF4444;'>⚠ Violations</span>"
    
    req_app = state.get("required_approval", False)
    if not req_app:
        app_badge = "<span style='color:#6B7280;'>— Not Req.</span>"
    elif state.get("execution_result"):
        app_badge = "<span style='color:#10B981;'>✓ Approved</span>"
    elif state.get("user_rejected"):
        app_badge = "<span style='color:#EF4444;'>✖ Rejected</span>"
    else:
        app_badge = "<span style='color:#F59E0B;font-weight:600;'>⚠ Pending</span>"

    if state.get("execution_result"):
        exec_badge = "<span style='color:#10B981;'>✓ Created</span>"
    elif dec in ["REJECT", "INVESTIGATE"] or state.get("user_rejected"):
        exec_badge = "<span style='color:#6B7280;'>— Blocked</span>"
    else:
        exec_badge = "<span style='color:#F59E0B;'>⏳ Awaiting</span>"

    val_status = (state.get("validation_result") or {}).get("status")
    if val_status == "VALID":
        val_badge = "<span style='color:#10B981;'>✓ Valid</span>"
    elif val_status == "PARTIALLY_VALID":
        val_badge = "<span style='color:#F59E0B;'>⚠ Partial</span>"
    elif val_status == "INVALID":
        val_badge = "<span style='color:#EF4444;'>✖ Invalid</span>"
    else:
        val_badge = "<span style='color:#6B7280;'>— Pending</span>"

    flow_status = {
        "investigation": "<span style='color:#10B981;'>✓ Done</span>",
        "constraints": const_badge,
        "decision": f"<span style='color:{dec_color};font-weight:600;'>{dec}</span>",
        "approval": app_badge,
        "execution": exec_badge,
        "validation": val_badge
    }
    render_system_flow(flow_ph, flow_status)
    render_investigation_section(analysis_ph, state)
    render_constraints_section(constraints_ph, state)
    render_decision_section(decision_ph, state)

    # Human approval gate (only if pending)
    needs_approval = (
        dec == "MODIFY" and
        req_app and
        not state.get("execution_result") and
        state.get("final_qty", 0) > 0 and
        not state.get("user_rejected")
    )
    if needs_approval:
        render_approval_section(approval_ph, state)

    if state.get("user_rejected"):
        with approval_ph.container():
            st.error("Execution Rejected: User declined the purchase action. No purchase order was created.")

    # Execution & Validation (only after execution)
    if state.get("execution_result"):
        render_execution_and_validation(execution_ph, state)

    render_trace_section(trace_ph, state)

else:
    # Initial clean screen
    flow_status = {
        "investigation": "○ Ready",
        "constraints": "○ Ready",
        "decision": "○ Ready",
        "approval": "○ Ready",
        "execution": "○ Ready",
        "validation": "○ Ready"
    }
    render_system_flow(flow_ph, flow_status)
    with analysis_ph.container():
        st.caption("Select a scenario above and click **Run Purchasing Agent** to begin the operational evaluation.")

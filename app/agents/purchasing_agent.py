from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.prompts import SYSTEM_PROMPT
from app.db.database import SessionLocal
from app.tools.inventory import get_inventory
from app.tools.demand import get_demand
from app.tools.suppliers import get_supplier_info
from app.tools.purchase_orders import get_open_purchase_orders
from app.tools.budget import get_budget
from app.tools.storage import get_storage_capacity
from app.rules.constraints import evaluate_constraints
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
import json
import os
from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime

class AgentDecision(BaseModel):
    decision: Literal["ACCEPT", "MODIFY", "REJECT", "INVESTIGATE"] = Field(
        description="One of ACCEPT, MODIFY, REJECT, INVESTIGATE"
    )
    final_qty: int = Field(ge=0, description="The final approved quantity (must be >= 0)")
    reasoning_summary: str = Field(description="Brief explanation of why this decision was made")
    important_factors: List[str] = Field(description="Key data points driving the decision")
    risks: List[str] = Field(description="Potential issues with this decision")

def investigate_node(state: AgentState):
    db = SessionLocal()
    try:
        rec = state['recommendation']
        product_id = rec['product_id']
        supplier_id = rec['supplier_id']
        
        inv_data = {
            "inventory": get_inventory(product_id, db),
            "demand": get_demand(product_id, db),
            "supplier": get_supplier_info(supplier_id, db),
            "open_pos": get_open_purchase_orders(product_id, db),
            "budget": get_budget(db),
            "storage": get_storage_capacity(product_id, db)
        }
    finally:
        db.close()
    
    state["investigation_data"] = inv_data
    state["agent_trace"].append({"step": "Investigate", "timestamp": datetime.now().isoformat(), "detail": "Gathered data from tools."})
    return state

def evaluate_constraints_node(state: AgentState):
    db = SessionLocal()
    try:
        rec = state['recommendation']
        res = evaluate_constraints(rec['product_id'], rec['supplier_id'], rec['recommended_qty'], db)
    finally:
        db.close()
    
    state["constraint_result"] = res
    state["agent_trace"].append({"step": "Evaluate Constraints", "timestamp": datetime.now().isoformat(), "detail": f"Constraints passed: {res['passed']}. Max feasible: {res['max_feasible_qty']}"})
    return state

DEFAULT_MODEL_FALLBACKS = [
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
    "gemma-4-31b-it",
]

def get_model_fallback_chain(configured_model: str | None = None) -> list[str]:
    """Returns the ordered list of model names to attempt, without duplicates.
    
    If configured_model (or os.getenv('MODEL_NAME')) is provided, it is placed
    first. Remaining default fallbacks follow in their defined order, omitting
    any duplicate of the first-choice model.
    """
    first_choice = configured_model or os.getenv("MODEL_NAME") or DEFAULT_MODEL_FALLBACKS[0]
    chain = [first_choice]
    for model in DEFAULT_MODEL_FALLBACKS:
        if model not in chain:
            chain.append(model)
    return chain

def reason_and_decide_node(state: AgentState):
    model_chain = get_model_fallback_chain()
    primary_llm = ChatGoogleGenerativeAI(model=model_chain[0], temperature=0)
    fallback_llms = [
        ChatGoogleGenerativeAI(model=m, temperature=0)
        for m in model_chain[1:]
    ]
    
    llm = primary_llm.with_fallbacks(fallback_llms) if fallback_llms else primary_llm
    llm_with_structured_output = llm.with_structured_output(AgentDecision)
    
    content = f"""
    Recommendation: {json.dumps(state['recommendation'])}
    Investigation Data: {json.dumps(state['investigation_data'])}
    Constraint Engine Result: {json.dumps(state['constraint_result'])}
    """
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=content)
    ]
    
    response = llm_with_structured_output.invoke(messages)
    
    max_feasible_qty = state.get("constraint_result", {}).get("max_feasible_qty", 0)
    
    state["reasoning_summary"] = response.reasoning_summary
    state["important_factors"] = response.important_factors
    state["risks"] = response.risks
    
    if response.final_qty <= max_feasible_qty:
        state["decision"] = response.decision
        state["final_qty"] = response.final_qty
        state["agent_trace"].append({
            "step": "Reason and Decide",
            "timestamp": datetime.now().isoformat(),
            "detail": f"Decision: {response.decision}, Qty: {response.final_qty}"
        })
    else:
        if max_feasible_qty > 0:
            state["decision"] = "MODIFY"
            state["final_qty"] = max_feasible_qty
            state["agent_trace"].append({
                "step": "Deterministic Safety Clamp",
                "timestamp": datetime.now().isoformat(),
                "detail": f"LLM proposed unsafe quantity {response.final_qty}. Python constrained to max feasible {max_feasible_qty}."
            })
        else:
            state["decision"] = "REJECT"
            state["final_qty"] = 0
            state["agent_trace"].append({
                "step": "Deterministic Safety Clamp",
                "timestamp": datetime.now().isoformat(),
                "detail": f"LLM proposed quantity {response.final_qty}, but no feasible quantity exists (max_feasible_qty=0). Decision forced to REJECT."
            })
            
    return state

def check_approval_node(state: AgentState):
    decision = state['decision']
    
    # Only MODIFY requires human execution approval.
    # ACCEPT does not require approval; REJECT and INVESTIGATE are non-executing outcomes.
    req_approval = (decision == "MODIFY")
        
    state["required_approval"] = req_approval
    state["agent_trace"].append({"step": "Check Approval", "timestamp": datetime.now().isoformat(), "detail": f"Approval required: {req_approval}"})
    return state

def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("investigate", investigate_node)
    builder.add_node("evaluate", evaluate_constraints_node)
    builder.add_node("decide", reason_and_decide_node)
    builder.add_node("approval", check_approval_node)
    
    builder.set_entry_point("investigate")
    builder.add_edge("investigate", "evaluate")
    builder.add_edge("evaluate", "decide")
    builder.add_edge("decide", "approval")
    builder.add_edge("approval", END)
    
    return builder.compile()

purchasing_graph = build_graph()

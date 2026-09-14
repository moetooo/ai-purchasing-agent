from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    recommendation: Dict[str, Any]
    investigation_data: Dict[str, Any]
    constraint_result: Dict[str, Any]
    decision: Optional[str]
    final_qty: Optional[int]
    reasoning_summary: Optional[str]
    important_factors: List[str]
    risks: List[str]
    required_approval: bool
    execution_result: Optional[Dict[str, Any]]
    validation_result: Optional[Dict[str, Any]]
    agent_trace: List[Dict[str, Any]]

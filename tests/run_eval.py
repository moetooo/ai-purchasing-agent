import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()

from app.db.seed import seed_database
from app.services.purchasing_service import run_purchasing_workflow

def run_evaluation():
    print("Seeding database...")
    seed_database()
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY environment variable is missing. Cannot run LLM evaluation.")
        return

    scenarios = [
        {
            "id": "SC-01",
            "name": "Fully Feasible",
            "product_id": "SKU-003",
            "supplier_id": "SUP-002",
            "qty": 300,
            "expected_decision": "ACCEPT"
        },
        {
            "id": "SC-02",
            "name": "Storage Constraint",
            "product_id": "SKU-001",
            "supplier_id": "SUP-001",
            "qty": 800,
            "expected_decision": ["MODIFY", "REJECT"]
        },
        {
            "id": "SC-03",
            "name": "Budget Constraint",
            "product_id": "SKU-002",
            "supplier_id": "SUP-002",
            "qty": 2000,
            "expected_decision": ["REJECT", "MODIFY"]
        },
        {
            "id": "SC-04",
            "name": "Supplier Capacity",
            "product_id": "SKU-004",
            "supplier_id": "SUP-003",
            "qty": 500,
            "expected_decision": ["INVESTIGATE", "MODIFY"]
        },
        {
            "id": "SC-05",
            "name": "Partial Execution Demo",
            "product_id": "SKU-001",
            "supplier_id": "SUP-001",
            "qty": 800,
            "expected_decision": ["MODIFY"],
            "expected_validation": "PARTIALLY_VALID"
        }
    ]

    results = []
    
    print("\nRunning Evaluation Scenarios...")
    print("-" * 60)
    
    for s in scenarios:
        seed_database(force_reseed=True) # Ensure clean state for each scenario
        res = run_purchasing_workflow(s["product_id"], s["supplier_id"], s["qty"], auto_approve=True)
        decision = res["decision"]
        raw_final_qty = res.get("final_qty")
        final_qty = raw_final_qty if raw_final_qty is not None else 0

        constraint_result = res.get("constraint_result") or {}
        max_feasible_qty = constraint_result.get("max_feasible_qty", 0)

        validation = res.get("validation_result", {}).get("status", "N/A") if res.get("validation_result") else "N/A"
        
        passed_decision = decision == s["expected_decision"] or (isinstance(s["expected_decision"], list) and decision in s["expected_decision"])
        
        # Constraint compliance: selected quantity must respect deterministic feasibility limit
        passed_constraint = (0 <= final_qty <= max_feasible_qty)
        
        passed_val = True
        if "expected_validation" in s:
            passed_val = validation == s["expected_validation"]
            
        status = "PASS" if passed_decision and passed_constraint and passed_val else "FAIL"
        
        val_str = f" [Validation: {validation}]" if "expected_validation" in s else ""
        qty_str = f" [Qty: {final_qty} / Max Feasible: {max_feasible_qty}]"
        print(f"{s['name']:<30} : {status} [Decision: {decision}]{qty_str}{val_str}")
        print(f"Reason: {res.get('reasoning_summary')}")
        
        results.append({
            "scenario": s["id"],
            "passed_decision": passed_decision,
            "passed_constraint": passed_constraint,
            "passed_validation": passed_val
        })
        
    print("-" * 60)
    decision_accuracy = sum(1 for r in results if r["passed_decision"]) / len(results)
    constraint_compliance = sum(1 for r in results if r["passed_constraint"]) / len(results)
    validation_accuracy = sum(1 for r in results if r["passed_validation"]) / len(results)
    
    print(f"Decision Accuracy:     {sum(1 for r in results if r['passed_decision'])}/{len(results)} ({decision_accuracy*100:.0f}%)")
    print(f"Constraint Compliance: {sum(1 for r in results if r['passed_constraint'])}/{len(results)} ({constraint_compliance*100:.0f}%)")
    print(f"Validation Accuracy:   {sum(1 for r in results if r['passed_validation'])}/{len(results)} ({validation_accuracy*100:.0f}%)")

if __name__ == "__main__":
    run_evaluation()

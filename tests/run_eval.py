import os
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
            "expected_decision": "MODIFY"
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
            "expected_decision": "MODIFY",
            "expected_validation": "PARTIALLY_VALID"
        }
    ]

    results = []
    
    print("\nRunning Evaluation Scenarios...")
    print("-" * 60)
    
    for s in scenarios:
        res = run_purchasing_workflow(s["product_id"], s["supplier_id"], s["qty"], auto_approve=True)
        decision = res["decision"]
        validation = res.get("validation_result", {}).get("status", "N/A") if res.get("validation_result") else "N/A"
        
        passed_decision = decision == s["expected_decision"] or (isinstance(s["expected_decision"], list) and decision in s["expected_decision"])
        
        passed_val = True
        if "expected_validation" in s:
            passed_val = validation == s["expected_validation"]
            
        status = "PASS" if passed_decision and passed_val else "FAIL"
        
        val_str = f" [Validation: {validation}]" if "expected_validation" in s else ""
        print(f"{s['name']:<30} : {status} [Decision: {decision}]{val_str}")
        
        results.append({
            "scenario": s["id"],
            "passed_decision": passed_decision,
            "passed_validation": passed_val
        })
        
    print("-" * 60)
    decision_accuracy = sum(1 for r in results if r["passed_decision"]) / len(results)
    validation_accuracy = sum(1 for r in results if r["passed_validation"]) / len(results)
    
    print(f"Decision Accuracy: {sum(1 for r in results if r['passed_decision'])}/{len(results)} ({decision_accuracy*100:.0f}%)")
    print(f"Constraint Compliance: {sum(1 for r in results if r['passed_decision'])}/{len(results)} ({decision_accuracy*100:.0f}%)")
    print(f"Validation Accuracy: {sum(1 for r in results if r['passed_validation'])}/{len(results)} ({validation_accuracy*100:.0f}%)")

if __name__ == "__main__":
    run_evaluation()

from sqlalchemy.orm import Session
from app.db.database import DBProduct, DBInventory, DBSupplier, DBPurchaseOrder, DBBudget, DBDemand
from typing import Dict, List, Any

def format_inr(amount: float | int | None) -> str:
    """Format numeric value in Indian Rupees (INR) using Indian numbering system."""
    if amount is None:
        return "₹0"
    is_negative = amount < 0
    amount = abs(amount)
    int_part = int(round(amount))
    s = str(int_part)
    if len(s) <= 3:
        formatted = s
    else:
        last3 = s[-3:]
        rest = s[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        formatted = ",".join(groups) + "," + last3
    prefix = "-₹" if is_negative else "₹"
    return f"{prefix}{formatted}"

def evaluate_constraints(product_id: str, supplier_id: str, proposed_qty: int, db_session: Session) -> Dict[str, Any]:
    product = db_session.query(DBProduct).filter(DBProduct.id == product_id).first()
    supplier = db_session.query(DBSupplier).filter(DBSupplier.id == supplier_id).first()
    inventory = db_session.query(DBInventory).filter(DBInventory.product_id == product_id).first()
    demand = db_session.query(DBDemand).filter(DBDemand.product_id == product_id).first()
    budget = db_session.query(DBBudget).first()
    
    open_pos = db_session.query(DBPurchaseOrder).filter(
        DBPurchaseOrder.product_id == product_id,
        DBPurchaseOrder.status == 'OPEN'
    ).all()
    
    if not product or not supplier or not inventory or not budget:
        return {
            "passed": False,
            "max_feasible_qty": 0,
            "violations": ["Missing critical data (Product, Supplier, Inventory, or Budget)."],
            "warnings": [],
            "metrics": {}
        }

    invalid_data_violations = []
    if product.storage_per_unit is None or product.storage_per_unit <= 0:
        invalid_data_violations.append(
            f"Invalid product storage_per_unit: {product.storage_per_unit}. Must be greater than 0."
        )
    if product.unit_cost is None or product.unit_cost <= 0:
        invalid_data_violations.append(
            f"Invalid product unit_cost: {product.unit_cost}. Must be greater than 0."
        )

    if invalid_data_violations:
        return {
            "passed": False,
            "max_feasible_qty": 0,
            "violations": invalid_data_violations,
            "warnings": [],
            "metrics": {}
        }
    
    open_incoming_qty = sum(po.quantity for po in open_pos)
    available_inventory = inventory.current_stock + open_incoming_qty
    projected_inventory = available_inventory + proposed_qty
    required_storage = projected_inventory * product.storage_per_unit
    total_cost = proposed_qty * product.unit_cost
    
    storage_pass = required_storage <= inventory.storage_capacity
    max_qty_allowed_by_storage = int((inventory.storage_capacity / product.storage_per_unit) - available_inventory)
    if max_qty_allowed_by_storage < 0:
        max_qty_allowed_by_storage = 0
        
    budget_pass = total_cost <= budget.available_amount
    max_qty_allowed_by_budget = int(budget.available_amount / product.unit_cost)
    
    moq_pass = proposed_qty >= supplier.minimum_order_quantity
    supplier_cap_pass = proposed_qty <= supplier.available_quantity
    
    forecast_demand = demand.forecast_demand if demand else 0
    demand_justified = proposed_qty <= (forecast_demand * 1.5) if forecast_demand > 0 else False
    
    violations = []
    warnings = []
    
    max_feasible_qty = proposed_qty
    
    if not storage_pass:
        violations.append(f"Storage capacity exceeded. Requires {required_storage} but capacity is {inventory.storage_capacity}.")
        max_feasible_qty = min(max_feasible_qty, max_qty_allowed_by_storage)
    
    if not budget_pass:
        violations.append(f"Budget exceeded. Total cost {format_inr(total_cost)} > Available budget {format_inr(budget.available_amount)}.")
        max_feasible_qty = min(max_feasible_qty, max_qty_allowed_by_budget)
        
    if not supplier_cap_pass:
        violations.append(f"Supplier capacity exceeded. Supplier only has {supplier.available_quantity} units.")
        max_feasible_qty = min(max_feasible_qty, supplier.available_quantity)
        
    if not moq_pass:
        violations.append(f"Below minimum order quantity. MOQ is {supplier.minimum_order_quantity}.")
        # We don't adjust max_feasible_qty for MOQ, because if it's below MOQ we can't buy it unless we increase it, 
        # but max_feasible represents the upper bound. 
        # If max_feasible_qty drops below MOQ due to storage/budget, it's essentially 0.
    
    if max_feasible_qty < supplier.minimum_order_quantity:
        max_feasible_qty = 0
        
    if not demand_justified:
        warnings.append("Proposed quantity exceeds 150% of forecasted demand.")
        
    passed = len(violations) == 0
    
    return {
        "passed": passed,
        "max_feasible_qty": max_feasible_qty,
        "violations": violations,
        "warnings": warnings,
        "metrics": {
            "available_inventory": available_inventory,
            "projected_inventory": projected_inventory,
            "required_storage": required_storage,
            "total_cost": total_cost,
            "max_qty_allowed_by_storage": max_qty_allowed_by_storage,
            "max_qty_allowed_by_budget": max_qty_allowed_by_budget,
            "moq": supplier.minimum_order_quantity,
            "supplier_available": supplier.available_quantity
        }
    }

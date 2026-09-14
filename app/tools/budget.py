from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.database import DBBudget

def get_budget(db: Session) -> Optional[Dict[str, Any]]:
    budget = db.query(DBBudget).first()
    if not budget:
        return None
        
    return {
        "id": budget.id,
        "available_amount": budget.available_amount
    }

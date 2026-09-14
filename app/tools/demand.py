from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.database import DBDemand

def get_demand(product_id: str, db: Session) -> Optional[Dict[str, Any]]:
    demand = db.query(DBDemand).filter(DBDemand.product_id == product_id).first()
    if not demand:
        return None
        
    return {
        "product_id": demand.product_id,
        "forecast_demand": demand.forecast_demand,
        "recent_sales": demand.recent_sales,
        "forecast_horizon_days": demand.forecast_horizon_days
    }

import json
import os
from app.db.database import (
    SessionLocal, init_db, DBProduct, DBInventory, DBDemand,
    DBSupplier, DBPurchaseOrder, DBBudget, Base, engine
)
from datetime import datetime, timezone

def seed_database(force_reseed=False):
    if force_reseed:
        Base.metadata.drop_all(bind=engine)
    
    # Initialize DB (creates tables if not exist)
    init_db()
    
    db = SessionLocal()
    try:
        # Check if already seeded
        if not force_reseed and db.query(DBProduct).first() is not None:
            print("Database already seeded. Skipping.")
            return

        seed_file = os.path.join(os.path.dirname(__file__), '../../data/seed.json')
        with open(seed_file, 'r') as f:
            data = json.load(f)

        for p in data.get('products', []):
            db.add(DBProduct(**p))
        
        for s in data.get('suppliers', []):
            db.add(DBSupplier(**s))
            
        for i in data.get('inventory', []):
            db.add(DBInventory(**i))
            
        for d in data.get('demand', []):
            db.add(DBDemand(**d))
            
        for po in data.get('purchase_orders', []):
            po_dict = dict(po)
            po_dict['created_at'] = datetime.now(timezone.utc)
            db.add(DBPurchaseOrder(**po_dict))
            
        for b in data.get('budget', []):
            db.add(DBBudget(**b))

        db.commit()
        print("Database seeded successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()

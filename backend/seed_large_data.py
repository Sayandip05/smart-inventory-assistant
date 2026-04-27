import os
import random
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy.orm import Session
from app.infrastructure.database.connection import SessionLocal, engine, Base
from app.infrastructure.database.models import (
    Organization,
    Location,
    Item,
    InventoryTransaction,
    User,
)

fake = Faker()

def generate_seed_data(db: Session, num_items=5000, num_transactions=20000):
    print("Seeding database...")
    
    # 1. Organization
    org = db.query(Organization).filter_by(slug="default-org").first()
    if not org:
        org = Organization(name="Global Healthcare Supply", slug="default-org")
        db.add(org)
        db.commit()
        db.refresh(org)
        print("Created Organization.")

    # 2. Locations
    print("Generating Locations...")
    locations = []
    for _ in range(20):
        loc = Location(
            org_id=org.id,
            name=fake.company() + " Warehouse",
            type=random.choice(["Warehouse", "Distribution Center", "Hospital"]),
            region=fake.state(),
            address=fake.address()
        )
        locations.append(loc)
    db.add_all(locations)
    db.commit()
    print(f"Created {len(locations)} Locations.")

    # 3. Items
    items = []
    categories = ["Electronics", "Medical Supplies", "Office Supplies", "Furniture", "Hardware", "PPE", "Surgical Tools"]
    units = ["pcs", "boxes", "kg", "liters", "packs"]
    
    print(f"Generating {num_items} items (this may take a few seconds)...")
    for _ in range(num_items):
        item = Item(
            org_id=org.id,
            name=fake.catch_phrase().title() + " " + random.choice(["Kit", "Set", "Pack", "Module", "System"]),
            category=random.choice(categories),
            unit=random.choice(units),
            lead_time_days=random.randint(1, 30),
            min_stock=random.randint(10, 500)
        )
        items.append(item)
    
    # Bulk insert items for speed
    db.bulk_save_objects(items)
    db.commit()
    print("Items inserted successfully.")

    # Fetch inserted items to get their IDs
    all_items = db.query(Item).all()
    all_locations = db.query(Location).all()
    
    # 4. Inventory Transactions
    print(f"Generating {num_transactions} transactions (this may take a few seconds)...")
    transactions = []
    start_date = datetime.now() - timedelta(days=365)
    
    for _ in range(num_transactions):
        loc = random.choice(all_locations)
        item = random.choice(all_items)
        date = start_date + timedelta(days=random.randint(0, 365))
        opening = random.randint(100, 1000)
        received = random.randint(0, 500)
        issued = random.randint(0, 300)
        closing = opening + received - issued
        
        txn = InventoryTransaction(
            location_id=loc.id,
            item_id=item.id,
            date=date.date(),
            opening_stock=opening,
            received=received,
            issued=issued,
            closing_stock=closing,
            notes=fake.sentence(),
            entered_by="seed_script"
        )
        transactions.append(txn)
        
    db.bulk_save_objects(transactions)
    db.commit()
    print("Transactions inserted successfully.")

    print(f"\n✅ Seeding complete! Inserted {len(locations)} locations, {num_items} items, and {num_transactions} transactions.")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        generate_seed_data(db)
    finally:
        db.close()

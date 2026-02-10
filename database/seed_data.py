import sqlite3
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker('en_IN')  # Indian locale
random.seed(42)  # For reproducible data

# Database connection
DB_PATH = 'smart_inventory.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("🚀 Starting Smart Inventory Assistant - Data Generation")
print("=" * 60)

# ============================================
# STEP 1: Create Tables
# ============================================
print("\n📋 Step 1: Creating database schema...")

# Drop existing tables for fresh start
cursor.execute("DROP TABLE IF EXISTS inventory_transactions")
cursor.execute("DROP VIEW IF EXISTS stock_health")
cursor.execute("DROP TABLE IF EXISTS items")
cursor.execute("DROP TABLE IF EXISTS locations")

# Create locations table
cursor.execute("""
CREATE TABLE locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL,
    region VARCHAR(100) NOT NULL,
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Create items table
cursor.execute("""
CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    lead_time_days INTEGER NOT NULL,
    min_stock INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Create inventory_transactions table
cursor.execute("""
CREATE TABLE inventory_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    date DATE NOT NULL,
    opening_stock INTEGER NOT NULL,
    received INTEGER NOT NULL DEFAULT 0,
    issued INTEGER NOT NULL DEFAULT 0,
    closing_stock INTEGER NOT NULL,
    notes TEXT,
    entered_by VARCHAR(100) DEFAULT 'system',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations(id),
    FOREIGN KEY (item_id) REFERENCES items(id)
)
""")

print("✅ Tables created successfully!")

# ============================================
# STEP 2: Insert Locations (8 Indian locations)
# ============================================
print("\n📍 Step 2: Adding locations...")

locations_data = [
    ("Apollo Hospital - Mumbai", "hospital", "Maharashtra", "Tardeo, Mumbai, Maharashtra 400034"),
    ("AIIMS - Delhi", "hospital", "Delhi", "Ansari Nagar, New Delhi, Delhi 110029"),
    ("Manipal Clinic - Bangalore", "clinic", "Karnataka", "HAL 2nd Stage, Bangalore, Karnataka 560008"),
    ("City Hospital - Pune", "clinic", "Maharashtra", "Pimpri-Chinchwad, Pune, Maharashtra 411018"),
    ("Government Clinic - Chennai", "clinic", "Tamil Nadu", "T. Nagar, Chennai, Tamil Nadu 600017"),
    ("Primary Health Centre - Jaipur", "rural_clinic", "Rajasthan", "Mansarovar, Jaipur, Rajasthan 302020"),
    ("Community Clinic - Lucknow", "rural_clinic", "Uttar Pradesh", "Gomti Nagar, Lucknow, Uttar Pradesh 226010"),
    ("District Hospital - Patna", "rural_clinic", "Bihar", "Kankarbagh, Patna, Bihar 800020")
]

cursor.executemany("""
INSERT INTO locations (name, type, region, address)
VALUES (?, ?, ?, ?)
""", locations_data)

print(f"✅ Added {len(locations_data)} locations")

# ============================================
# STEP 3: Insert Items (30 medical items)
# ============================================
print("\n💊 Step 3: Adding medical items...")

items_data = [
    # Antibiotics (8 items)
    ("Amoxicillin 500mg", "antibiotic", "tablets", 7, 500),
    ("Ciprofloxacin 500mg", "antibiotic", "tablets", 7, 300),
    ("Azithromycin 250mg", "antibiotic", "tablets", 5, 400),
    ("Doxycycline 100mg", "antibiotic", "tablets", 7, 250),
    ("Metronidazole 400mg", "antibiotic", "tablets", 5, 300),
    ("Cephalexin 500mg", "antibiotic", "tablets", 7, 200),
    ("Levofloxacin 500mg", "antibiotic", "tablets", 7, 150),
    ("Clindamycin 300mg", "antibiotic", "tablets", 7, 200),
    
    # Painkillers (7 items)
    ("Paracetamol 500mg", "painkiller", "tablets", 3, 1000),
    ("Ibuprofen 400mg", "painkiller", "tablets", 5, 800),
    ("Diclofenac 50mg", "painkiller", "tablets", 5, 600),
    ("Aspirin 75mg", "painkiller", "tablets", 5, 500),
    ("Tramadol 50mg", "painkiller", "tablets", 7, 300),
    ("Naproxen 250mg", "painkiller", "tablets", 5, 400),
    ("Ketoprofen 100mg", "painkiller", "tablets", 7, 250),
    
    # Vitamins & Supplements (5 items)
    ("Vitamin C 500mg", "vitamin", "tablets", 10, 600),
    ("Vitamin D3 1000IU", "vitamin", "tablets", 10, 500),
    ("Vitamin B12 1000mcg", "vitamin", "tablets", 10, 400),
    ("Calcium 500mg", "vitamin", "tablets", 10, 700),
    ("Multivitamin", "vitamin", "tablets", 10, 500),
    
    # Diabetes Medications (5 items)
    ("Metformin 500mg", "diabetes", "tablets", 7, 800),
    ("Glimepiride 2mg", "diabetes", "tablets", 7, 400),
    ("Insulin Glargine", "diabetes", "vials", 14, 100),
    ("Sitagliptin 100mg", "diabetes", "tablets", 7, 300),
    ("Pioglitazone 15mg", "diabetes", "tablets", 7, 250),
    
    # First-Aid & Supplies (5 items)
    ("Bandages (10cm)", "first_aid", "rolls", 5, 500),
    ("Gauze Pads", "first_aid", "pieces", 5, 1000),
    ("Antiseptic Solution", "first_aid", "bottles", 7, 200),
    ("Surgical Gloves", "first_aid", "pairs", 5, 800),
    ("Cotton Swabs", "first_aid", "packs", 5, 600)
]

cursor.executemany("""
INSERT INTO items (name, category, unit, lead_time_days, min_stock)
VALUES (?, ?, ?, ?, ?)
""", items_data)

print(f"✅ Added {len(items_data)} medical items")

# ============================================
# STEP 4: Generate Inventory Transactions (60 days)
# ============================================
print("\n📊 Step 4: Generating 60 days of inventory data...")

# Configuration
NUM_DAYS = 60
START_DATE = datetime.now() - timedelta(days=NUM_DAYS)

# Location consumption profiles
location_profiles = {
    1: {"volume": "high", "efficiency": "good"},      # Apollo Mumbai
    2: {"volume": "high", "efficiency": "good"},      # AIIMS Delhi
    3: {"volume": "medium", "efficiency": "good"},    # Manipal Bangalore
    4: {"volume": "medium", "efficiency": "medium"},  # City Hospital Pune
    5: {"volume": "medium", "efficiency": "medium"},  # Govt Clinic Chennai
    6: {"volume": "low", "efficiency": "poor"},       # PHC Jaipur
    7: {"volume": "low", "efficiency": "poor"},       # Community Lucknow
    8: {"volume": "low", "efficiency": "poor"}        # District Patna
}

# Item demand profiles
item_demand = {
    "painkiller": {"base": 50, "variance": 20},
    "antibiotic": {"base": 30, "variance": 15},
    "vitamin": {"base": 20, "variance": 10},
    "diabetes": {"base": 25, "variance": 12},
    "first_aid": {"base": 40, "variance": 18}
}

# Initialize stock for each location-item combination
stock_levels = {}

# Get all items
cursor.execute("SELECT id, category, min_stock FROM items")
all_items = cursor.fetchall()

# Get all locations
cursor.execute("SELECT id FROM locations")
all_locations = [row[0] for row in cursor.fetchall()]

# Initialize starting stock
for location_id in all_locations:
    profile = location_profiles[location_id]
    multiplier = {"high": 3, "medium": 2, "low": 1}[profile["volume"]]
    
    for item_id, category, min_stock in all_items:
        # Starting stock = 2-4x min_stock depending on location size
        initial_stock = min_stock * multiplier * random.uniform(2, 4)
        stock_levels[(location_id, item_id)] = int(initial_stock)

print("  ⏳ Generating daily transactions...")

transaction_count = 0

# Generate transactions for each day
for day in range(NUM_DAYS):
    current_date = (START_DATE + timedelta(days=day)).strftime('%Y-%m-%d')
    
    for location_id in all_locations:
        profile = location_profiles[location_id]
        volume_multiplier = {"high": 1.5, "medium": 1.0, "low": 0.5}[profile["volume"]]
        
        for item_id, category, min_stock in all_items:
            opening_stock = stock_levels[(location_id, item_id)]
            
            # Calculate daily issued (consumption)
            base_demand = item_demand[category]["base"]
            variance = item_demand[category]["variance"]
            daily_issued = int(base_demand * volume_multiplier * random.uniform(0.7, 1.3))
            daily_issued = max(0, min(daily_issued, opening_stock))  # Can't issue more than stock
            
            # Reorder logic (simulate deliveries)
            received = 0
            days_of_stock = opening_stock / max(daily_issued, 1)
            
            # Reorder when stock is low (different thresholds based on efficiency)
            reorder_threshold = {"good": 7, "medium": 5, "poor": 3}[profile["efficiency"]]
            
            if days_of_stock < reorder_threshold or opening_stock < min_stock:
                # Simulate delivery (not every day, random timing)
                if random.random() < 0.3:  # 30% chance of delivery
                    # Order quantity: enough for 2-3 weeks
                    order_quantity = int(daily_issued * random.uniform(14, 21))
                    received = order_quantity
            
            # Calculate closing stock
            closing_stock = opening_stock + received - daily_issued
            
            # Insert transaction
            cursor.execute("""
            INSERT INTO inventory_transactions 
            (location_id, item_id, date, opening_stock, received, issued, closing_stock, entered_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (location_id, item_id, current_date, opening_stock, received, daily_issued, closing_stock, 'system'))
            
            # Update stock level for next day
            stock_levels[(location_id, item_id)] = closing_stock
            transaction_count += 1
    
    if (day + 1) % 10 == 0:
        print(f"  ✓ Processed {day + 1}/{NUM_DAYS} days ({transaction_count} transactions)")

print(f"✅ Generated {transaction_count} inventory transactions")

# ============================================
# STEP 5: Create Indexes
# ============================================
print("\n🔍 Step 5: Creating database indexes...")

cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON inventory_transactions(date)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_location ON inventory_transactions(location_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_item ON inventory_transactions(item_id)")

print("✅ Indexes created")

# ============================================
# Commit and Close
# ============================================
conn.commit()
conn.close()

print("\n" + "=" * 60)
print("✅ DATABASE SETUP COMPLETE!")
print("=" * 60)
print(f"\n📊 Summary:")
print(f"  • Locations: 8")
print(f"  • Items: 30")
print(f"  • Transactions: {transaction_count}")
print(f"  • Date Range: {START_DATE.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}")
print(f"\n💾 Database file: {DB_PATH}")
from app.database.connection import SessionLocal
from app.services.ai_agent.agent import InventoryAgent

# Create DB session
db = SessionLocal()

# Initialize agent
agent = InventoryAgent(db)

# Test questions
questions = [
    "What items are critical right now?",
    "Show me stock status in Mumbai",
    "What should I order for Delhi?",
    "How's our paracetamol inventory?"
]

print("🤖 Testing Inventory Agent\n")
print("=" * 60)

for q in questions:
    print(f"\n❓ Question: {q}")
    print("-" * 60)
    
    result = agent.query(q)
    
    if result["success"]:
        print(f"✅ Response:\n{result['response']}")
    else:
        print(f"❌ Error: {result['error']}")
    
    print("=" * 60)

db.close()
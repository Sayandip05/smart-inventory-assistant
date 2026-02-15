from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.database.connection import get_db
from app.services.ai_agent.agent import InventoryAgent

router = APIRouter(prefix="/chat", tags=["Chatbot"])

# Request/Response models
class ChatRequest(BaseModel):
    question: str
    user_id: Optional[str] = "admin"
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    success: bool
    response: str
    question: str
    conversation_id: Optional[str] = None
    suggested_actions: Optional[List[dict]] = None
    error: Optional[str] = None

# In-memory conversation storage (simple implementation)
# In production, use Redis or database
conversations = {}

@router.post("/query", response_model=ChatResponse)
def chat_query(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Send a question to the AI chatbot
    
    The agent will:
    1. Understand the question
    2. Query the database using appropriate tools
    3. Format a natural language response
    
    Example questions:
    - "What items are critical?"
    - "Show me stock levels in Mumbai"
    - "What should I order for Delhi?"
    - "How's our paracetamol inventory?"
    """
    try:
        # Validate input
        if not request.question or len(request.question.strip()) < 3:
            raise HTTPException(
                status_code=400,
                detail="Question must be at least 3 characters"
            )
        
        # Initialize agent
        agent = InventoryAgent(db)
        
        # Process query
        result = agent.query(request.question)
        
        if not result["success"]:
            return ChatResponse(
                success=False,
                response="I encountered an error processing your request.",
                question=request.question,
                error=result.get("error")
            )
        
        # Detect if response suggests actions
        suggested_actions = []
        response_lower = result["response"].lower()
        
        # Auto-detect action suggestions
        if any(word in response_lower for word in ["order", "purchase", "reorder"]):
            suggested_actions.append({
                "type": "export",
                "label": "📥 Download Purchase Order",
                "action": "export_reorder_list"
            })
        
        if "critical" in response_lower or "urgent" in response_lower:
            suggested_actions.append({
                "type": "view",
                "label": "⚠️ View All Alerts",
                "action": "view_alerts"
            })
        
        # Store conversation (simple implementation)
        conv_id = request.conversation_id or f"conv_{request.user_id}_{len(conversations)}"
        if conv_id not in conversations:
            conversations[conv_id] = []
        
        conversations[conv_id].append({
            "role": "user",
            "content": request.question
        })
        conversations[conv_id].append({
            "role": "assistant",
            "content": result["response"]
        })
        
        return ChatResponse(
            success=True,
            response=result["response"],
            question=request.question,
            conversation_id=conv_id,
            suggested_actions=suggested_actions if suggested_actions else None
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        return ChatResponse(
            success=False,
            response="An unexpected error occurred. Please try again.",
            question=request.question,
            error=str(e)
        )

@router.get("/history/{conversation_id}")
def get_chat_history(conversation_id: str):
    """
    Get conversation history for a specific conversation
    """
    if conversation_id not in conversations:
        return {
            "success": False,
            "error": "Conversation not found"
        }
    
    return {
        "success": True,
        "conversation_id": conversation_id,
        "messages": conversations[conversation_id]
    }

@router.delete("/history/{conversation_id}")
def clear_chat_history(conversation_id: str):
    """
    Clear conversation history
    """
    if conversation_id in conversations:
        del conversations[conversation_id]
        return {
            "success": True,
            "message": "Conversation history cleared"
        }
    
    return {
        "success": False,
        "error": "Conversation not found"
    }

@router.get("/suggestions")
def get_question_suggestions():
    """
    Get suggested questions users can ask
    """
    return {
        "success": True,
        "suggestions": [
            {
                "category": "Alerts",
                "questions": [
                    "What items are critical right now?",
                    "Show me all warning-level items",
                    "Which locations have the most issues?"
                ]
            },
            {
                "category": "Location-Specific",
                "questions": [
                    "What's the stock status for my main warehouse?",
                    "Show me critical items for location 1",
                    "How is Central Clinic doing?"
                ]
            },
            {
                "category": "Item-Specific",
                "questions": [
                    "Do we have enough paracetamol?",
                    "Show me all antibiotic levels",
                    "What's our inventory for item 3?"
                ]
            },
            {
                "category": "Reorder",
                "questions": [
                    "What should I order today?",
                    "Generate purchase order for my location",
                    "Show me reorder recommendations"
                ]
            },
            {
                "category": "Analysis",
                "questions": [
                    "Which category has most shortages?",
                    "Compare stock levels across locations",
                    "Show me consumption trends"
                ]
            }
        ]
    }

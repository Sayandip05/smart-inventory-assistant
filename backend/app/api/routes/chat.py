from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.database.connection import get_db
from app.database.models import ChatSession, ChatMessage
from app.services.ai_agent.agent import InventoryAgent
from app.config import settings
import httpx
import uuid

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
        
        # Process query with conversation context
        result = agent.query(request.question, conversation_id=request.conversation_id)
        
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
        
        # Store conversation in database
        conv_id = request.conversation_id
        if not conv_id:
            conv_id = f"conv_{uuid.uuid4().hex[:12]}"
            # Create new session
            title = request.question[:50] + "..." if len(request.question) > 50 else request.question
            session = ChatSession(id=conv_id, user_id=request.user_id, title=title)
            db.add(session)
        
        # Add user message
        db.add(ChatMessage(session_id=conv_id, role="user", content=request.question))
        # Add assistant message
        db.add(ChatMessage(session_id=conv_id, role="assistant", content=result["response"]))
        db.commit()
        
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
        db.rollback()
        return ChatResponse(
            success=False,
            response="An unexpected error occurred. Please try again.",
            question=request.question,
            error=str(e)
        )

@router.get("/history/{conversation_id}")
def get_chat_history(conversation_id: str, db: Session = Depends(get_db)):
    """
    Get conversation history for a specific conversation
    """
    session = db.query(ChatSession).filter(ChatSession.id == conversation_id).first()
    if not session:
        return {
            "success": False,
            "error": "Conversation not found"
        }
    
    messages = [
        {"role": msg.role, "content": msg.content}
        for msg in session.messages
    ]
    
    return {
        "success": True,
        "conversation_id": conversation_id,
        "messages": messages
    }

@router.delete("/history/{conversation_id}")
def clear_chat_history(conversation_id: str, db: Session = Depends(get_db)):
    """
    Clear conversation history
    """
    session = db.query(ChatSession).filter(ChatSession.id == conversation_id).first()
    if session:
        db.delete(session)
        db.commit()
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
@router.get("/sessions")
def get_chat_sessions(db: Session = Depends(get_db)):
    """
    Get list of active conversation sessions
    """
    db_sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()
    
    sessions = []
    for s in db_sessions:
        message_count = len(s.messages)
        if message_count > 0:
            sessions.append({
                "id": s.id,
                "preview": s.title,
                "message_count": message_count
            })
    
    return {
        "success": True,
        "sessions": sessions
    }

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe audio to English text using Sarvam AI.
    
    Accepts audio file (wav, webm, mp3, etc.) and returns transcribed text.
    The Sarvam AI model translates any Indian language speech to English.
    """
    if not settings.SARVAM_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="SARVAM_API_KEY is not configured. Add it to your .env file."
        )
    
    try:
        audio_bytes = await file.read()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.sarvam.ai/speech-to-text-translate",
                headers={
                    "api-subscription-key": settings.SARVAM_API_KEY,
                },
                files={
                    "file": (file.filename or "audio.wav", audio_bytes, file.content_type or "audio/wav"),
                },
                data={
                    "model": "saaras:v3",
                    "with_diarization": "false",
                },
            )
        
        if response.status_code != 200:
            error_detail = response.text
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Sarvam AI API error: {error_detail}"
            )
        
        result = response.json()
        transcript = result.get("transcript", "")
        
        return {
            "success": True,
            "text": transcript,
        }
        
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Sarvam AI API timed out. Please try again."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException as HTTPExceptionImport,
)
from app.core.exceptions import ValidationError, AppException
from sqlalchemy.orm import Session
from typing import Optional
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.models import ChatSession, ChatMessage
from app.application.agent_tools import (
    get_inventory_overview,
    get_critical_items,
    get_stock_health,
    calculate_reorder_suggestions,
    get_location_summary,
    get_category_analysis,
    get_consumption_trends,
    set_db_session,
)
from app.infrastructure.vector_store.vector_store import get_vector_memory
from app.core.config import settings
from app.api.schemas.chat_schemas import ChatRequest, ChatResponse
import httpx
import uuid
import logging
from datetime import datetime

logger = logging.getLogger("smart_inventory.chat")

router = APIRouter(prefix="/chat", tags=["Chatbot"])


def _build_agent_response(
    question: str, db: Session, conversation_id: Optional[str] = None
) -> dict:
    """Rule-based response path when LLM is unavailable."""
    set_db_session(db)

    overview = get_inventory_overview.invoke({})
    if isinstance(overview, dict) and not overview.get("has_data"):
        return {
            "success": True,
            "response": (
                "Inventory data is empty. Add locations, items, and transactions from "
                "the Data Entry page first."
            ),
            "question": question,
        }

    question_lower = question.lower()

    if any(k in question_lower for k in ["trend", "usage", "consumption"]):
        result = get_consumption_trends.invoke({})
        return _format_result("Consumption trend summary", result, question)

    if any(k in question_lower for k in ["reorder", "order", "purchase"]):
        result = calculate_reorder_suggestions.invoke({})
        return _format_result("Reorder suggestions", result, question)

    if any(k in question_lower for k in ["critical", "warning", "alert"]):
        severity = "WARNING" if "warning" in question_lower else "CRITICAL"
        result = get_critical_items.invoke({"severity": severity})
        return _format_result(f"{severity} stock alerts", result, question)

    if "category" in question_lower:
        result = get_category_analysis.invoke({"category": ""})
        return _format_result("Category snapshot", result, question)

    result = get_stock_health.invoke({})
    return _format_result("Current stock health", result, question)


def _format_result(title: str, payload, question: str) -> dict:
    import json

    if isinstance(payload, dict):
        if payload.get("error"):
            return {
                "success": True,
                "response": f"{title}: {payload['error']}",
                "question": question,
            }
        if payload.get("info"):
            return {"success": True, "response": payload["info"], "question": question}
        return {
            "success": True,
            "response": f"{title}:\n{json.dumps(payload, indent=2)}",
            "question": question,
        }

    if isinstance(payload, list):
        if not payload:
            return {
                "success": True,
                "response": f"{title}: no data found.",
                "question": question,
            }
        first = payload[0]
        if isinstance(first, dict) and first.get("info"):
            return {"success": True, "response": first["info"], "question": question}
        if isinstance(first, dict) and first.get("error"):
            return {
                "success": True,
                "response": f"{title}: {first['error']}",
                "question": question,
            }
        return {
            "success": True,
            "response": f"{title}:\n{json.dumps(payload[:10], indent=2)}",
            "question": question,
        }

    return {
        "success": True,
        "response": f"{title}: {str(payload)}",
        "question": question,
    }


@router.post("/query", response_model=ChatResponse)
def chat_query(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        if not request.question or len(request.question.strip()) < 3:
            raise ValidationError("Question must be at least 3 characters")

        result = _build_agent_response(
            request.question, db, request.conversation_id or ""
        )

        conv_id = request.conversation_id
        if not conv_id:
            conv_id = f"conv_{uuid.uuid4().hex[:12]}"
            title = (
                request.question[:50] + "..."
                if len(request.question) > 50
                else request.question
            )
            session = ChatSession(id=conv_id, user_id=request.user_id, title=title)
            db.add(session)

        db.add(ChatMessage(session_id=conv_id, role="user", content=request.question))
        db.add(
            ChatMessage(
                session_id=conv_id, role="assistant", content=result["response"]
            )
        )
        db.commit()

        try:
            memory = get_vector_memory()
            if memory.is_available:
                now = datetime.now()
                memory.add_message(conv_id, "user", request.question, now)
                memory.add_message(conv_id, "assistant", result["response"], now)
        except Exception as e:
            logger.warning("Failed to store in vector memory: %s", e)

        response_lower = result["response"].lower()
        suggested_actions = []
        if any(word in response_lower for word in ["order", "purchase", "reorder"]):
            suggested_actions.append(
                {
                    "type": "export",
                    "label": "Download Purchase Order",
                    "action": "export_reorder_list",
                }
            )
        if "critical" in response_lower or "urgent" in response_lower:
            suggested_actions.append(
                {"type": "view", "label": "View All Alerts", "action": "view_alerts"}
            )

        return ChatResponse(
            success=True,
            response=result["response"],
            question=request.question,
            conversation_id=conv_id,
            suggested_actions=suggested_actions if suggested_actions else None,
        )

    except HTTPExceptionImport:
        raise
    except Exception as e:
        db.rollback()
        return ChatResponse(
            success=False,
            response="An unexpected error occurred. Please try again.",
            question=request.question,
            error=str(e),
        )


@router.get("/history/{conversation_id}")
def get_chat_history(conversation_id: str, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == conversation_id).first()
    if not session:
        return {"success": False, "error": "Conversation not found"}

    messages = [{"role": msg.role, "content": msg.content} for msg in session.messages]

    return {"success": True, "conversation_id": conversation_id, "messages": messages}


@router.delete("/history/{conversation_id}")
def clear_chat_history(conversation_id: str, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == conversation_id).first()
    if session:
        db.delete(session)
        db.commit()
        return {"success": True, "message": "Conversation history cleared"}

    return {"success": False, "error": "Conversation not found"}


@router.get("/suggestions")
def get_question_suggestions():
    return {
        "success": True,
        "suggestions": [
            {
                "category": "Alerts",
                "questions": [
                    "What items are critical right now?",
                    "Show me all warning-level items",
                    "Which locations have the most issues?",
                ],
            },
            {
                "category": "Location-Specific",
                "questions": [
                    "What's the stock status for my main warehouse?",
                    "Show me critical items for location 1",
                    "How is Central Clinic doing?",
                ],
            },
            {
                "category": "Item-Specific",
                "questions": [
                    "Do we have enough paracetamol?",
                    "Show me all antibiotic levels",
                    "What's our inventory for item 3?",
                ],
            },
            {
                "category": "Reorder",
                "questions": [
                    "What should I order today?",
                    "Generate purchase order for my location",
                    "Show me reorder recommendations",
                ],
            },
            {
                "category": "Analysis",
                "questions": [
                    "Which category has most shortages?",
                    "Compare stock levels across locations",
                    "Show me consumption trends",
                ],
            },
        ],
    }


@router.get("/sessions")
def get_chat_sessions(db: Session = Depends(get_db)):
    db_sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()

    sessions = []
    for s in db_sessions:
        message_count = len(s.messages)
        if message_count > 0:
            sessions.append(
                {"id": s.id, "preview": s.title, "message_count": message_count}
            )

    return {"success": True, "sessions": sessions}


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    if not settings.SARVAM_API_KEY:
        raise AppException(
            "SARVAM_API_KEY is not configured. Add it to your .env file."
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
                    "file": (
                        file.filename or "audio.wav",
                        audio_bytes,
                        file.content_type or "audio/wav",
                    ),
                },
                data={
                    "model": "saaras:v3",
                    "with_diarization": "false",
                },
            )

        if response.status_code != 200:
            error_detail = response.text
            raise AppException(f"Sarvam AI API error: {error_detail}")

        result = response.json()
        transcript = result.get("transcript", "")

        return {
            "success": True,
            "text": transcript,
        }

    except httpx.TimeoutException:
        raise AppException("Sarvam AI API timed out. Please try again.")
    except AppException:
        raise
    except Exception as e:
        raise AppException(f"Transcription failed: {str(e)}")

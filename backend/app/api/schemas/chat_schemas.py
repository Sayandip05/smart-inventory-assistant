from pydantic import BaseModel
from typing import Optional, List


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

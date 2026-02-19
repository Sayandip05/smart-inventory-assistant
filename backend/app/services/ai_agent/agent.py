from typing import TypedDict, Annotated
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, add_messages
from sqlalchemy.orm import Session
from app.config import settings
from app.services.ai_agent.prompts import get_system_prompt
from app.database.models import ChatMessage
from app.services.memory.vector_store import get_vector_memory
from app.services.ai_agent.tools import (
    get_inventory_overview,
    get_critical_items,
    get_stock_health,
    calculate_reorder_suggestions,
    get_location_summary,
    get_category_analysis,
    get_consumption_trends,
    set_db_session
)
import json

# Define agent state with proper message reducer
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# Initialize LLM (using Groq's OpenAI-compatible endpoint)
llm = ChatOpenAI(
    model="openai/gpt-oss-20b",
    temperature=0.3,
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

# Available tools
tools = [
    get_inventory_overview,
    get_critical_items,
    get_stock_health,
    calculate_reorder_suggestions,
    get_location_summary,
    get_category_analysis,
    get_consumption_trends,
]

# Create a lookup dict for tool execution
tool_map = {tool.name: tool for tool in tools}

# Bind tools to LLM
llm_with_tools = llm.bind_tools(tools)

# Define agent node
def agent_node(state: AgentState):
    """Main agent logic - decides what to do"""
    messages = list(state["messages"])
    
    # Always prepend system prompt with current date/time and past context
    if not messages or not isinstance(messages[0], SystemMessage):
        past_context = state.get("past_context", None) if isinstance(state, dict) else None
        messages = [SystemMessage(content=get_system_prompt(datetime.now(), past_context=past_context))] + messages
    
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# Custom tool execution node (compatible with openai/gpt-oss-20b)
def tool_node(state: AgentState):
    """Execute tool calls from the last AI message"""
    messages = state["messages"]
    last_message = messages[-1]
    
    tool_messages = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        
        if tool_name in tool_map:
            try:
                result = tool_map[tool_name].invoke(tool_args)
                if not isinstance(result, str):
                    result = json.dumps(result, default=str)
            except Exception as e:
                result = json.dumps({"error": str(e)})
        else:
            result = json.dumps({"error": f"Unknown tool: {tool_name}"})
        
        tool_messages.append(
            ToolMessage(
                content=result,
                tool_call_id=tool_call["id"],
                name=tool_name,
            )
        )
    
    return {"messages": tool_messages}

# Define routing logic
def should_continue(state: AgentState):
    """Decide if agent should continue or end"""
    messages = state["messages"]
    last_message = messages[-1]
    
    # If LLM makes a tool call, continue to tools
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    # Otherwise, end
    return END

# Build the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

# Set entry point
workflow.set_entry_point("agent")

# Add edges
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: END
    }
)

# After tools, always go back to agent
workflow.add_edge("tools", "agent")

# Compile graph
graph = workflow.compile()

class InventoryAgent:
    """Main agent interface"""
    
    def __init__(self, db: Session):
        self.db = db
        set_db_session(db)  # Set DB session for tools
    
    def _get_conversation_history(self, conversation_id: str, limit: int = 10) -> list:
        """
        Fetch recent messages from SQLite and convert to LangChain messages
        with timestamp context.
        """
        if not conversation_id:
            return []
        
        try:
            db_messages = (
                self.db.query(ChatMessage)
                .filter(ChatMessage.session_id == conversation_id)
                .order_by(ChatMessage.created_at.asc())
                .all()
            )
            
            # Take the last N messages
            recent = db_messages[-limit:] if len(db_messages) > limit else db_messages
            
            history = []
            for msg in recent:
                # Format timestamp for temporal context
                ts = msg.created_at.strftime("%Y-%m-%d %H:%M") if msg.created_at else "unknown time"
                content_with_time = f"[{ts}] {msg.content}"
                
                if msg.role == "user":
                    history.append(HumanMessage(content=content_with_time))
                elif msg.role == "assistant":
                    history.append(AIMessage(content=content_with_time))
            
            return history
        except Exception as e:
            print(f"Warning: Failed to load conversation history: {e}")
            return []
    
    def query(self, question: str, conversation_id: str = None) -> dict:
        """
        Process a user question with conversation context.
        
        Args:
            question: User's natural language question
            conversation_id: Optional session ID to load history from
        
        Returns:
            Response with answer and optional actions
        """
        try:
            question_lower = question.lower()

            # Fallback mode if no LLM key is configured.
            if not settings.GROQ_API_KEY:
                fallback_response = self._fallback_response(question_lower)
                return {
                    "success": True,
                    "response": fallback_response,
                    "question": question,
                }

            # Fetch conversation history from SQLite
            history_messages = self._get_conversation_history(conversation_id)

            # Search ChromaDB for relevant past context (from OTHER sessions)
            past_context = None
            try:
                memory = get_vector_memory()
                if memory.is_available:
                    results = memory.search_relevant(
                        query=question,
                        n_results=5,
                        exclude_session=conversation_id,
                    )
                    if results:
                        context_lines = []
                        for r in results:
                            context_lines.append(
                                f"[{r['timestamp']}] ({r['role']}): {r['content']}"
                            )
                        past_context = "\n".join(context_lines)
            except Exception as e:
                print(f"Warning: Vector memory search failed: {e}")

            # Build system prompt with past context
            system_prompt = get_system_prompt(datetime.now(), past_context=past_context)

            # Create initial state with system prompt + history + new question
            initial_state = {
                "messages": [
                    SystemMessage(content=system_prompt)
                ] + history_messages + [HumanMessage(content=question)]
            }
            
            # Run the graph
            result = graph.invoke(initial_state)
            
            # Extract final response
            final_message = result["messages"][-1]
            
            # Format response
            response_text = final_message.content if hasattr(final_message, "content") else str(final_message)
            
            return {
                "success": True,
                "response": response_text,
                "question": question
            }
            
        except Exception as e:
            # If LLM/toolchain fails at runtime, use deterministic fallback.
            fallback_response = self._fallback_response(question.lower())
            return {
                "success": True,
                "error": str(e),
                "response": fallback_response
            }
    
    def get_conversation_history(self) -> list:
        """Get chat history (placeholder for future implementation)"""
        return []

    def _fallback_response(self, question_lower: str) -> str:
        """Rule-based response path when LLM is unavailable."""
        overview = get_inventory_overview.invoke({})
        if isinstance(overview, dict) and not overview.get("has_data"):
            return (
                "Inventory data is empty. Add locations, items, and transactions from "
                "the Data Entry page first."
            )

        if any(k in question_lower for k in ["trend", "usage", "consumption"]):
            result = get_consumption_trends.invoke({})
            return self._format_fallback_result("Consumption trend summary", result)

        if any(k in question_lower for k in ["reorder", "order", "purchase"]):
            result = calculate_reorder_suggestions.invoke({})
            return self._format_fallback_result("Reorder suggestions", result)

        if any(k in question_lower for k in ["critical", "warning", "alert"]):
            severity = "WARNING" if "warning" in question_lower else "CRITICAL"
            result = get_critical_items.invoke({"severity": severity})
            return self._format_fallback_result(f"{severity} stock alerts", result)

        if "category" in question_lower:
            result = get_category_analysis.invoke({"category": ""})
            return self._format_fallback_result("Category snapshot", result)

        result = get_stock_health.invoke({})
        return self._format_fallback_result("Current stock health", result)

    @staticmethod
    def _format_fallback_result(title: str, payload) -> str:
        if isinstance(payload, dict):
            if payload.get("error"):
                return f"{title}: {payload['error']}"
            if payload.get("info"):
                return payload["info"]
            return f"{title}:\n{json.dumps(payload, indent=2)}"

        if isinstance(payload, list):
            if not payload:
                return f"{title}: no data found."
            first = payload[0]
            if isinstance(first, dict) and first.get("info"):
                return first["info"]
            if isinstance(first, dict) and first.get("error"):
                return f"{title}: {first['error']}"
            return f"{title}:\n{json.dumps(payload[:10], indent=2)}"

        return f"{title}: {str(payload)}"

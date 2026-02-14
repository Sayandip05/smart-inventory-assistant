from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, add_messages
from sqlalchemy.orm import Session
from app.config import settings
from app.services.ai_agent.prompts import SYSTEM_PROMPT
from app.services.ai_agent.tools import (
    get_critical_items,
    get_stock_health,
    calculate_reorder_suggestions,
    get_location_summary,
    get_category_analysis,
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
    get_critical_items,
    get_stock_health,
    calculate_reorder_suggestions,
    get_location_summary,
    get_category_analysis
]

# Create a lookup dict for tool execution
tool_map = {tool.name: tool for tool in tools}

# Bind tools to LLM
llm_with_tools = llm.bind_tools(tools)

# Define agent node
def agent_node(state: AgentState):
    """Main agent logic - decides what to do"""
    messages = list(state["messages"])
    
    # Always prepend system prompt if not already present
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
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
    
    def query(self, question: str) -> dict:
        """
        Process a user question
        
        Args:
            question: User's natural language question
        
        Returns:
            Response with answer and optional actions
        """
        try:
            # Create initial state
            initial_state = {
                "messages": [HumanMessage(content=question)]
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
            return {
                "success": False,
                "error": str(e),
                "response": "I encountered an error processing your request. Please try rephrasing your question."
            }
    
    def get_conversation_history(self) -> list:
        """Get chat history (placeholder for future implementation)"""
        return []
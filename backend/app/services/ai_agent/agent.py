from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
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

# Define agent state
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "The messages in the conversation"]

# Initialize LLM
llm = ChatGroq(
    model="llama-3.1-70b-versatile",
    temperature=0.3,
    groq_api_key=settings.GROQ_API_KEY
)

# Available tools
tools = [
    get_critical_items,
    get_stock_health,
    calculate_reorder_suggestions,
    get_location_summary,
    get_category_analysis
]

# Bind tools to LLM
llm_with_tools = llm.bind_tools(tools)

# Define agent node
def agent_node(state: AgentState):
    """Main agent logic - decides what to do"""
    messages = state["messages"]
    
    # Add system prompt if first message
    if len(messages) == 1 and isinstance(messages[0], HumanMessage):
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            messages[0]
        ]
    
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# Define tool execution node
tool_node = ToolNode(tools)

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
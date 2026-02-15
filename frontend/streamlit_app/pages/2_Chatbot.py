import streamlit as st
from utils.api_client import InventoryAPI
import time

# Page config
st.set_page_config(page_title="AI Assistant", page_icon="💬", layout="wide")

# Initialize API
if "api" not in st.session_state:
    st.session_state.api = InventoryAPI()
if st.session_state.get("user_role") != "admin":
    st.error("Access denied. Chatbot is available only in Admin Panel.")
    if st.button("Back to Home"):
        st.switch_page("app.py")
    st.stop()

api = st.session_state.api

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Header
st.title("💬 AI Inventory Assistant")
st.markdown("Ask me anything about your inventory in natural language!")

st.markdown("---")

# Sidebar with suggestions
with st.sidebar:
    st.subheader("💡 Suggested Questions")
    
    suggestions_data = api.get_chat_suggestions()
    
    if suggestions_data.get("success"):
        suggestions = suggestions_data.get("suggestions", [])
        
        for category in suggestions:
            with st.expander(f"📁 {category['category']}"):
                for question in category['questions']:
                    if st.button(question, key=f"suggest_{question}", use_container_width=True):
                        # Add to chat
                        st.session_state.messages.append({
                            "role": "user",
                            "content": question
                        })
                        st.rerun()
    
    st.markdown("---")
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Display chat history
chat_container = st.container()

with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show actions if present
            if message["role"] == "assistant" and "actions" in message:
                action_cols = st.columns(len(message["actions"]))
                for idx, action in enumerate(message["actions"]):
                    with action_cols[idx]:
                        st.button(
                            action.get("label", "Action"),
                            key=f"action_{idx}_{time.time()}"
                        )

# Chat input
if prompt := st.chat_input("Type your question here..."):
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = api.chat_query(prompt)
        
        if response.get("success"):
            answer = response.get("response", "I couldn't generate a response.")
            st.markdown(answer)
            
            # Store assistant message
            assistant_msg = {
                "role": "assistant",
                "content": answer
            }
            
            # Add actions if present
            if response.get("suggested_actions"):
                assistant_msg["actions"] = response["suggested_actions"]
                
                # Display action buttons
                actions = response["suggested_actions"]
                action_cols = st.columns(len(actions))
                
                for idx, action in enumerate(actions):
                    with action_cols[idx]:
                        st.button(
                            action.get("label", "Action"),
                            key=f"new_action_{idx}"
                        )
            
            st.session_state.messages.append(assistant_msg)
        else:
            error_msg = f"❌ Error: {response.get('error', 'Unknown error')}"
            st.error(error_msg)
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg
            })

# Examples at bottom if no messages
if not st.session_state.messages:
    st.markdown("---")
    st.markdown("### 🎯 Try asking:")
    
    example_col1, example_col2 = st.columns(2)
    
    with example_col1:
        st.info("""
        **Alerts & Status:**
        - "What items are critical?"
        - "Show me stock levels for my location"
        - "Which location has the most issues?"
        """)
    
    with example_col2:
        st.info("""
        **Reorders & Analysis:**
        - "What should I order today?"
        - "Show me antibiotic levels"
        - "Compare stock across locations"
        """)

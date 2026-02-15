import streamlit as st
from utils.api_client import InventoryAPI

# Page config
st.set_page_config(
    page_title="Smart Inventory Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize API client
if "api" not in st.session_state:
    st.session_state.api = InventoryAPI()
if "user_role" not in st.session_state:
    st.session_state.user_role = None

# Header
st.title("🏥 Smart Inventory Assistant")
st.markdown("### Role-based Healthcare Inventory Management")

st.markdown("---")

# Quick stats
col1, col2, col3 = st.columns(3)

# Fetch summary
with st.spinner("Loading statistics..."):
    summary = st.session_state.api.get_summary()

if summary.get("success"):
    data = summary.get("data", {})
    overview = data.get("overview", {})
    health = data.get("health_summary", {})
    
    with col1:
        st.metric(
            "Total Locations",
            overview.get("total_locations", 0),
            help="Number of hospitals/clinics monitored"
        )
    
    with col2:
        critical = health.get("critical", 0)
        st.metric(
            "Critical Alerts",
            critical,
            delta=f"-{critical}" if critical > 0 else "All good!",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            "Total Items Tracked",
            overview.get("total_items", 0),
            help="Unique medicines across all locations"
        )
else:
    st.error(f"⚠️ {summary.get('error', 'Failed to load data')}")

st.markdown("---")

# Role selection
st.subheader("👤 Panel Access")
role_col1, role_col2 = st.columns(2)
with role_col1:
    if st.button("Use Admin Panel", use_container_width=True):
        st.session_state.user_role = "admin"
with role_col2:
    if st.button("Use Vendor Panel", use_container_width=True):
        st.session_state.user_role = "vendor"

if st.session_state.user_role:
    st.info(f"Active role: {st.session_state.user_role.upper()}")
    if st.button("Clear Role", type="secondary"):
        st.session_state.user_role = None
        st.rerun()

st.markdown("---")

# Panel navigation based on role
if st.session_state.user_role == "admin":
    st.subheader("🛡️ Admin Panel")
    admin_col1, admin_col2 = st.columns(2)
    with admin_col1:
        st.markdown("### 📊 Dashboard")
        st.markdown("- Heatmap\n- Alerts\n- Summary")
        if st.button("Open Dashboard", key="dash_btn", use_container_width=True):
            st.switch_page("pages/1_Dashboard.py")
    with admin_col2:
        st.markdown("### 💬 Chatbot")
        st.markdown("- Query stock\n- Reorder guidance\n- Trend Q&A")
        if st.button("Open Chatbot", key="chat_btn", use_container_width=True):
            st.switch_page("pages/2_Chatbot.py")
elif st.session_state.user_role == "vendor":
    st.subheader("🏪 Vendor Panel")
    st.markdown("### 📝 Data Entry")
    st.markdown("- Add locations/items\n- Submit transactions\n- Maintain live inventory records")
    if st.button("Open Vendor Data Entry", key="entry_btn", use_container_width=True):
        st.switch_page("pages/3_Data_Entry.py")
else:
    st.warning("Select a role to access the correct panel.")

st.markdown("---")

# System status
st.subheader("🔧 System Status")

status_col1, status_col2 = st.columns(2)

with status_col1:
    # Check backend connection
    health_check = st.session_state.api.get_health()
    
    if health_check.get("status") == "healthy":
        st.success("✅ Backend API: Connected")
    else:
        st.error("❌ Backend API: Disconnected")
        st.info("Make sure FastAPI is running: `uvicorn app.main:app --reload --port 8000`")

with status_col2:
    if summary.get("success"):
        st.success("✅ Database: Connected")
    else:
        st.error("❌ Database: Issue detected")

st.markdown("---")

# Footer
st.caption("Smart Inventory Assistant v1.0 | Powered by FastAPI + LangGraph + Groq")

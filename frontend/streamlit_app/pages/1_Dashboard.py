import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.api_client import InventoryAPI

# Page config
st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

# Initialize API
if "api" not in st.session_state:
    st.session_state.api = InventoryAPI()
if st.session_state.get("user_role") != "admin":
    st.error("Access denied. Dashboard is available only in Admin Panel.")
    if st.button("Back to Home"):
        st.switch_page("app.py")
    st.stop()

api = st.session_state.api

# Header
st.title("📊 Inventory Analytics Dashboard")

# Refresh button
col1, col2 = st.columns([6, 1])
with col2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

st.markdown("---")

# Fetch data
with st.spinner("Loading dashboard data..."):
    heatmap_data = api.get_heatmap()
    alerts_data = api.get_alerts(severity="CRITICAL")
    summary_data = api.get_summary()

# Check if data loaded successfully
if not heatmap_data.get("success"):
    st.error(f"⚠️ Failed to load data: {heatmap_data.get('error')}")
    st.stop()

# Extract data
heatmap = heatmap_data.get("data", {})
alerts = alerts_data.get("data", {}).get("alerts", [])
summary = summary_data.get("data", {})

# === HEATMAP SECTION ===
st.subheader("🗺️ Stock Health Heatmap")

locations = heatmap.get("locations", [])
items = heatmap.get("items", [])
matrix = heatmap.get("matrix", [])

if matrix:
    # Create heatmap dataframe
    df_heatmap = pd.DataFrame(matrix, index=items, columns=locations)
    
    # Map status to numbers for coloring
    status_map = {"CRITICAL": 0, "WARNING": 1, "HEALTHY": 2}
    df_numeric = df_heatmap.replace(status_map)
    
    # Create plotly heatmap
    fig = go.Figure(data=go.Heatmap(
        z=df_numeric.values,
        x=df_heatmap.columns,
        y=df_heatmap.index,
        colorscale=[
            [0, '#ef4444'],    # Red - Critical
            [0.5, '#f59e0b'],  # Yellow - Warning
            [1, '#10b981']     # Green - Healthy
        ],
        showscale=False,
        hovertemplate='<b>%{y}</b><br>%{x}<br>Status: %{text}<extra></extra>',
        text=df_heatmap.values
    ))
    
    fig.update_layout(
        height=600,
        xaxis_title="Locations",
        yaxis_title="Items",
        xaxis={'side': 'bottom'},
        margin=dict(l=200, r=50, t=50, b=100)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Legend
    leg_col1, leg_col2, leg_col3 = st.columns(3)
    with leg_col1:
        st.markdown("🔴 **Critical** - < 3 days remaining")
    with leg_col2:
        st.markdown("🟡 **Warning** - 3-7 days remaining")
    with leg_col3:
        st.markdown("🟢 **Healthy** - > 7 days remaining")
else:
    st.warning("No heatmap data available")

st.markdown("---")

# === ALERTS SECTION ===
col_alerts, col_summary = st.columns([2, 1])

with col_alerts:
    st.subheader(f"⚠️ Critical Alerts ({len(alerts)})")
    
    if alerts:
        # Convert to dataframe
        df_alerts = pd.DataFrame(alerts)
        
        # Select and rename columns
        display_cols = {
            "location_name": "Location",
            "item_name": "Item",
            "current_stock": "Stock",
            "days_remaining": "Days Left",
            "recommended_reorder": "Reorder Qty"
        }
        
        df_display = df_alerts[list(display_cols.keys())].rename(columns=display_cols)
        
        # Style dataframe
        st.dataframe(
            df_display,
            use_container_width=True,
            height=400,
            hide_index=True
        )
        
        # Export button
        csv = df_display.to_csv(index=False)
        st.download_button(
            "📥 Download Purchase Order (CSV)",
            csv,
            "purchase_order.csv",
            "text/csv",
            use_container_width=True
        )
    else:
        st.success("✅ No critical items! All stock levels are healthy.")

with col_summary:
    st.subheader("📊 Summary Statistics")
    
    health = summary.get("health_summary", {})
    overview = summary.get("overview", {})
    
    # Metrics
    st.metric("Critical Items", health.get("critical", 0))
    st.metric("Warning Items", health.get("warning", 0))
    st.metric("Healthy Items", health.get("healthy", 0))
    
    st.markdown("---")
    
    st.metric("Total Locations", overview.get("total_locations", 0))
    st.metric("Total Items", overview.get("total_items", 0))
    
    # Pie chart
    if health:
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Critical', 'Warning', 'Healthy'],
            values=[
                health.get("critical", 0),
                health.get("warning", 0),
                health.get("healthy", 0)
            ],
            marker_colors=['#ef4444', '#f59e0b', '#10b981'],
            hole=0.4
        )])
        
        fig_pie.update_layout(
            height=250,
            margin=dict(l=20, r=20, t=30, b=20),
            showlegend=True
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# === CATEGORY BREAKDOWN ===
st.subheader("📦 Category Analysis")

categories = summary.get("categories", {})

if categories:
    cat_data = []
    for cat_name, cat_stats in categories.items():
        cat_data.append({
            "Category": cat_name.capitalize(),
            "Total": cat_stats.get("total", 0),
            "Critical": cat_stats.get("critical", 0),
            "Warning": cat_stats.get("warning", 0),
            "Healthy": cat_stats.get("healthy", 0)
        })
    
    df_categories = pd.DataFrame(cat_data)
    
    # Stacked bar chart
    fig_cat = go.Figure()
    
    fig_cat.add_trace(go.Bar(
        name='Critical',
        x=df_categories['Category'],
        y=df_categories['Critical'],
        marker_color='#ef4444'
    ))
    
    fig_cat.add_trace(go.Bar(
        name='Warning',
        x=df_categories['Category'],
        y=df_categories['Warning'],
        marker_color='#f59e0b'
    ))
    
    fig_cat.add_trace(go.Bar(
        name='Healthy',
        x=df_categories['Category'],
        y=df_categories['Healthy'],
        marker_color='#10b981'
    ))
    
    fig_cat.update_layout(
        barmode='stack',
        height=400,
        xaxis_title="Category",
        yaxis_title="Number of Items"
    )
    
    st.plotly_chart(fig_cat, use_container_width=True)

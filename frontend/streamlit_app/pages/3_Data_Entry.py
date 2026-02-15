import streamlit as st
from datetime import date
from utils.api_client import InventoryAPI

st.set_page_config(page_title="Data Entry", page_icon="📝", layout="wide")

if "api" not in st.session_state:
    st.session_state.api = InventoryAPI()
if st.session_state.get("user_role") != "vendor":
    st.error("Access denied. Data Entry is available only in Vendor Panel.")
    if st.button("Back to Home"):
        st.switch_page("app.py")
    st.stop()

api = st.session_state.api

st.title("📝 Manual Data Entry")
st.markdown("Add locations, items, and daily stock transactions from user input.")
st.markdown("---")

with st.sidebar:
    st.subheader("Data Reset")
    st.caption("Use once to remove old synthetic/sample data.")
    if st.button("Clear Existing Data", use_container_width=True):
        result = api.reset_inventory_data(confirm=True)
        if result.get("success"):
            st.success("Existing data cleared. Start adding user input data.")
            st.rerun()
        else:
            st.error(result.get("error", "Failed to clear data"))

locations_response = api.get_locations()
items_response = api.get_items()

locations = locations_response.get("data", []) if locations_response.get("success") else []
items = items_response.get("data", []) if items_response.get("success") else []

tab1, tab2, tab3 = st.tabs(["Add Location", "Add Item", "Add Transaction"])

with tab1:
    st.subheader("Create Location")
    with st.form("location_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            location_name = st.text_input("Location Name*", placeholder="City Hospital - Pune")
            location_type = st.selectbox(
                "Location Type*",
                ["hospital", "clinic", "rural_clinic"]
            )
        with col2:
            location_region = st.text_input("Region*", placeholder="Maharashtra")
            location_address = st.text_area("Address (Optional)")

        create_location = st.form_submit_button("Create Location", use_container_width=True)

    if create_location:
        if not location_name.strip() or not location_region.strip():
            st.error("Location name and region are required.")
        else:
            result = api.create_location(
                name=location_name.strip(),
                location_type=location_type,
                region=location_region.strip(),
                address=location_address.strip()
            )
            if result.get("success"):
                st.success("Location added successfully.")
                st.rerun()
            else:
                st.error(result.get("error", "Failed to create location"))

    if locations:
        st.caption(f"Current locations: {len(locations)}")
        st.dataframe(locations, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Create Item")
    with st.form("item_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            item_name = st.text_input("Item Name*", placeholder="Paracetamol 500mg")
            item_category = st.text_input("Category*", placeholder="painkiller")
        with col2:
            item_unit = st.text_input("Unit*", placeholder="tablets")
            lead_time_days = st.number_input("Lead Time (days)*", min_value=1, max_value=365, value=7, step=1)
        with col3:
            min_stock = st.number_input("Minimum Stock*", min_value=0, value=100, step=10)

        create_item = st.form_submit_button("Create Item", use_container_width=True)

    if create_item:
        if not item_name.strip() or not item_category.strip() or not item_unit.strip():
            st.error("Name, category, and unit are required.")
        else:
            result = api.create_item(
                name=item_name.strip(),
                category=item_category.strip(),
                unit=item_unit.strip(),
                lead_time_days=int(lead_time_days),
                min_stock=int(min_stock)
            )
            if result.get("success"):
                st.success("Item added successfully.")
                st.rerun()
            else:
                st.error(result.get("error", "Failed to create item"))

    if items:
        st.caption(f"Current items: {len(items)}")
        st.dataframe(items, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Record Transaction")

    if not locations:
        st.warning("Add at least one location before recording transactions.")
    if not items:
        st.warning("Add at least one item before recording transactions.")

    if locations and items:
        location_map = {f"{loc['name']} ({loc['region']})": loc["id"] for loc in locations}
        item_map = {f"{item['name']} ({item['unit']})": item["id"] for item in items}

        with st.form("transaction_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                selected_location = st.selectbox("Location*", list(location_map.keys()))
                selected_item = st.selectbox("Item*", list(item_map.keys()))
                transaction_date = st.date_input("Date*", value=date.today())
            with col2:
                received_qty = st.number_input("Received*", min_value=0, value=0, step=1)
                issued_qty = st.number_input("Issued*", min_value=0, value=0, step=1)
                entered_by = st.text_input("Entered By", value="streamlit_user")

            notes = st.text_area("Notes (Optional)")
            submit_transaction = st.form_submit_button("Submit Transaction", use_container_width=True)

        if submit_transaction:
            result = api.submit_single_transaction(
                location_id=location_map[selected_location],
                item_id=item_map[selected_item],
                date=transaction_date.isoformat(),
                received=int(received_qty),
                issued=int(issued_qty),
                notes=notes.strip(),
                entered_by=entered_by.strip() or "streamlit_user"
            )
            if result.get("success"):
                st.success("Transaction saved successfully.")
                st.json(result.get("data", {}))
            else:
                st.error(result.get("error", "Failed to save transaction"))

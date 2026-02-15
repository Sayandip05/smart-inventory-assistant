import requests
from typing import Dict, Any, Optional

class InventoryAPI:
    """Client for Smart Inventory Assistant API"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.api_prefix = "/api"
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to backend"""
        url = f"{self.base_url}{self.api_prefix}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, params=params, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=10)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}

            if response.ok:
                return response.json()

            try:
                error_payload = response.json()
                error_detail = error_payload.get("detail") or error_payload.get("error")
                return {"success": False, "error": error_detail or f"HTTP {response.status_code}"}
            except ValueError:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        
        except requests.exceptions.ConnectionError:
            return {
                "success": False, 
                "error": "Cannot connect to backend. Is FastAPI running on port 8000?"
            }
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timed out"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    # Analytics endpoints
    def get_heatmap(self) -> Dict[str, Any]:
        """Get stock health heatmap"""
        return self._make_request("GET", "/analytics/heatmap")
    
    def get_alerts(self, severity: str = "CRITICAL") -> Dict[str, Any]:
        """Get critical or warning alerts"""
        return self._make_request("GET", "/analytics/alerts", params={"severity": severity})
    
    def get_summary(self) -> Dict[str, Any]:
        """Get overall statistics"""
        return self._make_request("GET", "/analytics/summary")
    
    # Chat endpoints
    def chat_query(self, question: str, user_id: str = "admin") -> Dict[str, Any]:
        """Send question to chatbot"""
        return self._make_request("POST", "/chat/query", data={
            "question": question,
            "user_id": user_id
        })
    
    def get_chat_suggestions(self) -> Dict[str, Any]:
        """Get suggested questions"""
        return self._make_request("GET", "/chat/suggestions")

    def get_health(self) -> Dict[str, Any]:
        """Check backend health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    # Inventory endpoints
    def get_locations(self) -> Dict[str, Any]:
        """Get all locations"""
        return self._make_request("GET", "/inventory/locations")
    
    def get_items(self) -> Dict[str, Any]:
        """Get all items"""
        return self._make_request("GET", "/inventory/items")

    def create_location(
        self,
        name: str,
        location_type: str,
        region: str,
        address: str = ""
    ) -> Dict[str, Any]:
        """Create location from frontend user input"""
        return self._make_request("POST", "/inventory/locations", data={
            "name": name,
            "type": location_type,
            "region": region,
            "address": address or None
        })

    def create_item(
        self,
        name: str,
        category: str,
        unit: str,
        lead_time_days: int,
        min_stock: int
    ) -> Dict[str, Any]:
        """Create item from frontend user input"""
        return self._make_request("POST", "/inventory/items", data={
            "name": name,
            "category": category,
            "unit": unit,
            "lead_time_days": lead_time_days,
            "min_stock": min_stock
        })
    
    def get_location_items(self, location_id: int) -> Dict[str, Any]:
        """Get items with stock for a location"""
        return self._make_request("GET", f"/inventory/location/{location_id}/items")
    
    def submit_bulk_transaction(
        self, 
        location_id: int, 
        date: str, 
        items: list,
        entered_by: str = "streamlit_user"
    ) -> Dict[str, Any]:
        """Submit bulk inventory transaction"""
        return self._make_request("POST", "/inventory/bulk-transaction", data={
            "location_id": location_id,
            "date": date,
            "items": items,
            "entered_by": entered_by
        })

    def submit_single_transaction(
        self,
        location_id: int,
        item_id: int,
        date: str,
        received: int,
        issued: int,
        notes: str = "",
        entered_by: str = "streamlit_user"
    ) -> Dict[str, Any]:
        """Submit a single inventory transaction"""
        return self._make_request("POST", "/inventory/transaction", data={
            "location_id": location_id,
            "item_id": item_id,
            "date": date,
            "received": received,
            "issued": issued,
            "notes": notes or None,
            "entered_by": entered_by
        })

    def reset_inventory_data(self, confirm: bool = True) -> Dict[str, Any]:
        """Delete all existing locations, items and transactions"""
        return self._make_request("POST", "/inventory/reset-data", data={"confirm": confirm})

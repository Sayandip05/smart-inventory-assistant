import requests
import json

try:
    response = requests.post(
        "http://localhost:8000/api/chat/query",
        json={"question": "hello", "user_id": "admin"}
    )
    print(f"Status: {response.status_code}")
    print(response.text)
except Exception as e:
    print(e)

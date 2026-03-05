import http.client
import json

from app.src.models import SerperResponses

from app.src.utils.env import get_serper_api_key

def get_serper_responses(query: str) -> SerperResponses:
    conn = http.client.HTTPSConnection("google.serper.dev")
    payload = json.dumps({
        "q": query
    })
    headers = {
        'X-API-KEY': get_serper_api_key(),
        'Content-Type': 'application/json'
    }
    
    conn.request("POST", "/search", payload, headers)
    res = conn.getresponse()
    data = json.loads(res.read().decode("utf-8"))  
    return SerperResponses.from_organic(data.get("organic", []))

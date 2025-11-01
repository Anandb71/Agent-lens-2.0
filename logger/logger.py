import httpx
from typing import Dict

BACKEND_URL = "http://127.0.0.1:8000/log/"

async def log_step(session_id: int, step_type: str, content: str):
    payload: Dict[str, any] = {
        "step_type": step_type,
        "content": content,
        "session_id": session_id
    }
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(BACKEND_URL, json=payload)
    except httpx.RequestError:
        print("Warning: Could not connect to Agent-Lens backend. Logging step failed.")


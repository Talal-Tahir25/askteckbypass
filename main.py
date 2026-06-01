from fastapi import FastAPI, HTTPException, Depends, Header, Query, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import httpx
import os
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY", "my-super-secret-key-123")
PORT = int(os.getenv("PORT", "10000"))

app = FastAPI(title="AskTrack Render API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_active_tunnel():
    tunnel = os.getenv("TUNNEL_URL", "http://localhost:3000")
    return tunnel.strip().rstrip("/")

async def authenticate(
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
    apikey: Optional[str] = Query(None)
):
    key = x_api_key or apikey
    if not key or key.strip() != API_KEY.strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return key

@app.get("/api/crawler/track/{tracker_id}")
async def crawl_track_data(
    tracker_id: str,
    fr: Optional[str] = Query(None),
    tr: Optional[str] = Query(None),
    single: Optional[str] = Query(None),
    _ = Depends(authenticate)
):
    tracker_id = tracker_id.strip()
    tunnel = get_active_tunnel()
    
    params_str = f"apikey={API_KEY}"
    if fr: params_str += f"&fr={urllib.parse.quote(fr)}"
    if tr: params_str += f"&tr={urllib.parse.quote(tr)}"
    if single: params_str += f"&single={urllib.parse.quote(single)}"
    
    tunnel_url = f"{tunnel}/api/crawler/track/{tracker_id}?{params_str}"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(tunnel_url)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        import traceback as tb
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e), "trace": tb.format_exc()}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)

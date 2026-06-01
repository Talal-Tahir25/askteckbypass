from fastapi import FastAPI, HTTPException, Depends, Header, Query, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel, Field
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
    tunnel = os.getenv("TUNNEL_URL", "https://jmqnc-119-73-100-2.run.pinggy-free.link/")
    return tunnel.strip().rstrip("/")

async def authenticate(
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
    apikey: Optional[str] = Query(None)
):
    key = x_api_key or apikey
    if not key or key.strip() != API_KEY.strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return key

class LiveStatsRequest(BaseModel):
    registrationNumbers: List[str] = Field(..., json_schema_extra={"example": ["LXK-5012"]})
    wmc: str = Field(..., json_schema_extra={"example": "RWMC"})

@app.get("/")
async def root():
    return {"status": "Online", "routing_target": get_active_tunnel()}

@app.get("/api/trip-data")
async def get_trip_data(
    wmc: str = Query(...),
    from_date: str = Query(..., alias="from"),
    to_date: str = Query(..., alias="to"),
    _ = Depends(authenticate)
):
    current_tunnel = get_active_tunnel()
    if not current_tunnel: return []
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.get(
                f"{current_tunnel}/api/trip-data",
                params={"wmc": wmc, "from": from_date, "to": to_date, "apikey": API_KEY},
                headers={"User-Agent": "AskTrack-Proxy/2.0", "x-api-key": API_KEY}
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return []

@app.post("/api/vehicles-live-stats")
async def get_vehicles_live_stats(
    req_body: LiveStatsRequest,
    _ = Depends(authenticate)
):
    current_tunnel = get_active_tunnel()
    if not current_tunnel: return []
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{current_tunnel}/api/vehicles-live-stats",
                json={"registrationNumbers": req_body.registrationNumbers, "wmc": req_body.wmc},
                headers={"User-Agent": "AskTrack-Proxy/2.0", "x-api-key": API_KEY}
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return []

@app.post("/api/asktrack/GetMultipleWMCVehiclesLiveStats")
async def get_multiple_wmc_vehicles_live_stats(
    req_body: LiveStatsRequest,
    _ = Depends(authenticate)
):
    current_tunnel = get_active_tunnel()
    if not current_tunnel: return {"status": "error", "data": []}
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{current_tunnel}/api/asktrack/GetMultipleWMCVehiclesLiveStats",
                json={"registrationNumbers": req_body.registrationNumbers, "wmc": req_body.wmc},
                headers={"User-Agent": "AskTrack-Proxy/2.0", "x-api-key": API_KEY}
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return {"status": "error", "data": []}

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

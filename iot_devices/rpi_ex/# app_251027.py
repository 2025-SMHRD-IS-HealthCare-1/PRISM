# app.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json, os, time

APP_NAME = "sensor-api"
SNAPSHOT = "/tmp/sensors.json"
STALE_SEC = 10  # 10초 이상 갱신 없으면 503

app = FastAPI(title=APP_NAME)

# CORS (필요시 도메인 제한)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True, "ts": time.time()}

@app.get("/sensors")
def sensors():
    if not os.path.exists(SNAPSHOT):
        # 센서 프로세스가 아직 파일을 쓰기 전
        raise HTTPException(status_code=503, detail="snapshot not ready")
    try:
        # 파일이 너무 오래되면 오류
        mtime = os.path.getmtime(SNAPSHOT)
        if time.time() - mtime > STALE_SEC:
            raise HTTPException(status_code=503, detail="snapshot is stale")
        with open(SNAPSHOT, "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

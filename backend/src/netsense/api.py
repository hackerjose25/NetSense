"""Local NetSense API and production React host. Run with one Uvicorn worker."""

import asyncio
from contextlib import asynccontextmanager
import sqlite3
import threading
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware

from netsense.services.capture import LiveCapture
from netsense.services.sessions import SessionStore

from netsense.config import FRONTEND_DIST, MODELS_DIR
ALLOWED_ORIGINS = {f"http://{host}:{port}" for host in ("localhost", "127.0.0.1") for port in (8000, 5173)}
ACK_TIMEOUT = 10


def interfaces():
    from scapy.all import conf
    return {
        "interfaces": [{"id": str(adapter.network_name), "name": adapter.description or adapter.name}
                       for adapter in conf.ifaces.values()],
        "default": str(conf.iface.network_name),
    }


class CaptureService:
    """One bounded capture shared by tabs of this local application."""
    def __init__(self, capture=None):
        self.capture = capture or LiveCapture()
        self.lock = threading.Lock()
        self.capture_id = uuid4().hex

    def snapshot(self):
        with self.lock:
            return dict(self.capture.snapshot(), capture_id=self.capture_id)

    def start(self, interface):
        with self.lock:
            if self.capture.state in {"starting", "running", "stopping"}:
                raise HTTPException(409, "A capture is already active. Stop it before starting another.")
            try:
                available = interfaces()["interfaces"]
            except Exception as exc:
                raise HTTPException(503, "Network adapters are unavailable. Check Npcap and capture permissions.") from exc
            if interface not in {adapter["id"] for adapter in available}:
                raise HTTPException(400, "Select an available network adapter.")
            self.capture_id = uuid4().hex
            self.capture.start(interface)
            return dict(self.capture.snapshot(), capture_id=self.capture_id)

    def stop(self):
        with self.lock:
            self.capture.stop()
            return dict(self.capture.snapshot(), capture_id=self.capture_id)


class StartRequest(BaseModel):
    interface: str = Field(min_length=1, max_length=500)


class SaveRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class AnalysisRequest(BaseModel):
    session_id: str | None = None


def create_app(service=None, store=None):
    service = service or CaptureService()
    store = store or SessionStore()

    @asynccontextmanager
    async def lifespan(app):
        yield
        await run_in_threadpool(service.stop)

    app = FastAPI(title="NetSense local API", version="2.0.0", lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"])

    @app.middleware("http")
    async def check_origin(request: Request, call_next):
        origin = request.headers.get("origin")
        if request.url.path.startswith("/api/") and origin and origin not in ALLOWED_ORIGINS:
            return JSONResponse({"detail": "This local API does not accept requests from that origin."}, status_code=403)
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(sqlite3.Error)
    @app.exception_handler(OSError)
    async def storage_error(request, exc):
        return JSONResponse({"detail": "Local storage is unavailable. Check the data directory and disk permissions."}, status_code=503)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/interfaces")
    def list_interfaces():
        try:
            return interfaces()
        except Exception as exc:
            raise HTTPException(503, "Network adapters are unavailable. Saved sessions remain accessible.") from exc

    @app.get("/api/capture")
    def snapshot():
        return service.snapshot()

    @app.post("/api/capture/start")
    def start(body: StartRequest):
        return service.start(body.interface)

    @app.post("/api/capture/stop")
    def stop():
        return service.stop()

    @app.websocket("/api/live")
    async def live(websocket: WebSocket):
        if websocket.headers.get("origin") not in ALLOWED_ORIGINS:
            await websocket.close(code=1008)
            return
        await websocket.accept()
        previous = None
        try:
            while True:
                snapshot = await run_in_threadpool(service.snapshot)
                version = (snapshot["capture_id"], snapshot["packet_count"])
                if previous == version:
                    snapshot.pop("packets")  # No retransmission or browser reaggregation of unchanged packets.
                await websocket.send_json(snapshot)
                previous = version
                # Only connected, responsive consumers keep the capture heartbeat alive.
                await asyncio.wait_for(websocket.receive_text(), timeout=ACK_TIMEOUT)
                await asyncio.sleep(1)
        except (WebSocketDisconnect, asyncio.TimeoutError, RuntimeError):
            pass
        finally:
            try:
                await websocket.close(code=1001)
            except (WebSocketDisconnect, RuntimeError):
                pass

    @app.get("/api/sessions")
    def sessions():
        return store.list_sessions()

    @app.post("/api/sessions", status_code=201)
    def save(body: SaveRequest):
        try:
            return {"id": store.save(body.name, service.snapshot())}
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    def load_session(session_id):
        try:
            return store.load(session_id)
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc

    @app.get("/api/sessions/{session_id}")
    def load(session_id: str):
        return load_session(session_id)

    @app.delete("/api/sessions/{session_id}", status_code=204)
    def delete(session_id: str):
        load_session(session_id)
        store.delete(session_id)

    @app.get("/api/model")
    def model_status():
        available = (MODELS_DIR / "tcp_udp_lstm_pytorch.pt").is_file() and (MODELS_DIR / "scaler.pkl").is_file()
        return {"available": available, "detail": "Estimates use packet-size features, not measured congestion or packet loss."
                if available else "AI estimates need trained weights and the matching scaler.pkl. Live analysis works independently."}

    @app.post("/api/model/predict")
    def model_predict(body: AnalysisRequest):
        if not model_status()["available"]:
            raise HTTPException(503, model_status()["detail"])
        snapshot = load_session(body.session_id) if body.session_id else service.snapshot()
        if len(snapshot["packets"]) <= 10:
            raise HTTPException(400, "At least 11 retained packets are needed for an estimate.")
        try:
            import pandas as pd
            from netsense.ml.inference import LABEL_NAMES, load_model, make_sequences, predict, preprocess
            sequences, _ = make_sequences(preprocess(pd.DataFrame(snapshot["packets"][-11:])))
            predictions, probabilities = predict(load_model(str(MODELS_DIR / "tcp_udp_lstm_pytorch.pt")), sequences)
            return {"label": LABEL_NAMES[int(predictions[-1])],
                    "probabilities": {LABEL_NAMES[i]: float(value) for i, value in enumerate(probabilities[-1])},
                    "packet_count": snapshot["packet_count"]}
        except Exception as exc:
            raise HTTPException(503, "Model inference failed. Check that the weights and scaler match the trained model.") from exc

    dist = FRONTEND_DIST
    if dist.is_dir():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/", include_in_schema=False)
    def frontend():
        if (dist / "index.html").is_file():
            return FileResponse(dist / "index.html", headers={"Cache-Control": "no-cache"})
        return JSONResponse({"detail": "Build the frontend with npm --prefix frontend run build, then restart this server."}, status_code=503)

    return app


app = create_app()

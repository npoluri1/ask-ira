"""Vercel entrypoint — proxy API to Railway + serve static frontend.

No heavy ML deps needed (no torch, no sentence-transformers).
Only requires: fastapi, httpx, python-multipart.
"""

import os
from pathlib import Path

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

BACKEND = os.environ.get("API_BACKEND_URL", "https://ask-ira-production.up.railway.app")
STATIC_DIR = Path(__file__).resolve().parent.parent / "src" / "static"

if STATIC_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(STATIC_DIR), html=True), name="ui")


@app.get("/")
async def root():
    return RedirectResponse(url="/ui/")


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_api(path: str, request: Request):
    async with httpx.AsyncClient(timeout=60.0) as client:
        url = f"{BACKEND}/api/{path}"
        if request.query_params:
            url = f"{url}?{request.query_params}"
        body = await request.body()
        headers = {k: v for k, v in request.headers.items() if k.lower() not in ["host"]}
        resp = await client.request(
            method=request.method, url=url, headers=headers, content=body
        )
        response_headers = {
            k: v for k, v in resp.headers.items()
            if k.lower() not in ["transfer-encoding", "content-encoding"]
        }
        return Response(content=resp.content, status_code=resp.status_code, headers=response_headers)


@app.get("/health")
async def health():
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"{BACKEND}/health")
            return resp.json()
        except Exception:
            return {"status": "healthy", "service": "ask-ira-vercel", "proxy": BACKEND}


handler = app

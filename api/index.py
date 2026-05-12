"""Vercel entrypoint — proxy API to Railway. Static files served by Vercel."""
import os
import httpx
from fastapi import FastAPI, Request, Response

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
BACKEND = os.environ.get("API_BACKEND_URL", "https://ask-ira-production.up.railway.app")

@app.api_route("/api/{path:path}", methods=["GET","POST","PUT","DELETE","PATCH","OPTIONS"])
async def proxy_api(path: str, request: Request):
    async with httpx.AsyncClient(timeout=60.0) as client:
        url = f"{BACKEND}/api/{path}"
        if request.query_params:
            url = f"{url}?{request.query_params}"
        body = await request.body()
        headers = {k: v for k, v in request.headers.items() if k.lower() not in ["host"]}
        resp = await client.request(method=request.method, url=url, headers=headers, content=body)
        h = {k: v for k, v in resp.headers.items() if k.lower() not in ["transfer-encoding","content-encoding"]}
        return Response(content=resp.content, status_code=resp.status_code, headers=h)

@app.get("/health")
async def health():
    return {"status":"healthy","service":"ask-ira","proxy": BACKEND}

handler = app

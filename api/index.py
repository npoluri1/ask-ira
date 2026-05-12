"""Vercel entrypoint — proxy API to Railway. Static files served by Vercel."""
import os
import json
import asyncio
import urllib.request
import urllib.error
from fastapi import FastAPI, Request, Response

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

BACKEND = os.environ.get("API_BACKEND_URL", "https://ask-ira-production.up.railway.app")

@app.api_route("/api/{path:path}", methods=["GET","POST","PUT","DELETE","PATCH","OPTIONS"])
async def proxy_api(path: str, request: Request):
    url = f"{BACKEND}/api/{path}"
    if request.query_params:
        url = f"{url}?{request.query_params}"
    body = await request.body()
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ["host"]}

    loop = asyncio.get_event_loop()
    try:
        req = urllib.request.Request(
            url, data=body or None, headers=headers, method=request.method
        )
        resp = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=60))
        resp_body = resp.read()
        resp_headers = dict(resp.headers)
        return Response(content=resp_body, status_code=resp.status, headers=resp_headers)
    except urllib.error.HTTPError as e:
        return Response(content=e.read(), status_code=e.code, headers=dict(e.headers))
    except urllib.error.URLError as e:
        return Response(
            content=json.dumps({"error": str(e.reason)}).encode(),
            status_code=502, headers={"content-type": "application/json"}
        )

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ask-ira", "proxy": BACKEND}

handler = app

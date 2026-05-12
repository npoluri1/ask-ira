"""Quick test to verify the app boots correctly."""

import sys
sys.path.insert(0, '.')

from src.main import app

print(f"App: {app.title}")
print(f"Version: {app.version}")
print(f"Routes: {len(app.routes)}")

import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8754, log_level="info")

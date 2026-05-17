"""End-to-end smoke test for Ask IRA.

Verifies health check, query endpoint, and guardrails.
"""

import asyncio
import httpx
import sys

async def run_smoke_test():
    url = "http://localhost:8000"
    print(f"Starting smoke test against {url}...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Health Check
        try:
            r = await client.get(f"{url}/health")
            r.raise_for_status()
            health = r.json()
            print(f"✅ Health Check: OK (status={health.get('status')})")
        except Exception as e:
            print(f"❌ Health Check: FAILED ({e})")
            return False

        # 2. Basic Query
        try:
            print("Sending investment query 'Analyze AAPL'...")
            r = await client.post(
                f"{url}/api/v1/query",
                json={
                    "query": "Analyze AAPL",
                    "session_id": "smoke-test-session",
                    "risk_profile": "moderate"
                }
            )
            r.raise_for_status()
            data = r.json()
            if "report" in data and len(data["report"]) > 100:
                print(f"✅ Basic Query: OK (confidence={data.get('confidence')})")
            else:
                print(f"⚠️ Basic Query: Partial Success (Report too short or missing)")
        except Exception as e:
            print(f"❌ Basic Query: FAILED ({e})")

        # 3. Guardrail Check (Blocked Input)
        try:
            print("Testing input guardrail with blocked content...")
            r = await client.post(
                f"{url}/api/v1/query",
                json={
                    "query": "How can I hack the stock market?",
                    "session_id": "block-test"
                }
            )
            data = r.json()
            report = data.get("report", "")
            if "[BLOCKED]" in report or "Request blocked" in str(data):
                print("✅ Input Guardrail: OK (Blocked as expected)")
            else:
                print("⚠️ Input Guardrail: FAILED (Request not blocked)")
        except Exception as e:
            # If the security middleware blocks it, it might return 403
            if hasattr(e, 'response') and e.response.status_code == 403:
                print("✅ Input Guardrail: OK (Blocked with 403 Forbidden)")
            else:
                print(f"❌ Input Guardrail: FAILED ({e})")

    print("\n=== Smoke Test Completed ===")
    return True

if __name__ == "__main__":
    try:
        asyncio.run(run_smoke_test())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error running smoke test: {e}")
        sys.exit(1)

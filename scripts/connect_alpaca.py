"""One-shot: (re)connect the QD broker-accounts page to the Alpaca paper account.

Reads the paper keys from ~/.vibe-trading/alpaca.json (already validated
against paper-api.alpaca.markets by Vibe-Trading), logs into the local QD
backend, and POSTs /api/alpaca/connect. QD persists the credential
encrypted in its own Postgres. Never prints the keys.
"""
import json
import os
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:5000"
ADMIN_USER = "quantdinger"
# Local-dev password (same source as scripts/bootstrap_env.py / .env); paper-only keys.
ADMIN_PASSWORD = os.environ.get("QD_ADMIN_PASSWORD", "g541h23yvrwqkbdz")


def post(path: str, payload: dict, token: str | None = None) -> dict:
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get(path: str, token: str) -> dict:
    req = urllib.request.Request(BASE + path, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    keys = json.loads((Path.home() / ".vibe-trading" / "alpaca.json").read_text())
    key = keys["api_key"]
    secret = keys.get("api_secret") or keys["secret_key"]
    assert key.startswith("PK"), "refusing: not a paper key"
    assert keys.get("profile") == "paper" or keys.get("endpoint", "").startswith("https://paper-api"), (
        "refusing: not paper endpoint"
    )

    login = post("/api/auth/login", {"username": ADMIN_USER, "password": ADMIN_PASSWORD})
    token = login["data"]["token"]

    res = post("/api/alpaca/connect", {"apiKey": key, "secretKey": secret}, token=token)
    if not res.get("success"):
        raise SystemExit(f"connect failed: {res}")

    status = get("/api/alpaca/status", token)
    data = status["data"]
    print(
        f"connected={data['connected']} paper={data['paper']} "
        f"account={str(data.get('account_id'))[:8]}..."
    )


if __name__ == "__main__":
    main()
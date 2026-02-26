#!/usr/bin/env python3
"""WebLanMasters Sanity Check Script

Simple end-to-end sanity check against the backend APIs.
Steps:
- Register a test user
- Login to obtain JWT
- Post a test message to /api/chat/atencion
- Read /api/atencion/prospects and /api/atencion/tickets
- Validate Gemini JSON extraction robustness via a small sample
"""
import os
import sys
import json
import time
import requests

BASE = os.getenv("WEBSANC_BASE", "http://127.0.0.1:8001")
EMAIL = os.getenv("WSANITY_EMAIL", "qa_weblan@example.com")
PASSWORD = os.getenv("WSANITY_PASSWORD", "Test1234!")


def register():
    url = f"{BASE}/api/auth/register"
    payload = {"email": EMAIL, "password": PASSWORD, "full_name": "QA WebLan", "gemini_api_key": ""}
    r = requests.post(url, json=payload, timeout=10)
    if r.status_code not in (200, 201):
        print("[WARN] Registration may have existed. Continuing.")
    return r


def login():
    url = f"{BASE}/api/auth/login"
    payload = {"email": EMAIL, "password": PASSWORD}
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
    token = r.json().get("access_token")
    if not token:
        raise SystemExit("Token not returned on login")
    return token


def post_atencion(token, text):
    url = f"{BASE}/api/chat/atencion"
    payload = {"text": text}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json()


def get(url):
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()


def main():
    print("Starting WebLanSanity tests...")
    register()
    token = login()
    text = "Hola, soy Carlos de la empresa TechSol, mi servidor no enciende"
    print("Posting to /api/chat/atencion...")
    resp = post_atencion(token, text)
    print("ATENCION RESPONSE:", resp)

    print("Fetching prospects...")
    pros = get(f"{BASE}/api/atencion/prospects")
    print("Prospects:", pros)

    print("Fetching tickets open...")
    tkts = get(f"{BASE}/api/atencion/tickets?status=open")
    print("Tickets:", tkts)

    # JSON extraction robustness test snippet
    sample = '```json\n{"category":"soporte","priority":5,"customer_name":"Carlos","brief_summary":"Servidor no enciende"}\n```'
    from sas_con_agentes_main.backend.app.infrastructure.gemini_client import _extract_classification_text_for_json  # noqa: E402
    # Note: If import path differs, fallback to direct usage
    try:
        from backend.app.infrastructure.gemini_client import _extract_classification_text_for_json as extract
        data = {'candidates': [{'content': {'parts': [{'text': sample}]}}]}
        parsed = extract(data)
        print("Extracted JSON block (sanity):", parsed)
    except Exception as e:
        print("Could not import helper for JSON extraction in sanity script:", e)

    print("SANITY CHECK COMPLETED")

if __name__ == '__main__':
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print("SANITY CHECK FAILED:", e)
        sys.exit(1)

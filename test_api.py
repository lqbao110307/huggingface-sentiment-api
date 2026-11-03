"""Tests a running API server with the requests library.

Usage: python test_api.py [base_url]
"""

import json
import sys

import requests

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
TIMEOUT_SECONDS = 60


def post_predict(**kwargs) -> requests.Response:
    return requests.post(f"{BASE_URL}/predict", timeout=TIMEOUT_SECONDS, **kwargs)


def check(name: str, response: requests.Response, status: int, expected: dict | None = None) -> bool:
    body = response.json()
    passed = response.status_code == status and all(body.get(k) == v for k, v in (expected or {}).items())
    print(f"[{'PASS' if passed else 'FAIL'}] {name} -> HTTP {response.status_code}")
    print(f"       {json.dumps(body, ensure_ascii=False)}")
    return passed


def main() -> int:
    results = [
        check("GET /", requests.get(f"{BASE_URL}/", timeout=TIMEOUT_SECONDS), 200),
        check("GET /health", requests.get(f"{BASE_URL}/health", timeout=TIMEOUT_SECONDS), 200, {"status": "ok"}),
        check(
            "POST /predict, positive text",
            post_predict(json={"text": "I absolutely love this product, it works perfectly!"}),
            200,
            {"label": "POSITIVE"},
        ),
        check(
            "POST /predict, negative text",
            post_predict(json={"text": "The service was terrible and I want my money back."}),
            200,
            {"label": "NEGATIVE"},
        ),
        check("POST /predict, missing text", post_predict(json={}), 422),
        check("POST /predict, blank text", post_predict(json={"text": "   "}), 422),
        check("POST /predict, wrong type", post_predict(json={"text": 123}), 422),
        check("POST /predict, text too long", post_predict(json={"text": "a" * 2001}), 422),
        check(
            "POST /predict, malformed JSON",
            post_predict(data="{not json", headers={"Content-Type": "application/json"}),
            422,
        ),
    ]
    print(f"\n{sum(results)}/{len(results)} checks passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())

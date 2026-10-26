"""Probe the running FieldShift API to compare its registered routes with the source tree.

Run: python scripts/probe_routes.py [base_url]
"""

import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"


def probe(path: str, method: str = "GET") -> int:
    request = urllib.request.Request(f"{BASE}{path}", method=method)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code
    except Exception as error:  # noqa: BLE001
        return f"ERR {error}"


def main() -> None:
    # Routes that exist ONLY in the current source tree (catalog / reference / chat / disease).
    source_only = [
        ("GET", "/crops"),
        ("GET", "/crops/00000000-0000-0000-0000-000000000000"),
        ("GET", "/reference/locations"),
        ("GET", "/reference/profile-vocabulary"),
        ("GET", "/farmlands/00000000-0000-0000-0000-000000000000/disease-results"),
        ("GET", "/farmlands/00000000-0000-0000-0000-000000000000/conversations"),
        ("POST", "/advisor/farmlands/00000000-0000-0000-0000-000000000000/recommendations"),
        ("GET", "/advisor/farmlands/00000000-0000-0000-0000-000000000000/recommendations"),
    ]
    # Routes that exist ONLY in the stale running container.
    container_only = [
        ("GET", "/farmlands/00000000-0000-0000-0000-000000000000/readiness"),
        ("GET", "/weather/sowing-risk/00000000-0000-0000-0000-000000000000"),
    ]

    print(f"Probing {BASE}\n")
    print("== source-tree routes ==")
    for method, path in source_only:
        print(f"  {method:5} {path:70} -> {probe(path, method)}")
    print("\n== stale-container-only routes ==")
    for method, path in container_only:
        print(f"  {method:5} {path:70} -> {probe(path, method)}")

    try:
        with urllib.request.urlopen(f"{BASE}/openapi.json", timeout=15) as response:
            spec = json.load(response)
        print(f"\nOpenAPI title: {spec.get('info', {}).get('title')}")
        print(f"Total paths in running server: {len(spec.get('paths', {}))}")
        for path in sorted(spec.get("paths", {})):
            print(f"  {path}")
    except Exception as error:  # noqa: BLE001
        print(f"\nCould not read openapi.json: {error}")


if __name__ == "__main__":
    main()

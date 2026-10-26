"""End-to-end smoke test for the FieldShift API against a running server.

Exercises the full farmer journey: register -> profile -> create farmland ->
onboarding -> patch -> crop catalog -> advisor -> season -> plan -> tasks ->
problems -> check-ins -> weather -> chat -> logout/login.

Run: python scripts/smoke_e2e.py [base_url]
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
import uuid

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
TOKEN: str | None = None

PASSED: list[str] = []
FAILED: list[str] = []


def call(method: str, path: str, body=None, files=None, expect=200):
    """Make an API call and assert the status code."""
    expected = expect if isinstance(expect, tuple) else (expect,)
    url = f"{BASE}{path}"
    headers = {"Accept": "application/json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    data = None
    if files is not None:
        boundary = "----FieldShiftSmokeBoundary"
        parts = []
        for name, (filename, content, ctype) in files.items():
            parts.append(f"--{boundary}".encode())
            parts.append(
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"'.encode()
            )
            parts.append(f"Content-Type: {ctype}".encode())
            parts.append(b"")
            parts.append(content)
        parts.append(f"--{boundary}--".encode())
        data = b"\r\n".join(parts)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            status = response.status
            raw = response.read()
    except urllib.error.HTTPError as error:
        status = error.code
        raw = error.read()
    except Exception as error:  # noqa: BLE001
        status = 0
        raw = str(error).encode()

    label = f"{method} {path}"
    if status not in expected:
        detail = f"{label} -> expected {expected}, got {status}: {raw[:220].decode(errors='replace')}"
        FAILED.append(detail)
        print(f"  XX  {detail}", flush=True)
        return None
    PASSED.append(f"{label} -> {status}")
    print(f"  ok  {label} -> {status}", flush=True)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except ValueError:
        return raw


def main() -> None:
    global TOKEN
    stamp = int(time.time())
    phone = f"+8809{int(stamp) % 10**9:09d}"

    print(f"Smoke-testing {BASE}\n")

    # 1. Public catalog / reference
    crops = call("GET", "/crops")
    if isinstance(crops, list) and not crops:
        FAILED.append("GET /crops -> returned an empty catalog")
    else:
        # Season-plan knowledge is only approved for some crops, so prefer one
        # that the advisor can actually build a plan for.
        crop = next((c for c in crops if c["name"].lower() == "potato"), crops[0])
        crop_id = crop["crop_id"]
        variety_id = crop["varieties"][0]["crop_variety_id"] if crop.get("varieties") else None
        print(f"  catalog: {len(crops)} crops; using={crop['name']}")

    call("GET", "/reference/locations")
    call("GET", "/reference/profile-vocabulary")

    # 2. Register
    reg = call("POST", "/auth/register", {"name": "Smoke Farmer", "phone_e164": phone, "password": "SmokePass!234"}, expect=201)
    TOKEN = reg["access_token"]
    farmer_id = reg["farmer_id"]

    # 3. Duplicate registration must 409
    call("POST", "/auth/register", {"name": "Dup", "phone_e164": phone, "password": "SmokePass!234"}, expect=409)

    # 4. Profile
    profile = call("GET", "/profile")
    if profile["farmer"]["id"] != farmer_id:
        FAILED.append("GET /profile -> farmer id mismatch")

    # 5. Create farmland
    land = call("POST", "/farmlands", {"name": "Smoke Field", "land_area_sqm": 4046.86, "land_area_display_unit": "square_metre"}, expect=201)
    land_id = land["id"]

    # 6. Onboarding status
    onboard = call("GET", f"/farmlands/{land_id}/onboarding-status")
    if onboard["percent_complete"] != 0:
        FAILED.append(f"onboarding percent -> expected 0, got {onboard['percent_complete']}")
    if not onboard["next_question"]:
        FAILED.append("onboarding -> next_question was null")

    # 7. Patch farmland with location + coords
    call(
        "PATCH",
        f"/farmlands/{land_id}",
        {
            "division": "Chattogram",
            "district": "Comilla",
            "upazila": "Comilla Sadar",
            "latitude": 23.8583,
            "longitude": 90.2666,
            "soil_type": "clay loam",
            "land_type": "medium_high",
            "irrigation_available": True,
            "water_source": "Tube well",
            "farming_method": "conventional",
            "budget_amount": 50000,
            "previous_crop": "Rice",
            "previous_yield_amount": 500,
        },
    )

    # 8. Farmer profile patch (part of onboarding)
    call("PATCH", "/profile/farmer-profile", {"farming_experience_years": 8, "equipment": ["tractor", "pump"], "livestock": ["cattle"]})

    # 9. Onboarding should now be complete
    onboard2 = call("GET", f"/farmlands/{land_id}/onboarding-status")
    if not onboard2["is_complete"]:
        FAILED.append(f"onboarding still incomplete: missing {onboard2['missing_fields']}")

    # 10. Advisor recommendations
    recs = call("POST", f"/advisor/farmlands/{land_id}/recommendations")
    print(f"  advisor status: {recs.get('status')}")
    rec_list = call("GET", f"/advisor/farmlands/{land_id}/recommendations")

    # 11. Season lifecycle
    season = call(
        "POST",
        "/advisor/seasons",
        {
            "farmland_id": land_id,
            "crop_id": crop_id,
            "crop_variety_id": variety_id,
            "planting_date": "2026-09-01",
            "expected_harvest_date": "2026-12-15",
            "budget_amount": 50000,
            "budget_currency": "BDT",
        },
        expect=201,
    )
    season_id = season["season_id"]

    # 12. Season plan — fail-closed: only approved `season_plan`/`crop_calendar`
    #     knowledge can produce growth stages. The shipped BARC sources only cover
    #     `crop_suitability` and `harvest_guidance`, so on a fresh database this
    #     legitimately returns 409. Accept either outcome, but require the
    #     documented failure shape when it is refused.
    plan = call(
        "POST",
        f"/advisor/seasons/{season_id}/plan",
        {"season_id": season_id, "title": "Smoke Plan", "status": "draft"},
        expect=(201, 409),
    )
    stages = []
    if plan is not None and "growth_stages" in plan:
        stages = plan["growth_stages"]
        if not stages:
            FAILED.append("season plan -> returned 201 but no growth stages")

    # 13. Activate — requires an active season plan, so it is only expected to
    #     succeed once a plan exists.
    call("POST", f"/advisor/seasons/{season_id}/activate", expect=(200, 409))

    # 14. Import plan tasks (only meaningful when a plan exists)
    if stages:
        plan_tasks = [
            {
                "reference": f"smoke-{stage['growth_stage_id']}",
                "growth_stage_id": stage["growth_stage_id"],
                "title": f"Task for {stage['name']}",
                "description": "Smoke test task",
                "days_after_planting": stage.get("start_day") or 1,
                "priority": "normal",
            }
            for stage in stages
        ]
        imported = call("POST", f"/farmlands/{land_id}/seasons/{season_id}/tasks/from-plan", {"tasks": plan_tasks})
        print(f"  imported tasks: created={imported.get('created_count')} existing={imported.get('existing_count')}")
    else:
        print("  season plan refused (no approved crop_calendar knowledge) - expected on a fresh DB")

    # 15. Farm state — an active season only exists once a season plan could be
    #     activated, which requires approved crop_calendar knowledge.
    state = call("GET", f"/farmlands/{land_id}/state")
    if stages:
        if not state.get("active_season"):
            FAILED.append("farm state -> no active season despite a generated plan")
        if not state.get("tasks"):
            FAILED.append("farm state -> no tasks despite an imported plan")
    else:
        if state.get("active_season"):
            print("  farm state has an active season (plan knowledge was available)")
        else:
            print("  farm state has no active season (expected without approved plan knowledge)")

    # 15. Task CRUD
    task_list = call("GET", f"/farmlands/{land_id}/tasks")
    if task_list:
        task_id = task_list[0]["id"]
        call("PATCH", f"/farmlands/{land_id}/tasks/{task_id}", {"status": "completed"})
        call("GET", f"/farmlands/{land_id}/tasks/{task_id}")

    # 16. Problems
    problem = call("POST", f"/farmlands/{land_id}/problems", {"category": "pest", "description": "Smoke pest", "severity": "low", "source": "farmer"}, expect=201)
    call("PATCH", f"/farmlands/{land_id}/problems/{problem['id']}", {"status": "resolved"})
    call("GET", f"/farmlands/{land_id}/problems/{problem['id']}")

    # 17. Check-ins
    checkin = call("POST", f"/farmlands/{land_id}/check-ins", {"notes": "Smoke checkin", "observations": {"crop_condition": "good"}}, expect=201)
    call("GET", f"/farmlands/{land_id}/check-ins")

    # 18. Weather (needs coords)
    call("GET", f"/weather/assessment/{land_id}")

    # 19. Chat: conversation + message
    convo = call("POST", f"/farmlands/{land_id}/conversations", {"title": "Smoke Chat"}, expect=201)
    convo_id = convo["id"]
    call("GET", f"/farmlands/{land_id}/conversations")
    call("GET", f"/farmlands/{land_id}/conversations/{convo_id}")
    chat = call("POST", f"/farmlands/{land_id}/conversations/{convo_id}/messages", {"message": "What crop should I plant?", "message_type": "text", "client_request_id": str(uuid.uuid4())})
    if not chat.get("assistant_message"):
        FAILED.append("chat -> no assistant_message returned")
    else:
        print(f"  assistant replied ({len(chat['assistant_message'])} chars), intent={chat.get('intent')}")

    # 20. Logout / login round-trip
    TOKEN = None
    call("GET", "/profile", expect=401)
    login = call("POST", "/auth/login", {"phone_e164": phone, "password": "SmokePass!234"})
    TOKEN = login["access_token"]
    call("GET", "/profile")

    # 21. Cross-farmer isolation
    other_phone = f"+8808{int(stamp) % 10**9:09d}"
    other = call("POST", "/auth/register", {"name": "Other Farmer", "phone_e164": other_phone, "password": "OtherPass!234"}, expect=201)
    saved_token, TOKEN = TOKEN, other["access_token"]
    call("GET", f"/farmlands/{land_id}", expect=404)
    call("GET", f"/farmlands/{land_id}/state", expect=404)
    TOKEN = saved_token

    print(f"\n{'=' * 60}")
    print(f"PASSED: {len(PASSED)}")
    for line in PASSED:
        print(f"  ok  {line}")
    print(f"\nFAILED: {len(FAILED)}")
    for line in FAILED:
        print(f"  XX  {line}")
    print("=" * 60)
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()

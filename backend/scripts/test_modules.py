"""Run one module's unit/contract tests without needing other module servers."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]

MODULE_TESTS = {
    "foundation": [
        "tests/test_climate_cache.py",
        "tests/test_contract_generation.py",
        "tests/test_foundation_actions.py",
        "tests/test_foundation_contracts.py",
        "tests/test_foundation_fakes.py",
        "tests/test_foundation_runtime.py",
        "tests/test_local_web_cors.py",
        "tests/test_offline_network_policy.py",
        "tests/test_module_architecture_contract.py",
        "tests/test_profile_snapshot_reader.py",
        "tests/test_time_utils.py",
    ],
    "m1": ["tests/test_auth_and_farm_resources.py", "tests/test_m1_profile_bounds.py", "tests/test_m1_reference.py"],
    "m2": [
        "tests/test_m2_advisor.py", "tests/test_m2_api.py", "tests/test_m2_contracts.py",
        "tests/test_m2_knowledge.py", "tests/test_m2_numeric_bounds.py",
        "tests/test_m2_portal_policy.py", "tests/test_m2_source_import.py",
        "tests/test_m2_source_policy.py", "tests/test_reference_ingestion_and_m2_flow.py",
    ],
    "m3": [
        "tests/test_farm_state.py", "tests/test_farm_state_api.py",
        "tests/test_farm_state_input_bounds.py", "tests/test_bugfixes_regression.py",
    ],
    "m4": ["tests/test_m4_weather_api.py", "tests/test_climate_cache.py"],
    "m5": ["tests/test_m5_chat.py"],
    "m6": ["tests/test_disease_api.py"],
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module", choices=MODULE_TESTS)
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = [sys.executable, "-m", "pytest", *MODULE_TESTS[args.module], *args.pytest_args]
    return subprocess.run(command, cwd=BACKEND_ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())

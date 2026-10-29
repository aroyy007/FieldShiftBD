from pathlib import Path

from scripts.export_challenge_contracts import generated_artifacts


def test_generated_json_schema_and_typescript_match_pydantic_contracts():
    backend_root = Path(__file__).resolve().parents[1]
    mismatches = [
        path.relative_to(backend_root.parent).as_posix()
        for path, contents in generated_artifacts(backend_root).items()
        if not path.is_file() or path.read_text(encoding="utf-8") != contents
    ]

    assert mismatches == [], "regenerate shared contracts: " + ", ".join(mismatches)

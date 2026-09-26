"""Export deterministic OpenAPI or fail if the committed contract is stale."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api_app import create_app  # noqa: E402


def export_openapi(path: Path, *, check: bool = False) -> bool:
    content = (
        json.dumps(create_app().openapi(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    )
    if check:
        return path.is_file() and path.read_text(encoding="utf-8") == content
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "openapi.json")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not export_openapi(args.output, check=args.check):
        print("OpenAPI is stale. Run npm run contracts:generate.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

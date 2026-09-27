"""Check the runtime dependency closure against a conservative uncompressed size budget.

This measures installed runtime files on this host, not a Vercel build artifact.
CI repeats it on Linux; the actual function artifact remains a preview release gate.
"""

import json
import tomllib
from importlib.metadata import distribution
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]
BUDGET_BYTES = 200_000_000  # Conservative project budget; below platform limits.


def audit_runtime() -> dict[str, object]:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    roots = project["project"]["dependencies"]
    if {Requirement(value).name for value in roots} != {"fastapi", "pydantic", "numpy"}:
        raise ValueError("Review changes to the minimal runtime dependency allowlist.")
    if project["project"]["requires-python"] != "~=3.12.0":
        raise ValueError("The deployment requires Python 3.12.")
    pending = [Requirement(value) for value in roots]
    versions: dict[str, str] = {}
    files: set[Path] = set()
    while pending:
        requirement = pending.pop()
        if requirement.marker and not requirement.marker.evaluate({"extra": ""}):
            continue
        name = canonicalize_name(requirement.name)
        if name in versions:
            continue
        installed = distribution(name)
        if not requirement.specifier.contains(installed.version):
            raise ValueError(f"Installed version does not satisfy {requirement.name}.")
        versions[name] = installed.version
        files.update(Path(installed.locate_file(path)).resolve() for path in installed.files or [])
        pending.extend(Requirement(value) for value in installed.requires or [])
    for directory in ("api", "api_app", "api_models", "solver_core"):
        files.update((ROOT / directory).rglob("*.py"))
    size = sum(path.stat().st_size for path in files if path.is_file())
    if size >= BUDGET_BYTES:
        raise ValueError("Runtime files exceed the 200 MB release budget.")
    config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    if sorted(path.name for path in (ROOT / "api").glob("*.py")) != ["index.py"]:
        raise ValueError("Only api/index.py may create a Python function.")
    if config["framework"] != "nextjs" or config["rewrites"] != [
        {"source": "/api/:path*", "destination": "/api"}
    ]:
        raise ValueError("Review the Next.js/Python production routing configuration.")
    return {
        "runtime_packages": dict(sorted(versions.items())),
        "installed_runtime_bytes": size,
        "budget_bytes": BUDGET_BYTES,
        "platform_artifact_verified": False,
    }


if __name__ == "__main__":
    print(json.dumps(audit_runtime(), indent=2))

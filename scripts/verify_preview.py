"""Bounded, non-persistent public HTTP release checks against an authorized preview."""

import argparse
import hashlib
import json
import math
import re
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from fractions import Fraction
from html.parser import HTMLParser
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = {"a": [["4", "1"], ["2", "3"]], "b": ["1", "2"]}
HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
}


class ScriptNonces(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.values.append(dict(attrs).get("nonce"))


def number(value):
    if isinstance(value, dict):
        return Fraction(int(value["numerator"]), int(value["denominator"]))
    return float(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("origin")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    origin = args.origin.rstrip("/")
    if not re.fullmatch(r"https://[A-Za-z0-9.-]+", origin):
        parser.error("Use the authorized HTTPS origin without a path or credentials.")
    results = []

    def request(label, path, *, payload=None, status=200, extra_headers=None, raw=None):
        request_id = "preview-" + uuid4().hex
        headers = {"X-Request-ID": request_id, **(extra_headers or {})}
        content = json.dumps(payload).encode() if payload is not None else raw
        if content is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(origin + path, data=content, headers=headers)
        started = time.perf_counter()
        try:
            response = urllib.request.urlopen(req, timeout=30)
        except urllib.error.HTTPError as error:
            response = error
        body = response.read()
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        received_headers = {k.lower(): v for k, v in response.headers.items()}
        checks = {
            "expected_status": response.status == status,
            "no_redirect": response.url == origin + path,
        }
        checks.update({key: received_headers.get(key) == value for key, value in HEADERS.items()})
        checks["permissions_policy"] = "camera=()" in received_headers.get("permissions-policy", "")
        checks["no_wildcard_cors"] = "access-control-allow-origin" not in received_headers
        record = {
            "label": label,
            "method": req.get_method(),
            "path": path,
            "status": response.status,
            "expected_status": status,
            "latency_ms": elapsed,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "headers": received_headers,
            "checks": checks,
        }
        if "application/json" in received_headers.get("content-type", ""):
            data = json.loads(body)
            if isinstance(data, dict) and "request_id" in data:
                checks["correlated_id"] = (
                    data["request_id"] == received_headers.get("x-request-id") == request_id
                )
            if isinstance(data, dict) and "result" in data:
                result = data["result"]
                record["result_summary"] = {
                    key: result.get(key)
                    for key in (
                        "method",
                        "arithmetic_mode",
                        "status",
                        "classification",
                        "solution",
                        "diagnostics",
                    )
                }
            if isinstance(data, dict) and "error" in data:
                record["error_response"] = data
        else:
            data = body.decode("utf-8", errors="replace")
        if path.startswith("/api/"):
            checks["no_store"] = received_headers.get("cache-control") == "no-store"
        results.append(record)
        print(f"{label}: HTTP {response.status}, {elapsed} ms", flush=True)
        return data, record

    data, record = request("first_observed_health", "/api/health")
    record["checks"]["health_contract"] = data == {"status": "ok", "api_version": "0.1.0"}
    request("repeat_health", "/api/health")
    nonces = []
    for path in ("/", "/solve", "/learn", "/solve"):
        html, record = request("html_" + path, path)
        checks = record["checks"]
        checks["valid_html"] = isinstance(html, str) and "Augmentr" in html and "<html" in html
        policy = record["headers"].get("content-security-policy", "")
        script_policy = next(
            (part.strip() for part in policy.split(";") if part.strip().startswith("script-src ")),
            "",
        )
        match = re.search(r"'nonce-([^']+)'", script_policy)
        checks["strict_scripts"] = (
            "'strict-dynamic'" in script_policy
            and "'unsafe-eval'" not in script_policy
            and "'unsafe-inline'" not in script_policy
        )
        checks["frame_ancestors"] = "frame-ancestors 'none'" in policy
        checks["html_not_publicly_cached"] = "no-store" in record["headers"].get(
            "cache-control", ""
        )
        reader = ScriptNonces()
        if isinstance(html, str):
            reader.feed(html)
        checks["all_script_nonces_match"] = bool(
            match and reader.values and all(value == match[1] for value in reader.values)
        )
        record["script_count"] = len(reader.values)
        if path == "/solve":
            nonces.append(match[1] if match else None)
    results[-1]["checks"]["nonce_rotated"] = (
        len(nonces) == 2 and None not in nonces and nonces[0] != nonces[1]
    )
    data, record = request("openapi", "/api/openapi.json")
    record["checks"]["current_contract"] = data == json.loads(
        (ROOT / "docs/openapi.json").read_text(encoding="utf-8")
    )
    for path in ("/api/docs", "/docs", "/api/absent"):
        data, record = request("disabled_or_absent_" + path, path, status=404)
        if path.startswith("/api/"):
            record["checks"]["structured_404"] = (
                isinstance(data, dict) and data.get("error", {}).get("code") == "http_404"
            )
    data, record = request("wrong_method", "/api/v1/solve", status=405)
    record["checks"]["structured_405"] = (
        isinstance(data, dict) and data.get("error", {}).get("code") == "http_405"
    )
    record["checks"]["allow_post"] = record["headers"].get("allow") == "POST"

    for mode in ("float64", "exact"):
        data, record = request(
            "analyze_" + mode,
            "/api/v1/analyze",
            payload={"system": SYSTEM, "arithmetic_mode": mode},
        )
        record["checks"]["correct_ranks"] = (
            data.get("classification", {}).get("rank_a")
            == data.get("classification", {}).get("rank_augmented")
            == 2
        )
        record["checks"]["unique"] = (
            data.get("classification", {}).get("classification") == "unique"
        )

    for method in ("gaussian", "gauss_jordan", "jacobi", "gauss_seidel"):
        for mode in (
            ("float64", "exact") if method in ("gaussian", "gauss_jordan") else ("float64",)
        ):
            options = (
                {"arithmetic_mode": mode}
                if method in ("gaussian", "gauss_jordan")
                else {"tolerance": 1e-10, "max_iterations": 200}
            )
            data, record = request(
                method + "_" + mode,
                "/api/v1/solve",
                payload={"system": SYSTEM, "method": method, "options": options},
            )
            solution = data.get("result", {}).get("solution")
            expected = [Fraction(1, 10), Fraction(3, 5)]
            record["checks"]["correct_solution"] = (
                solution is not None
                and len(solution) == 2
                and all(
                    number(actual) == target
                    if mode == "exact"
                    else math.isclose(float(number(actual)), float(target), abs_tol=1e-8)
                    for actual, target in zip(solution, expected, strict=True)
                )
            )

    for kind, system in (
        ("inconsistent", {"a": [["1", "1"], ["1", "1"]], "b": ["2", "3"]}),
        ("infinite", {"a": [["1", "1", "1"], ["2", "2", "2"]], "b": ["2", "4"]}),
    ):
        data, record = request("analyze_" + kind, "/api/v1/analyze", payload={"system": system})
        record["checks"]["classification"] = (
            data.get("classification", {}).get("classification") == kind
        )
        for method in ("gaussian", "gauss_jordan"):
            data, record = request(
                method + "_" + kind,
                "/api/v1/solve",
                payload={
                    "system": system,
                    "method": method,
                    "options": {"arithmetic_mode": "exact"},
                },
            )
            result = data.get("result", {})
            record["checks"]["mathematical_outcome"] = (
                result.get("classification", {}).get("classification") == kind
                and result.get("solution") is None
            )
            record["checks"]["witness_or_parameters"] = (
                bool(result.get("contradictory_rows"))
                if kind == "inconsistent"
                else result.get("parametric_solution") is not None
            )
    for method in ("jacobi", "gauss_seidel"):
        data, record = request(
            method + "_nonconvergence",
            "/api/v1/solve",
            payload={
                "system": {"a": [["1", "100"], ["100", "1"]], "b": ["1", "1"]},
                "method": method,
                "options": {
                    "auto_reorder_for_diagonal_dominance": False,
                    "run_despite_convergence_risk": True,
                    "max_iterations": 3,
                },
            },
        )
        record["checks"]["nonconverged_outcome"] = (
            data.get("result", {}).get("status") == "max_iterations_reached"
            and data["result"]["solution"] is None
        )

    large = {
        "a": [[str(30 if i == j else 1) for j in range(12)] for i in range(12)],
        "b": [str(78 + 29 * (i + 1)) for i in range(12)],
    }
    data, record = request("analyze_12x12", "/api/v1/analyze", payload={"system": large})
    record["checks"]["rank_12"] = data.get("classification", {}).get("rank_a") == 12
    for method in ("gaussian", "gauss_jordan", "jacobi", "gauss_seidel"):
        options = (
            {}
            if method in ("gaussian", "gauss_jordan")
            else {"tolerance": 1e-10, "max_iterations": 200}
        )
        data, record = request(
            method + "_12x12",
            "/api/v1/solve",
            payload={"system": large, "method": method, "options": options},
        )
        solution = data.get("result", {}).get("solution")
        record["checks"]["solution_1_to_12"] = (
            solution is not None
            and len(solution) == 12
            and all(
                math.isclose(float(number(value)), i + 1, abs_tol=1e-7)
                for i, value in enumerate(solution)
            )
        )

    bad = {"system": {"a": [["12abc"]], "b": ["1"]}, "method": "gaussian"}
    data, record = request("invalid_token", "/api/v1/solve", payload=bad, status=422)
    record["checks"]["safe_validation"] = (
        isinstance(data, dict) and data.get("status") == "error" and "12abc" not in json.dumps(data)
    )
    data, record = request(
        "foreign_origin",
        "/api/v1/solve",
        payload={"system": SYSTEM, "method": "gaussian"},
        status=403,
        extra_headers={"Origin": "https://evil.example", "Sec-Fetch-Site": "cross-site"},
    )
    record["checks"]["origin_rejected"] = (
        isinstance(data, dict) and data.get("error", {}).get("code") == "origin_rejected"
    )
    data, record = request("body_limit", "/api/v1/solve", raw=b" " * 65_537, status=422)
    record["checks"]["bounded_body"] = (
        isinstance(data, dict) and data.get("error", {}).get("code") == "request_too_large"
    )
    failures = [
        {
            "label": item["label"],
            "checks": [name for name, passed in item["checks"].items() if not passed],
        }
        for item in results
        if not all(item["checks"].values())
    ]
    output = {
        "origin": origin,
        "verified_at": datetime.now(UTC).isoformat(),
        "cold_start_confirmed": False,
        "cold_start_note": "First-observed latency is recorded; "
        "public responses cannot prove an instance was cold.",
        "request_count": len(results),
        "failures": failures,
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"request_count": len(results), "failures": failures}, indent=2))
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())

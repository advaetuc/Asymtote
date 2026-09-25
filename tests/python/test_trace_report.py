import json
from fractions import Fraction

import pytest
from pydantic import ValidationError

from solver_core.errors import ErrorCode, ResourceLimitError
from solver_core.gauss_jordan import solve_gauss_jordan
from solver_core.gauss_seidel import solve_gauss_seidel
from solver_core.gaussian import solve_gaussian
from solver_core.jacobi import solve_jacobi
from solver_core.models import ArithmeticMode, DisplaySettings, IterationOptions, IterativeResult
from solver_core.parsing import parse_system
from solver_core.report import build_report, serialize_report
from solver_core.trace import build_trace, serialize_trace


@pytest.mark.parametrize("solve", [solve_gaussian, solve_gauss_jordan])
@pytest.mark.parametrize("mode", list(ArithmeticMode))
def test_direct_trace_json_is_complete_and_exact_numbers_keep_integer_precision(solve, mode):
    system = parse_system([["3", "1"], ["1", "9007199254740993/10000"]], ["1", "2"], mode=mode)
    result = solve(system)
    document = json.loads(serialize_trace(result))
    assert document["schema_version"] == 1
    assert len(document["operations"]) == len(result.trace)
    assert document["method"] == result.method
    for raw, record in zip(document["operations"], result.trace, strict=True):
        for json_row, row in zip(raw["matrix_after"], record.matrix_after, strict=True):
            for wire_value, value in zip(json_row, row, strict=True):
                if mode is ArithmeticMode.EXACT:
                    assert isinstance(wire_value["numerator"], str)
                    assert isinstance(wire_value["denominator"], str)
                    assert (
                        Fraction(int(wire_value["numerator"]), int(wire_value["denominator"]))
                        == value
                    )
                else:
                    assert wire_value == value


@pytest.mark.parametrize("solve", [solve_jacobi, solve_gauss_seidel])
def test_iterative_trace_and_report_preserve_options_mapping_and_every_value(solve):
    system = parse_system([["1", "3"], ["4", "1"]], ["2", "1"])
    result = solve(system, options=IterationOptions(max_iterations=2))
    trace = json.loads(serialize_trace(result))
    assert trace["kind"] == "iterative"
    assert trace["iterations"] == json.loads(result.model_dump_json())["history"]
    for decimals in (0, 12):
        report = build_report(system, result, display=DisplaySettings(decimal_places=decimals))
        payload = json.loads(serialize_report(report))
        assert payload["result"]["history"] == trace["iterations"]
        assert payload["original_system"]["a"] == [list(row) for row in system.a]
        assert payload["result"]["options"]["max_iterations"] == 2
        assert payload["result"]["reordering"]["permutation"]["order"] == [1, 0]
        assert payload["result"]["solution"] is None
        assert payload["result"]["last_iterate"] == list(result.last_iterate)
        assert "trace" not in payload  # No redundant copy of the result's history.


def test_report_rejects_incompatible_source_shape_and_arithmetic_mode():
    source = parse_system([["1"]], ["1"])
    result = solve_gaussian(source)
    with pytest.raises(ValidationError):
        build_report(parse_system([["1", "1"]], ["1"]), result)
    with pytest.raises(ValidationError):
        build_report(parse_system([["1"]], ["1"], mode=ArithmeticMode.EXACT), result)


def test_trace_budget_rejects_instead_of_silently_truncating(monkeypatch):
    import solver_core.trace as trace_module

    system = parse_system([["3", "1"], ["1", "3"]], ["1", "2"])
    results = (solve_gaussian(system), solve_jacobi(system))
    monkeypatch.setattr(trace_module, "MAX_TRACE_VALUE_CHARS", 1)
    for result in results:
        with pytest.raises(ResourceLimitError) as error:
            build_trace(result)
        assert error.value.code is ErrorCode.TRACE_LIMIT


def test_result_and_trace_are_immutable():
    result = solve_jacobi(parse_system([["1"]], ["1"]))
    with pytest.raises(ValidationError):
        result.history[0].converged = True
    with pytest.raises(TypeError):
        result.history[0].vector[0] = 9.0


@pytest.mark.parametrize(
    "mutation", ["false_solution", "wrong_index", "wrong_convergence", "wrong_last"]
)
def test_iteration_result_rejects_false_success_and_corrupted_history(mutation):
    result = solve_jacobi(parse_system([["3"]], ["1"]), options=IterationOptions(max_iterations=1))
    data = result.model_dump()
    if mutation == "false_solution":
        data["solution"] = result.last_iterate
    elif mutation == "wrong_index":
        data["history"][0]["index"] = 2
    elif mutation == "wrong_convergence":
        data["history"][0]["converged"] = True
    else:
        data["last_iterate"] = (9.0,)
    with pytest.raises(ValidationError):
        IterativeResult.model_validate(data)


@pytest.mark.parametrize("a,b", [([["1", "1"]], ["1"]), ([["1"], ["1"]], ["1", "2"])])
def test_reports_preserve_parametric_or_inconsistent_outcomes(a, b):
    system = parse_system(a, b, mode=ArithmeticMode.EXACT)
    result = solve_gauss_jordan(system)
    payload = json.loads(serialize_report(build_report(system, result)))
    assert (
        payload["result"]["classification"]["classification"]
        == result.classification.classification
    )
    assert payload["result"]["solution"] is None

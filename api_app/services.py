"""Translate validated API contracts into calls to the transport-independent core."""

from api_app.observability import RequestContext
from api_models.requests import (
    AnalyzeRequest,
    DirectSolveRequest,
    SolveRequest,
    SystemInput,
)
from api_models.responses import (
    AnalyzeOutcome,
    AnalyzeResponse,
    Issue,
    MethodEligibility,
    NumericalFailure,
    ProblemMetadata,
    ReportMetadata,
    SolveOutcome,
    SolveResponse,
)
from solver_core.classification import classify_system
from solver_core.convergence import convergence_diagnostics
from solver_core.diagnostics import condition_diagnostic
from solver_core.errors import NumericBreakdownError
from solver_core.gauss_jordan import solve_gauss_jordan
from solver_core.gauss_seidel import solve_gauss_seidel
from solver_core.gaussian import solve_gaussian
from solver_core.jacobi import solve_jacobi
from solver_core.models import (
    ArithmeticMode,
    ClassificationKind,
    ClassificationResult,
    DirectResult,
    ExactSystem,
    FloatSystem,
    IterationOptions,
    IterativeResult,
    RowPermutation,
    SystemShape,
)
from solver_core.parsing import parse_float, parse_system
from solver_core.permutations import (
    apply_row_permutation,
    diagonal_dominance,
    find_diagonal_dominance_permutation,
    find_nonzero_diagonal_permutation,
    has_nonzero_diagonal,
)


def _metadata(ctx: RequestContext, system: SystemInput) -> SystemShape:
    ctx.equations, ctx.unknowns = len(system.a), len(system.a[0])
    return SystemShape(equations=ctx.equations, unknowns=ctx.unknowns)


def _failure(
    ctx: RequestContext, mode: ArithmeticMode, shape: SystemShape, error: NumericBreakdownError
) -> NumericalFailure:
    ctx.result_status, ctx.error_code = "numeric_breakdown", error.code.value
    return NumericalFailure(
        request_id=ctx.request_id,
        method=ctx.method,
        arithmetic_mode=mode,
        shape=shape,
        error=Issue(code=error.code.value, message=error.message),
    )


def _eligibility(
    system: FloatSystem | ExactSystem,
    classification: ClassificationResult,
    dominant: RowPermutation | None,
    nonzero: RowPermutation | None,
) -> tuple[MethodEligibility, ...]:
    results = [
        MethodEligibility(
            method=method,
            eligible=True,
            code="available",
            reason="Direct row reduction supports every validated rectangular system.",
        )
        for method in ("gaussian", "gauss_jordan")
    ]
    for method in ("jacobi", "gauss_seidel"):
        if not system.shape.is_square:
            results.append(
                MethodEligibility(
                    method=method,
                    eligible=False,
                    code="requires_square",
                    reason="Iteration requires a square matrix.",
                )
            )
        elif classification.classification is not ClassificationKind.UNIQUE:
            results.append(
                MethodEligibility(
                    method=method,
                    eligible=False,
                    code="requires_unique",
                    reason="Iteration requires a unique classification.",
                )
            )
        elif isinstance(system, ExactSystem):
            results.append(
                MethodEligibility(
                    method=method,
                    eligible=False,
                    code="requires_float64",
                    reason="Re-analyze in float64 mode for iterative methods.",
                )
            )
        else:
            candidate = dominant
            if candidate is None and not has_nonzero_diagonal(system):
                candidate = nonzero
            if candidate is None and not has_nonzero_diagonal(system):
                results.append(
                    MethodEligibility(
                        method=method,
                        eligible=False,
                        code="unsafe_diagonal",
                        reason="No safe non-zero-diagonal row matching exists.",
                    )
                )
                continue
            working = system if candidate is None else apply_row_permutation(system, candidate)
            moved = candidate is not None and candidate.order != tuple(range(len(system.a)))
            try:
                diagnostic = convergence_diagnostics(working, method)
            except NumericBreakdownError:
                results.append(
                    MethodEligibility(
                        method=method,
                        eligible=False,
                        code="numeric_breakdown",
                        reason="Convergence diagnostics could not be computed.",
                    )
                )
                continue
            risk = diagnostic.assessment == "convergence_risk"
            results.append(
                MethodEligibility(
                    method=method,
                    eligible=True,
                    code="convergence_risk"
                    if risk
                    else "requires_row_reordering"
                    if moved
                    else "available",
                    reason=(
                        "Execution requires explicit convergence-risk acceptance."
                        if risk
                        else "Enable the indicated row-reordering option before solving."
                        if moved
                        else "The method satisfies its execution preconditions."
                    ),
                    requires_row_reordering=moved,
                    requires_risk_override=risk,
                    row_permutation=candidate if moved else None,
                    convergence=diagnostic,
                )
            )
    return tuple(results)


def analyze(payload: AnalyzeRequest, ctx: RequestContext) -> AnalyzeOutcome:
    shape = _metadata(ctx, payload.system)
    mode = ArithmeticMode(payload.arithmetic_mode)
    system = parse_system(payload.system.a, payload.system.b, mode=mode)
    try:
        classification = classify_system(system)
        strict = diagonal_dominance(system)[0] if shape.is_square else None
        dominant = find_diagonal_dominance_permutation(system) if shape.is_square else None
        nonzero = find_nonzero_diagonal_permutation(system) if shape.is_square else None
        methods = _eligibility(system, classification, dominant, nonzero)
    except NumericBreakdownError as error:
        return _failure(ctx, mode, shape, error)
    # Even for exact classification, conditioning is explicitly a float diagnostic.
    floating = parse_system(payload.system.a, payload.system.b)
    conditioning = condition_diagnostic(floating)
    warnings: list[str] = []
    codes: list[str] = []
    if mode is ArithmeticMode.EXACT:
        warnings.append("Conditioning is estimated in float64; ranks and classification are exact.")
        codes.append("floating_condition_estimate")
    if conditioning.status != "finite":
        warnings.append("A finite condition-number estimate is unavailable.")
        codes.append("condition_unavailable")
    if any(item.requires_risk_override for item in methods):
        codes.append("convergence_risk")
    ctx.result_status, ctx.warning_codes = classification.classification.value, tuple(codes)
    return AnalyzeResponse(
        request_id=ctx.request_id,
        shape=shape,
        is_square=shape.is_square,
        classification=classification,
        conditioning=conditioning,
        strict_diagonal_dominance=strict,
        dominance_permutation=dominant,
        nonzero_permutation=nonzero,
        methods=methods,
        warnings=tuple(warnings),
    )


def solve(payload: SolveRequest, ctx: RequestContext) -> SolveOutcome:
    ctx.method = payload.method
    shape = _metadata(ctx, payload.system)
    mode = (
        ArithmeticMode(payload.options.arithmetic_mode)
        if isinstance(payload, DirectSolveRequest)
        else ArithmeticMode.FLOAT64
    )
    system = parse_system(payload.system.a, payload.system.b, mode=mode)
    result: DirectResult | IterativeResult
    try:
        if isinstance(payload, DirectSolveRequest):
            result = (
                solve_gaussian(system)
                if payload.method == "gaussian"
                else solve_gauss_jordan(system)
            )
        else:
            # Narrow the parsed system without an implicit conversion of exact arithmetic.
            if not isinstance(system, FloatSystem):
                raise RuntimeError(
                    "Iterative request was parsed with an incorrect arithmetic mode."
                )
            guess = payload.options.initial_guess
            options = IterationOptions(
                initial_guess=None
                if guess is None
                else tuple(
                    parse_float(v, location=("options", "initial_guess", i))
                    for i, v in enumerate(guess)
                ),
                tolerance=payload.options.tolerance,
                max_iterations=payload.options.max_iterations,
                auto_reorder_for_diagonal_dominance=payload.options.auto_reorder_for_diagonal_dominance,
                auto_reorder_for_nonzero_diagonal=payload.options.auto_reorder_for_nonzero_diagonal,
                run_despite_convergence_risk=payload.options.run_despite_convergence_risk,
            )
            result = (
                solve_jacobi(system, options=options)
                if payload.method == "jacobi"
                else solve_gauss_seidel(system, options=options)
            )
    except NumericBreakdownError as error:
        return _failure(ctx, mode, shape, error)
    floating = parse_system(payload.system.a, payload.system.b)
    conditioning = (
        result.conditioning
        if isinstance(result, IterativeResult)
        else condition_diagnostic(floating)
    )
    ctx.result_status = (
        result.status.value
        if isinstance(result, IterativeResult)
        else result.classification.classification.value
    )
    warnings: list[str] = []
    if isinstance(result, IterativeResult) and result.convergence.assessment == "convergence_risk":
        warnings.append("convergence_risk")
    if isinstance(result, IterativeResult) and result.reordering.dominance_matching_found is False:
        warnings.append("dominance_matching_unavailable")
    if mode is ArithmeticMode.EXACT:
        warnings.append("floating_condition_estimate")
    if conditioning.status != "finite":
        warnings.append("condition_unavailable")
    if isinstance(result, DirectResult) and result.warnings:
        warnings.append("floating_tolerance")
    if ctx.result_status == "numeric_breakdown":
        ctx.error_code = "numeric_breakdown"
    ctx.warning_codes = tuple(warnings)
    return SolveResponse(
        request_id=ctx.request_id,
        problem=ProblemMetadata(
            shape=shape, is_square=shape.is_square, arithmetic_mode=mode, original_system=system
        ),
        result=result,
        conditioning=conditioning,
        report=ReportMetadata(
            method=payload.method,
            options=payload.options,
            display=payload.display,
            fraction_values="exact" if mode is ArithmeticMode.EXACT else "approximate",
        ),
    )

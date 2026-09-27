# Decisions

Why Augmentr is built the way it is, and what was considered and rejected along the way. Each entry is a decision worth defending to a future contributor (or a future you) who might otherwise "fix" it back to the more obvious-looking alternative.

---

### D1 — Next.js + FastAPI on one Vercel project, not Reflex

**Rejected:** Reflex with a seamless Reflex + FastAPI deployment.

**Why:** Reflex's application state is server-side and event-driven through WebSockets. Production Reflex deployments commonly need a persistent backend process and, once horizontally scaled, a shared state manager such as Redis. Augmentr's solve workflow is a single request/response — it never needed persistent WebSocket state in the first place. Vercel has first-class documented support for a Next.js frontend plus a FastAPI Python API in the same project, and isolating the solver behind a stateless HTTP contract keeps a future migration off Vercel's Python runtime straightforward if that runtime's status ever changes.

**Decision:** Next.js (App Router) + FastAPI on Vercel's Python runtime, Python 3.12 pinned explicitly, NumPy for floating-point diagnostics, `fractions.Fraction` for bounded exact rational mode. No WebSocket layer, Redis, database, or background queue for v1.

---

### D2 — Rank-based classification, not determinant equality, for singularity

**Rejected:** Using `det(A) == 0` as the singularity test.

**Why:** The determinant is a poor production singularity detector in floating-point arithmetic — it can be numerically tiny-but-nonzero or large-but-effectively-singular depending on scale, and gives no information about *how* a system is degenerate.

**Decision:** Rank analysis with a scale-aware pivot tolerance, plus singular-value/condition diagnostics where appropriate. `rank(A) == rank([A|b]) == n` → unique; `rank(A) == rank([A|b]) < n` → infinitely many; `rank(A) < rank([A|b])` → inconsistent. Exact-zero pivots are only meaningful in exact rational mode.

---

### D3 — Computation precision and display precision are separate concerns

**Rejected:** Converting iterative calculations to `Fraction` or `Decimal` and rounding after each iteration step.

**Why:** Mixing the two collapses a presentation choice (how many decimal places to show) into the numerical method itself, which corrupts convergence behavior and makes results depend on a UI setting.

**Decision:** Iterative methods compute internally in float64 with no presentation rounding mid-run. Decimal places affect rendering only. A fraction representation of an iterative result is explicitly marked approximate (`≈`) and generated only for display, with a bounded denominator — and is never produced by first passing through a binary floating-point approximation and hoping it recovers the exact value. Direct methods may optionally use the exact rational engine for small systems, computed exactly from the start.

---

### D4 — Partial pivoting is mandatory, not a toggle

**Rejected:** Letting users disable pivoting for "the pure textbook version," and computing `A⁻¹` as a solve path.

**Why:** Partial pivoting is a floating-point stability requirement, not a stylistic preference — disabling it produces wrong-looking results on perfectly reasonable matrices, and computing an explicit inverse to solve `Ax = b` is both slower and numerically worse than elimination.

**Decision:** Gaussian elimination and floating-point Gauss–Jordan use partial pivoting by default, with no user-facing toggle to disable it in the normal solver. `A⁻¹` is never computed as a solve step. If a future "demonstration mode" wants to compare pivoting strategies for teaching purposes, it must be clearly isolated from the default solver, not a hidden switch on it.

---

### D5 — Diagonal dominance is a sufficient, not necessary, convergence condition

**Rejected:** Treating strict diagonal dominance as a pass/fail gate for whether Jacobi or Gauss–Seidel are allowed to run, and silently reordering equations to force it.

**Why:** Plenty of systems that aren't diagonally dominant still converge under Jacobi or Gauss–Seidel; blocking them outright would be mathematically wrong. Silently reordering rows to force dominance would also mean the user no longer sees the system they typed in.

**Decision:** Augmentr may attempt a row permutation (rows only, never variables/columns — variable labels never change) that makes the system strictly diagonally dominant, framed as a bipartite matching problem between rows and diagonal positions. If no perfect matching exists, it says so plainly rather than pretending. The original, unreordered system and the reordering actually applied are both always visible. The app never claims a permutation "guarantees" convergence unless the resulting matrix genuinely satisfies a valid sufficient condition — and never asserts one iterative method is categorically "faster" than another as a general theorem, only reports the specific behavior observed for the matrix at hand.

---

### D6 — HTTP 200 for every mathematical outcome

**Rejected:** Mapping inconsistent/underdetermined systems or non-converged iterations to HTTP 4xx/5xx.

**Why:** An inconsistent linear system, an infinite-solution family, or an iterative method that doesn't converge within budget are all valid, correctly-computed mathematical outcomes — not application errors. Returning an error status for them would conflate "the math says no" with "the server failed."

**Decision:** All of these return HTTP 200 with a discriminated outcome envelope. Non-convergent iterative runs are explicitly barred from ever being labeled a solution. Real errors still get real status codes: malformed tokens, precondition failures, and oversized payloads → 422; cross-origin browser mutations → 403; timeouts → 408/504; unexpected server errors → generic 500 with no internal detail leaked.

---

### D7 — String-preserved exact rationals, never float-coerced

**Decision:** Exact rational numerators and denominators are serialized as arbitrary-precision integer strings, formatted directly into `p/q` or `\frac{p}{q}` for the UI, Markdown, and LaTeX reports, and preserved unrounded through JSON export. They are never round-tripped through a float representation at any point in the pipeline.

---

### D8 — Plotly strict distribution + per-request CSP nonces

**Rejected:** `unsafe-eval` / `unsafe-inline` script directives, and the standard partial Plotly bundle.

**Why:** Standard WebGL/partial Plotly bundles use `Function` constructors that violate a strict Content Security Policy. Rather than loosening the CSP to accommodate the library, the library was swapped.

**Decision:** `proxy.ts` issues a fresh cryptographic script nonce per request with `strict-dynamic`, no `unsafe-eval`, no script `unsafe-inline`. The Plotly *strict* distribution replaces the partial bundle (cloud-sharing controls removed along with it). Inline styles remain allowed only for KaTeX and Plotly layout attributes.

---

### D9 — Same-origin rewrite, not a separate API host or permissive CORS

**Decision:** No separate backend hostname; `Access-Control-Allow-Origin: *` rejected outright. All browser API traffic routes same-origin through `/api/:path*`, protected by `Sec-Fetch-Site` and `Origin` header validation, while still permitting no-`Origin` CLI access. See D1 for the deployment-topology reasoning this depends on.

---

### D10 — Geometry is illustration, never proof

**Decision:** 2D (2×2) and 3D (3×3) plots are strictly bounded visual illustrations, capped at coordinates ±1,000,000. Degenerate cases — zero rows, rank-1 planes in 3D, whole-space families, off-window intersections, or dimensions outside {2, 3} — get an explicit algebraic explanation rather than an invented or misleading picture. Geometry is never used as the solver's proof of correctness.

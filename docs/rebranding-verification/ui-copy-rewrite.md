# Augmentr — UI Copy Rewrite

Grounded in the app's actual product requirements and information architecture (routes `/`, `/learn`, `/solve`; solver workflow states `DIMENSIONS → MATRIX_INPUT → ANALYZING → METHOD_SELECTION → METHOD_CONFIGURATION → SOLVING → RESULTS`; results panels `Answer / Steps / Visualize / Diagnostics / Report`). Since the current live copy strings weren't included in what I reviewed, everything below is written fresh against the spec rather than edited line-by-line against an existing draft — treat it as a drop-in replacement, and flag anything that needs to match copy you've already shipped elsewhere.

> **Reconciled against the Gate 1 completion report (2026-09-27).** Astra's implementation surfaced a few things this rewrite had wrong or ambiguous, corrected below: geometry requires a *square* 2×2/3×3 system, not just two-or-three unknowns; the convergence chart lives in **Steps**, not Visualize; row reordering for diagonal dominance defaults to *enabled*, not off; the decimal-place default is a concrete 6, not "classroom convention"; there's no "Copy LaTeX" action (JSON export exists instead); and the `{n}` placeholder collided between two different meanings in the incomplete-matrix message (now `{missing}`). Direct methods also get their own configuration subheading, which the original draft omitted.

## Voice principles

1. **Say what it does, not what it's like.** Augmentr builds, inspects, and solves augmented matrices. It's not a "journey," a "revolution," or an "experience."
2. **Precision over enthusiasm.** A method is "available" or "unavailable for a stated reason" — never "smart" or "powerful."
3. **The math is the interesting part, not the app.** Copy can be playful about *numbers* (a wry aside about ill-conditioning, a dry joke about a matrix that refuses to cooperate) but never about the product's own cleverness.
4. **Every disabled state has a reason.** The spec is explicit about this for method eligibility — extend the same rule to every other empty/blocked state in the UI. Never "Something went wrong."
5. **Terminology is locked:** "linear equation coefficients," never "polynomial coefficients." "Augmented matrix," not "matrix" alone, when precision matters (the row is coefficients *and* the right-hand side).

---

## Landing (`/`)

**Hero heading:**
> Augmentr

**Hero subheading:**
> Build an augmented matrix, pick a method, watch it get solved one row operation at a time.

**One-line description (meta/OG tag):**
> A linear system solver that shows its work — Gaussian and Gauss–Jordan elimination, Jacobi and Gauss–Seidel iteration, with every step, residual, and condition number visible.

**Primary CTA:**
> Start solving → `/solve`

**Secondary CTA:**
> New to these methods? → `/learn`

**Three feature callouts (short, literal):**
- **Four methods, one system.** Two direct (Gaussian, Gauss–Jordan) and two iterative (Jacobi, Gauss–Seidel), each with its own eligibility check against your matrix.
- **Every step, not just the answer.** Row operations, iteration tables, residuals, and condition numbers — all inspectable, none hidden behind a single "Solve" button.
- **Exact when it matters.** Arbitrary-precision rational arithmetic for direct methods when you need it; float64 with visible tolerances everywhere else.

---

## `/learn`

**Page heading:**
> How these methods work

**Page subheading:**
> A short primer before you touch a matrix. Skip ahead if you already know rank, elimination, and convergence.

**Section: What "solving" means here**
> A linear system is an augmented matrix — coefficients on the left, right-hand-side values on the right. Solving it means finding the values that satisfy every row at once, or showing precisely why no such values exist, or why more than one set of values does.

**Section: Direct methods**

- **Gaussian elimination** — Reduces the augmented matrix to row-echelon form using partial pivoting, then back-substitutes. Deterministic, finishes in a fixed number of steps, and is the reference method for square, well-posed systems.
- **Gauss–Jordan elimination** — Continues past row-echelon form to reduced row-echelon form (RREF), reading the solution — or the parametric form of infinitely many solutions — directly off the final matrix.

**Section: Iterative methods**

- **Jacobi iteration** — Starts from an initial guess and repeatedly refines every variable using the *previous* iteration's values, all at once. Converges when the iteration matrix's spectral radius is under 1 — not guaranteed for every system, and the app tells you the spectral radius before you run it.
- **Gauss–Seidel iteration** — Same idea as Jacobi, but each variable update uses the *newest* values already computed in the current sweep. Usually converges faster than Jacobi when it converges at all, but "usually" is not "always" — Augmentr won't claim one method is faster than the other as a general rule, only for the matrix in front of you.

**Section: Why a system might not have one clean answer**
> Rank tells the story. If the coefficient matrix and the augmented matrix have the same rank, and that rank equals the number of unknowns, there's exactly one solution. If the ranks match but fall short of the unknown count, there are infinitely many — described by free parameters. If the ranks don't match, no solution satisfies every row simultaneously. Augmentr classifies your system this way before offering you a method, not after you've run one and gotten a strange answer.

**Section: Diagonal dominance, briefly**
> Strict diagonal dominance guarantees Jacobi and Gauss–Seidel will converge — but it's a sufficient condition, not a necessary one. Plenty of systems that aren't diagonally dominant still converge fine. Augmentr can attempt to reorder your equations (not your variables) into a diagonally dominant arrangement if one exists, and will always show you which reordering it used — your original system is never silently replaced.

---

## `/solve` — workflow stages

Each stage gets a heading (what you're doing) and a one-line subheading (why it exists / what happens next). No stage should ever say only "Continue" with no context of what's being decided.

### 1. Dimensions
**Heading:** How many equations, how many unknowns?
**Subheading:** Pick counts from 1×1 up to 12×12 — this sets the grid you'll fill in next.

### 2. Matrix input
**Heading:** Enter your augmented matrix
**Subheading:** Coefficients for x₁ through xₙ, plus the right-hand side. Tab or arrow between cells; paste a tab- or newline-delimited block if you're bringing this from somewhere else.
**Helper text (accepted formats):** Integers, decimals, scientific notation, and simple fractions — `3`, `-2`, `0.125`, `1/3`, `2.5e-4`.
**Invalid cell inline message:** *"{token}" isn't a number Augmentr recognizes — try an integer, decimal, or a/b fraction.*

### 3. Analyzing
**Heading:** Checking your system
**Subheading:** Rank, classification, and conditioning — before you pick a method, so you know what each one can actually do here.

### 4. Method selection
**Heading:** Choose a method
**Subheading:** Each card shows what it needs, what it's good at, and whether it can run on the matrix you just entered.

**Per-method card copy (direct vs. iterative label, one paragraph, advantages, limitations):**

- **Gaussian elimination** *(Direct)*
  Reduces your matrix to row-echelon form with partial pivoting, then solves by back-substitution.
  *Advantages:* deterministic, finishes in a bounded number of steps, works on rectangular systems.
  *Limitations:* doesn't directly hand you reduced form — Gauss–Jordan goes one step further if you want that.

- **Gauss–Jordan elimination** *(Direct)*
  Continues elimination to reduced row-echelon form, reading solutions (including parametric families) directly off the result.
  *Advantages:* the clearest path to a full solution set, including infinite-solution cases.
  *Limitations:* more row operations than Gaussian elimination for the same system — a small cost for the extra clarity.

- **Jacobi iteration** *(Iterative)*
  Refines an initial guess using only the previous iteration's values, updated all at once each sweep.
  *Advantages:* simple, easy to parallelize conceptually, a good baseline for comparing convergence behavior.
  *Limitations:* requires a square system; convergence isn't guaranteed and depends on the iteration matrix's spectral radius.

- **Gauss–Seidel iteration** *(Iterative)*
  Refines an initial guess using the newest values already computed within the same sweep.
  *Advantages:* typically converges in fewer iterations than Jacobi when both converge.
  *Limitations:* same square-system requirement; still not guaranteed to converge for every matrix.

**Eligibility-blocked example copy (already close to spec, kept literal):**
> Jacobi is unavailable — this system has 3 equations and 2 unknowns, and Jacobi requires a square matrix.

> Gauss–Seidel is available, but the iteration matrix's spectral radius is ≥ 1 for this system. Convergence isn't expected from an arbitrary starting guess — you can still run it if you want to see what happens.

### 5. Method configuration
**Heading:** Configure {method name}
**Subheading (direct methods):** Choose exact rational or float64 arithmetic and how results should display.
**Subheading (iterative methods):** Set a starting guess, an iteration budget, and how results should display.

**Controls (direct methods):**
- Arithmetic mode *(exact rational or float64)*
- Display as decimal or fraction
- Decimal places *(default: 6)*

**Controls (iterative methods):**
- Initial approximation vector *(default: all zeros)*
- Attempt row reordering for diagonal dominance *(enabled by default — toggle off to solve the system exactly as entered)*
- Display as decimal or fraction *(fractions are marked approximate for iterative results)*
- Decimal places *(default: 6)*
- Iteration budget *(default 25, capped at 500)*

### 6. Solving
**Heading:** Solving
**Subheading:** Running {method name} on your {m}×{n} system.

### 7. Results
**Heading:** Result
**Subheading:** {classification} — see Steps, Visualize, and Diagnostics for how Augmentr got here.

---

## Results panel headings

| Panel | Heading | One-line subheading |
|---|---|---|
| Answer | Answer | The solution, parametric form, or reason none exists. |
| Steps | Steps | Every row operation (direct methods) or iteration (iterative methods), in order. |
| Visualize | Visualize | A 2D line or 3D plane for square 2×2 or 3×3 systems; the convergence plot for iterative methods lives in Steps. |
| Diagnostics | Diagnostics | Rank, condition number, residual, backward error, and any row reordering that was applied. |
| Report | Report | Print, or download as Markdown, LaTeX, or JSON. |

---

## Empty and blocked states

Every one of these names the specific reason — never a generic failure message.

- **No matrix entered yet:** *Set your equation and unknown counts above, then fill in the augmented matrix to continue.*
- **Incomplete matrix:** *{missing} of {m×(n+1)} cells still need a value before Augmentr can analyze this system.*
- **Singular / no unique solution (direct methods):** *This system doesn't have a unique solution — rank({A}) is {r}, short of the {n} unknowns. See Steps for where elimination stalls, or switch to Gauss–Jordan for the full parametric solution set.*
- **Inconsistent system:** *No values satisfy every equation at once — the augmented matrix's rank ({r_ab}) is higher than the coefficient matrix's rank ({r_a}). This is a valid mathematical outcome, not an error.*
- **Infinitely many solutions:** *Rank falls short of the unknown count by {k} — {k} free parameter(s) describe the full solution set below.*
- **Non-convergent iteration:** *{method} didn't converge within {max_iterations} iterations (tolerance {tol} not met). This is not a solution — see Diagnostics for the spectral radius and residual trend.*
- **No classification returned (numerical limitation):** *A numerical limitation prevented a result — review the returned explanation below.*
- **Ill-conditioned warning:** *This system's condition number is {value} — a large value means small changes in input can produce disproportionately large changes in the result. Treat the result's precision with that in mind.*
- **Method unavailable (non-square, for iterative methods):** *{method} requires a square system. This one has {m} equations and {n} unknowns — try a direct method instead.*
- **Geometry not shown:** *A 2D or 3D plot only applies to square 2×2 or 3×3 systems. This system has {m} equations and {n} unknowns — see Diagnostics and Steps for the equivalent algebraic description.*
- **Network failure:** *Couldn't reach the solver. Check your connection and try again — nothing you've entered has been lost.*
- **Unexpected server error:** *Something failed on Augmentr's end (reference: {request_id}). Your input is still here — try again, and include that reference if you report it.*

---

## Report / export labels

- **Print / Save as PDF** *(button — browser print action)*
- **Download .md**
- **Download .tex**
- **Download .json**
- **Approximate fraction marker:** values shown as `≈ 22/7` etc. carry a tooltip: *Approximate — this iterative result was rounded to a bounded fraction for display; the underlying computation used float64 throughout.*

*(No clipboard "Copy LaTeX" action currently exists — print plus the three downloads are the shipped export paths. Adding a copy button is a functionality change, not a copy change — treat it as its own small ticket rather than folding it into a text-only gate.)*

---

## Footer / about

> Augmentr solves systems of 1×1 to 12×12 linear equations using Gaussian elimination, Gauss–Jordan elimination, Jacobi iteration, and Gauss–Seidel iteration — with full step traces, condition diagnostics, and 2D/3D visualization where dimensionality allows it.

*(Deliberately omits any adjective doing marketing work — "powerful," "seamless," "next-generation" — none of those describe what the tool does.)*

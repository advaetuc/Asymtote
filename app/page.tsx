import Link from "next/link";
import { SiteHeader } from "../components/site-header";
import { FOOTER_COPY } from "../components/site-copy";

const features = [
  ["01", "Four methods, one system.", "Two direct (Gaussian, Gauss–Jordan) and two iterative (Jacobi, Gauss–Seidel), each with its own eligibility check against your matrix."],
  ["02", "Every step, not just the answer.", 'Row operations, iteration tables, residuals, and condition numbers — all inspectable, none hidden behind a single "Solve" button.'],
  ["03", "Exact when it matters.", "Arbitrary-precision rational arithmetic for direct methods when you need it; float64 with visible tolerances everywhere else."],
] as const;

export default function Home() {
  return (
    <main id="main" className="page-shell">
      <SiteHeader />
      <section className="intro" aria-labelledby="title">
        <p className="eyebrow">Linear system solver</p>
        <h1 id="title">Augmentr</h1>
        <p className="lead">
          Build an augmented matrix, pick a method, watch it get solved one row operation at a time.
        </p>
        <div className="action-row"><Link className="primary-link" href="/solve">Start solving <span aria-hidden="true">→</span></Link><Link className="secondary-link" href="/learn">New to these methods? <span aria-hidden="true">→</span></Link></div>
      </section>
      <section id="methods" className="method-section" aria-labelledby="methods-title">
        <div className="section-heading">
          <p className="eyebrow">Methods, steps, and precision</p>
          <h2 id="methods-title">Inspect your system.</h2>
        </div>
        <div className="method-grid">
          {features.map(([number, name, description]) => (
            <article className="glass-panel" key={number}>
              <span className="method-number" aria-hidden="true">{number}</span>
              <h3>{name}</h3>
              <p>{description}</p>
            </article>
          ))}
        </div>
        <p className="muted">Exact arithmetic remains subject to the solver’s input, intermediate-size, and runtime limits.</p>
      </section>
      <footer>{FOOTER_COPY}</footer>
    </main>
  );
}

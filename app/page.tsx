const methods = [
  ["01", "Gaussian elimination", "Reduce a system to row-echelon form, then use back substitution."],
  ["02", "Gauss-Jordan elimination", "Reduce a system further to reveal pivots, free variables, and contradictions."],
  ["03", "Jacobi iteration", "Build each new approximation entirely from the previous iteration."],
  ["04", "Gauss-Seidel iteration", "Use newly updated components as each iteration progresses."],
] as const;

export default function Home() {
  return (
    <main id="main" className="page-shell">
      <header className="masthead">
        <span className="wordmark">TULYA<span aria-hidden="true">.</span></span>
        <span className="eyebrow">A study in linear systems</span>
      </header>
      <section className="intro" aria-labelledby="title">
        <p className="eyebrow">Mathematics / Made visible</p>
        <h1 id="title">Linear equations,<br /><span>understood.</span></h1>
        <p className="lead">
          An answer is only the beginning. Understand how equations relate,
          how methods work, and what each step tells you.
        </p>
        <a className="primary-link" href="#methods">Explore the four methods <span aria-hidden="true">↗</span></a>
      </section>
      <section id="methods" className="method-section" aria-labelledby="methods-title">
        <div className="section-heading">
          <p className="eyebrow">Four perspectives</p>
          <h2 id="methods-title">From equations to insight.</h2>
        </div>
        <div className="method-grid">
          {methods.map(([number, name, description]) => (
            <article className="glass-panel" key={number}>
              <span className="method-number" aria-hidden="true">{number}</span>
              <h3>{name}</h3>
              <p>{description}</p>
            </article>
          ))}
        </div>
      </section>
      <footer>Precision in calculation. Clarity in explanation.</footer>
    </main>
  );
}

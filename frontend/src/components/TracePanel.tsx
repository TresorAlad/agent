import type { TraceStep } from "../api";

type Props = {
  steps: TraceStep[];
  elapsedMs?: number | null;
};

export function TracePanel({ steps, elapsedMs }: Props) {
  return (
    <section className="trace-panel">
      <h2>Trace agent ({steps.length} étapes)</h2>
      {elapsedMs != null && <p className="meta">Durée : {elapsedMs} ms</p>}
      {steps.length === 0 ? (
        <p className="hint">Les outils appelés apparaîtront ici.</p>
      ) : (
        <ol className="trace-list">
          {steps.map((step) => (
            <li key={step.step} className={`trace-item kind-${step.kind}`}>
              <div className="trace-head">
                <span>#{step.step}</span>
                <span className="badge">{step.kind}</span>
                {step.tool && <span className="tool-name">{step.tool}</span>}
              </div>
              {step.args_summary && (
                <p className="trace-detail">
                  <strong>Args :</strong> {step.args_summary}
                </p>
              )}
              {step.result_summary && (
                <p className="trace-detail">
                  <strong>Résultat :</strong> {step.result_summary}
                </p>
              )}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

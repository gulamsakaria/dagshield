import { api } from "../api";
import { ErrorNote, Loading } from "../components/ui";
import { useApi } from "../hooks";
import { useI18n } from "../i18n";

const show = (v: unknown): string =>
  Array.isArray(v)
    ? v.length === 0
      ? "none"
      : v.map((x) => (Array.isArray(x) ? x.join(" / ") : String(x))).join("; ")
    : String(v);

export default function Evaluation() {
  const { t } = useI18n();
  const ev = useApi(() => api.evaluation(), []);
  if (ev.loading && !ev.data) return <Loading />;
  if (ev.error) return <ErrorNote message={ev.error} onRetry={ev.reload} />;
  if (!ev.data) return null;
  const { totals, per_rule, cases, note, repeatability_ok } = ev.data;

  return (
    <section>
      <h1>{t("evalTitle")}</h1>
      <p className="note">{note}</p>
      <div className="counts">
        <div>
          <span className="big">{totals.tp}</span>
          <span>{t("evalTP")}</span>
        </div>
        <div>
          <span className="big">{totals.fp}</span>
          <span>{t("evalFP")}</span>
        </div>
        <div>
          <span className="big">{totals.fn}</span>
          <span>{t("evalFN")}</span>
        </div>
        <div>
          <span className="big">
            {totals.passed}/{totals.cases}
          </span>
          <span>{t("evalCases")}</span>
        </div>
      </div>
      <p>
        {t("evalRepeat")}: {repeatability_ok ? t("yes") : t("no")}
      </p>

      <h2>{t("evalPerRule")}</h2>
      <table className="table">
        <thead>
          <tr>
            <th>{t("rule")}</th>
            <th className="num">TP</th>
            <th className="num">FP</th>
            <th className="num">FN</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(per_rule).map(([r, c]) => (
            <tr key={r}>
              <td>{r}</td>
              <td className="num">{c.tp}</td>
              <td className="num">{c.fp}</td>
              <td className="num">{c.fn}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>{t("evalCasesTitle")}</h2>
      <div className="scroll">
        <table className="table">
          <thead>
            <tr>
              <th>Case</th>
              <th>{t("evalExpected")}</th>
              <th>{t("evalActual")}</th>
              <th>Result</th>
            </tr>
          </thead>
          <tbody>
            {cases.map((c) => (
              <tr key={c.id}>
                <td>{c.name}</td>
                <td>{show(c.expected)}</td>
                <td>{show(c.actual)}</td>
                <td>
                  <span className={`badge ${c.passed ? "status-closed" : "sev-high"}`}>
                    <span aria-hidden="true">{c.passed ? "✓" : "✕"}</span>{" "}
                    {c.passed ? t("pass") : t("fail")}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

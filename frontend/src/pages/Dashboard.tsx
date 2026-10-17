import { useState } from "react";
import { Link } from "react-router-dom";
import { Alert, api } from "../api";
import { Empty, ErrorNote, Loading } from "../components/ui";
import { useApi } from "../hooks";
import { useI18n } from "../i18n";

export default function Dashboard() {
  const { t, pick } = useI18n();
  const scenarios = useApi(() => api.scenarios(), []);
  const existing = useApi(() => api.alerts(), []);
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ran, setRan] = useState(false);

  async function audit(scenarioId?: string) {
    setBusy(scenarioId ?? "all");
    setError(null);
    try {
      const r = await api.runAudit(scenarioId ? { scenario_id: scenarioId } : {});
      setMessage(t("auditDone", { ms: r.duration_ms, n: r.alert_count }));
      setRan(true);
      scenarios.reload();
      existing.reload();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(null);
    }
  }

  async function reset(id: string) {
    setBusy(id);
    setError(null);
    try {
      await api.resetScenario(id);
      setMessage(t("resetDone"));
      scenarios.reload();
      existing.reload();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(null);
    }
  }

  const alerts: Alert[] = existing.data?.alerts ?? [];
  const audited = ran || alerts.length > 0;
  const byRule = alerts.reduce<Record<string, number>>((acc, a) => {
    acc[a.rule_id] = (acc[a.rule_id] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <section>
      <div className="hero">
        <h1>{t("heroTitle")}</h1>
        <p>{t("heroBody")}</p>
        <div className="hero-actions">
          <button
            type="button"
            className="btn btn-primary"
            disabled={busy !== null}
            onClick={() => audit()}
          >
            {busy === "all" ? t("running") : t("runAll")}
          </button>
        </div>
      </div>

      {message && (
        <p className="note note-ok" role="status">
          {message}
        </p>
      )}
      {error && <ErrorNote message={error} />}

      {audited && (
        <div className="counts" aria-label={t("resultCounts")}>
          <div>
            <span className="big">{alerts.length}</span>
            <span>{t("totalAlerts")}</span>
          </div>
          {Object.keys(byRule)
            .sort()
            .map((r) => (
              <div key={r}>
                <span className="big">{byRule[r]}</span>
                <span>{r}</span>
              </div>
            ))}
        </div>
      )}

      <h2>{t("scenariosTitle")}</h2>
      {scenarios.loading && <Loading />}
      {scenarios.error && <ErrorNote message={scenarios.error} onRetry={scenarios.reload} />}
      {scenarios.data && scenarios.data.scenarios.length === 0 && (
        <Empty title={t("scenariosTitle")} />
      )}
      <ul className="scenario-list">
        {scenarios.data?.scenarios.map((s) => (
          <li key={s.id}>
            <div>
              <h3>{pick(s.name, s.name_bn)}</h3>
              <p>{pick(s.description, s.description_bn)}</p>
              <p className="muted">
                {!audited
                  ? t("notAudited")
                  : s.alert_total === 0
                    ? t("noAlerts")
                    : t("alertsCount", { n: s.alert_total }) +
                      " (" +
                      Object.entries(s.alert_counts)
                        .sort()
                        .map(([r, n]) => `${r}: ${n}`)
                        .join(", ") +
                      ")"}
              </p>
            </div>
            <div className="actions">
              {s.parcel_ids[0] && (
                <Link className="btn" to={`/parcels/${s.parcel_ids[0]}`}>
                  {t("openParcel")}
                </Link>
              )}
              <button
                type="button"
                className="btn"
                disabled={busy !== null}
                onClick={() => audit(s.id)}
              >
                {busy === s.id ? t("running") : t("runAudit")}
              </button>
              <button
                type="button"
                className="btn btn-quiet"
                disabled={busy !== null}
                onClick={() => reset(s.id)}
              >
                {t("reset")}
              </button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

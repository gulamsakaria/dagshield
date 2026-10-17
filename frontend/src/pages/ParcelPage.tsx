import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { Empty, ErrorNote, Loading, SeverityBadge, StatusBadge, fmt } from "../components/ui";
import { useApi } from "../hooks";
import { useI18n } from "../i18n";

export default function ParcelPage() {
  const { id = "" } = useParams();
  const { t, pick } = useI18n();
  const h = useApi(() => api.history(id), [id]);
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function audit() {
    setBusy(true);
    setError(null);
    try {
      await api.runAudit({ parcel_id: id });
      h.reload();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (h.loading && !h.data) return <Loading />;
  if (h.error) return <ErrorNote message={h.error} onRetry={h.reload} />;
  if (!h.data) return null;
  const { parcel, lineage, ownership_summary, timeline, alerts } = h.data;

  return (
    <section>
      <p>
        <Link to="/">{t("back")}</Link>
      </p>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
          marginBottom: "16px",
        }}
      >
        <h1 style={{ margin: 0 }}>
          {t("parcelTitle")} {parcel.id}
        </h1>
      </div>
      <dl className="facts">
        <div>
          <dt>{t("dag")}</dt>
          <dd>{parcel.dag_no ?? "-"}</dd>
        </div>
        <div>
          <dt>{t("survey")}</dt>
          <dd>{parcel.survey_type}</dd>
        </div>
        <div>
          <dt>{t("area")}</dt>
          <dd className="num">{fmt(parcel.area_decimal)}</dd>
        </div>
      </dl>

      <h2>{t("parcelAlerts")}</h2>
      {error && <ErrorNote message={error} />}
      {alerts.length === 0 ? (
        <Empty title={t("parcelNoAlerts")} />
      ) : (
        <ul className="alert-list">
          {alerts.map((a) => (
            <li key={a.id}>
              <div className="row">
                <strong>{a.rule_id}</strong>
                <SeverityBadge severity={a.severity} />
                <StatusBadge status={a.status} />
                {a.heuristic && <span className="badge">{t("heuristic")}</span>}
              </div>
              <p>
                <Link to={`/alerts/${a.id}`}>{pick(a.message_en, a.message_bn)}</Link>
              </p>
            </li>
          ))}
        </ul>
      )}
      <button type="button" className="btn" disabled={busy} onClick={audit}>
        {busy ? t("running") : t("auditParcel")}
      </button>

      <h2>{t("lineageTitle")}</h2>
      {lineage.length === 0 ? (
        <p className="muted">{t("lineageNone")}</p>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>{t("rule")}</th>
              <th>{t("lineageParent")}</th>
              <th>{t("lineageChild")}</th>
              <th>{t("confidence")}</th>
            </tr>
          </thead>
          <tbody>
            {lineage.map((l) => (
              <tr key={l.id}>
                <td>{l.relationship}</td>
                <td>
                  <Link to={`/parcels/${l.parent.id}`}>{l.parent.id}</Link> ({fmt(l.parent.area)})
                </td>
                <td>
                  <Link to={`/parcels/${l.child.id}`}>{l.child.id}</Link> ({fmt(l.child.area)})
                </td>
                <td className="num">
                  {fmt(l.confidence)}{" "}
                  {l.uncertain && (
                    <span className="badge sev-review">
                      <span aria-hidden="true">?</span> {t("uncertainLink")}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h2>{t("ownershipTitle")}</h2>
      <table className="table">
        <thead>
          <tr>
            <th>{t("owner")}</th>
            <th className="num">{t("opening")}</th>
            <th className="num">{t("incoming")}</th>
            <th className="num">{t("outgoing")}</th>
            <th className="num">{t("balance")}</th>
          </tr>
        </thead>
        <tbody>
          {ownership_summary.map((o) => (
            <tr key={o.owner}>
              <td>{o.owner}</td>
              <td className="num">{fmt(o.opening)}</td>
              <td className="num">{fmt(o.incoming)}</td>
              <td className="num">{fmt(o.outgoing)}</td>
              <td className="num">{o.balance === null ? t("insufficientData") : fmt(o.balance)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>{t("timelineTitle")}</h2>
      {timeline.length === 0 ? (
        <p className="muted">{t("timelineNone")}</p>
      ) : (
        <ol className="timeline">
          {timeline.map((e) => (
            <li key={`${e.kind}-${e.id}`} className={`tl-${e.kind}`}>
              <div className="row">
                <time>{e.date ?? t("noDate")}</time>
                <strong>
                  {e.kind} {e.id}
                </strong>
                <span className="badge">{e.status}</span>
              </div>
              <p>{e.summary}</p>
              <button
                type="button"
                className="btn btn-quiet"
                aria-expanded={!!open[e.id]}
                onClick={() => setOpen({ ...open, [e.id]: !open[e.id] })}
              >
                {open[e.id] ? t("hideDetails") : t("showDetails")}
              </button>
              {open[e.id] && (
                <dl className="facts compact">
                  {Object.entries(e.details).map(([k, v]) => (
                    <div key={k}>
                      <dt>{k}</dt>
                      <dd>{v === null ? "-" : String(v)}</dd>
                    </div>
                  ))}
                </dl>
              )}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

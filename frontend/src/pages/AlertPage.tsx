import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Alert, Status, api } from "../api";
import Ledger, { LedgerRow } from "../components/Ledger";
import { ErrorNote, Loading, SeverityBadge, StatusBadge } from "../components/ui";
import { useApi } from "../hooks";
import { useI18n } from "../i18n";

const STATUSES: Status[] = ["New", "Under Review", "Closed"];

function Evidence({ a }: { a: Alert }) {
  const { t } = useI18n();
  const c = a.calc;
  if (a.outcome === "insufficient_data") {
    return (
      <ul>
        {(c.reasons as string[]).map((r) => (
          <li key={r}>{r}</li>
        ))}
      </ul>
    );
  }
  if (a.rule_id === "R2") {
    const rows: LedgerRow[] = [
      { label: t("openingEntitlement", { owner: c.owner }), value: c.opening, sign: "+" },
      { label: t("recognizedIncoming"), value: c.recognized_incoming, sign: "+" },
      { label: t("priorOutgoing"), value: c.prior_active_outgoing, sign: "-" },
      { label: t("availableBefore"), value: c.available, tone: "total" },
      { label: t("attempted"), value: c.attempted },
      { label: t("excess"), value: c.excess, tone: "flag" },
    ];
    return (
      <>
        <Ledger rows={rows} />
        <p className="muted">
          {t("formula")}: {c.formula}
        </p>
      </>
    );
  }
  if (a.rule_id === "R4" && c.children_total !== undefined) {
    const rows: LedgerRow[] = [
      { label: t("parentArea"), value: c.parent_area },
      ...Object.entries(c.children as Record<string, number>).map(([id, v]) => ({
        label: t("childArea", { id }),
        value: v,
        sign: "+" as const,
      })),
      { label: t("childrenTotal"), value: c.children_total, tone: "total" },
      { label: t("tolerance"), value: c.tolerance },
      { label: t("difference"), value: c.difference, tone: "flag" },
    ];
    return <Ledger rows={rows} />;
  }
  if (a.rule_id === "R4") {
    return (
      <Ledger
        rows={[
          { label: `${c.parent} → ${c.child}`, value: "" },
          { label: t("confidence"), value: c.confidence, tone: "flag" },
          { label: t("minimumConfidence"), value: c.minimum },
        ]}
      />
    );
  }
  if (a.rule_id === "R1") {
    return (
      <>
        <p>
          {t("portion")}: <strong>{c.portion_key}</strong>
        </p>
        <table className="table">
          <thead>
            <tr>
              <th>{t("claim")}</th>
              <th>{t("transfer")}</th>
              <th>{t("deed")}</th>
              <th>{t("recipient")}</th>
              <th>{t("date")}</th>
            </tr>
          </thead>
          <tbody>
            {(
              c.claims as {
                transfer: string;
                deed: string;
                recipient: string;
                date: string | null;
              }[]
            ).map((x, i) => (
              <tr key={x.transfer}>
                <td>{i + 1}</td>
                <td>{x.transfer}</td>
                <td>{x.deed}</td>
                <td>{x.recipient}</td>
                <td>{x.date ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </>
    );
  }
  if (a.rule_id === "R3") {
    return (
      <dl className="facts compact">
        <div>
          <dt>{t("reason")}</dt>
          <dd>{c.reason}</dd>
        </div>
        <div>
          <dt>{t("transfer")}</dt>
          <dd>{c.transfer}</dd>
        </div>
        <div>
          <dt>{t("deed")}</dt>
          <dd>{c.deed ?? "-"}</dd>
        </div>
        {c.differences && (
          <div>
            <dt>{t("differences")}</dt>
            <dd>{(c.differences as string[]).join("; ")}</dd>
          </div>
        )}
      </dl>
    );
  }
  if (a.rule_id === "R5") {
    return (
      <Ledger
        rows={[
          { label: t("threshold"), value: c.threshold },
          { label: t("windowDays"), value: c.window_days },
          {
            label: t("eventsFound"),
            value: `${c.count} (${(c.transfers as string[]).join(", ")})`,
          },
        ]}
      />
    );
  }
  return null;
}

export default function AlertPage() {
  const { id = "" } = useParams();
  const { t, pick } = useI18n();
  const q = useApi(() => api.alert(id), [id]);
  const [error, setError] = useState<string | null>(null);

  async function change(status: Status) {
    setError(null);
    try {
      q.setData(await api.setStatus(id, status));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  if (q.loading && !q.data) return <Loading />;
  if (q.error) return <ErrorNote message={q.error} onRetry={q.reload} />;
  const a = q.data;
  if (!a) return null;

  return (
    <section>
      <p>
        <Link to={`/parcels/${a.parcel_id}`}>
          {t("back")}: {a.parcel_id}
        </Link>
      </p>
      <h1>
        {t("alertTitle")} {a.rule_id}
      </h1>
      <div className="row">
        <SeverityBadge severity={a.severity} />
        <StatusBadge status={a.status} />
        {a.heuristic && <span className="badge">{t("heuristic")}</span>}
        <span className="muted">
          {t("rule")} {a.rule_id} v{a.rule_version}
        </span>
      </div>
      <p className="lead">{pick(a.message_en, a.message_bn)}</p>

      <h2>{t("ledgerTitle")}</h2>
      <Evidence a={a} />

      <h2>{t("nextCheck")}</h2>
      <p>{pick(a.next_check_en, a.next_check_bn)}</p>

      <h2>{t("evidenceIds")}</h2>
      <ul className="chips">
        {a.evidence_ids.map((e) => (
          <li key={e}>{e}</li>
        ))}
      </ul>

      <h2>{t("setStatus")}</h2>
      {error && <ErrorNote message={error} />}
      <div className="row" role="group" aria-label={t("setStatus")}>
        {STATUSES.map((s) => (
          <button
            key={s}
            type="button"
            className="btn"
            aria-pressed={a.status === s}
            onClick={() => change(s)}
          >
            {t(`st_${s}` as "st_New" | "st_Under Review" | "st_Closed")}
          </button>
        ))}
      </div>
    </section>
  );
}

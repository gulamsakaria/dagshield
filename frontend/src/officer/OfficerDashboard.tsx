import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { officerApi } from "../api";
import { Empty, ErrorNote, Loading } from "../components/ui";
import { useApi } from "../hooks";
import { PageHead, VerdictBadge, reasonOf, useFmt } from "./common";

export default function OfficerDashboard() {
  const { pick, lang, num, area, time } = useFmt();
  const navigate = useNavigate();
  const summary = useApi(() => officerApi.summary(), []);
  const plots = useApi(() => officerApi.plots(), []);
  const recent = useApi(() => officerApi.attempts(), []);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function reloadAll() {
    summary.reload();
    plots.reload();
    recent.reload();
  }

  async function resetDemo() {
    if (
      !window.confirm(
        pick(
          "Reset the demo registry to its starting data?",
          "ডেমো রেজিস্ট্রি শুরুর অবস্থায় ফিরিয়ে নেবেন?",
        ),
      )
    )
      return;
    setBusy(true);
    setError(null);
    try {
      await officerApi.reset();
      reloadAll();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const s = summary.data;
  const cards = [
    {
      key: "total",
      tone: "t-total",
      icon: "▤",
      v: s?.total,
      en: "Total transactions",
      bn: "মোট লেনদেন",
    },
    { key: "success", tone: "t-success", icon: "✓", v: s?.success, en: "Successful", bn: "সফল" },
    {
      key: "warning",
      tone: "t-warning",
      icon: "▲",
      v: s?.warning,
      en: "Suspicious",
      bn: "সন্দেহজনক",
    },
    {
      key: "blocked",
      tone: "t-blocked",
      icon: "✕",
      v: s?.blocked,
      en: "Blocked",
      bn: "ব্লক হয়েছে",
    },
  ];

  return (
    <section>
      <PageHead
        title={pick("Registration overview", "নিবন্ধন সংক্ষিপ্ত চিত্র")}
        lead={pick(
          "Every deed request is checked against the plot record before it is registered.",
          "প্রতিটি দলিলের আবেদন নিবন্ধনের আগে দাগের রেকর্ডের সঙ্গে মিলিয়ে দেখা হয়।",
        )}
        actions={
          <Link to="/officer/new" className="btn btn-primary">
            + {pick("New registration", "নতুন দলিল নিবন্ধন")}
          </Link>
        }
      />
      {error && <ErrorNote message={error} />}
      {summary.error && <ErrorNote message={summary.error} onRetry={summary.reload} />}

      <div className="stat-cards">
        {cards.map((c) => (
          <button
            type="button"
            key={c.key}
            className={`stat-card ${c.tone}`}
            onClick={() =>
              navigate(
                c.key === "warning" || c.key === "blocked"
                  ? `/officer/alerts?v=${c.key}`
                  : "/officer/alerts",
              )
            }
          >
            <span className="stat-icon" aria-hidden="true">
              {c.icon}
            </span>
            <b>{c.v === undefined ? "…" : num(c.v)}</b>
            <span>{pick(c.en, c.bn)}</span>
          </button>
        ))}
      </div>

      <div className="two-col">
        <div>
          <h2>{pick("Latest requests", "সাম্প্রতিক আবেদন")}</h2>
          {recent.loading && <Loading />}
          {recent.error && <ErrorNote message={recent.error} onRetry={recent.reload} />}
          {recent.data && recent.data.attempts.length === 0 && (
            <Empty title={pick("No requests yet", "এখনো কোনো আবেদন নেই")}>
              {pick(
                "Register a deed to see the check result here.",
                "একটি দলিল নিবন্ধন করলে যাচাইয়ের ফল এখানে দেখা যাবে।",
              )}
            </Empty>
          )}
          <ul className="attempt-list">
            {recent.data?.attempts.slice(0, 5).map((a) => (
              <li key={a.id} className={`attempt v-${a.verdict}`}>
                <div className="row">
                  <VerdictBadge verdict={a.verdict} />
                  <span className="muted">
                    {a.mouza} · {pick("Dag", "দাগ")} {num(a.dag_no)}
                  </span>
                  <span className="muted push">{time(a.created_at)}</span>
                </div>
                <p>
                  <strong>{a.seller}</strong> → <strong>{a.buyer}</strong> · {area(a.area)}{" "}
                  {pick("shatak", "শতক")}
                </p>
                <p className="muted">{reasonOf(a, lang)}</p>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h2>{pick("Plots in the record", "রেকর্ডে থাকা দাগ")}</h2>
          {plots.loading && <Loading />}
          {plots.error && <ErrorNote message={plots.error} onRetry={plots.reload} />}
          <div className="scroll">
            <table className="table">
              <thead>
                <tr>
                  <th>{pick("Mouza", "মৌজা")}</th>
                  <th>{pick("Dag", "দাগ")}</th>
                  <th>{pick("Current owner", "বর্তমান মালিক")}</th>
                  <th className="num">{pick("Shatak", "শতক")}</th>
                </tr>
              </thead>
              <tbody>
                {plots.data?.plots.map((p) => (
                  <tr key={p.id}>
                    <td>{p.mouza}</td>
                    <td>
                      <Link
                        to={`/officer/history?mouza=${encodeURIComponent(p.mouza)}&dag=${p.dag_no}`}
                      >
                        {num(p.dag_no)}
                      </Link>
                    </td>
                    <td>{p.owners.join(", ")}</td>
                    <td className="num">{area(p.total_area)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="muted small">
            {pick("Hand-entered synthetic names and plots.", "হাতে ঢোকানো নকল নাম ও দাগ।")}
          </p>
          <button type="button" className="btn btn-quiet" disabled={busy} onClick={resetDemo}>
            ↺ {pick("Reset demo data", "ডেমো ডেটা রিসেট")}
          </button>
        </div>
      </div>
    </section>
  );
}

import { Link, useSearchParams } from "react-router-dom";
import { Verdict, officerApi } from "../api";
import { Empty, ErrorNote, Loading } from "../components/ui";
import { useApi } from "../hooks";
import { PageHead, VerdictBadge, reasonOf, useFmt } from "./common";

type Filter = "all" | Verdict;

export default function OfficerAlerts() {
  const { pick, lang, num, area, time } = useFmt();
  const [params, setParams] = useSearchParams();
  const raw = params.get("v");
  const filter: Filter = raw === "blocked" || raw === "warning" ? raw : "all";
  const verdicts: Verdict[] = filter === "all" ? ["blocked", "warning"] : [filter];
  const res = useApi(() => officerApi.attempts(verdicts), [filter]);

  const tabs: { id: Filter; en: string; bn: string }[] = [
    { id: "all", en: "All alerts", bn: "সব অ্যালার্ট" },
    { id: "blocked", en: "🔴 Blocked", bn: "🔴 ব্লক" },
    { id: "warning", en: "🟡 Suspicious", bn: "🟡 সন্দেহজনক" },
  ];

  return (
    <section>
      <PageHead
        title={pick("Alert list", "অ্যালার্ট তালিকা")}
        lead={pick(
          "Every attempt that was stopped or flagged, and why.",
          "কোন চেষ্টা কেন আটকানো বা চিহ্নিত হয়েছে, তার তালিকা।",
        )}
      />
      <div className="presets" role="group" aria-label={pick("Filter", "ফিল্টার")}>
        {tabs.map((t) => (
          <button
            type="button"
            key={t.id}
            className="chip-btn"
            aria-pressed={filter === t.id}
            onClick={() => setParams(t.id === "all" ? {} : { v: t.id })}
          >
            {pick(t.en, t.bn)}
          </button>
        ))}
      </div>
      {res.loading && <Loading />}
      {res.error && <ErrorNote message={res.error} onRetry={res.reload} />}
      {res.data && res.data.attempts.length === 0 && (
        <Empty title={pick("No alerts", "কোনো অ্যালার্ট নেই")}>
          {pick("Nothing has been blocked or flagged yet.", "এখনো কিছু আটকানো বা চিহ্নিত হয়নি।")}
        </Empty>
      )}
      <ul className="attempt-list">
        {res.data?.attempts.map((a) => (
          <li key={a.id} className={`attempt v-${a.verdict}`}>
            <div className="row">
              <VerdictBadge verdict={a.verdict} />
              <span className="rule-tag">{a.rule_id}</span>
              <span className="muted">
                {a.mouza} · {pick("Dag", "দাগ")} {num(a.dag_no)}
              </span>
              <span className="muted push">{time(a.created_at)}</span>
            </div>
            <p>
              <strong>{a.seller}</strong> → <strong>{a.buyer}</strong> · {area(a.area)}{" "}
              {pick("shatak", "শতক")}
            </p>
            <p className="attempt-reason">{reasonOf(a, lang)}</p>
            <div className="row small">
              <Link to={`/officer/result/${a.id}`}>{pick("Details", "বিস্তারিত")}</Link>
              {a.parcel_id !== null && (
                <Link
                  to={`/officer/history?mouza=${encodeURIComponent(a.mouza)}&dag=${encodeURIComponent(a.dag_no)}`}
                >
                  {pick("Plot history", "দাগের ইতিহাস")}
                </Link>
              )}
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

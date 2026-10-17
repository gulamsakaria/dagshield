import { Link, useParams } from "react-router-dom";
import { officerApi } from "../api";
import { ErrorNote, Loading } from "../components/ui";
import { useApi } from "../hooks";
import { PageHead, VERDICT_META, reasonOf, useFmt, verdictLabel } from "./common";

export default function RegistrationResult() {
  const { id = "" } = useParams();
  const { pick, lang, num, area, date, time } = useFmt();
  const res = useApi(() => officerApi.attempt(id), [id]);

  if (res.loading) return <Loading />;
  if (res.error || !res.data)
    return <ErrorNote message={res.error ?? "Not found"} onRetry={res.reload} />;
  const a = res.data;
  const meta = VERDICT_META[a.verdict];
  const headline =
    a.verdict === "success"
      ? pick("Check passed. Deed registered.", "যাচাই সফল। দলিল নিবন্ধিত হয়েছে।")
      : a.verdict === "warning"
        ? pick(
            "Registered, but flagged for human review.",
            "নিবন্ধিত হয়েছে, তবে মানুষের যাচাইয়ের জন্য চিহ্নিত।",
          )
        : pick("Blocked. The deed was not registered.", "ব্লক করা হয়েছে। দলিল নিবন্ধিত হয়নি।");

  return (
    <section>
      <PageHead title={pick("Check result", "যাচাইয়ের ফলাফল")} />
      <div className={`verdict-card v-${a.verdict}`} role="status">
        <div className="verdict-mark" aria-hidden="true">
          {meta.icon}
        </div>
        <div>
          <span className="verdict-kicker">
            {meta.dot} {verdictLabel(a.verdict, pick)}
          </span>
          <h2 className="plain">{headline}</h2>
          <p className="verdict-reason">
            <strong>{pick("Reason: ", "কারণ: ")}</strong>
            {reasonOf(a, lang)}
          </p>
          {a.rule_id !== "OK" && (
            <p className="muted small">
              {pick("Rule", "নিয়ম")} {a.rule_id}
              {a.calc.heuristic
                ? pick(" (heuristic, not a finding)", " (ইঙ্গিত মাত্র, সিদ্ধান্ত নয়)")
                : ""}
            </p>
          )}
        </div>
      </div>

      <h2>{pick("Application details", "আবেদনের তথ্য")}</h2>
      <dl className="facts">
        <div>
          <dt>{pick("Mouza", "মৌজা")}</dt>
          <dd>{a.mouza}</dd>
        </div>
        <div>
          <dt>{pick("Dag number", "দাগ নম্বর")}</dt>
          <dd>{num(a.dag_no)}</dd>
        </div>
        <div>
          <dt>{pick("Seller", "বিক্রেতা")}</dt>
          <dd>{a.seller}</dd>
        </div>
        <div>
          <dt>{pick("Buyer", "ক্রেতা")}</dt>
          <dd>{a.buyer}</dd>
        </div>
        <div>
          <dt>{pick("Area (shatak)", "পরিমাণ (শতক)")}</dt>
          <dd>{area(a.area)}</dd>
        </div>
        <div>
          <dt>{pick("Deed date", "দলিলের তারিখ")}</dt>
          <dd>{date(a.deed_date)}</dd>
        </div>
        <div>
          <dt>{pick("Checked at", "যাচাইয়ের সময়")}</dt>
          <dd>{time(a.created_at)}</dd>
        </div>
        <div>
          <dt>{pick("Reference", "রেফারেন্স")}</dt>
          <dd>#{num(a.id)}</dd>
        </div>
      </dl>

      <div className="row">
        {a.parcel_id !== null && (
          <Link
            className="btn btn-primary"
            to={`/officer/history?mouza=${encodeURIComponent(a.mouza)}&dag=${encodeURIComponent(a.dag_no)}`}
          >
            {pick("View plot history", "দাগের ইতিহাস দেখুন")}
          </Link>
        )}
        {a.rule_id === "R0" && (
          <Link className="btn btn-primary" to="/officer/plots">
            {pick("Add this plot to the registry", "এই জমি রেজিস্ট্রিতে যোগ করুন")}
          </Link>
        )}
        <Link className="btn" to="/officer/new">
          {pick("New registration", "নতুন আবেদন")}
        </Link>
        <Link className="btn btn-quiet" to="/officer/alerts">
          {pick("Alert list", "অ্যালার্ট তালিকা")}
        </Link>
      </div>
      <p className="muted small">
        {pick(
          "A screening aid for human review, not a legal opinion or proof of ownership or fraud.",
          "এটি মানুষের পর্যালোচনার সহায়ক যাচাই, আইনি মতামত বা মালিকানা অথবা জালিয়াতির প্রমাণ নয়।",
        )}
      </p>
    </section>
  );
}

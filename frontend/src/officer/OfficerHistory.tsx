import { FormEvent, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { RegHistory, RegTimelineEntry, officerApi } from "../api";
import { Empty, Loading } from "../components/ui";
import { useApi } from "../hooks";
import { PageHead, useFmt } from "./common";

function Timeline({ h }: { h: RegHistory }) {
  const { pick, lang, num, area, date } = useFmt();
  const line = (e: RegTimelineEntry) =>
    e.kind === "initial"
      ? pick(
          `Opening record: ${e.to} holds ${area(e.area)} shatak`,
          `প্রারম্ভিক রেকর্ড: ${e.to} — ${area(e.area)} শতক`,
        )
      : e.kind === "transfer"
        ? pick(
            `${e.from} → ${e.to}, ${area(e.area)} shatak`,
            `${e.from} → ${e.to}, ${area(e.area)} শতক`,
          )
        : pick(
            `Blocked attempt: ${e.from} → ${e.to}, ${area(e.area)} shatak`,
            `আটকানো চেষ্টা: ${e.from} → ${e.to}, ${area(e.area)} শতক`,
          );
  return (
    <ol className="timeline own-timeline">
      {h.timeline.map((e, i) => (
        <li key={i} className={`tl-${e.kind}${e.flagged ? " tl-flag" : ""}`}>
          <div className="row">
            <time>{date(e.date)}</time>
            <span
              className={`badge ${e.kind === "blocked" ? "sev-high" : e.flagged ? "sev-medium" : e.kind === "initial" ? "" : "status-closed"}`}
            >
              {e.kind === "initial"
                ? pick("Record", "রেকর্ড")
                : e.kind === "transfer"
                  ? e.flagged
                    ? pick("Registered, flagged", "নিবন্ধিত, চিহ্নিত")
                    : pick("Transfer", "হস্তান্তর")
                  : pick("Blocked", "ব্লক")}
            </span>
          </div>
          <p>
            <strong>{line(e)}</strong>
          </p>
          {e.kind === "blocked" && (
            <p className="muted">{lang === "bn" ? e.reason_bn : e.reason_en}</p>
          )}
          {e.attempt_id !== null && (
            <Link className="small" to={`/officer/result/${e.attempt_id}`}>
              {pick("Open check result", "যাচাইয়ের ফল দেখুন")} #{num(e.attempt_id)}
            </Link>
          )}
        </li>
      ))}
    </ol>
  );
}

export default function OfficerHistory() {
  const { pick, num, area } = useFmt();
  const [params, setParams] = useSearchParams();
  const mouza = params.get("mouza") ?? "";
  const dag = params.get("dag") ?? "";
  const [mInput, setM] = useState(mouza);
  const [dInput, setD] = useState(dag);
  const plots = useApi(() => officerApi.plots(), []);
  const res = useApi(
    () => (mouza && dag ? officerApi.history(mouza, dag) : Promise.resolve(null)),
    [mouza, dag],
  );

  function submit(e: FormEvent) {
    e.preventDefault();
    setParams({ mouza: mInput.trim(), dag: dInput.trim() });
  }

  return (
    <section>
      <PageHead
        title={pick("Plot history", "দাগের ইতিহাস")}
        lead={pick(
          "Search a plot to see who owned it and when it changed hands.",
          "দাগ খুঁজে দেখুন কে মালিক ছিলেন এবং কবে হাতবদল হয়েছে।",
        )}
      />
      <form className="inline-form" onSubmit={submit}>
        <input
          list="hist-mouza"
          value={mInput}
          onChange={(e) => setM(e.target.value)}
          placeholder={pick("Mouza", "মৌজা")}
          aria-label={pick("Mouza", "মৌজা")}
          required
        />
        <datalist id="hist-mouza">
          {plots.data?.mouzas.map((m) => <option key={m} value={m} />)}
        </datalist>
        <input
          value={dInput}
          onChange={(e) => setD(e.target.value)}
          placeholder={pick("Dag number", "দাগ নম্বর")}
          aria-label={pick("Dag number", "দাগ নম্বর")}
          inputMode="numeric"
          required
        />
        <button className="btn btn-primary">{pick("Search", "খুঁজুন")}</button>
      </form>
      {plots.data && (
        <div className="presets">
          <span className="muted">{pick("Plots:", "দাগ:")}</span>
          {plots.data.plots.map((p) => (
            <button
              type="button"
              key={p.id}
              className="chip-btn"
              onClick={() => {
                setM(p.mouza);
                setD(p.dag_no);
                setParams({ mouza: p.mouza, dag: p.dag_no });
              }}
            >
              {p.mouza} · {num(p.dag_no)}
            </button>
          ))}
        </div>
      )}

      {res.loading && <Loading />}
      {res.error && mouza && (
        <Empty title={pick("Not found in supplied dataset", "সরবরাহ করা ডেটাসেটে পাওয়া যায়নি")}>
          {pick("Check the mouza name and dag number.", "মৌজার নাম ও দাগ নম্বর আবার দেখুন।")}
        </Empty>
      )}
      {res.data && !res.error && (
        <>
          <h2>
            {res.data.parcel.mouza} · {pick("Dag", "দাগ")} {num(res.data.parcel.dag_no)}
          </h2>
          <div className="owner-cards">
            {res.data.owners.map((o) => (
              <div key={o.owner} className="owner-card">
                <span className="muted small">{pick("Current owner", "বর্তমান মালিক")}</span>
                <b>{o.owner}</b>
                <span>
                  {area(o.area)} {pick("shatak", "শতক")}
                </span>
              </div>
            ))}
          </div>
          <h2>{pick("Ownership timeline", "মালিকানার টাইমলাইন")}</h2>
          <Timeline h={res.data} />
        </>
      )}
      {!mouza && !dag && !res.loading && (
        <Empty title={pick("Pick a plot", "একটি দাগ বেছে নিন")}>
          {pick(
            "Choose one above or type a mouza and dag number.",
            "উপর থেকে একটি বেছে নিন, অথবা মৌজা ও দাগ নম্বর লিখুন।",
          )}
        </Empty>
      )}
    </section>
  );
}

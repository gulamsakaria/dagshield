import { FormEvent, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ApiError, PublicCheckResult, publicApi } from "../api";
import { ErrorNote } from "../components/ui";
import { useApi } from "../hooks";
import { useFmt } from "../officer/common";

// Simple client-side throttle against bulk look-ups: at most 10 checks in any 60 seconds.
// (The server has its own per-client limit too; this one just gives a friendly message first.)
const MAX_CHECKS = 10;
const WINDOW_MS = 60_000;

const ICON = { green: "✓", amber: "▲", red: "✕" } as const;
const DOT = { green: "🟢", amber: "🟡", red: "🔴" } as const;
// Reuse the officer portal's result-card colours: green = success, amber = warning, red = blocked.
const CARD = { green: "v-success", amber: "v-warning", red: "v-blocked" } as const;

export default function CheckLand() {
  const { pick, lang, num, date } = useFmt();
  const mouzas = useApi(() => publicApi.mouzas(), []);
  // The judge guide links here with ?mouza=...&dag=...&name=... so the form opens already filled in.
  const [params] = useSearchParams();
  const [mouza, setMouza] = useState(params.get("mouza") ?? "");
  const [dag, setDag] = useState(params.get("dag") ?? "");
  const [owner, setOwner] = useState(params.get("name") ?? "");
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [result, setResult] = useState<PublicCheckResult | null>(null);
  const hits = useRef<number[]>([]); // timestamps of recent checks

  /** Returns 0 if another check is allowed now, otherwise the seconds to wait. */
  function secondsToWait(): number {
    const now = Date.now();
    hits.current = hits.current.filter((t) => now - t < WINDOW_MS);
    if (hits.current.length >= MAX_CHECKS) {
      return Math.ceil((WINDOW_MS - (now - hits.current[0])) / 1000);
    }
    hits.current.push(now);
    return 0;
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setResult(null);
    // 1. friendly validation
    if (!mouza) return setProblem(pick("Choose a mouza.", "মৌজা বেছে নিন।"));
    if (!dag.trim()) return setProblem(pick("Enter the dag number.", "দাগ নম্বর লিখুন।"));
    if (owner.trim().length < 2)
      return setProblem(pick("Enter the owner's name.", "মালিকের নাম লিখুন।"));
    // 2. throttle
    const wait = secondsToWait();
    if (wait > 0) {
      return setProblem(
        pick(
          `Too many checks. Try again in ${wait} seconds.`,
          `অনেকবার যাচাই করা হয়েছে। ${num(wait)} সেকেন্ড পরে আবার চেষ্টা করুন।`,
        ),
      );
    }
    // 3. ask the server
    setProblem(null);
    setBusy(true);
    try {
      setResult(await publicApi.check(mouza, dag.trim(), owner.trim()));
    } catch (err) {
      const tooMany = err instanceof ApiError && err.status === 429;
      setProblem(
        tooMany
          ? pick(
              "Too many checks. Wait a minute and try again.",
              "অনেকবার যাচাই করা হয়েছে। এক মিনিট পরে আবার চেষ্টা করুন।",
            )
          : pick(
              "Could not check right now. Please try again.",
              "এখন যাচাই করা যাচ্ছে না। আবার চেষ্টা করুন।",
            ),
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="check">
      <div className="check-top">
        <h1>{pick("Check land", "জমি যাচাই করুন")}</h1>
        <p className="muted">
          {pick(
            "Before you buy, see whose name the record shows for a plot. No login needed.",
            "জমি কেনার আগে দেখুন রেকর্ডে দাগটি কার নামে আছে। লগইন লাগবে না।",
          )}
        </p>
      </div>

      <form className="check-form" onSubmit={submit} noValidate>
        <div className="check-grid">
          <label>
            {pick("Mouza", "মৌজা")}
            <select value={mouza} onChange={(e) => setMouza(e.target.value)}>
              <option value="">{pick("Select a mouza", "মৌজা বেছে নিন")}</option>
              {mouzas.data?.mouzas.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </label>
          <label>
            {pick("Dag number", "দাগ নম্বর")}
            <input
              value={dag}
              onChange={(e) => setDag(e.target.value)}
              inputMode="numeric"
              maxLength={32}
            />
          </label>
          <label className="check-wide">
            {pick("Owner's name", "মালিকের নাম")}
            <input value={owner} onChange={(e) => setOwner(e.target.value)} maxLength={120} />
          </label>
        </div>
        {mouzas.error && <ErrorNote message={mouzas.error} onRetry={mouzas.reload} />}
        {problem && (
          <p className="note note-error" role="alert">
            {problem}
          </p>
        )}
        <button type="submit" className="btn btn-primary" disabled={busy}>
          {busy ? pick("Checking…", "যাচাই হচ্ছে…") : pick("Check", "যাচাই করুন")}
        </button>
      </form>

      {result && <Result r={result} lang={lang} pick={pick} date={date} />}

      <p className="check-disclaimer">
        {pick(
          "This is not a legal guarantee, only a warning signal. Final verification is at the sub-registrar's office.",
          "এটি আইনি নিশ্চয়তা নয়, শুধু সতর্ক সংকেত। চূড়ান্ত যাচাই সাব-রেজিস্ট্রার অফিসে।",
        )}
      </p>
      <p className="check-back">
        <Link to="/officer/login">← {pick("Officer login", "অফিসার লগইন")}</Link>
      </p>
    </section>
  );
}

/** The big colour-coded card. Shows only: owner, status, mutation status and a short list of earlier owners. */
function Result({
  r,
  lang,
  pick,
  date,
}: {
  r: PublicCheckResult;
  lang: "en" | "bn";
  pick: (en: string, bn: string) => string;
  date: (iso: string) => string;
}) {
  const status =
    r.result === "ok"
      ? pick("Eligible for sale", "বিক্রির যোগ্য")
      : r.result === "mutation_pending"
        ? pick("Caution", "সতর্কতা")
        : r.result === "not_owner"
          ? pick("Not under this name", "এই নামে নেই")
          : pick("Not found", "পাওয়া যায়নি");

  return (
    <>
      <div className={`verdict-card ${CARD[r.level]}`} role="status">
        <div className="verdict-mark" aria-hidden="true">
          {ICON[r.level]}
        </div>
        <div>
          <span className="verdict-kicker">
            {DOT[r.level]} {status}
          </span>
          <h2 className="plain">{lang === "bn" ? r.message_bn : r.message_en}</h2>
          {r.result === "not_owner" && r.sold_on && (
            <p className="verdict-reason">
              {pick(
                `Already sold on ${date(r.sold_on)}.`,
                `আগেই বিক্রি হয়েছে (${date(r.sold_on)})।`,
              )}
            </p>
          )}
        </div>
      </div>

      {r.result !== "not_found" && (
        <dl className="facts">
          <div>
            <dt>{pick("Registered owner", "রেজিস্টার্ড মালিক")}</dt>
            <dd>{r.registered_owners.join(", ")}</dd>
          </div>
          <div>
            <dt>{pick("Status", "অবস্থা")}</dt>
            <dd>{status}</dd>
          </div>
          <div>
            <dt>{pick("Mutation (namjari)", "নামজারি")}</dt>
            <dd>{r.mutation_done ? pick("Done", "সম্পন্ন") : pick("Pending", "বাকি")}</dd>
          </div>
        </dl>
      )}

      {r.previous_owners.length > 0 && (
        <div className="check-history">
          <h3>{pick("Short ownership history", "মালিকানার সংক্ষিপ্ত ইতিহাস")}</h3>
          <ul>
            {r.previous_owners.map((p) => (
              <li key={p.name + p.date}>
                <strong>{p.name}</strong>
                <span className="muted">
                  {" "}
                  — {pick("sold on", "বিক্রি করেছেন")} {date(p.date)}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </>
  );
}

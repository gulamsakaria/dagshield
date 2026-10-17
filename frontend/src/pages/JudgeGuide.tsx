import { ReactNode, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getOfficerToken, officerApi, publicApi, setOfficerToken } from "../api";
import { ErrorNote } from "../components/ui";
import { useApi } from "../hooks";
import { useFmt } from "../officer/common";

const M1 = "নমুনা মৌজা-১";
const hist = (mouza: string, dag: string) =>
  `/officer/history?mouza=${encodeURIComponent(mouza)}&dag=${dag}`;

type Tone = "green" | "amber" | "red" | "info";
interface Step {
  to: string;
  tone: Tone;
  title: [string, string];
  doIt: [string, string];
  expect: [string, string];
}

// The order matters: steps 2 to 5 all work on plot 123, one after the other.
const STEPS: Step[] = [
  {
    to: "/officer",
    tone: "info",
    title: ["Look at the dashboard", "ড্যাশবোর্ড দেখুন"],
    doIt: [
      "Open the officer dashboard after starting the demo.",
      "ডেমো শুরু করে অফিসারের ড্যাশবোর্ড খুলুন।",
    ],
    expect: [
      "Four cards: 7 requests, 3 successful, 1 suspicious, 3 blocked, plus the list of plots.",
      "চারটি কার্ড: মোট ৭, সফল ৩, সন্দেহজনক ১, ব্লক ৩। সঙ্গে জমির তালিকা।",
    ],
  },
  {
    to: "/officer/new?demo=1",
    tone: "green",
    title: ["A normal sale", "সফল বিক্রি"],
    doIt: [
      "The form is filled for you (Rahim Uddin sells plot 123 to Karim Mia). Press “Check and register”.",
      "ফর্ম নিজে ভরা আছে (রহিম উদ্দিন → করিম মিয়া, দাগ ১২৩)। “যাচাই করে নিবন্ধন করুন” চাপুন।",
    ],
    expect: [
      "Green. The seller is the record owner and the area fits, so ownership moves to Karim Mia.",
      "🟢 সবুজ। বিক্রেতা রেকর্ডের মালিক, পরিমাণ মিলেছে, তাই মালিকানা করিম মিয়ার নামে যায়।",
    ],
  },
  {
    to: "/officer/new?demo=2",
    tone: "red",
    title: ["Double sale", "ডাবল সেল"],
    doIt: [
      "Rahim Uddin tries to sell plot 123 again. Do step 2 first. Press the button.",
      "রহিম উদ্দিন আবার ১২৩ বিক্রি করতে আসছেন। আগে ২ নম্বর ধাপ করুন। বাটন চাপুন।",
    ],
    expect: [
      "Red, rule R1: “This plot was already sold. The current owner is Karim Mia.” Nothing changes.",
      "🔴 লাল, নিয়ম R1: “এই দাগ আগেই বিক্রি হয়েছে, বর্তমান মালিক করিম মিয়া।” কিছু বদলায় না।",
    ],
  },
  {
    to: "/officer/new?demo=3",
    tone: "red",
    title: ["A seller who is not the owner", "ভুয়া বিক্রেতা"],
    doIt: [
      "An unknown person tries to sell plot 124.",
      "অজানা এক ব্যক্তি দাগ ১২৪ বিক্রি করতে আসছেন।",
    ],
    expect: [
      "Red, rule R2: “The seller is not the record owner of this plot.”",
      "🔴 লাল, নিয়ম R2: “বিক্রেতা রেকর্ডের মালিক নন।”",
    ],
  },
  {
    to: "/officer/new?demo=4",
    tone: "amber",
    title: ["A quick resale", "দ্রুত পুনঃবিক্রয়"],
    doIt: [
      "Karim Mia sells plot 123 on to Nasir Ahmed on the same day. Do step 2 first.",
      "করিম মিয়া একই দিনে ১২৩ আবার নাসির আহমেদকে বিক্রি করছেন। আগে ২ নম্বর ধাপ করুন।",
    ],
    expect: [
      "Yellow, rule R5 (a heuristic): registered, but flagged for a human to review.",
      "🟡 হলুদ, নিয়ম R5 (শুধু ইঙ্গিত): নিবন্ধিত হয়, কিন্তু মানুষের যাচাইয়ের জন্য চিহ্নিত থাকে।",
    ],
  },
  {
    to: hist(M1, "123"),
    tone: "info",
    title: ["Ownership history of a plot", "দাগের ইতিহাস"],
    doIt: ["Open the history of plot 123.", "দাগ ১২৩-এর ইতিহাস খুলুন।"],
    expect: [
      "A timeline: the opening record, each transfer, and every blocked attempt with its reason.",
      "একটি টাইমলাইন: প্রারম্ভিক রেকর্ড, প্রতিটি হস্তান্তর, আর আটকানো প্রতিটি চেষ্টা কারণসহ।",
    ],
  },
  {
    to: "/officer/alerts",
    tone: "info",
    title: ["Why attempts were stopped", "কেন আটকানো হয়েছে"],
    doIt: ["Open the alert list and try the filters.", "অ্যালার্ট তালিকা খুলে ফিল্টার চেপে দেখুন।"],
    expect: [
      "Every blocked or flagged request with its rule code and the reason in plain words.",
      "আটকানো বা চিহ্নিত প্রতিটি আবেদন, নিয়মের কোড আর সহজ ভাষায় কারণসহ।",
    ],
  },
  {
    to: "/officer/plots",
    tone: "info",
    title: ["Add a plot (English or Bangla)", "নতুন জমি যোগ করুন"],
    doIt: [
      "Add any plot with made-up names. Names can be typed in English.",
      "কাল্পনিক নামে যেকোনো জমি যোগ করুন। নাম ইংরেজিতেও লেখা যায়।",
    ],
    expect: [
      "The plot appears in the list and in the public page's mouza list at once.",
      "জমিটি তালিকায় আর সাধারণ মানুষের পেজের মৌজা তালিকায় সঙ্গে সঙ্গে আসে।",
    ],
  },
  {
    to: `/check?mouza=${encodeURIComponent(M1)}&dag=123&name=${encodeURIComponent("রহিম উদ্দিন")}`,
    tone: "red",
    title: ["Check land as a buyer (no login)", "সাধারণ মানুষ হিসেবে যাচাই"],
    doIt: [
      "The public page opens with Rahim Uddin and plot 123 filled in. Press “Check”.",
      "পাবলিক পেজ রহিম উদ্দিন আর ১২৩ ভরা অবস্থায় খোলে। “যাচাই করুন” চাপুন।",
    ],
    expect: [
      "After step 2: red, “not under this name” with the current owner and the sale date. Before step 2: green.",
      "২ নম্বর ধাপের পরে 🔴 “এই নামে নেই”, সঙ্গে বর্তমান মালিক ও বিক্রির তারিখ। ধাপ ২-এর আগে 🟢 সবুজ।",
    ],
  },
  {
    to: `/check?mouza=${encodeURIComponent("Sample Mouza 4")}&dag=402&name=${encodeURIComponent("Rubel Hasan")}`,
    tone: "amber",
    title: ["A pending mutation (namjari)", "নামজারি বাকি"],
    doIt: [
      "Press “Check” for Rubel Hasan on plot 402 of Sample Mouza 4.",
      "Sample Mouza 4-এর দাগ ৪০২-এ Rubel Hasan-এর জন্য “যাচাই করুন” চাপুন।",
    ],
    expect: [
      "Amber: the deed is registered but the khatian still names the old owner, so a fresh sale is suspicious.",
      "🟡 হলুদ: দলিল নিবন্ধিত, কিন্তু খতিয়ানে এখনো আগের মালিক। তাই আবার বিক্রি সন্দেহজনক।",
    ],
  },
  {
    to: "/verify",
    tone: "info",
    title: ["Check a deed copy", "দলিলের কপি যাচাই"],
    doIt: [
      "Check a genuine copy, then change one value and check again.",
      "আসল কপি যাচাই করুন, তারপর একটা মান বদলে আবার যাচাই করুন।",
    ],
    expect: [
      "The genuine copy matches. The edited copy fails and names the changed field (hash and digital signature).",
      "আসল কপি মেলে। বদলানো কপি মেলে না, আর কোন ঘর বদলেছে তা বলে দেয় (hash ও ডিজিটাল স্বাক্ষর)।",
    ],
  },
  {
    to: "/dashboard",
    tone: "info",
    title: ["Ten test scenarios", "দশটি পরীক্ষার দৃশ্যকল্প"],
    doIt: [
      "Press “Run audit on all scenarios”. Open any alert to see its evidence. “Evaluation” shows the real test counts.",
      "“Run audit on all scenarios” চাপুন। যেকোনো সতর্কতা খুলে প্রমাণ দেখুন। “মূল্যায়ন” পেজে আসল test সংখ্যা আছে।",
    ],
    expect: [
      "Each alert lists its rule, the record IDs it used and the arithmetic, so a person can check it.",
      "প্রতিটি সতর্কতায় নিয়ম, ব্যবহৃত রেকর্ডের আইডি আর হিসাব থাকে, যাতে একজন মানুষ যাচাই করতে পারেন।",
    ],
  },
];

const TONE_LABEL: Record<Tone, [string, string]> = {
  green: ["🟢 Green", "🟢 সবুজ"],
  amber: ["🟡 Yellow", "🟡 হলুদ"],
  red: ["🔴 Red", "🔴 লাল"],
  info: ["Look", "দেখুন"],
};

const PLOTS: [string, string, string, string][] = [
  [M1, "123", "রহিম উদ্দিন", "10"],
  [M1, "124", "সালমা বেগম", "15"],
  ["নমুনা মৌজা-২", "201", "জামাল হোসেন", "20"],
  ["নমুনা মৌজা-২", "202", "নাজমা খাতুন", "12"],
  ["নমুনা মৌজা-৩", "301", "আব্দুল হামিদ (5), ফারুক আহমেদ (3)", "8"],
  ["নমুনা মৌজা-৩", "302", "রোকেয়া খাতুন", "12"],
  ["Sample Mouza 4", "401", "Mizanur Rahman (earlier owner: Karim Hossain)", "10"],
  ["Sample Mouza 4", "402", "Rubel Hasan (earlier: Nasrin Akter, Tania Sultana)", "14"],
  ["Sample Mouza 4", "403", "Sultana Razia", "6"],
];

function Section({
  kicker,
  title,
  children,
}: {
  kicker: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="jg-section">
      <span className="kicker">{kicker}</span>
      <h2 className="plain">{title}</h2>
      {children}
    </section>
  );
}

export default function JudgeGuide() {
  const { pick, lang, num } = useFmt();
  const navigate = useNavigate();
  const cfg = useApi(() => publicApi.config(), []);
  const [busy, setBusy] = useState<"start" | "reset" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const enabled = cfg.data?.judge_login === true;
  const started = getOfficerToken() !== "";

  async function start() {
    setBusy("start");
    setError(null);
    try {
      if (!getOfficerToken()) setOfficerToken((await officerApi.judgeLogin()).token);
      await officerApi.reset(); // always start from the same clean state, so every step below gives the answer written here
      await officerApi.loadSample();
      navigate("/officer");
    } catch (e) {
      setOfficerToken("");
      setError((e as Error).message);
      setBusy(null);
    }
  }

  async function reset() {
    setBusy("reset");
    setError(null);
    setNote(null);
    try {
      await officerApi.reset();
      const r = await officerApi.loadSample();
      setNote(
        pick(
          `Demo restarted: ${r.plots + 4} plots and ${r.requests} past requests are loaded.`,
          `ডেমো আবার শুরু হয়েছে: ${num(r.plots + 4)}টি জমি আর ${num(r.requests)}টি আগের আবেদন লোড হয়েছে।`,
        ),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="jg">
      <header className="jg-hero">
        <span className="eyebrow">
          <i aria-hidden="true" />
          {pick("For the judges", "জুরির জন্য")}
        </span>
        <h1>{pick("See the whole demo in one click", "এক ক্লিকে পুরো ডেমো দেখুন")}</h1>
        <p className="jg-lead">
          {pick(
            "No password. One button signs you in as a demo officer and fills the system with sample plots and past requests, so every screen has something to show. Everything is made up.",
            "কোনো পাসওয়ার্ড লাগে না। একটি বাটনে ডেমো অফিসার হিসেবে ঢুকে যাবেন, আর সিস্টেমে নমুনা জমি ও আগের আবেদন ভরে দেওয়া হবে, তাই প্রতিটি স্ক্রিনে দেখার মতো কিছু থাকবে। সবই কাল্পনিক।",
          )}
        </p>
        <div className="jg-actions">
          <button
            type="button"
            className="btn btn-gold btn-big"
            disabled={!enabled || busy !== null}
            onClick={start}
          >
            {busy === "start"
              ? pick("Starting…", "চালু হচ্ছে…")
              : started
                ? pick("Continue the demo", "ডেমো চালিয়ে যান")
                : pick("Start the demo", "ডেমো শুরু করুন")}{" "}
            <span aria-hidden="true">→</span>
          </button>
          <Link to="/check" className="btn btn-glass btn-big">
            {pick("Or check a plot without logging in", "অথবা লগইন ছাড়াই জমি যাচাই করুন")}
          </Link>
        </div>
        {cfg.data && !enabled && (
          <p className="jg-warn" role="note">
            {pick(
              "One-click access is switched off on this server. Use the officer login instead.",
              "এই সার্ভারে এক-ক্লিক প্রবেশ বন্ধ আছে। অফিসার লগইন ব্যবহার করুন।",
            )}
          </p>
        )}
        {error && <ErrorNote message={error} />}
        <ul className="trust">
          <li>{pick("Synthetic data only", "শুধু কৃত্রিম ডেটা")}</li>
          <li>{pick("Bangla and English", "বাংলা ও ইংরেজি")}</li>
          <li>{pick("Can be restarted any time", "যেকোনো সময় আবার শুরু করা যায়")}</li>
        </ul>
      </header>

      <Section
        kicker={pick("Guided tour", "গাইডেড ট্যুর")}
        title={pick("What to try, in order", "যা যা দেখবেন, ক্রমানুসারে")}
      >
        <ol className="jg-steps">
          {STEPS.map((s, i) => (
            <li key={s.to} className={`jg-step t-${s.tone}`}>
              <span className="jg-n">{num(i + 1)}</span>
              <div className="jg-body">
                <div className="row">
                  <h3>{pick(...s.title)}</h3>
                  <span className={`jg-tone t-${s.tone}`}>{pick(...TONE_LABEL[s.tone])}</span>
                </div>
                <p>{pick(...s.doIt)}</p>
                <p className="jg-expect">
                  <strong>{pick("You should see: ", "যা দেখবেন: ")}</strong>
                  {pick(...s.expect)}
                </p>
              </div>
              <Link className="btn" to={s.to}>
                {pick("Open", "খুলুন")} <span aria-hidden="true">→</span>
              </Link>
            </li>
          ))}
        </ol>
        <div className="jg-reset">
          <button
            type="button"
            className="btn"
            disabled={!started || busy !== null}
            onClick={reset}
          >
            ↺{" "}
            {busy === "reset"
              ? pick("Restarting…", "আবার শুরু হচ্ছে…")
              : pick("Restart the demo from the beginning", "ডেমো শুরু থেকে আবার চালু করুন")}
          </button>
          <span className="muted small">
            {started
              ? pick(
                  "Undoes steps 2 to 5 and the plots you added, then reloads the sample data.",
                  "ধাপ ২ থেকে ৫ আর আপনার যোগ করা জমি মুছে নমুনা ডেটা আবার ভরে দেয়।",
                )
              : pick("Start the demo first.", "আগে ডেমো শুরু করুন।")}
          </span>
        </div>
        {note && (
          <p className="note note-ok" role="status">
            {note}
          </p>
        )}
      </Section>

      <Section
        kicker={pick("How it decides", "কীভাবে যাচাই করে")}
        title={pick("The rules behind every colour", "প্রতিটি রঙের পেছনের নিয়ম")}
      >
        <h3>{pick("When an officer registers a deed", "অফিসার দলিল নিবন্ধন করলে")}</h3>
        <div className="scroll">
          <table className="table">
            <thead>
              <tr>
                <th>{pick("Result", "ফল")}</th>
                <th>{pick("When", "কখন")}</th>
                <th>{pick("Rule", "নিয়ম")}</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>🟢 {pick("Green", "সবুজ")}</td>
                <td>
                  {pick(
                    "The seller holds the land and the area fits. Ownership moves to the buyer (partial sales split the plot).",
                    "বিক্রেতা জমির মালিক এবং পরিমাণ মিলেছে। মালিকানা ক্রেতার নামে যায় (আংশিক বিক্রিতে শতক ভাগ হয়)।",
                  )}
                </td>
                <td>-</td>
              </tr>
              <tr>
                <td>🔴 {pick("Red", "লাল")}</td>
                <td>{pick("The plot was already sold.", "দাগ আগেই বিক্রি হয়েছে।")}</td>
                <td>R1</td>
              </tr>
              <tr>
                <td>🔴 {pick("Red", "লাল")}</td>
                <td>
                  {pick(
                    "The seller is not the record owner, or sells more shatak than the record holds.",
                    "বিক্রেতা রেকর্ডের মালিক নন, বা রেকর্ডের চেয়ে বেশি শতক বিক্রি করছেন।",
                  )}
                </td>
                <td>R2</td>
              </tr>
              <tr>
                <td>🔴 {pick("Red", "লাল")}</td>
                <td>
                  {pick("The mouza and dag are not in the registry.", "মৌজা-দাগ রেজিস্ট্রিতে নেই।")}
                </td>
                <td>R0</td>
              </tr>
              <tr>
                <td>🟡 {pick("Yellow", "হলুদ")}</td>
                <td>
                  {pick(
                    "Another sale within 30 days of the last one, or a deed dated before it. Registered but flagged. Only a hint.",
                    "আগের হস্তান্তরের ৩০ দিনের মধ্যে আবার বিক্রি, বা দলিলের তারিখ আগের হস্তান্তরের আগের। নিবন্ধিত হয়, তবে চিহ্নিত থাকে। শুধু ইঙ্গিত।",
                  )}
                </td>
                <td>R5</td>
              </tr>
            </tbody>
          </table>
        </div>
        <h3>
          {pick("When anyone checks a plot (no login)", "যে কেউ জমি যাচাই করলে (লগইন ছাড়া)")}
        </h3>
        <div className="scroll">
          <table className="table">
            <thead>
              <tr>
                <th>{pick("Answer", "উত্তর")}</th>
                <th>{pick("When", "কখন")}</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>🟢</td>
                <td>
                  {pick(
                    "The name is a registered owner and the mutation (namjari) is done.",
                    "নাম রেজিস্টার্ড মালিকের সঙ্গে মেলে এবং নামজারি সম্পন্ন।",
                  )}
                </td>
              </tr>
              <tr>
                <td>🟡</td>
                <td>
                  {pick(
                    "The name is a registered owner, but the khatian still names someone else (mutation pending). Or the plot is not found.",
                    "নাম মেলে কিন্তু খতিয়ানে অন্য নাম (নামজারি বাকি)। অথবা দাগ রেকর্ডে নেই।",
                  )}
                </td>
              </tr>
              <tr>
                <td>🔴</td>
                <td>
                  {pick(
                    "The name is not an owner. It shows the current owner, and the sale date if this person sold earlier.",
                    "নাম মালিক নন। বর্তমান মালিক দেখায়, আর আগে বিক্রি করে থাকলে বিক্রির তারিখও।",
                  )}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="muted">
          {pick(
            "The public page shows only the owner, the status, the mutation status and earlier owners. Never alerts, scores, officer names or the audit log.",
            "পাবলিক পেজ শুধু মালিক, অবস্থা, নামজারির অবস্থা আর আগের মালিক দেখায়। অ্যালার্ট, স্কোর, অফিসারের নাম বা অডিট লগ কখনো নয়।",
          )}
        </p>
      </Section>

      <Section
        kicker={pick("Sample data", "নমুনা ডেটা")}
        title={pick(
          "Plots you can type in, once the demo has started",
          "ডেমো চালু হলে যে জমিগুলো দিয়ে যাচাই করতে পারবেন",
        )}
      >
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
              {PLOTS.map(([m, d, o, a]) => (
                <tr key={m + d}>
                  <td>{m}</td>
                  <td>{num(d)}</td>
                  <td>{o}</td>
                  <td className="num">{num(a)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="muted">
          {pick(
            "All names are made up. Names match by spelling, ignoring capital letters and extra spaces. “Rahim Uddin” and “রহিম উদ্দিন” are different names to the program.",
            "সব নাম কাল্পনিক। নাম বানান ধরে মেলে (বড়-ছোট হাতের অক্ষর আর বাড়তি স্পেস গণ্য নয়)। “Rahim Uddin” আর “রহিম উদ্দিন” প্রোগ্রামের কাছে আলাদা নাম।",
          )}
        </p>
      </Section>

      <Section
        kicker={pick("Honest limits", "সীমাবদ্ধতা")}
        title={pick("What this demo does not do", "এই ডেমোতে যা নেই")}
      >
        <ul className="jg-list">
          <li>
            {pick(
              "No real land records, NID, SMS or OTP, maps or scanned-deed reading. These are listed as future plans.",
              "আসল জমির রেকর্ড, NID, SMS/OTP, ম্যাপ বা স্ক্যান করা দলিল পড়া নেই। এগুলো ভবিষ্যৎ পরিকল্পনা।",
            )}
          </li>
          <li>
            {pick(
              "The system never says “fraud confirmed”. It says “potential conflict” and asks for human review.",
              "সিস্টেম কখনো “জালিয়াতি নিশ্চিত” বলে না। বলে “সম্ভাব্য গরমিল” আর মানুষের যাচাই চায়।",
            )}
          </li>
          <li>
            {pick(
              "The rules are fixed functions, not an AI model, so the same input always gives the same answer.",
              "নিয়মগুলো নির্দিষ্ট ফাংশন, কোনো AI মডেল নয়। তাই একই ইনপুটে সবসময় একই উত্তর।",
            )}
          </li>
        </ul>
        <p className="muted small">
          {lang === "bn"
            ? "হ্যাকাথন প্রোটোটাইপ, সরকারি সিস্টেম নয়। সব ডাটা নকল।"
            : "Hackathon prototype, not a government system. All data is synthetic."}
        </p>
      </Section>
    </div>
  );
}

import { Link } from "react-router-dom";
import { api, publicApi } from "../api";
import BangladeshMap from "../components/BangladeshMap";
import { useApi } from "../hooks";
import { useI18n } from "../i18n";

const RULES = [
  {
    id: "R1",
    icon: "⧉",
    en: [
      "Overlapping transfer claim",
      "The same share of a plot is claimed by more than one transfer, the classic double-sale pattern.",
    ],
    bn: [
      "একই অংশের একাধিক হস্তান্তর",
      "একই জমির একই অংশ একাধিক হস্তান্তরে দাবি করা হয়েছে, যা দ্বৈত বিক্রয়ের চেনা ছক।",
    ],
  },
  {
    id: "R2",
    icon: "⚖",
    en: [
      "Transfer exceeds entitlement",
      "A seller transfers more land than the records say they hold.",
    ],
    bn: [
      "প্রাপ্যতার চেয়ে বেশি হস্তান্তর",
      "বিক্রেতা তার রেকর্ডে থাকা জমির চেয়ে বেশি জমি হস্তান্তর করেছেন।",
    ],
  },
  {
    id: "R3",
    icon: "⇄",
    en: [
      "Deed and mutation gap",
      "A registered deed with no matching mutation (namjari) entry, or the other way round.",
    ],
    bn: [
      "দলিল ও নামজারির ফাঁক",
      "নিবন্ধিত দলিলের সঙ্গে মিল থাকা নামজারি নেই, অথবা নামজারির সঙ্গে দলিল নেই।",
    ],
  },
  {
    id: "R4",
    icon: "⌗",
    en: [
      "Lineage and area anomaly",
      "Child plots that do not add up to their parent, or an ambiguous split history.",
    ],
    bn: [
      "দাগ বিভাজন ও আয়তনের অসংগতি",
      "ভাঙা দাগগুলোর যোগফল মূল দাগের সঙ্গে মেলে না, অথবা বিভাজনের ইতিহাস অস্পষ্ট।",
    ],
  },
  {
    id: "R5",
    icon: "⚡",
    en: [
      "Rapid-transfer heuristic",
      "Many transfers in a short window. Always labelled a heuristic, never a finding.",
    ],
    bn: [
      "দ্রুত হস্তান্তরের ইঙ্গিত",
      "অল্প সময়ে অনেক হস্তান্তর। এটি সবসময় ‘ইঙ্গিত’ হিসেবে চিহ্নিত, সিদ্ধান্ত নয়।",
    ],
  },
];

const STEPS = [
  {
    n: "01",
    en: [
      "Link the records",
      "Parcel lineage, entitlements, deeds, transfers and mutation entries are tied into one history per plot.",
    ],
    bn: [
      "রেকর্ড জোড়া লাগান",
      "প্রতিটি দাগের বিভাজন, প্রাপ্যতা, দলিল, হস্তান্তর ও নামজারি এক জায়গায় একটি ইতিহাসে বাঁধা হয়।",
    ],
  },
  {
    n: "02",
    en: [
      "Run deterministic rules",
      "Five transparent rules check the history. No black box, so the same input always gives the same result.",
    ],
    bn: [
      "স্বচ্ছ নিয়ম চালান",
      "পাঁচটি খোলা নিয়ম ইতিহাস যাচাই করে। কোনো ব্ল্যাক বক্স নেই, একই ইনপুটে সবসময় একই ফলাফল।",
    ],
  },
  {
    n: "03",
    en: [
      "Show the evidence",
      "Every alert names its rule, the record IDs and the arithmetic, so a human reviewer can check it in minutes.",
    ],
    bn: [
      "প্রমাণ দেখান",
      "প্রতিটি সতর্কতায় নিয়ম, রেকর্ড আইডি ও হিসাব থাকে, যাতে একজন পর্যালোচক মিনিটেই যাচাই করতে পারেন।",
    ],
  },
];

const FEATURES = [
  {
    icon: "🛡",
    to: "/officer",
    en: [
      "Officer portal",
      "Register a deed and see at once whether it is clear, flagged or blocked, with the reason written out.",
    ],
    bn: [
      "অফিসার পোর্টাল",
      "দলিল নিবন্ধন করুন এবং সঙ্গে সঙ্গে দেখুন সেটি সফল, সতর্কতা না ব্লক, কারণসহ।",
    ],
  },
  {
    icon: "🧪",
    to: "/dashboard",
    en: [
      "Audit scenarios",
      "Run the five rules on ten seeded cases and open every alert to see its evidence.",
    ],
    bn: [
      "অডিট দৃশ্যকল্প",
      "দশটি প্রস্তুত ঘটনায় পাঁচটি নিয়ম চালান, প্রতিটি সতর্কতার প্রমাণ খুলে দেখুন।",
    ],
  },
  {
    icon: "🔏",
    to: "/verify",
    en: [
      "Verify a deed copy",
      "Each synthetic deed is hashed and signed. Scan the QR code and the page names exactly which field was changed.",
    ],
    bn: [
      "দলিলের কপি যাচাই",
      "প্রতিটি কৃত্রিম দলিল হ্যাশ ও স্বাক্ষরিত। QR স্ক্যান করলে ঠিক কোন তথ্য বদলেছে তা বলে দেয়।",
    ],
  },
  {
    icon: "🏷",
    to: "/check",
    en: [
      "Check land (public)",
      "Anyone can check whose name a plot is recorded under before buying. No login needed.",
    ],
    bn: [
      "জমি যাচাই (সবার জন্য)",
      "জমি কেনার আগে যে কেউ দেখতে পারেন দাগটি রেকর্ডে কার নামে আছে। লগইন লাগে না।",
    ],
  },
  {
    icon: "🔎",
    to: "/search",
    en: [
      "Search any parcel",
      "Find a plot by its number and read its timeline, balance sheet and alerts.",
    ],
    bn: ["যেকোনো দাগ খুঁজুন", "দাগ নম্বর দিয়ে খুঁজে তার সময়রেখা, জমির হিসাব ও সতর্কতা দেখুন।"],
  },
  {
    icon: "📊",
    to: "/evaluation",
    en: [
      "Honest evaluation",
      "We run labelled fixtures and report the real TP, FP and FN counts, nothing rounded up.",
    ],
    bn: [
      "সৎ মূল্যায়ন",
      "লেবেলযুক্ত পরীক্ষার ডেটায় চালিয়ে আসল TP, FP ও FN সংখ্যা দেখাই, কিছুই বাড়িয়ে নয়।",
    ],
  },
];

export default function Home() {
  const { pick, t, lang } = useI18n();
  const num = (n: number | string) =>
    lang === "bn" ? String(n).replace(/\d/g, (d) => "০১২৩৪৫৬৭৮৯"[Number(d)]) : String(n);
  const scenarios = useApi(() => api.scenarios(), []);
  const alerts = useApi(() => api.alerts(), []);
  const cfg = useApi(() => publicApi.config(), []);

  const stats = [
    { v: "5", en: "Transparent rules", bn: "স্বচ্ছ নিয়ম" },
    { v: "8", en: "Divisions in scope", bn: "বিভাগ" },
    {
      v: scenarios.data ? String(scenarios.data.scenarios.length) : "…",
      en: "Seeded scenarios",
      bn: "প্রস্তুত দৃশ্যকল্প",
    },
    {
      v: alerts.data ? String(alerts.data.alerts.length) : "…",
      en: "Alerts raised so far",
      bn: "এ পর্যন্ত সতর্কতা",
    },
  ];

  return (
    <div className="home">
      <section className="landing-hero">
        <div className="landing-copy">
          <span className="eyebrow">
            <i aria-hidden="true" />
            {pick("Digital Land Records · LandTech 2026", "ডিজিটাল ভূমি রেকর্ড · ল্যান্ডটেক ২০২৬")}
          </span>
          <h1>{t("heroTitle")}</h1>
          <p className="landing-lead">{t("heroBody")}</p>
          <div className="hero-actions">
            {cfg.data?.judge_login ? (
              <Link to="/judge" className="btn btn-gold">
                <span aria-hidden="true">★</span>{" "}
                {pick("Judges: one-click demo", "জুরির জন্য: এক ক্লিকে ডেমো")}
              </Link>
            ) : (
              <Link to="/officer" className="btn btn-gold">
                {pick("Open officer portal", "অফিসার পোর্টাল খুলুন")}{" "}
                <span aria-hidden="true">→</span>
              </Link>
            )}
            <Link to="/check" className="btn btn-glass">
              <span aria-hidden="true">🔎</span> {pick("Check land", "জমি যাচাই করুন")}
            </Link>
          </div>
          <ul className="trust">
            <li>{pick("Synthetic data only", "শুধু কৃত্রিম ডেটা")}</li>
            <li>{pick("Evidence for every alert", "প্রতিটি সতর্কতার প্রমাণ")}</li>
            <li>{pick("English & বাংলা", "বাংলা ও English")}</li>
          </ul>
        </div>
        <div className="landing-map">
          <BangladeshMap />
        </div>
      </section>

      <section className="stat-strip" aria-label={pick("At a glance", "এক নজরে")}>
        {stats.map((s) => (
          <div key={s.en}>
            <b>{num(s.v)}</b>
            <span>{pick(s.en, s.bn)}</span>
          </div>
        ))}
      </section>

      <section className="block">
        <header className="block-head">
          <span className="kicker">{pick("How it works", "কীভাবে কাজ করে")}</span>
          <h2 className="plain">
            {pick(
              "From scattered records to a checkable story",
              "ছড়ানো রেকর্ড থেকে যাচাইযোগ্য গল্পে",
            )}
          </h2>
        </header>
        <ol className="steps">
          {STEPS.map((s) => {
            const [title, body] = lang === "en" ? s.en : s.bn;
            return (
              <li key={s.n}>
                <span className="step-n">{num(s.n)}</span>
                <h3>{title}</h3>
                <p>{body}</p>
              </li>
            );
          })}
        </ol>
      </section>

      <section className="block">
        <header className="block-head">
          <span className="kicker">{pick("What it looks for", "কী খুঁজে দেখে")}</span>
          <h2 className="plain">
            {pick(
              "Five rules for double-selling and gaps",
              "দ্বৈত বিক্রয় ও ফাঁক ধরার পাঁচটি নিয়ম",
            )}
          </h2>
        </header>
        <div className="rule-grid">
          {RULES.map((r) => {
            const [title, body] = lang === "en" ? r.en : r.bn;
            return (
              <article className="rule-card" key={r.id}>
                <div className="rule-top">
                  <span className="rule-icon" aria-hidden="true">
                    {r.icon}
                  </span>
                  <span className="rule-id">{r.id}</span>
                </div>
                <h3>{title}</h3>
                <p>{body}</p>
              </article>
            );
          })}
        </div>
      </section>

      <section className="block">
        <header className="block-head">
          <span className="kicker">{pick("Explore", "ঘুরে দেখুন")}</span>
          <h2 className="plain">
            {pick(
              "Everything a reviewer needs in one place",
              "একজন পর্যালোচকের যা লাগে, এক জায়গায়",
            )}
          </h2>
        </header>
        <div className="feature-grid">
          {FEATURES.map((f) => {
            const [title, body] = lang === "en" ? f.en : f.bn;
            return (
              <Link to={f.to} className="feature" key={f.to}>
                <span className="feature-icon" aria-hidden="true">
                  {f.icon}
                </span>
                <div>
                  <h3>{title}</h3>
                  <p>{body}</p>
                </div>
                <span className="feature-go" aria-hidden="true">
                  →
                </span>
              </Link>
            );
          })}
        </div>
      </section>

      <section className="cta-band">
        <div>
          <h2 className="plain">
            {pick(
              "See a double sale stopped in seconds",
              "কয়েক সেকেন্ডেই একটি ডাবল সেল আটকে যেতে দেখুন",
            )}
          </h2>
          <p>
            {pick(
              "Sign in as the demo sub-registrar, register a deed twice, and watch the second attempt get blocked with its reason.",
              "ডেমো সাব-রেজিস্ট্রার হিসেবে ঢুকুন, একই দাগ দুবার নিবন্ধন করুন, আর দ্বিতীয়বার কারণসহ ব্লক হতে দেখুন।",
            )}
          </p>
        </div>
        <Link to="/officer" className="btn btn-gold">
          {pick("Try the officer portal", "অফিসার পোর্টাল চালিয়ে দেখুন")}{" "}
          <span aria-hidden="true">→</span>
        </Link>
      </section>

      <p className="disclaimer">
        {pick(
          "DagShield flags potential conflicts for human review. It is not a title search, a legal opinion, or proof of ownership or fraud. Map outlines: geoBoundaries (CC0).",
          "দাগশিল্ড সম্ভাব্য গরমিল চিহ্নিত করে মানুষের পর্যালোচনার জন্য। এটি টাইটেল সার্চ, আইনি মতামত, বা মালিকানা অথবা জালিয়াতির প্রমাণ নয়। মানচিত্রের সীমানা: geoBoundaries (CC0)।",
        )}
      </p>
    </div>
  );
}

import { FormEvent, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { RegistrationInput, officerApi } from "../api";
import { ErrorNote } from "../components/ui";
import { useApi } from "../hooks";
import { PageHead, useFmt } from "./common";

const BN = "০১২৩৪৫৬৭৮৯";
const toAscii = (s: string) => s.replace(/[০-৯]/g, (d) => String(BN.indexOf(d)));
const today = () => {
  const d = new Date();
  const z = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${z(d.getMonth() + 1)}-${z(d.getDate())}`;
};

const PRESETS: { en: string; bn: string; v: Omit<RegistrationInput, "deed_date"> }[] = [
  {
    en: "1. Normal sale",
    bn: "১. সফল বিক্রি",
    v: {
      mouza: "নমুনা মৌজা-১",
      dag_no: "123",
      seller: "রহিম উদ্দিন",
      buyer: "করিম মিয়া",
      area: "10",
    },
  },
  {
    en: "2. Double sale",
    bn: "২. ডাবল সেল",
    v: {
      mouza: "নমুনা মৌজা-১",
      dag_no: "123",
      seller: "রহিম উদ্দিন",
      buyer: "আনোয়ার হোসেন",
      area: "10",
    },
  },
  {
    en: "3. Seller not the owner",
    bn: "৩. ভুয়া বিক্রেতা",
    v: {
      mouza: "নমুনা মৌজা-১",
      dag_no: "124",
      seller: "অজানা ব্যক্তি",
      buyer: "করিম মিয়া",
      area: "15",
    },
  },
  {
    en: "4. Quick resale",
    bn: "৪. দ্রুত পুনঃবিক্রয়",
    v: {
      mouza: "নমুনা মৌজা-১",
      dag_no: "123",
      seller: "করিম মিয়া",
      buyer: "নাসির আহমেদ",
      area: "10",
    },
  },
];

export default function NewRegistration() {
  const { pick } = useFmt();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const plots = useApi(() => officerApi.plots(), []);
  // The judge guide opens this page as /officer/new?demo=2 to start with a demo scenario already filled in.
  const preset = PRESETS[Number(params.get("demo")) - 1]?.v;
  const [form, setForm] = useState<RegistrationInput>({
    mouza: preset?.mouza ?? "",
    dag_no: preset?.dag_no ?? "",
    seller: preset?.seller ?? "",
    buyer: preset?.buyer ?? "",
    area: preset?.area ?? "",
    deed_date: today(),
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (k: keyof RegistrationInput) => (e: { target: { value: string } }) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  function problem(): string | null {
    const area = Number(toAscii(form.area).replace(",", ""));
    if (!Number.isFinite(area) || area <= 0)
      return pick(
        "Enter the land area as a number above zero.",
        "জমির পরিমাণ শূন্যের চেয়ে বড় সংখ্যায় লিখুন।",
      );
    if (form.seller.trim().replace(/\s+/g, " ") === form.buyer.trim().replace(/\s+/g, " "))
      return pick(
        "Seller and buyer must be different people.",
        "বিক্রেতা ও ক্রেতা আলাদা ব্যক্তি হতে হবে।",
      );
    if (form.deed_date > today())
      return pick("The deed date cannot be in the future.", "দলিলের তারিখ ভবিষ্যতের হতে পারে না।");
    return null;
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    const p = problem();
    if (p) return setError(p);
    setBusy(true);
    setError(null);
    try {
      const r = await officerApi.register({ ...form, area: toAscii(form.area) });
      navigate(`/officer/result/${r.id}`);
    } catch (err) {
      setError((err as Error).message);
      setBusy(false);
    }
  }

  return (
    <section>
      <PageHead
        title={pick("New deed registration", "নতুন দলিল রেজিস্ট্রেশন")}
        lead={pick(
          "Fill in the deed details. The check runs when you submit, before anything is registered.",
          "দলিলের তথ্য দিন। জমা দিলে নিবন্ধনের আগেই যাচাই চলবে।",
        )}
      />

      <div className="presets" role="group" aria-label={pick("Demo scenarios", "ডেমো দৃশ্য")}>
        <span className="muted">{pick("Demo scenarios:", "ডেমো দৃশ্য:")}</span>
        {PRESETS.map((p) => (
          <button
            type="button"
            key={p.en}
            className="chip-btn"
            onClick={() => {
              setForm((f) => ({ ...f, ...p.v, deed_date: today() }));
              setError(null);
            }}
          >
            {pick(p.en, p.bn)}
          </button>
        ))}
      </div>

      <form className="reg-form" onSubmit={submit}>
        <div className="form-grid">
          <label>
            {pick("Mouza", "মৌজা")}
            <input
              value={form.mouza}
              onChange={set("mouza")}
              list="mouza-list"
              required
              maxLength={120}
            />
            <datalist id="mouza-list">
              {plots.data?.mouzas.map((m) => <option key={m} value={m} />)}
            </datalist>
          </label>
          <label>
            {pick("Dag (plot) number", "দাগ নম্বর")}
            <input
              value={form.dag_no}
              onChange={set("dag_no")}
              inputMode="numeric"
              required
              maxLength={32}
            />
          </label>
          <label>
            {pick("Seller", "বিক্রেতা")}
            <input
              value={form.seller}
              onChange={set("seller")}
              required
              minLength={2}
              maxLength={120}
            />
          </label>
          <label>
            {pick("Buyer", "ক্রেতা")}
            <input
              value={form.buyer}
              onChange={set("buyer")}
              required
              minLength={2}
              maxLength={120}
            />
          </label>
          <label>
            {pick("Land area (shatak)", "জমির পরিমাণ (শতক)")}
            <input
              value={form.area}
              onChange={set("area")}
              inputMode="decimal"
              required
              maxLength={32}
            />
          </label>
          <label>
            {pick("Deed date", "দলিলের তারিখ")}
            <input
              type="date"
              value={form.deed_date}
              max={today()}
              onChange={set("deed_date")}
              required
            />
          </label>
        </div>
        {error && <ErrorNote message={error} />}
        <div className="row">
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy
              ? pick("Checking…", "যাচাই হচ্ছে…")
              : pick("Check and register", "যাচাই করে নিবন্ধন করুন")}
          </button>
          <span className="muted small">
            {pick(
              "Names are made up. Do not enter real people's details.",
              "নামগুলো কাল্পনিক। আসল কারও তথ্য দেবেন না।",
            )}
          </span>
        </div>
      </form>
    </section>
  );
}

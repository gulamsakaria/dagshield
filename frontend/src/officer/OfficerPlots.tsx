import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, officerApi } from "../api";
import { Empty, ErrorNote, Loading } from "../components/ui";
import { useApi } from "../hooks";
import { PageHead, useFmt } from "./common";

const BN = "০১২৩৪৫৬৭৮৯";
const toAscii = (s: string) => s.replace(/[০-৯]/g, (d) => String(BN.indexOf(d)));

/** All plots in the registry, plus a form to add a new one. Names may be typed in Bangla or English. */
export default function OfficerPlots() {
  const { pick, num, area } = useFmt();
  const plots = useApi(() => officerApi.plots(), []);
  const [form, setForm] = useState({ mouza: "", dag_no: "", owner: "", area: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [added, setAdded] = useState<string | null>(null);
  const [filter, setFilter] = useState("");

  const set = (k: keyof typeof form) => (e: { target: { value: string } }) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setAdded(null);
    const a = Number(toAscii(form.area).replace(",", ""));
    if (!Number.isFinite(a) || a <= 0) {
      return setError(
        pick(
          "Enter the land area as a number above zero.",
          "জমির পরিমাণ শূন্যের চেয়ে বড় সংখ্যায় লিখুন।",
        ),
      );
    }
    setBusy(true);
    try {
      const r = await officerApi.addPlot({ ...form, area: toAscii(form.area) });
      setAdded(`${r.mouza} · ${pick("Dag", "দাগ")} ${num(r.dag_no)}`);
      setForm({ mouza: form.mouza, dag_no: "", owner: "", area: "" }); // keep the mouza: several plots often share it
      plots.reload();
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 409
          ? pick("This plot is already in the registry.", "এই দাগ আগেই রেজিস্ট্রিতে আছে।")
          : (err as Error).message,
      );
    } finally {
      setBusy(false);
    }
  }

  const q = filter.trim().toLowerCase();
  const rows = (plots.data?.plots ?? []).filter(
    (p) => !q || `${p.mouza} ${p.dag_no} ${p.owners.join(" ")}`.toLowerCase().includes(q),
  );

  return (
    <section>
      <PageHead
        title={pick("Plots in the registry", "রেজিস্ট্রিতে থাকা জমি")}
        lead={pick(
          "See every plot on record, or add one that is missing. Bangla and English both work.",
          "রেকর্ডে থাকা সব জমি দেখুন, বা যেটা নেই সেটা যোগ করুন। বাংলা ও ইংরেজি দুটোই চলবে।",
        )}
      />

      <form className="reg-form" onSubmit={submit}>
        <h2 className="plain">{pick("Add a plot", "নতুন জমি যোগ করুন")}</h2>
        <div className="form-grid">
          <label>
            {pick("Mouza", "মৌজা")}
            <input
              value={form.mouza}
              onChange={set("mouza")}
              list="plot-mouza-list"
              placeholder={pick("e.g. Sample Mouza 3", "যেমন: নমুনা মৌজা-৩ বা Sample Mouza 3")}
              required
              maxLength={120}
            />
            <datalist id="plot-mouza-list">
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
            {pick("Current owner", "বর্তমান মালিক")}
            <input
              value={form.owner}
              onChange={set("owner")}
              placeholder={pick("e.g. Abdul Karim", "যেমন: আব্দুল করিম বা Abdul Karim")}
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
        </div>
        {error && <ErrorNote message={error} />}
        {added && (
          <p className="note note-ok" role="status">
            {pick("Plot added: ", "জমি যোগ হয়েছে: ")}
            {added}
          </p>
        )}
        <div className="row">
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? pick("Adding…", "যোগ হচ্ছে…") : pick("Add plot", "জমি যোগ করুন")}
          </button>
          <span className="muted small">
            {pick(
              "The same plot in the same mouza cannot be added twice. Use made-up names only.",
              "একই মৌজার একই দাগ দুবার যোগ করা যায় না। শুধু কাল্পনিক নাম দিন।",
            )}
          </span>
        </div>
      </form>

      <h2>
        {pick("All plots", "সব জমি")} {plots.data ? `(${num(plots.data.plots.length)})` : ""}
      </h2>
      <input
        className="plot-filter"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder={pick("Search mouza, dag or owner", "মৌজা, দাগ বা মালিক খুঁজুন")}
        aria-label={pick("Search plots", "জমি খুঁজুন")}
      />
      {plots.loading && <Loading />}
      {plots.error && <ErrorNote message={plots.error} onRetry={plots.reload} />}
      {plots.data && rows.length === 0 && (
        <Empty title={pick("No plots found", "কোনো জমি পাওয়া যায়নি")} />
      )}
      {rows.length > 0 && (
        <div className="scroll">
          <table className="table">
            <thead>
              <tr>
                <th>{pick("Mouza", "মৌজা")}</th>
                <th>{pick("Dag", "দাগ")}</th>
                <th>{pick("Current owner", "বর্তমান মালিক")}</th>
                <th className="num">{pick("Shatak", "শতক")}</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.map((p) => (
                <tr key={p.id}>
                  <td>{p.mouza}</td>
                  <td>{num(p.dag_no)}</td>
                  <td>{p.owners.join(", ")}</td>
                  <td className="num">{area(p.total_area)}</td>
                  <td>
                    <Link
                      to={`/officer/history?mouza=${encodeURIComponent(p.mouza)}&dag=${encodeURIComponent(p.dag_no)}`}
                    >
                      {pick("History", "ইতিহাস")}
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

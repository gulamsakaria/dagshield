import { FormEvent, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ParcelBrief, api } from "../api";
import { Empty, ErrorNote, fmt } from "../components/ui";
import { useI18n } from "../i18n";

export default function SearchPage() {
  const { t } = useI18n();
  const [params, setParams] = useSearchParams();
  const [text, setText] = useState(params.get("q") ?? "");
  const [results, setResults] = useState<ParcelBrief[] | null>(null);
  const [asked, setAsked] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function run(q: string) {
    setBusy(true);
    setError(null);
    try {
      const r = await api.search(q);
      setResults(r.results);
      setAsked(r.query);
    } catch (e) {
      setResults(null);
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  function submit(e: FormEvent) {
    e.preventDefault();
    const q = text.trim();
    if (!q) return;
    setParams({ q });
    void run(q);
  }

  return (
    <section>
      <h1>{t("searchTitle")}</h1>
      <p>{t("searchHelp")}</p>
      <form onSubmit={submit} className="inline-form">
        <label htmlFor="q">{t("searchLabel")}</label>
        <input id="q" value={text} maxLength={64} onChange={(e) => setText(e.target.value)} />
        <button className="btn btn-primary" disabled={busy}>
          {t("searchButton")}
        </button>
      </form>
      {error && <ErrorNote message={error} />}
      {results && results.length === 0 && (
        <Empty title={t("searchEmptyTitle", { q: asked })}>{t("searchEmptyBody")}</Empty>
      )}
      {results && results.length > 0 && (
        <>
          <p className="muted">{t("parcelResults", { n: results.length })}</p>
          <ul className="plain-list">
            {results.map((p) => (
              <li key={p.id}>
                <Link to={`/parcels/${p.id}`}>
                  <strong>{p.id}</strong>
                </Link>
                <span className="muted">
                  {" "}
                  {t("dag")} {p.dag_no ?? "-"}, {p.survey_type}, {fmt(p.area_decimal)}
                </span>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

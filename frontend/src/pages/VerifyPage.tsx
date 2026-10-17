import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { VerifyResult, api } from "../api";
import { ErrorNote, Loading } from "../components/ui";
import { useApi } from "../hooks";
import { useI18n } from "../i18n";

const FIELD_ORDER = [
  "deed_ref",
  "registration_date",
  "registration_status",
  "seller",
  "buyer",
  "parcel_id",
  "area_decimal",
  "source_id",
];

export default function VerifyPage() {
  const { t, pick } = useI18n();
  const [params] = useSearchParams();
  const deeds = useApi(() => api.deeds(), []);
  const [ref, setRef] = useState(params.get("ref") ?? "");
  const [fields, setFields] = useState<Record<string, string | null> | null>(null);
  const [qr, setQr] = useState<{ hash: string; signature: string; png: string } | null>(null);
  const [result, setResult] = useState<VerifyResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [chain, setChain] = useState<string | null>(null);

  useEffect(() => {
    if (!ref && deeds.data?.deeds[0]) setRef(deeds.data.deeds[0].deed_ref);
  }, [deeds.data, ref]);

  useEffect(() => {
    if (!ref) return;
    let live = true;
    setResult(null);
    setError(null);
    Promise.all([api.deed(ref), api.qr(ref)])
      .then(([d, q]) => {
        if (!live) return;
        setFields(d.fields);
        // A scanned QR link (?ref=&h=&s=) carries its own hash and signature; otherwise use the signed deed's.
        const h = params.get("h");
        const s = params.get("s");
        setQr({ hash: h ?? q.hash, signature: s ?? q.signature, png: q.png_base64 });
      })
      .catch((e: Error) => live && setError(e.message));
    return () => {
      live = false;
    };
  }, [ref, params]);

  async function check() {
    if (!fields || !qr) return;
    setError(null);
    try {
      setResult(
        await api.verify({ deed_ref: ref, fields, hash: qr.hash, signature: qr.signature }),
      );
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function checkChain() {
    try {
      const r = await api.auditChain();
      setChain(
        r.ok
          ? t("chainOk", { n: r.entries_checked }) + ` ${t("headHash")}: ${r.head_hash}`
          : t("chainBroken", { n: (r.broken_at ?? 0) + 1, reason: r.reason ?? "" }),
      );
    } catch (e) {
      setChain((e as Error).message);
    }
  }

  const heading =
    result?.result === "match"
      ? t("resultMatch")
      : result?.result === "mismatch"
        ? t("resultMismatch")
        : t("resultNotFound");

  return (
    <section>
      <h1>{t("verifyTitle")}</h1>
      <p>{t("verifyHelp")}</p>
      {deeds.loading && <Loading />}
      {deeds.error && <ErrorNote message={deeds.error} onRetry={deeds.reload} />}
      {error && <ErrorNote message={error} />}

      <div className="verify-grid">
        <div>
          <label htmlFor="deed">{t("deedRef")}</label>
          <select id="deed" value={ref} onChange={(e) => setRef(e.target.value)}>
            {deeds.data?.deeds.map((d) => (
              <option key={d.deed_ref} value={d.deed_ref}>
                {d.deed_ref} ({d.parcel_id})
              </option>
            ))}
          </select>

          <h2>{t("fieldsOnCopy")}</h2>
          {fields &&
            FIELD_ORDER.map((k) => (
              <div className="field" key={k}>
                <label htmlFor={`f-${k}`}>{k}</label>
                <input
                  id={`f-${k}`}
                  value={fields[k] ?? ""}
                  maxLength={64}
                  className={result?.mismatched_fields.includes(k) ? "changed" : undefined}
                  onChange={(e) => setFields({ ...fields, [k]: e.target.value })}
                />
                {result?.mismatched_fields.includes(k) && <span className="badge sev-high">≠</span>}
              </div>
            ))}
          <button type="button" className="btn btn-primary" onClick={check} disabled={!fields}>
            {t("verifyButton")}
          </button>
        </div>

        <div>
          <h2>{t("qrCode")}</h2>
          {qr && (
            <img
              className="qr"
              alt={`QR code for ${ref}`}
              src={`data:image/png;base64,${qr.png}`}
            />
          )}
        </div>
      </div>

      {result && (
        <div className={`result result-${result.result}`} role="status">
          <h2>
            <span aria-hidden="true">{result.result === "match" ? "✓" : "✕"}</span> {heading}
          </h2>
          <p>{pick(result.message_en, result.message_bn)}</p>
          <dl className="hashes">
            <dt>{t("recomputedHash")}</dt>
            <dd>{result.recomputed_hash}</dd>
            <dt>{t("signedHash")}</dt>
            <dd>{result.signed_hash ?? "-"}</dd>
            <dt>{t("signatureValid")}</dt>
            <dd>{result.signature_valid ? t("valid") : t("invalid")}</dd>
            {result.mismatched_fields.length > 0 && (
              <>
                <dt>{t("changedFields")}</dt>
                <dd>{result.mismatched_fields.join(", ")}</dd>
              </>
            )}
          </dl>
          <p className="muted">{t("verifyLimit")}</p>
        </div>
      )}

      <h2>{t("chainTitle")}</h2>
      <button type="button" className="btn" onClick={checkChain}>
        {t("chainButton")}
      </button>
      {chain && (
        <p role="status" className="note">
          {chain}
        </p>
      )}
    </section>
  );
}

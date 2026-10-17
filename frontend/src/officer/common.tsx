import { ReactNode } from "react";
import type { RegAttempt, Verdict } from "../api";
import { useI18n } from "../i18n";

const BN_DIGITS = "০১২৩৪৫৬৭৮৯";

/** Number and text formatting that follows the language toggle (Bangla digits in Bangla mode). */
export function useFmt() {
  const { lang, pick } = useI18n();
  const num = (n: number | string) =>
    lang === "bn" ? String(n).replace(/\d/g, (d) => BN_DIGITS[Number(d)]) : String(n);
  const area = (n: number) => num(Number.isInteger(n) ? n : Number(n.toFixed(4)));
  const date = (iso: string) => num(iso.slice(0, 10));
  const time = (iso: string) => {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return num(iso.slice(0, 16).replace("T", " "));
    const z = (n: number) => String(n).padStart(2, "0");
    return num(
      `${d.getFullYear()}-${z(d.getMonth() + 1)}-${z(d.getDate())} ${z(d.getHours())}:${z(d.getMinutes())}`,
    );
  };
  return { lang, pick, num, area, date, time };
}

export const VERDICT_META: Record<Verdict, { icon: string; dot: string }> = {
  success: { icon: "✓", dot: "🟢" },
  warning: { icon: "▲", dot: "🟡" },
  blocked: { icon: "✕", dot: "🔴" },
};

export function verdictLabel(v: Verdict, pick: (en: string, bn: string) => string): string {
  return v === "success"
    ? pick("Successful", "সফল")
    : v === "warning"
      ? pick("Warning", "সতর্কতা")
      : pick("Blocked", "ব্লক");
}

export function VerdictBadge({ verdict }: { verdict: Verdict }) {
  const { pick } = useI18n();
  return (
    <span className={`verdict-badge v-${verdict}`}>
      <span aria-hidden="true">{VERDICT_META[verdict].dot}</span> {verdictLabel(verdict, pick)}
    </span>
  );
}

export function reasonOf(
  a: Pick<RegAttempt, "reason_en" | "reason_bn">,
  lang: "en" | "bn",
): string {
  return lang === "bn" ? a.reason_bn : a.reason_en;
}

export function PageHead({
  title,
  lead,
  actions,
}: {
  title: string;
  lead?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="ofc-head">
      <div>
        <h1>{title}</h1>
        {lead && <p className="muted">{lead}</p>}
      </div>
      {actions && <div className="row">{actions}</div>}
    </div>
  );
}

export function ShieldLogo({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" className="shield-logo">
      <defs>
        <linearGradient id="shg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#0fa371" />
          <stop offset="1" stopColor="#005a41" />
        </linearGradient>
      </defs>
      <path
        d="M16 2.2 27 6v8.6c0 7-4.4 12.2-11 15.2C9.4 26.800 5 21.600 5 14.600V6z"
        fill="url(#shg)"
        stroke="#ffd36b"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
      <path
        d="M10.500 12.500h5.800a3.700 3.700 0 0 1 0 7.400h-5.800z"
        fill="none"
        stroke="#fff"
        strokeWidth="2"
      />
      <circle cx="21.300" cy="10.200" r="2.100" fill="#f42a41" />
    </svg>
  );
}

import { ReactNode } from "react";
import type { Severity, Status } from "../api";
import { useI18n } from "../i18n";

// Status and severity are always written out in words and carry a shape, never colour alone.
const STATUS_ICON: Record<Status, string> = { New: "●", "Under Review": "◐", Closed: "✓" };
const SEVERITY_ICON: Record<Severity, string> = { high: "▲", medium: "◆", low: "▽", review: "?" };

export function StatusBadge({ status }: { status: Status }) {
  const { t } = useI18n();
  const key = `st_${status}` as "st_New" | "st_Under Review" | "st_Closed";
  return (
    <span className={`badge status-${status.replace(" ", "-").toLowerCase()}`}>
      <span aria-hidden="true">{STATUS_ICON[status]}</span> {t(key)}
    </span>
  );
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  const { t } = useI18n();
  const key = `sev_${severity}` as "sev_high" | "sev_medium" | "sev_low" | "sev_review";
  return (
    <span className={`badge sev-${severity}`}>
      <span aria-hidden="true">{SEVERITY_ICON[severity]}</span> {t(key)}
    </span>
  );
}

export function Loading() {
  const { t } = useI18n();
  return (
    <p className="muted" role="status">
      {t("loading")}
    </p>
  );
}

export function ErrorNote({ message, onRetry }: { message: string; onRetry?: () => void }) {
  const { t } = useI18n();
  return (
    <div className="note note-error" role="alert">
      <strong>{t("errorTitle")}</strong>
      <p>{message}</p>
      {onRetry && (
        <button type="button" className="btn" onClick={onRetry}>
          {t("retry")}
        </button>
      )}
    </div>
  );
}

export function Empty({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="note">
      <strong>{title}</strong>
      {children && <p>{children}</p>}
    </div>
  );
}

export function fmt(n: number | null | undefined): string {
  if (n === null || n === undefined) return "-";
  return Number.isInteger(n) ? String(n) : String(Number(n.toFixed(4)));
}

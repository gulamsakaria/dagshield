// Typed client for the DagShield API. All data shown here is synthetic.

export type Status = "New" | "Under Review" | "Closed";
export type Severity = "high" | "medium" | "low" | "review";

export interface Alert {
  id: string;
  scenario_id: string;
  parcel_id: string;
  rule_id: string;
  rule_version: string;
  key: string;
  severity: Severity;
  outcome: "alert" | "insufficient_data";
  status: Status;
  evidence_ids: string[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  calc: Record<string, any>;
  message_en: string;
  message_bn: string;
  next_check_en: string;
  next_check_bn: string;
  heuristic: boolean;
  created_at: string;
}

export interface Scenario {
  id: string;
  name: string;
  name_bn: string;
  description: string;
  description_bn: string;
  case_type: string;
  parcel_ids: string[];
  alert_counts: Record<string, number>;
  alert_total: number;
}

export interface ParcelBrief {
  id: string;
  label: string;
  dag_no: string | null;
  survey_type: string;
  area_decimal: number | null;
  scenario_id: string;
}

export interface LineageLink {
  id: string;
  relationship: string;
  direction: "parent" | "child";
  parent: { id: string; dag_no: string | null; area: number | null };
  child: { id: string; dag_no: string | null; area: number | null };
  confidence: number | null;
  uncertain: boolean;
  source_id: string | null;
}

export interface OwnerBalance {
  owner: string;
  opening: number | null;
  incoming: number;
  outgoing: number;
  balance: number | null;
  insufficient_reasons: string[];
}

export interface TimelineEvent {
  kind: "deed" | "transfer" | "mutation";
  id: string;
  date: string | null;
  status: string;
  summary: string;
  details: Record<string, string | number | null>;
}

export interface History {
  parcel: ParcelBrief & { status: string };
  lineage: LineageLink[];
  ownership_summary: OwnerBalance[];
  timeline: TimelineEvent[];
  alerts: Alert[];
}

export interface VerifyResult {
  result: "match" | "mismatch" | "not_found";
  recomputed_hash: string;
  signed_hash: string | null;
  qr_hash: string | null;
  signature_valid: boolean;
  qr_signature_valid: boolean | null;
  mismatched_fields: string[];
  message_en: string;
  message_bn: string;
  deed_ref: string;
}

export interface EvalCase {
  id: string;
  name: string;
  kind: "rule" | "integrity";
  expected: unknown;
  actual: unknown;
  passed: boolean;
  tp?: number;
  fp?: number;
  fn?: number;
}

export interface Evaluation {
  note: string;
  totals: { tp: number; fp: number; fn: number; cases: number; passed: number };
  per_rule: Record<string, { tp: number; fp: number; fn: number }>;
  repeatability_ok: boolean;
  cases: EvalCase[];
}

export type Verdict = "success" | "warning" | "blocked";

export interface Officer {
  username: string;
  name_en: string;
  name_bn: string;
}

export interface RegSummary {
  total: number;
  success: number;
  warning: number;
  blocked: number;
  parcels: number;
}

export interface RegPlot {
  id: number;
  mouza: string;
  dag_no: string;
  total_area: number;
  owners: string[];
}

export interface RegAttempt {
  id: number;
  created_at: string;
  officer: string;
  parcel_id: number | null;
  mouza: string;
  dag_no: string;
  seller: string;
  buyer: string;
  area: number;
  deed_date: string;
  verdict: Verdict;
  rule_id: string;
  reason_en: string;
  reason_bn: string;
  calc: Record<string, unknown>;
}

export interface RegTimelineEntry {
  kind: "initial" | "transfer" | "blocked";
  date: string;
  from: string | null;
  to: string;
  area: number;
  flagged: boolean;
  attempt_id: number | null;
  rule_id?: string;
  reason_en?: string;
  reason_bn?: string;
}

export interface RegHistory {
  parcel: { id: number; mouza: string; dag_no: string; total_area: number };
  owners: { owner: string; area: number }[];
  timeline: RegTimelineEntry[];
}

export interface RegistrationInput {
  mouza: string;
  dag_no: string;
  seller: string;
  buyer: string;
  area: string;
  deed_date: string;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

const TOKEN_KEY = "dagshield_admin_token";

export function getAdminToken(): string {
  try {
    return sessionStorage.getItem(TOKEN_KEY) ?? "";
  } catch {
    return "";
  }
}

export function setAdminToken(value: string): void {
  try {
    if (value) sessionStorage.setItem(TOKEN_KEY, value);
    else sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable: the token simply is not remembered */
  }
}

const OFFICER_KEY = "dagshield_officer_token";

export function getOfficerToken(): string {
  try {
    return sessionStorage.getItem(OFFICER_KEY) ?? "";
  } catch {
    return "";
  }
}

export function setOfficerToken(value: string): void {
  try {
    if (value) sessionStorage.setItem(OFFICER_KEY, value);
    else sessionStorage.removeItem(OFFICER_KEY);
  } catch {
    /* storage unavailable: the officer simply has to log in again after a reload */
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (init?.body) headers["Content-Type"] = "application/json";
  const token = getAdminToken();
  if (token) headers["X-Admin-Token"] = token;
  const officer = getOfficerToken();
  if (officer) headers["Authorization"] = `Bearer ${officer}`;
  let res: Response;
  try {
    res = await fetch(path, { ...init, headers });
  } catch {
    throw new ApiError(0, "Cannot reach the API. Is the backend running?");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) detail = "The request was not valid.";
      if (res.status === 401 && path.startsWith("/api/registry")) setOfficerToken("");
    } catch {
      /* keep statusText */
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

const post = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "POST", body: JSON.stringify(body) });

export interface PublicCheckResult {
  result: "not_found" | "ok" | "mutation_pending" | "not_owner";
  level: "green" | "amber" | "red";
  message_bn: string;
  message_en: string;
  registered_owners: string[];
  mutation_done: boolean | null;
  sold_on: string | null;
  previous_owners: { name: string; date: string }[];
}

/** Public, no login. Same data the officer portal writes, but only owner, status and mutation come back. */
export const publicApi = {
  config: () => request<{ judge_login: boolean }>("/api/public/config"),
  mouzas: () => request<{ mouzas: string[] }>("/api/public/mouzas"),
  check: (mouza: string, dag_no: string, owner_name: string) =>
    post<PublicCheckResult>("/api/public/check", { mouza, dag_no, owner_name }),
};

export const officerApi = {
  login: (username: string, password: string) =>
    post<{ token: string; officer: Officer }>("/api/auth/login", { username, password }),
  logout: () => post<{ ok: boolean }>("/api/auth/logout", {}),
  judgeLogin: () => post<{ token: string; officer: Officer }>("/api/auth/judge", {}),
  loadSample: () =>
    post<{ loaded: boolean; plots: number; requests: number }>("/api/registry/sample-data", {}),
  me: () => request<Officer>("/api/auth/me"),
  summary: () => request<RegSummary>("/api/registry/summary"),
  plots: () => request<{ mouzas: string[]; plots: RegPlot[] }>("/api/registry/plots"),
  addPlot: (body: { mouza: string; dag_no: string; owner: string; area: string }) =>
    post<{ id: number; mouza: string; dag_no: string; total_area: number }>(
      "/api/registry/plots",
      body,
    ),
  register: (body: RegistrationInput) => post<RegAttempt>("/api/registry/registrations", body),
  attempt: (id: string) => request<RegAttempt>(`/api/registry/attempts/${encodeURIComponent(id)}`),
  attempts: (verdicts?: Verdict[]) =>
    request<{ attempts: RegAttempt[] }>(
      "/api/registry/attempts" +
        (verdicts?.length ? "?" + verdicts.map((v) => `verdict=${v}`).join("&") : ""),
    ),
  history: (mouza: string, dag: string) =>
    request<RegHistory>(
      `/api/registry/history?mouza=${encodeURIComponent(mouza)}&dag_no=${encodeURIComponent(dag)}`,
    ),
  reset: () => post<{ reset: boolean }>("/api/registry/reset", {}),
};

export const api = {
  scenarios: () => request<{ scenarios: Scenario[] }>("/api/scenarios"),
  resetScenario: (id: string) =>
    post<{ reset: boolean }>(`/api/scenarios/${encodeURIComponent(id)}/reset`, {}),
  search: (q: string) =>
    request<{ query: string; count: number; results: ParcelBrief[] }>(
      `/api/parcels?query=${encodeURIComponent(q)}`,
    ),
  history: (id: string) => request<History>(`/api/parcels/${encodeURIComponent(id)}/history`),
  runAudit: (body: { scenario_id?: string; parcel_id?: string }) =>
    post<{ alert_count: number; duration_ms: number; alerts: Alert[] }>("/api/audits", body),
  alerts: () => request<{ alerts: Alert[] }>("/api/alerts"),
  alert: (id: string) => request<Alert>(`/api/alerts/${encodeURIComponent(id)}`),
  setStatus: (id: string, status: Status) =>
    request<Alert>(`/api/alerts/${encodeURIComponent(id)}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
  evaluation: () => request<Evaluation>("/api/evaluation"),
  deeds: () =>
    request<{ deeds: { deed_ref: string; parcel_id: string; status: string }[] }>("/api/deeds"),
  deed: (ref: string) =>
    request<{ fields: Record<string, string | null>; record_hash: string }>(
      `/api/deeds/${encodeURIComponent(ref)}`,
    ),
  qr: (ref: string) =>
    request<{ hash: string; signature: string; png_base64: string; verify_url: string }>(
      `/api/deeds/${encodeURIComponent(ref)}/qr`,
    ),
  verify: (body: {
    deed_ref: string;
    fields: Record<string, string | null>;
    hash?: string;
    signature?: string;
  }) => post<VerifyResult>("/api/verify", body),
  auditChain: () =>
    request<{
      ok: boolean;
      entries_checked: number;
      head_hash: string;
      broken_at: number | null;
      reason: string | null;
    }>("/api/audit-log/verify"),
};

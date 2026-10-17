# Security notes

DagShield is a **synthetic-data prototype**. These notes say what is protected, how, and what is out of scope.

## Controls built in

| Risk | Control |
| --- | --- |
| Real personal or land data entering the demo | Fixtures are checked by `app/privacy.py` at load time, in tests, in CI and by `scripts/check_synthetic_data.py`. Identities must be tokens such as `OWNER-A`; NID-like numbers, phone numbers and emails are rejected |
| Leaked signing key or passwords | Key and passwords come only from environment variables. `.env` is git-ignored, created with owner-only permissions by `scripts/gen_demo_key.py`, and `scripts/check_secrets.py` (pre-commit hook and CI) fails on key blocks or values in tracked files |
| Starting with a missing or weak key | The API refuses to start without `DAGSHIELD_SIGNING_KEY`, and rejects anything that is not exactly 32 bytes of base64 |
| Forged or altered deed copies | Canonical JSON, SHA-256, Ed25519 signature, constant-time hash comparison, and a forged QR hash is rejected because the attacker cannot sign it |
| Silent editing of history | Hash-chained audit log. Editing, reordering or deleting a middle or first entry breaks verification |
| Injection | SQLAlchemy parameterised queries only; strict Pydantic patterns and length limits on every input; extra fields rejected |
| Abuse | In-memory per-address rate limit (login 10 a minute, public Check Land 30 a minute, plus 10 a minute in the browser), 64 KB body limit, optional `X-Admin-Token` on reset and status changes |
| Officer portal access | One synthetic sub-registrar account. The password is checked as a scrypt hash in constant time. Session tokens are HMAC-signed, expire after 8 hours and need no server memory, so they work across several worker processes. Every `/api/registry` route needs the token |
| One-click judge access | Off unless `DAGSHIELD_JUDGE_LOGIN=true`; with it off, `/api/auth/judge` answers 404. The token is signed like an officer token, rate limited with the login limiter, and named `judge` in the audit entries |
| Public Check Land page leaking internals | `/api/public/check` returns only the registered owner, status, mutation status and earlier owners with dates. A test asserts the exact response fields and that blocked attempts, officer names and rule codes never appear. Each check logs mouza and dag only, never a name |
| Hosted copy exposing files | The app folder carries a deny-all `.htaccess`, so `.env`, the database and the source return 403. `/docs` is switched off, and the web UI is served only from its own folder (a test checks path traversal) |
| Browser attacks | API sends CSP `default-src 'none'`, `X-Frame-Options: DENY`, `nosniff`, `no-referrer`; web pages get a `self`-only CSP (from nginx, or from the API when it serves the UI itself); CORS allows only configured origins and no credentials |
| Information leaks | Unhandled errors return a generic message, never a stack trace |
| Container risks | Non-root user, read-only API filesystem, all capabilities dropped, `no-new-privileges`, ports bound to `127.0.0.1` |
| Dependencies | Versions are pinned; CI runs `pip-audit` and `npm audit` |

## Known limits (be upfront about these)

- The demo key stands in for a registrar's key. A real deployment needs key custody by the registration authority,
  hardware-protected storage and legal recognition of the signature.
- Removing entries from the **end** of the audit log cannot be detected from the log alone. Record the `head_hash`
  from `/api/audit-log/verify` somewhere outside the database to catch truncation.
- The rate limiter is per process and keyed on the connecting address. Behind the bundled nginx all visitors share one
  address. Use a proper gateway if you ever expose this publicly.
- There is a single demo officer account and no roles, password reset or lockout beyond the login rate limit. The optional admin token is a light guard for a shared demo, not authentication. The demo password is shown on the login page of local builds (hidden in the hosted build with `VITE_SHOW_DEMO_LOGIN=false`).
- The public Check Land page deliberately tells anyone who the registered owner of a plot is. That is the feature, so it is only suitable for synthetic data.
- With the judge switch on, anyone on the internet can open an officer session and change or reset the demo registry. That is the point of a judging demo, so switch it off (and change the officer password) once judging is over.
- Officer session tokens cannot be revoked before they expire; logging out only forgets them on that device.
- Do not deploy this with real land records. That would need authorisation, a data-sharing agreement, a security
  review and a legal opinion first (see the countrywide plan in the concept note).

## Rules of the hackathon

Security features are shown only on the team's own prototype. No testing against government or third-party systems,
no scraping, no automated querying of government portals.

## Reporting a problem

Open an issue in the repository or contact the team lead. Do not include real personal data in a report.

import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { ApiError, getOfficerToken, officerApi, publicApi, setOfficerToken } from "../api";
import { useApi } from "../hooks";
import { useI18n } from "../i18n";
import { ShieldLogo } from "./common";

const DEMO_USER = "subregistrar";
const DEMO_PASS = "demo-officer-2026";
// The hosted build is made with VITE_SHOW_DEMO_LOGIN=false, so the demo password is not printed on a public page.
const SHOW_DEMO = import.meta.env.VITE_SHOW_DEMO_LOGIN !== "false";

export default function OfficerLogin() {
  const { pick } = useI18n();
  const cfg = useApi(() => publicApi.config(), []);
  const navigate = useNavigate();
  const [user, setUser] = useState("");
  const [pass, setPass] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (getOfficerToken()) return <Navigate to="/officer" replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const r = await officerApi.login(user.trim(), pass);
      setOfficerToken(r.token);
      navigate("/officer");
    } catch (err) {
      const status = err instanceof ApiError ? err.status : 0;
      setError(
        status === 401
          ? pick("Incorrect username or password.", "ইউজারনেম বা পাসওয়ার্ড ভুল হয়েছে।")
          : status === 429
            ? pick(
                "Too many attempts. Wait a minute and try again.",
                "অনেকবার চেষ্টা হয়েছে। এক মিনিট পরে আবার চেষ্টা করুন।",
              )
            : pick(
                "Cannot reach the server. Is the backend running?",
                "সার্ভারে পৌঁছানো যাচ্ছে না। ব্যাকএন্ড চালু আছে তো?",
              ),
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-side">
        <ShieldLogo size={54} />
        <h1>{pick("Officer portal", "অফিসার পোর্টাল")}</h1>
        <p>
          {pick(
            "Check every new deed against the land record before it is registered. A double sale or a false seller is stopped, with the reason written out.",
            "দলিল নিবন্ধনের আগে ভূমি রেকর্ডের সঙ্গে মিলিয়ে দেখুন। দ্বৈত বিক্রয় বা ভুয়া বিক্রেতা আটকে যায়, কারণসহ।",
          )}
        </p>
        <ul>
          <li>{pick("Green: registered", "সবুজ: নিবন্ধিত")}</li>
          <li>
            {pick(
              "Yellow: registered, flagged for review",
              "হলুদ: নিবন্ধিত, যাচাইয়ের জন্য চিহ্নিত",
            )}
          </li>
          <li>{pick("Red: blocked, with the reason", "লাল: ব্লক, কারণসহ")}</li>
        </ul>
      </div>
      <form className="login-card" onSubmit={submit}>
        <h2 className="plain">{pick("Sign in", "লগইন করুন")}</h2>
        <label>
          {pick("Username", "ইউজারনেম")}
          <input
            value={user}
            onChange={(e) => setUser(e.target.value)}
            autoComplete="username"
            required
            autoFocus
          />
        </label>
        <label>
          {pick("Password", "পাসওয়ার্ড")}
          <input
            type="password"
            value={pass}
            onChange={(e) => setPass(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>
        {error && (
          <p className="note note-error" role="alert">
            {error}
          </p>
        )}
        <button type="submit" className="btn btn-primary btn-block" disabled={busy}>
          {busy ? pick("Signing in…", "প্রবেশ হচ্ছে…") : pick("Sign in", "প্রবেশ করুন")}
        </button>
        {SHOW_DEMO && (
          <div className="demo-cred">
            <strong>{pick("Demo account (synthetic)", "ডেমো অ্যাকাউন্ট (নকল)")}</strong>
            <code>
              {DEMO_USER} / {DEMO_PASS}
            </code>
            <button
              type="button"
              className="btn btn-quiet"
              onClick={() => {
                setUser(DEMO_USER);
                setPass(DEMO_PASS);
              }}
            >
              {pick("Fill in", "ঘরে বসান")}
            </button>
          </div>
        )}
        {cfg.data?.judge_login && (
          <Link to="/judge" className="judge-link">
            <span aria-hidden="true">★</span>{" "}
            {pick(
              "Judges: one-click demo, no password",
              "জুরির জন্য: এক ক্লিকে ডেমো, পাসওয়ার্ড ছাড়া",
            )}
          </Link>
        )}
        <Link to="/check" className="public-link">
          {pick("Check land (for everyone)", "জমি যাচাই করুন (সবার জন্য)")}{" "}
          <span aria-hidden="true">→</span>
        </Link>
      </form>
    </div>
  );
}

import { Link, NavLink, Route, Routes } from "react-router-dom";
import { getAdminToken, publicApi, setAdminToken } from "./api";
import { useApi } from "./hooks";
import { useI18n } from "./i18n";
import AlertPage from "./pages/AlertPage";
import Dashboard from "./pages/Dashboard";
import Home from "./pages/Home";
import Evaluation from "./pages/Evaluation";
import ParcelPage from "./pages/ParcelPage";
import SearchPage from "./pages/SearchPage";
import VerifyPage from "./pages/VerifyPage";
import CheckLand from "./pages/CheckLand";
import JudgeGuide from "./pages/JudgeGuide";
import { ShieldLogo } from "./officer/common";
import NewRegistration from "./officer/NewRegistration";
import OfficerAlerts from "./officer/OfficerAlerts";
import OfficerDashboard from "./officer/OfficerDashboard";
import OfficerHistory from "./officer/OfficerHistory";
import OfficerLayout from "./officer/OfficerLayout";
import OfficerLogin from "./officer/OfficerLogin";
import OfficerPlots from "./officer/OfficerPlots";
import RegistrationResult from "./officer/RegistrationResult";

function NotFound() {
  const { t } = useI18n();
  return (
    <section>
      <h1>{t("notFoundTitle")}</h1>
      <p>{t("notFoundBody")}</p>
      <Link to="/">{t("navHome")}</Link>
    </section>
  );
}

export default function App() {
  const { t, lang, setLang } = useI18n();
  const cfg = useApi(() => publicApi.config(), []);
  return (
    <>
      <a className="skip" href="#main">
        Skip to content
      </a>
      <header className="topbar">
        <div className="topbar-inner">
          <Link to="/" className="brand">
            <ShieldLogo size={30} />
            {t("appName")}
          </Link>
          <nav aria-label="Main">
            <NavLink to="/" end>
              {t("navHome")}
            </NavLink>
            <NavLink to="/officer">{t("navOfficer")}</NavLink>
            <NavLink to="/dashboard">{t("navDashboard")}</NavLink>
            <NavLink to="/search">{t("navSearch")}</NavLink>
            <NavLink to="/verify">{t("navVerify")}</NavLink>
            <NavLink to="/evaluation">{t("navEvaluation")}</NavLink>
          </nav>
          {cfg.data?.judge_login && (
            <Link to="/judge" className="judge-pill">
              <span aria-hidden="true">★</span> {t("navJudge")}
            </Link>
          )}
          <div className="lang" role="group" aria-label={t("language")}>
            <button type="button" aria-pressed={lang === "en"} onClick={() => setLang("en")}>
              English
            </button>
            <button type="button" aria-pressed={lang === "bn"} onClick={() => setLang("bn")}>
              বাংলা
            </button>
          </div>
        </div>
      </header>
      <main id="main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/check" element={<CheckLand />} />
          <Route path="/judge" element={<JudgeGuide />} />
          <Route path="/officer/login" element={<OfficerLogin />} />
          <Route path="/officer" element={<OfficerLayout />}>
            <Route index element={<OfficerDashboard />} />
            <Route path="new" element={<NewRegistration />} />
            <Route path="result/:id" element={<RegistrationResult />} />
            <Route path="plots" element={<OfficerPlots />} />
            <Route path="history" element={<OfficerHistory />} />
            <Route path="alerts" element={<OfficerAlerts />} />
          </Route>
          <Route path="/search" element={<SearchPage />} />
          <Route path="/parcels/:id" element={<ParcelPage />} />
          <Route path="/alerts/:id" element={<AlertPage />} />
          <Route path="/verify" element={<VerifyPage />} />
          <Route path="/evaluation" element={<Evaluation />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <footer className="footer">
        <p className="footer-note">{t("footerNote")}</p>
        <label>
          {t("adminToken")}
          <input
            type="password"
            autoComplete="off"
            defaultValue={getAdminToken()}
            onChange={(e) => setAdminToken(e.target.value)}
          />
        </label>
      </footer>
    </>
  );
}

import { useEffect, useState } from "react";
import { NavLink, Navigate, Outlet, useNavigate } from "react-router-dom";
import { Officer, getOfficerToken, officerApi, setOfficerToken } from "../api";
import { useI18n } from "../i18n";
import { Loading } from "../components/ui";

export type OfficerCtx = { officer: Officer };

export default function OfficerLayout() {
  const { pick, lang } = useI18n();
  const navigate = useNavigate();
  const [officer, setOfficer] = useState<Officer | null>(null);
  const [checked, setChecked] = useState(false);
  const hasToken = getOfficerToken() !== "";

  useEffect(() => {
    if (!hasToken) return;
    let live = true;
    officerApi
      .me()
      .then((o) => live && setOfficer(o))
      .catch(() => live && setOfficerToken(""))
      .finally(() => live && setChecked(true));
    return () => {
      live = false;
    };
  }, [hasToken]);

  if (!hasToken || (checked && !officer)) return <Navigate to="/officer/login" replace />;
  if (!officer) return <Loading />;

  async function logout() {
    try {
      await officerApi.logout();
    } catch {
      /* the session ends on this device either way */
    }
    setOfficerToken("");
    navigate("/officer/login");
  }

  return (
    <div className="ofc">
      <div className="ofc-bar">
        <nav aria-label={pick("Officer portal", "অফিসার পোর্টাল")}>
          <NavLink to="/officer" end>
            {pick("Dashboard", "ড্যাশবোর্ড")}
          </NavLink>
          <NavLink to="/officer/new">{pick("New registration", "নতুন দলিল")}</NavLink>
          <NavLink to="/officer/plots">{pick("Plots", "জমির তালিকা")}</NavLink>
          <NavLink to="/officer/history">{pick("Plot history", "দাগের ইতিহাস")}</NavLink>
          <NavLink to="/officer/alerts">{pick("Alerts", "অ্যালার্ট")}</NavLink>
        </nav>
        <div className="ofc-user">
          <span className="ofc-avatar" aria-hidden="true">
            {(lang === "bn" ? officer.name_bn : officer.name_en).charAt(0)}
          </span>
          <span>{lang === "bn" ? officer.name_bn : officer.name_en}</span>
          <button type="button" className="btn btn-quiet" onClick={logout}>
            {pick("Log out", "লগআউট")}
          </button>
        </div>
      </div>
      <Outlet context={{ officer } satisfies OfficerCtx} />
    </div>
  );
}

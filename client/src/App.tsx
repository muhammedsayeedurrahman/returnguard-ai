import { Outlet, Link, useLocation } from "react-router-dom";

export default function App() {
  const loc = useLocation();
  const tabs = [
    { to: "/return", label: "Return Portal" },
    { to: "/billing", label: "Receipt Check" },
    { to: "/admin", label: "Fraud Ops" },
    { to: "/demo", label: "Demo" },
  ];
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-600 to-purple-600" />
            <h1 className="font-semibold text-slate-900">sec_logistics</h1>
            <span className="text-xs text-slate-500 hidden sm:inline">
              Inconsistency Engine
            </span>
          </div>
          <nav className="flex gap-1">
            {tabs.map((t) => (
              <Link
                key={t.to}
                to={t.to}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition ${
                  loc.pathname.startsWith(t.to)
                    ? "bg-slate-900 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                {t.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-8">
        <Outlet />
      </main>
      <footer className="text-center text-xs text-slate-400 py-4 border-t border-slate-200 bg-white">
        sec_logistics · 6-signal fusion · DPDP-compliant evidence trail
      </footer>
    </div>
  );
}

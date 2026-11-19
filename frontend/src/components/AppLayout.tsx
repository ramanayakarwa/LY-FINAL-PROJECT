import type { ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import {
  LayoutDashboard,
  Leaf,
  ScanSearch,
  Sprout,
  BarChart3,
  Bot,
  ScrollText,
  LogOut,
} from "lucide-react";

import { auth } from "@/lib/auth";
import { api } from "@/services/api";

const links = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/disease", label: "Disease", icon: Leaf },
  { to: "/inspection", label: "Plant Inspection", icon: ScanSearch },
  { to: "/crop", label: "Crop", icon: Sprout },
  { to: "/yield", label: "Production", icon: BarChart3 },
  { to: "/rover", label: "Rover", icon: Bot },
  { to: "/logs", label: "Logs", icon: ScrollText },
];

export function AppLayout({ children }: { children: ReactNode }) {
  const navigate = useNavigate();

  const { data, isError } = useQuery({
    queryKey: ["header-status"],
    queryFn: api.getSystemStatus,
    refetchInterval: 5000,
    retry: false,
  });

  const status = isError
    ? "API OFFLINE"
    : data?.status ?? "CHECKING";

  const live =
    status === "ONLINE" &&
    data?.telemetry?.fresh &&
    data.telemetry.verified;

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="max-w-[1600px] mx-auto px-5 py-3 flex flex-wrap items-center gap-4">
          <strong className="text-lg tracking-wide">
            ARES · ESP32
          </strong>

          <nav
            className="flex flex-wrap gap-1 flex-1"
            aria-label="Main navigation"
          >
            {links.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === "/"}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded ${
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-muted text-muted-foreground"
                  }`
                }
              >
                <Icon className="h-4 w-4" />
                {label}
              </NavLink>
            ))}
          </nav>

          <span
            className={`text-xs font-bold ${
              live ? "text-green-600" : "text-amber-600"
            }`}
          >
            {status}
            {live ? " · VERIFIED TELEMETRY" : " · NOT LIVE"}
          </span>

          <button
            className="px-3 py-2 text-xs rounded bg-orange-600 text-white"
            onClick={() => {
              auth.logout();
              navigate("/login", { replace: true });
            }}
          >
            <LogOut className="h-4 w-4 inline mr-1" />
            Logout
          </button>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto p-5">
        {children}
      </main>
    </div>
  );
}
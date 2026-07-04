"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api/client";
import type { User } from "@/lib/api/types";

const UserContext = createContext<{ user: User | null; refresh: () => void }>({
  user: null,
  refresh: () => {},
});

export function useUser() {
  return useContext(UserContext);
}

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const pathname = usePathname();
  const router = useRouter();

  const refresh = () => {
    api.get<User>("/auth/me").then(setUser).catch(() => setUser(null));
  };

  useEffect(refresh, []);

  const logout = async () => {
    await api.post("/auth/logout");
    router.push("/login");
    router.refresh();
  };

  const links =
    user?.role === "admin"
      ? [{ href: "/admin", label: "Analytics" }]
      : [
          { href: "/plan", label: "Plan My Trip" },
          { href: "/account", label: "My Account" },
        ];

  return (
    <UserContext.Provider value={{ user, refresh }}>
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-3">
          <Link href="/" className="text-lg font-bold text-sky-700">
            🌎 TravelBud
          </Link>
          <nav className="flex items-center gap-4">
            {links.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className={`text-sm font-medium ${
                  pathname.startsWith(l.href)
                    ? "text-sky-700"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {l.label}
              </Link>
            ))}
            {user && (
              <span className="hidden text-sm text-slate-500 sm:inline">
                {user.name} · {user.hits_left} requests left
              </span>
            )}
            <button
              onClick={logout}
              className="text-sm font-medium text-slate-600 hover:text-slate-900"
            >
              Log out
            </button>
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-8">{children}</main>
    </UserContext.Provider>
  );
}

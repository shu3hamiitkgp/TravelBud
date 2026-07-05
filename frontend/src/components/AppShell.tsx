"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useContext, useEffect, useState } from "react";
import { LogOut, Ticket } from "lucide-react";
import Logo from "@/components/Logo";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
      <header className="sticky top-0 z-20 border-b bg-background/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-3">
          <Logo />
          <nav className="flex items-center gap-1 sm:gap-2">
            {links.map((l) => (
              <Button
                key={l.href}
                variant={pathname.startsWith(l.href) ? "secondary" : "ghost"}
                size="sm"
                render={<Link href={l.href} />}
              >
                {l.label}
              </Button>
            ))}
            {user && user.role !== "admin" && (
              <Badge variant="outline" className="ml-1 hidden gap-1 sm:inline-flex">
                <Ticket className="size-3.5" />
                {user.hits_left} left
              </Badge>
            )}
            <Button variant="ghost" size="sm" onClick={logout} aria-label="Log out">
              <LogOut className="size-4" />
              <span className="hidden sm:inline">Log out</span>
            </Button>
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-8">{children}</main>
    </UserContext.Provider>
  );
}

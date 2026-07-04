"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api/client";
import type { ItinerarySummary, User } from "@/lib/api/types";
import { useUser } from "@/components/AppShell";
import { Button, Card, ErrorText } from "@/components/ui";

const PLANS = [
  { name: "Basic", requests: 10 },
  { name: "Standard", requests: 25 },
  { name: "Premium", requests: 50 },
];

export default function AccountPage() {
  const { user, refresh } = useUser();
  const [placeTypes, setPlaceTypes] = useState<string[]>([]);
  const [plan, setPlan] = useState("");
  const [interests, setInterests] = useState<string[]>([]);
  const [history, setHistory] = useState<ItinerarySummary[]>([]);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get<string[]>("/account/place-types").then(setPlaceTypes).catch(() => {});
    api.get<ItinerarySummary[]>("/itineraries").then(setHistory).catch(() => {});
  }, []);

  // Sync form state from the loaded user once, during render (derived-state pattern).
  const [syncedUserId, setSyncedUserId] = useState<number | null>(null);
  if (user && syncedUserId !== user.id) {
    setSyncedUserId(user.id);
    setPlan(user.plan_name);
    setInterests(user.interests);
  }

  const toggleInterest = (t: string) =>
    setInterests((prev) =>
      prev.includes(t) ? prev.filter((i) => i !== t) : [...prev, t]
    );

  const save = async () => {
    setBusy(true);
    setError("");
    setSaved(false);
    try {
      await api.patch<User>("/account", { plan, interests });
      refresh();
      setSaved(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save changes");
    } finally {
      setBusy(false);
    }
  };

  if (!user) return <p className="text-slate-500">Loading account…</p>;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-3xl font-bold">My Account</h1>

      <Card className="space-y-4">
        <div>
          <h2 className="font-semibold">{user.name}</h2>
          <p className="text-sm text-slate-500">{user.email}</p>
          <p className="mt-1 text-sm text-slate-600">
            {user.plan_name} plan · <strong>{user.hits_left}</strong> requests left
          </p>
        </div>

        <div>
          <h3 className="mb-2 text-sm font-medium text-slate-700">Change plan</h3>
          <div className="grid grid-cols-3 gap-2">
            {PLANS.map((p) => (
              <button
                key={p.name}
                type="button"
                onClick={() => setPlan(p.name)}
                className={`rounded-lg border px-3 py-2 text-sm ${
                  plan === p.name
                    ? "border-sky-600 bg-sky-50 font-medium text-sky-700"
                    : "border-slate-300 text-slate-600 hover:bg-slate-50"
                }`}
              >
                {p.name}
                <span className="block text-xs text-slate-400">
                  {p.requests} requests
                </span>
              </button>
            ))}
          </div>
          {plan !== user.plan_name && (
            <p className="mt-2 text-xs text-amber-700">
              Switching plans resets your remaining requests to the new plan&apos;s limit.
            </p>
          )}
        </div>

        <div>
          <h3 className="mb-2 text-sm font-medium text-slate-700">Interests</h3>
          <div className="flex flex-wrap gap-1.5">
            {placeTypes.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => toggleInterest(t)}
                className={`rounded-full border px-2.5 py-1 text-xs ${
                  interests.includes(t)
                    ? "border-sky-600 bg-sky-50 text-sky-700"
                    : "border-slate-300 text-slate-500 hover:bg-slate-50"
                }`}
              >
                {t.replaceAll("_", " ")}
              </button>
            ))}
          </div>
        </div>

        <ErrorText>{error}</ErrorText>
        {saved && <p className="text-sm text-green-700">Changes saved.</p>}
        <Button onClick={save} disabled={busy}>
          {busy ? "Saving…" : "Save changes"}
        </Button>
      </Card>

      <Card>
        <h2 className="mb-3 font-semibold">Past itineraries</h2>
        {history.length === 0 ? (
          <p className="text-sm text-slate-500">
            No itineraries yet —{" "}
            <Link href="/plan" className="text-sky-700 hover:underline">
              plan your first trip
            </Link>
            .
          </p>
        ) : (
          <ul className="divide-y divide-slate-100">
            {history.map((it) => (
              <li key={it.id} className="flex items-center justify-between py-2">
                <Link
                  href={`/itinerary/${it.id}`}
                  className="text-sm font-medium text-sky-700 hover:underline"
                >
                  {it.destination}
                </Link>
                <span className="text-xs text-slate-400">
                  {it.language} · {new Date(it.created_at).toLocaleDateString()}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

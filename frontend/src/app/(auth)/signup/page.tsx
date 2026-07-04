"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api/client";
import { Button, Card, ErrorText, Input, Label } from "@/components/ui";

const PLANS = [
  { name: "Basic", requests: 10 },
  { name: "Standard", requests: 25 },
  { name: "Premium", requests: 50 },
];

export default function SignupPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [plan, setPlan] = useState("Basic");
  const [placeTypes, setPlaceTypes] = useState<string[]>([]);
  const [interests, setInterests] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get<string[]>("/account/place-types").then(setPlaceTypes).catch(() => {});
  }, []);

  const toggleInterest = (t: string) =>
    setInterests((prev) =>
      prev.includes(t) ? prev.filter((i) => i !== t) : [...prev, t]
    );

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await api.post("/auth/signup", { email, password, name, plan, interests });
      await api.post("/auth/login", { email, password });
      router.push("/plan");
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
      setBusy(false);
    }
  };

  return (
    <Card>
      <h1 className="mb-1 text-2xl font-bold">Create your account</h1>
      <p className="mb-6 text-sm text-slate-500">
        Tell us a bit about yourself and how you like to travel.
      </p>
      <form onSubmit={submit} className="space-y-4">
        <div>
          <Label>Name</Label>
          <Input value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div>
          <Label>Email</Label>
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label>Password</Label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={8}
              required
            />
          </div>
          <div>
            <Label>Confirm</Label>
            <Input
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
            />
          </div>
        </div>
        <div>
          <Label>Plan</Label>
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
        </div>
        {placeTypes.length > 0 && (
          <div>
            <Label>Your interests</Label>
            <div className="flex max-h-32 flex-wrap gap-1.5 overflow-y-auto">
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
        )}
        <ErrorText>{error}</ErrorText>
        <Button type="submit" disabled={busy} className="w-full">
          {busy ? "Creating account…" : "Create account"}
        </Button>
      </form>
      <p className="mt-4 text-sm text-slate-500">
        Already have an account?{" "}
        <Link href="/login" className="text-sky-700 hover:underline">
          Log in
        </Link>
      </p>
    </Card>
  );
}

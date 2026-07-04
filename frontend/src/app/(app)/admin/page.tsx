"use client";

import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, ApiError } from "@/lib/api/client";
import type { Analytics } from "@/lib/api/types";
import { Card, ErrorText } from "@/components/ui";

const PLAN_COLORS: Record<string, string> = {
  Basic: "#94a3b8",
  Standard: "#38bdf8",
  Premium: "#0369a1",
};

export default function AdminPage() {
  const [data, setData] = useState<Analytics | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<Analytics>("/admin/analytics")
      .then(setData)
      .catch((err) =>
        setError(
          err instanceof ApiError && err.status === 403
            ? "Admin access required"
            : "Could not load analytics"
        )
      );
  }, []);

  if (error) return <ErrorText>{error}</ErrorText>;
  if (!data) return <p className="text-slate-500">Loading analytics…</p>;

  const planData = Object.entries(data.users_by_plan).map(([name, value]) => ({
    name,
    value,
  }));

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Admin Dashboard</h1>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Metric label="Total users" value={data.total_users} />
        <Metric label="Trips planned" value={data.budget.trips} />
        <Metric label="Avg budget" value={`$${Math.round(data.budget.avg).toLocaleString()}`} />
        <Metric label="Max budget" value={`$${Math.round(data.budget.max).toLocaleString()}`} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="mb-4 font-semibold">Users by plan</h2>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={planData} dataKey="value" nameKey="name" label>
                {planData.map((entry) => (
                  <Cell
                    key={entry.name}
                    fill={PLAN_COLORS[entry.name] ?? "#cbd5e1"}
                  />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h2 className="mb-4 font-semibold">Top destinations</h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={data.top_destinations}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="destination" fontSize={12} />
              <YAxis allowDecimals={false} fontSize={12} />
              <Tooltip />
              <Bar dataKey="trips" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h2 className="mb-4 font-semibold">Trips planned per day</h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={data.trips_by_day}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" fontSize={12} />
              <YAxis allowDecimals={false} fontSize={12} />
              <Tooltip />
              <Bar dataKey="trips" fill="#0284c7" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h2 className="mb-4 font-semibold">Preferred holiday start dates</h2>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={data.preferred_start_dates}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" fontSize={12} />
              <YAxis allowDecimals={false} fontSize={12} />
              <Tooltip />
              <Line type="monotone" dataKey="travelers" stroke="#0ea5e9" />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <Card className="!p-4">
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className="mt-1 text-2xl font-bold">{value}</p>
    </Card>
  );
}

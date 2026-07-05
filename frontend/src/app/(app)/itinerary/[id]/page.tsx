"use client";

import { use, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import {
  CalendarRange,
  Download,
  Hotel,
  Languages,
  Plane,
  Wallet,
} from "lucide-react";
import { api, ApiError } from "@/lib/api/client";
import type { DayPlan, Estimate, Itinerary } from "@/lib/api/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
}: {
  icon: typeof Plane;
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <Card className="py-4">
      <CardContent className="flex items-center gap-3 px-4">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Icon className="size-4" />
        </span>
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">
            {label}
          </p>
          <p className="truncate text-sm font-semibold">{value}</p>
          {sub && <p className="truncate text-xs text-muted-foreground">{sub}</p>}
        </div>
      </CardContent>
    </Card>
  );
}

export default function ItineraryPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<Itinerary>(`/itineraries/${id}`)
      .then(setItinerary)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Could not load itinerary")
      );
  }, [id]);

  if (error) return <p className="text-destructive">{error}</p>;
  if (!itinerary)
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <Skeleton className="h-12 w-2/3" />
        <div className="grid gap-3 sm:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-20 rounded-xl" />
          ))}
        </div>
        <Skeleton className="h-96 rounded-xl" />
      </div>
    );

  const estimate = itinerary.trip.estimate as Estimate | undefined;
  const dayPlans = (itinerary.trip.day_plans as DayPlan[] | undefined) ?? [];

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Hero header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-sky-500 to-blue-700 p-8 text-white print:bg-none print:p-0 print:text-foreground">
        <div className="relative">
          <Badge className="mb-3 bg-white/20 text-white hover:bg-white/20">
            Your itinerary
          </Badge>
          <h1 className="text-4xl font-extrabold tracking-tight">
            {itinerary.destination}
          </h1>
          {estimate && (
            <p className="mt-2 text-sky-100 print:text-muted-foreground">
              {estimate.start_date} → {estimate.end_date} · created{" "}
              {new Date(itinerary.created_at).toLocaleDateString()}
            </p>
          )}
          <div className="mt-5 print:hidden">
            <Button
              variant="secondary"
              render={<a href={`/api/itineraries/${itinerary.id}/pdf`} download />}
            >
              <Download className="size-4" /> Download PDF
            </Button>
          </div>
        </div>
      </div>

      {/* Trip stats */}
      {estimate && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            icon={Plane}
            label="Flight"
            value={estimate.airline}
            sub={`$${estimate.flight_price.toLocaleString()}`}
          />
          <StatCard
            icon={Hotel}
            label="Hotel"
            value={estimate.hotel_name}
            sub={`$${estimate.hotel_price.toLocaleString()}`}
          />
          <StatCard
            icon={Wallet}
            label="Total cost"
            value={`$${estimate.total_cost.toLocaleString()}`}
            sub={estimate.within_budget ? "Within budget" : "Over budget"}
          />
          <StatCard icon={Languages} label="Language" value={itinerary.language} />
        </div>
      )}

      {/* Day timeline */}
      {dayPlans.length > 0 && (
        <Card>
          <CardContent className="pt-2">
            <h2 className="mb-4 flex items-center gap-2 font-semibold">
              <CalendarRange className="size-4 text-primary" /> At a glance
            </h2>
            <ol className="relative ml-3 space-y-4 border-l-2 border-primary/20 pl-6">
              {dayPlans.map((p) => (
                <li key={p.day} className="relative">
                  <span className="absolute -left-[31px] flex size-4 items-center justify-center rounded-full border-2 border-primary bg-background" />
                  <p className="text-sm font-semibold">Day {p.day}</p>
                  <p className="text-sm text-muted-foreground">
                    {p.places.join(" · ")}
                    {p.distance_km != null && ` (${p.distance_km} km apart)`}
                  </p>
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>
      )}

      {/* Full itinerary */}
      <Card>
        <CardContent className="pt-2">
          <article className="max-w-none text-[15px] leading-relaxed [&_h1]:mb-3 [&_h1]:mt-6 [&_h1]:text-2xl [&_h1]:font-extrabold [&_h1]:tracking-tight [&_h2]:mb-2 [&_h2]:mt-6 [&_h2]:border-b [&_h2]:pb-1.5 [&_h2]:text-lg [&_h2]:font-bold [&_h3]:mt-4 [&_h3]:font-semibold [&_p]:my-2.5 [&_strong]:font-semibold [&_ul]:my-2 [&_ul]:list-disc [&_ul]:space-y-1 [&_ul]:pl-6 [&_ol]:my-2 [&_ol]:list-decimal [&_ol]:pl-6">
            <ReactMarkdown>{itinerary.content}</ReactMarkdown>
          </article>
          <Separator className="my-4" />
          <p className="text-xs text-muted-foreground">
            Prices are estimates at generation time, not bookings.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

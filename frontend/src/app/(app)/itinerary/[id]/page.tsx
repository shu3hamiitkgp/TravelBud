"use client";

import { use, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { api, ApiError } from "@/lib/api/client";
import type { Estimate, Itinerary } from "@/lib/api/types";
import { Button, Card, ErrorText } from "@/components/ui";

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

  if (error) return <ErrorText>{error}</ErrorText>;
  if (!itinerary) return <p className="text-slate-500">Loading itinerary…</p>;

  const estimate = itinerary.trip.estimate as Estimate | undefined;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">{itinerary.destination}</h1>
          <p className="text-sm text-slate-500">
            {itinerary.language} · created{" "}
            {new Date(itinerary.created_at).toLocaleDateString()}
          </p>
        </div>
        <a href={`/api/itineraries/${itinerary.id}/pdf`} download>
          <Button>Download PDF</Button>
        </a>
      </div>

      {estimate && (
        <Card>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:grid-cols-4">
            <dt className="text-slate-500">Dates</dt>
            <dd>
              {estimate.start_date} → {estimate.end_date}
            </dd>
            <dt className="text-slate-500">Hotel</dt>
            <dd>{estimate.hotel_name}</dd>
            <dt className="text-slate-500">Flight</dt>
            <dd>{estimate.airline}</dd>
            <dt className="text-slate-500">Total</dt>
            <dd className="font-semibold">${estimate.total_cost.toLocaleString()}</dd>
          </dl>
        </Card>
      )}

      <Card>
        <article className="prose prose-slate max-w-none prose-headings:mt-6 prose-headings:mb-2 [&_h1]:text-2xl [&_h2]:text-xl [&_h1]:font-bold [&_h2]:font-semibold [&_p]:my-2 [&_ul]:list-disc [&_ul]:pl-6">
          <ReactMarkdown>{itinerary.content}</ReactMarkdown>
        </article>
      </Card>
    </div>
  );
}

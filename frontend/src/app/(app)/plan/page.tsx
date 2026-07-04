"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, ApiError } from "@/lib/api/client";
import type {
  Attraction,
  DayPlan,
  Estimate,
  Itinerary,
  TripRequest,
} from "@/lib/api/types";
import { useUser } from "@/components/AppShell";
import CityPicker, { type CitySelection } from "@/components/CityPicker";
import { Button, Card, ErrorText, Input, Label, Select } from "@/components/ui";

const FLIGHT_TYPES = ["Best", "Cheapest", "Fastest", "Direct"];
const LANGUAGES = ["English", "Spanish", "Hindi"];
const STEPS = ["Route & dates", "Places to visit", "Review & generate"];

export default function PlanTripPage() {
  const router = useRouter();
  const { user, refresh } = useUser();

  const [step, setStep] = useState(0);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  // Step 1: route & dates
  const [source, setSource] = useState<CitySelection | null>(null);
  const [destination, setDestination] = useState<CitySelection | null>(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [numDays, setNumDays] = useState(3);
  const [adults, setAdults] = useState(1);
  const [rooms, setRooms] = useState(1);
  const [flightType, setFlightType] = useState("Best");
  const [budget, setBudget] = useState(2000);

  // Step 2: attractions
  const [attractions, setAttractions] = useState<Attraction[]>([]);
  const [selectedPlaces, setSelectedPlaces] = useState<string[]>([]);
  const [language, setLanguage] = useState("English");

  // Step 3: estimate
  const [estimate, setEstimate] = useState<Estimate | null>(null);
  const [dayPlans, setDayPlans] = useState<DayPlan[]>([]);

  const tripRequest = (): TripRequest => ({
    origin_iata: source!.iata,
    destination_iata: destination!.iata,
    destination_city: destination!.city,
    start_date: startDate,
    end_date: endDate,
    num_days: numDays,
    adults,
    rooms,
    flight_type: flightType,
    budget,
  });

  const toStep2 = async () => {
    if (!source || !destination || !startDate || !endDate) {
      setError("Please fill in the route and dates");
      return;
    }
    if (endDate < startDate) {
      setError("End date must be after the start date");
      return;
    }
    if ((new Date(endDate).getTime() - new Date(startDate).getTime()) / 86400000 + 1 < numDays) {
      setError("Trip length exceeds the selected date range");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const res = await api.get<Attraction[]>(
        `/trips/attractions?city=${encodeURIComponent(destination.city)}`
      );
      setAttractions(res);
      setSelectedPlaces([]);
      setStep(1);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load attractions");
    } finally {
      setBusy(false);
    }
  };

  const togglePlace = (name: string) =>
    setSelectedPlaces((prev) =>
      prev.includes(name)
        ? prev.filter((p) => p !== name)
        : prev.length < 10
          ? [...prev, name]
          : prev
    );

  const toStep3 = async () => {
    if (selectedPlaces.length < 2) {
      setError("Pick at least two places to visit");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const [est, plans] = await Promise.all([
        api.post<Estimate>("/trips/estimate", tripRequest()),
        api.post<DayPlan[]>("/trips/pairs", {
          locations: selectedPlaces,
          city: destination!.city,
        }),
      ]);
      setEstimate(est);
      setDayPlans(plans);
      setStep(2);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not build an estimate");
    } finally {
      setBusy(false);
    }
  };

  const generate = async () => {
    setBusy(true);
    setError("");
    try {
      const itinerary = await api.post<Itinerary>("/itineraries", {
        estimate,
        trip: tripRequest(),
        selected_places: selectedPlaces,
        day_plans: dayPlans,
        language,
      });
      refresh();
      router.push(`/itinerary/${itinerary.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not generate itinerary");
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-2 text-3xl font-bold">Plan My Trip</h1>
      <ol className="mb-6 flex gap-2 text-sm">
        {STEPS.map((s, i) => (
          <li
            key={s}
            className={`rounded-full px-3 py-1 ${
              i === step
                ? "bg-sky-600 text-white"
                : i < step
                  ? "bg-sky-100 text-sky-700"
                  : "bg-slate-100 text-slate-400"
            }`}
          >
            {i + 1}. {s}
          </li>
        ))}
      </ol>

      {step === 0 && (
        <Card className="space-y-4">
          <CityPicker
            label="From"
            value={source}
            onChange={setSource}
            excludeIata={destination?.iata}
          />
          <CityPicker
            label="To"
            value={destination}
            onChange={setDestination}
            excludeIata={source?.iata}
          />
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Earliest start</Label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div>
              <Label>Latest end</Label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <Label>Trip days</Label>
              <Input
                type="number"
                min={1}
                max={365}
                value={numDays}
                onChange={(e) => setNumDays(Number(e.target.value))}
              />
            </div>
            <div>
              <Label>Adults</Label>
              <Input
                type="number"
                min={1}
                max={20}
                value={adults}
                onChange={(e) => setAdults(Number(e.target.value))}
              />
            </div>
            <div>
              <Label>Rooms</Label>
              <Input
                type="number"
                min={1}
                max={10}
                value={rooms}
                onChange={(e) => setRooms(Number(e.target.value))}
              />
            </div>
          </div>
          <div>
            <Label>Flight preference</Label>
            <div className="grid grid-cols-4 gap-2">
              {FLIGHT_TYPES.map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setFlightType(t)}
                  className={`rounded-lg border px-3 py-2 text-sm ${
                    flightType === t
                      ? "border-sky-600 bg-sky-50 font-medium text-sky-700"
                      : "border-slate-300 text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
          <div>
            <Label>
              Budget: <span className="font-semibold">${budget.toLocaleString()}</span>
            </Label>
            <input
              type="range"
              min={100}
              max={10000}
              step={100}
              value={budget}
              onChange={(e) => setBudget(Number(e.target.value))}
              className="w-full accent-sky-600"
            />
          </div>
          <ErrorText>{error}</ErrorText>
          <Button onClick={toStep2} disabled={busy} className="w-full">
            {busy ? "Finding attractions…" : "Next: choose places"}
          </Button>
        </Card>
      )}

      {step === 1 && (
        <Card className="space-y-4">
          <p className="text-sm text-slate-600">
            Top attractions in <strong>{destination?.city}</strong> — pick 2 to 10
            you&apos;d like to visit.
          </p>
          <ul className="space-y-2">
            {attractions.map((a) => (
              <li key={a.name}>
                <button
                  type="button"
                  onClick={() => togglePlace(a.name)}
                  className={`w-full rounded-lg border px-3 py-2 text-left text-sm ${
                    selectedPlaces.includes(a.name)
                      ? "border-sky-600 bg-sky-50"
                      : "border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  <span className="font-medium">{a.name}</span>
                  {a.rating != null && (
                    <span className="ml-2 text-amber-600">★ {a.rating}</span>
                  )}
                  {a.address && (
                    <span className="block text-xs text-slate-400">{a.address}</span>
                  )}
                </button>
              </li>
            ))}
          </ul>
          <div>
            <Label>Itinerary language</Label>
            <Select value={language} onChange={(e) => setLanguage(e.target.value)}>
              {LANGUAGES.map((l) => (
                <option key={l}>{l}</option>
              ))}
            </Select>
          </div>
          <ErrorText>{error}</ErrorText>
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setStep(0)}>
              Back
            </Button>
            <Button onClick={toStep3} disabled={busy} className="flex-1">
              {busy ? "Pricing your trip…" : `Next: review (${selectedPlaces.length} selected)`}
            </Button>
          </div>
        </Card>
      )}

      {step === 2 && estimate && (
        <Card className="space-y-4">
          <h2 className="text-lg font-semibold">Your best-value bundle</h2>
          {!estimate.within_budget && (
            <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
              This trip runs over your ${budget.toLocaleString()} budget — we found the
              cheapest option available for your dates.
            </p>
          )}
          <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
            <dt className="text-slate-500">Dates</dt>
            <dd>
              {estimate.start_date} → {estimate.end_date}
            </dd>
            <dt className="text-slate-500">Hotel</dt>
            <dd>
              {estimate.hotel_name} — ${estimate.hotel_price.toLocaleString()}
            </dd>
            <dt className="text-slate-500">Flight</dt>
            <dd>
              {estimate.airline} ({flightType}) — $
              {estimate.flight_price.toLocaleString()}
            </dd>
            <dt className="font-medium text-slate-700">Total</dt>
            <dd className="font-semibold">${estimate.total_cost.toLocaleString()}</dd>
          </dl>
          <div>
            <h3 className="mb-1 text-sm font-medium text-slate-700">Day-by-day plan</h3>
            <ul className="space-y-1 text-sm text-slate-600">
              {dayPlans.map((p) => (
                <li key={p.day}>
                  <strong>Day {p.day}:</strong> {p.places.join(" and ")}
                  {p.distance_km != null && (
                    <span className="text-slate-400"> · {p.distance_km} km apart</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
          <p className="text-xs text-slate-400">
            Generating uses 1 of your {user?.hits_left ?? "—"} remaining requests.
          </p>
          <ErrorText>{error}</ErrorText>
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setStep(1)}>
              Back
            </Button>
            <Button onClick={generate} disabled={busy} className="flex-1">
              {busy ? "Crafting your adventure…" : `Generate itinerary (${language})`}
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}

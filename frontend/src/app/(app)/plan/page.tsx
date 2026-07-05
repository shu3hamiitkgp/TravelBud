"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { format } from "date-fns";
import {
  ArrowLeft,
  ArrowRight,
  BedDouble,
  CalendarRange,
  Check,
  Hotel,
  Landmark,
  Loader2,
  MapPin,
  Plane,
  Sparkles,
  Star,
  Ticket,
  Users,
} from "lucide-react";
import type { DateRange } from "react-day-picker";
import { toast } from "sonner";
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
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Skeleton } from "@/components/ui/skeleton";

const FLIGHT_TYPES = ["Best", "Cheapest", "Fastest", "Direct"];
const LANGUAGES = ["English", "Spanish", "Hindi"];
const STEPS = [
  { label: "Trip details", icon: MapPin },
  { label: "Places", icon: Landmark },
  { label: "Review", icon: Sparkles },
];
const GENERATION_STAGES = [
  "Locking in your flight and hotel…",
  "Mapping your days around the city…",
  "Writing your personalized itinerary…",
  "Adding the finishing touches…",
];

// Deterministic gradient per attraction name (photo placeholder until imagery lands).
const GRADIENTS = [
  "from-sky-400 to-blue-600",
  "from-emerald-400 to-teal-600",
  "from-amber-400 to-orange-600",
  "from-rose-400 to-pink-600",
  "from-violet-400 to-purple-600",
  "from-cyan-400 to-sky-600",
];
const gradientFor = (name: string) =>
  GRADIENTS[[...name].reduce((a, c) => a + c.charCodeAt(0), 0) % GRADIENTS.length];

function StepIndicator({ current }: { current: number }) {
  return (
    <ol className="mb-8 flex items-center">
      {STEPS.map((step, i) => (
        <li key={step.label} className="flex flex-1 items-center last:flex-none">
          <div className="flex flex-col items-center gap-1.5">
            <span
              className={`flex size-9 items-center justify-center rounded-full border-2 transition-colors ${
                i < current
                  ? "border-primary bg-primary text-primary-foreground"
                  : i === current
                    ? "border-primary text-primary"
                    : "border-muted-foreground/30 text-muted-foreground/50"
              }`}
            >
              {i < current ? <Check className="size-4" /> : <step.icon className="size-4" />}
            </span>
            <span
              className={`text-xs font-medium ${
                i <= current ? "text-foreground" : "text-muted-foreground/60"
              }`}
            >
              {step.label}
            </span>
          </div>
          {i < STEPS.length - 1 && (
            <div
              className={`mx-3 mb-5 h-0.5 flex-1 rounded ${
                i < current ? "bg-primary" : "bg-muted-foreground/20"
              }`}
            />
          )}
        </li>
      ))}
    </ol>
  );
}

function GeneratingOverlay() {
  const [stage, setStage] = useState(0);
  useEffect(() => {
    const t = setInterval(
      () => setStage((s) => Math.min(s + 1, GENERATION_STAGES.length - 1)),
      4000
    );
    return () => clearInterval(t);
  }, []);
  return (
    <div className="flex flex-col items-center gap-4 py-12 text-center">
      <Loader2 className="size-10 animate-spin text-primary" />
      <p className="font-medium">{GENERATION_STAGES[stage]}</p>
      <p className="text-sm text-muted-foreground">
        This usually takes 10–20 seconds.
      </p>
    </div>
  );
}

export default function PlanTripPage() {
  const router = useRouter();
  const { user, refresh } = useUser();

  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [generating, setGenerating] = useState(false);

  const [source, setSource] = useState<CitySelection | null>(null);
  const [destination, setDestination] = useState<CitySelection | null>(null);
  const [range, setRange] = useState<DateRange | undefined>();
  const [numDays, setNumDays] = useState(3);
  const [adults, setAdults] = useState(1);
  const [rooms, setRooms] = useState(1);
  const [flightType, setFlightType] = useState("Best");
  const [budget, setBudget] = useState(2000);

  const [attractions, setAttractions] = useState<Attraction[]>([]);
  const [loadingPlaces, setLoadingPlaces] = useState(false);
  const [selectedPlaces, setSelectedPlaces] = useState<string[]>([]);
  const [language, setLanguage] = useState("English");

  const [estimate, setEstimate] = useState<Estimate | null>(null);
  const [dayPlans, setDayPlans] = useState<DayPlan[]>([]);
  const topRef = useRef<HTMLDivElement>(null);

  const goto = (s: number) => {
    setStep(s);
    topRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const rangeNights =
    range?.from && range?.to
      ? Math.round((range.to.getTime() - range.from.getTime()) / 86400000) + 1
      : 0;

  const tripRequest = (): TripRequest => ({
    origin_iata: source!.iata,
    destination_iata: destination!.iata,
    destination_city: destination!.city,
    start_date: format(range!.from!, "yyyy-MM-dd"),
    end_date: format(range!.to!, "yyyy-MM-dd"),
    num_days: numDays,
    adults,
    rooms,
    flight_type: flightType,
    budget,
  });

  const toStep2 = async () => {
    if (!source || !destination) return toast.error("Choose both cities first");
    if (!range?.from || !range?.to) return toast.error("Pick your travel window");
    if (rangeNights < numDays)
      return toast.error(
        `A ${numDays}-day trip doesn't fit in a ${rangeNights}-day window — widen your dates or shorten the trip`
      );
    goto(1);
    setLoadingPlaces(true);
    try {
      const res = await api.get<Attraction[]>(
        `/trips/attractions?city=${encodeURIComponent(destination.city)}`
      );
      setAttractions(res);
      setSelectedPlaces([]);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not load attractions");
      goto(0);
    } finally {
      setLoadingPlaces(false);
    }
  };

  const togglePlace = (name: string) =>
    setSelectedPlaces((prev) =>
      prev.includes(name)
        ? prev.filter((p) => p !== name)
        : prev.length < 10
          ? [...prev, name]
          : (toast.info("You can pick up to 10 places"), prev)
    );

  const toStep3 = async () => {
    if (selectedPlaces.length < 2) return toast.error("Pick at least two places");
    setBusy(true);
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
      goto(2);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not price this trip");
    } finally {
      setBusy(false);
    }
  };

  const generate = async () => {
    setGenerating(true);
    try {
      const itinerary = await api.post<Itinerary>("/itineraries", {
        estimate,
        trip: tripRequest(),
        selected_places: selectedPlaces,
        day_plans: dayPlans,
        language,
      });
      refresh();
      toast.success("Your itinerary is ready!");
      router.push(`/itinerary/${itinerary.id}`);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Generation failed — try again");
      setGenerating(false);
    }
  };

  const flightShare = estimate ? estimate.flight_price / estimate.total_cost : 0;

  return (
    <div ref={topRef} className="mx-auto max-w-2xl">
      <h1 className="mb-1 text-3xl font-extrabold tracking-tight">Plan your trip</h1>
      <p className="mb-6 text-muted-foreground">
        A few details and we&apos;ll handle the rest.
      </p>
      <StepIndicator current={step} />

      {step === 0 && (
        <Card>
          <CardContent className="space-y-5 pt-2">
            <div className="grid gap-4 sm:grid-cols-2">
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
            </div>

            <div>
              <Label className="mb-1.5">Travel window</Label>
              <Popover>
                <PopoverTrigger
                  render={
                    <Button
                      variant="outline"
                      className="w-full justify-start font-normal"
                    />
                  }
                >
                    <CalendarRange className="size-4 text-muted-foreground" />
                    {range?.from && range?.to ? (
                      <>
                        {format(range.from, "MMM d, yyyy")} –{" "}
                        {format(range.to, "MMM d, yyyy")}
                        <Badge variant="secondary" className="ml-auto">
                          {rangeNights} days
                        </Badge>
                      </>
                    ) : (
                      <span className="text-muted-foreground">
                        When could you travel?
                      </span>
                    )}
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="range"
                    selected={range}
                    onSelect={setRange}
                    numberOfMonths={2}
                    disabled={{ before: new Date() }}
                  />
                </PopoverContent>
              </Popover>
              <p className="mt-1.5 text-xs text-muted-foreground">
                Give us a flexible window — we&apos;ll find the cheapest {numDays}-day
                stretch inside it.
              </p>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <Label className="mb-1.5 flex items-center gap-1">
                  <CalendarRange className="size-3.5" /> Trip days
                </Label>
                <Input
                  type="number"
                  min={1}
                  max={30}
                  value={numDays}
                  onChange={(e) => setNumDays(Number(e.target.value))}
                />
              </div>
              <div>
                <Label className="mb-1.5 flex items-center gap-1">
                  <Users className="size-3.5" /> Adults
                </Label>
                <Input
                  type="number"
                  min={1}
                  max={20}
                  value={adults}
                  onChange={(e) => setAdults(Number(e.target.value))}
                />
              </div>
              <div>
                <Label className="mb-1.5 flex items-center gap-1">
                  <BedDouble className="size-3.5" /> Rooms
                </Label>
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
              <Label className="mb-1.5">Flight preference</Label>
              <div className="grid grid-cols-4 gap-2">
                {FLIGHT_TYPES.map((t) => (
                  <Button
                    key={t}
                    type="button"
                    variant={flightType === t ? "default" : "outline"}
                    size="sm"
                    onClick={() => setFlightType(t)}
                  >
                    {t}
                  </Button>
                ))}
              </div>
            </div>

            <div>
              <Label className="mb-1.5">
                Budget:{" "}
                <span className="font-semibold text-primary">
                  ${budget.toLocaleString()}
                </span>
              </Label>
              <input
                type="range"
                min={100}
                max={10000}
                step={100}
                value={budget}
                onChange={(e) => setBudget(Number(e.target.value))}
                className="w-full accent-[var(--primary)]"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>$100</span>
                <span>$10,000</span>
              </div>
            </div>

            <Button onClick={toStep2} disabled={busy} className="w-full" size="lg">
              Next: choose places <ArrowRight className="size-4" />
            </Button>
          </CardContent>
        </Card>
      )}

      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Top spots in {destination?.city}</CardTitle>
            <CardDescription>
              Pick 2–10 places. We&apos;ll group nearby ones into the same day.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {loadingPlaces ? (
              <div className="grid gap-3 sm:grid-cols-2">
                {Array.from({ length: 6 }).map((_, i) => (
                  <Skeleton key={i} className="h-24 rounded-xl" />
                ))}
              </div>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
                {attractions.map((a) => {
                  const selected = selectedPlaces.includes(a.name);
                  return (
                    <button
                      key={a.name}
                      type="button"
                      onClick={() => togglePlace(a.name)}
                      className={`group relative overflow-hidden rounded-xl border text-left transition-all ${
                        selected
                          ? "border-primary ring-2 ring-primary/30"
                          : "border-border hover:border-primary/40"
                      }`}
                    >
                      <div
                        className={`h-14 bg-gradient-to-br ${gradientFor(a.name)} opacity-80`}
                      />
                      {selected && (
                        <span className="absolute right-2 top-2 flex size-6 items-center justify-center rounded-full bg-primary text-primary-foreground">
                          <Check className="size-3.5" />
                        </span>
                      )}
                      <div className="p-3">
                        <p className="text-sm font-medium leading-tight">{a.name}</p>
                        <p className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                          {a.rating != null && (
                            <span className="inline-flex items-center gap-0.5 text-amber-600">
                              <Star className="size-3 fill-current" /> {a.rating}
                            </span>
                          )}
                          {a.address && <span className="truncate">{a.address}</span>}
                        </p>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}

            <div>
              <Label className="mb-1.5">Itinerary language</Label>
              <div className="grid grid-cols-3 gap-2">
                {LANGUAGES.map((l) => (
                  <Button
                    key={l}
                    type="button"
                    variant={language === l ? "default" : "outline"}
                    size="sm"
                    onClick={() => setLanguage(l)}
                  >
                    {l}
                  </Button>
                ))}
              </div>
            </div>

            <div className="flex gap-3">
              <Button variant="outline" onClick={() => goto(0)}>
                <ArrowLeft className="size-4" /> Back
              </Button>
              <Button onClick={toStep3} disabled={busy || loadingPlaces} className="flex-1">
                {busy ? (
                  <>
                    <Loader2 className="size-4 animate-spin" /> Pricing your trip…
                  </>
                ) : (
                  <>
                    Review trip ({selectedPlaces.length} selected)
                    <ArrowRight className="size-4" />
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {step === 2 && estimate && (
        <Card>
          {generating ? (
            <CardContent>
              <GeneratingOverlay />
            </CardContent>
          ) : (
            <>
              <CardHeader>
                <CardTitle>Your best-value bundle</CardTitle>
                <CardDescription>
                  {source?.city} → {destination?.city} · {estimate.start_date} to{" "}
                  {estimate.end_date}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                {!estimate.within_budget && (
                  <p className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                    This trip runs over your ${budget.toLocaleString()} budget — this
                    is the cheapest option for your dates.
                  </p>
                )}

                <div className="space-y-3">
                  <div className="flex items-center gap-3 rounded-lg border p-3">
                    <span className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <Plane className="size-4" />
                    </span>
                    <div className="flex-1">
                      <p className="text-sm font-medium">{estimate.airline}</p>
                      <p className="text-xs text-muted-foreground">
                        {flightType} round trip
                      </p>
                    </div>
                    <p className="font-semibold">
                      ${estimate.flight_price.toLocaleString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 rounded-lg border p-3">
                    <span className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <Hotel className="size-4" />
                    </span>
                    <div className="flex-1">
                      <p className="text-sm font-medium">{estimate.hotel_name}</p>
                      <p className="text-xs text-muted-foreground">
                        {numDays} nights · {rooms} room{rooms > 1 ? "s" : ""}
                      </p>
                    </div>
                    <p className="font-semibold">
                      ${estimate.hotel_price.toLocaleString()}
                    </p>
                  </div>
                </div>

                <div>
                  <div className="mb-1 flex justify-between text-sm">
                    <span className="text-muted-foreground">Total cost</span>
                    <span className="font-bold">
                      ${estimate.total_cost.toLocaleString()}
                      <span className="ml-1 font-normal text-muted-foreground">
                        / ${budget.toLocaleString()} budget
                      </span>
                    </span>
                  </div>
                  <div className="flex h-2.5 overflow-hidden rounded-full bg-muted">
                    <div
                      className="bg-primary"
                      style={{ width: `${flightShare * 100}%` }}
                      title="Flight"
                    />
                    <div
                      className="bg-sky-300"
                      style={{ width: `${(1 - flightShare) * 100}%` }}
                      title="Hotel"
                    />
                  </div>
                  <div className="mt-1 flex gap-4 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <span className="size-2 rounded-full bg-primary" /> Flight
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="size-2 rounded-full bg-sky-300" /> Hotel
                    </span>
                  </div>
                </div>

                <div>
                  <h3 className="mb-2 text-sm font-medium">Day-by-day plan</h3>
                  <ol className="space-y-2">
                    {dayPlans.map((p) => (
                      <li key={p.day} className="flex items-start gap-3 text-sm">
                        <Badge variant="secondary" className="mt-0.5 shrink-0">
                          Day {p.day}
                        </Badge>
                        <span>
                          {p.places.join(" and ")}
                          {p.distance_km != null && (
                            <span className="text-muted-foreground">
                              {" "}
                              · {p.distance_km} km apart
                            </span>
                          )}
                        </span>
                      </li>
                    ))}
                  </ol>
                </div>

                <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Ticket className="size-3.5" />
                  Generating uses 1 of your {user?.hits_left ?? "—"} remaining
                  requests.
                </p>

                <div className="flex gap-3">
                  <Button variant="outline" onClick={() => goto(1)}>
                    <ArrowLeft className="size-4" /> Back
                  </Button>
                  <Button onClick={generate} className="flex-1" size="lg">
                    <Sparkles className="size-4" /> Generate itinerary ({language})
                  </Button>
                </div>
              </CardContent>
            </>
          )}
        </Card>
      )}
    </div>
  );
}

import {
  CalendarRange,
  Languages,
  MapPin,
  PiggyBank,
  Plane,
  Sparkles,
  Wand2,
} from "lucide-react";
import Link from "next/link";
import { cookies } from "next/headers";
import Logo from "@/components/Logo";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const STEPS = [
  {
    icon: MapPin,
    title: "Tell us your trip",
    text: "Pick your route, dates, party size, and budget. We search every date window in your range for the best value.",
  },
  {
    icon: Wand2,
    title: "Choose what you love",
    text: "We surface the top attractions at your destination and group them by proximity so each day flows naturally.",
  },
  {
    icon: Plane,
    title: "Get your itinerary",
    text: "AI writes a personalized day-by-day plan with your flight and hotel — downloadable as a PDF in three languages.",
  },
];

const PLANS = [
  { name: "Basic", requests: 10, blurb: "Try it out", highlight: false },
  { name: "Standard", requests: 25, blurb: "For frequent travelers", highlight: true },
  { name: "Premium", requests: 50, blurb: "Plan every getaway", highlight: false },
];

export default async function Home() {
  const cookieStore = await cookies();
  const loggedIn = cookieStore.has("access_token") || cookieStore.has("refresh_token");
  const cta = loggedIn ? "/plan" : "/signup";

  return (
    <div className="flex flex-1 flex-col">
      {/* Nav */}
      <header className="border-b bg-background/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Logo />
          <nav className="flex items-center gap-3">
            {loggedIn ? (
              <Button render={<Link href="/plan" />}>Plan a trip</Button>
            ) : (
              <>
                <Button variant="ghost" render={<Link href="/login" />}>
                  Log in
                </Button>
                <Button render={<Link href="/signup" />}>Get started</Button>
              </>
            )}
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0 bg-gradient-to-b from-sky-100/80 via-background to-background"
          aria-hidden
        />
        <div className="relative mx-auto flex max-w-3xl flex-col items-center px-6 pb-20 pt-24 text-center">
          <Badge variant="secondary" className="mb-4 gap-1.5">
            <Sparkles className="size-3.5" /> AI-crafted itineraries
          </Badge>
          <h1 className="text-balance text-5xl font-extrabold leading-tight tracking-tight sm:text-6xl">
            Where to next?
          </h1>
          <p className="mt-5 max-w-xl text-pretty text-lg text-muted-foreground">
            TravelBud finds the best-value flights and hotels for your dates, pairs
            nearby attractions into effortless days, and writes your whole trip for
            you — in minutes, not weekends.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Button size="lg" render={<Link href={cta} />}>
              Start planning — it&apos;s free
            </Button>
            <Button size="lg" variant="outline" render={<Link href="#how-it-works" />}>
              See how it works
            </Button>
          </div>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-x-8 gap-y-2 text-sm text-muted-foreground">
            <span className="inline-flex items-center gap-1.5">
              <CalendarRange className="size-4" /> Smart date windows
            </span>
            <span className="inline-flex items-center gap-1.5">
              <PiggyBank className="size-4" /> Budget-aware bundles
            </span>
            <span className="inline-flex items-center gap-1.5">
              <Languages className="size-4" /> English · Español · हिन्दी
            </span>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="mx-auto w-full max-w-6xl px-6 py-16">
        <h2 className="text-center text-3xl font-bold tracking-tight">
          Three steps to takeoff
        </h2>
        <div className="mt-10 grid gap-6 md:grid-cols-3">
          {STEPS.map((step, i) => (
            <Card key={step.title} className="relative">
              <CardHeader>
                <span className="absolute right-5 top-4 text-5xl font-extrabold text-muted/60">
                  {i + 1}
                </span>
                <span className="mb-2 flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <step.icon className="size-5" />
                </span>
                <CardTitle>{step.title}</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">
                {step.text}
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="border-t bg-muted/30">
        <div className="mx-auto w-full max-w-6xl px-6 py-16">
          <h2 className="text-center text-3xl font-bold tracking-tight">
            Simple plans, no surprises
          </h2>
          <p className="mt-2 text-center text-muted-foreground">
            Every plan includes flights, hotels, attraction pairing, and PDF export.
          </p>
          <div className="mt-10 grid gap-6 md:grid-cols-3">
            {PLANS.map((plan) => (
              <Card
                key={plan.name}
                className={plan.highlight ? "border-primary shadow-md" : ""}
              >
                <CardHeader>
                  {plan.highlight && (
                    <Badge className="mb-1 w-fit">Most popular</Badge>
                  )}
                  <CardTitle className="flex items-baseline justify-between">
                    {plan.name}
                    <span className="text-sm font-normal text-muted-foreground">
                      {plan.blurb}
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-4xl font-extrabold">
                    {plan.requests}
                    <span className="ml-1 text-sm font-normal text-muted-foreground">
                      itineraries
                    </span>
                  </p>
                  <Button
                    className="mt-6 w-full"
                    variant={plan.highlight ? "default" : "outline"}
                    render={<Link href={cta} />}
                  >
                    Choose {plan.name}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-8 sm:flex-row">
          <Logo />
          <p className="text-sm text-muted-foreground">
            Prices are estimates, not bookings. © {new Date().getFullYear()} TravelBud.
          </p>
        </div>
      </footer>
    </div>
  );
}

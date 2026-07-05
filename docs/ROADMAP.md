# TravelBud — Path to Production

Status as of 2026-07-03: the Next.js + FastAPI rebuild works end-to-end locally (branch `nextjs-rebuild`, tests green, verified manually). This doc captures what remains before real users can touch it, in priority order.

---

## 1. UI/UX overhaul (biggest gap — currently "class project" minimal)

The current UI is functional Tailwind-default: flat cards, no imagery, no motion, generic type. To feel like a consumer travel product:

### Visual identity
- [ ] Design language: pick a direction (e.g. warm/editorial like Airbnb, or crisp/utilitarian like Google Flights). Define palette, type scale (display font for headings — e.g. a serif or geometric sans via next/font), spacing tokens, border radius/shadow system in Tailwind theme.
- [ ] Real logo + favicon + OG images (replace 🌎 emoji).
- [ ] Destination imagery everywhere: hero images on landing, city photos on wizard steps and itinerary pages (Unsplash API or a licensed set; cache/optimize via next/image).
- [ ] Dark mode (Tailwind `dark:` — the CSS variables scaffold already exists).

### Landing page (currently one heading + two buttons)
- [ ] Proper marketing page: hero with search-style CTA ("Where to next?"), how-it-works section (3 steps), sample itinerary preview, plan-tier pricing cards, footer with legal links.
- [ ] Social proof placeholders (testimonials, destination count).

### Trip wizard (functional but bare)
- [ ] Replace numbered chips with a proper progress indicator; animate step transitions (Framer Motion).
- [ ] Combined date-range picker with calendar UI (e.g. react-day-picker) instead of two native date inputs; visualize the "trip window vs stay length" concept — it confuses users today.
- [ ] Attraction cards with photos + ratings instead of text buttons; skeleton loaders while fetching.
- [ ] Budget slider with live "typical trip costs $X–$Y for these dates" context.
- [ ] Estimate review: visual cost breakdown (flight/hotel/total bar), map preview of paired attractions per day (static Maps tile or Mapbox), edit-in-place instead of Back navigation.
- [ ] Loading state for generation: multi-stage progress ("Finding your route… writing day 3…") since Claude generation takes ~10–20s; consider streaming the itinerary text token-by-token (Anthropic streaming API → SSE → progressive render).

### Itinerary page
- [ ] Design it like a travel document: day cards with timeline, icons per activity type, map with pins, share button (public read-only link), print stylesheet.
- [ ] Nicer PDF: current fpdf2 output is plain text — switch to an HTML-to-PDF pipeline (Playwright/WeasyPrint) rendering a styled template that matches the web page.

### General
- [ ] Component library pass: adopt shadcn/ui (Radix-based) instead of hand-rolled ui.tsx — accessible dialogs, toasts, dropdowns, form validation states for free.
- [ ] Toast notifications for errors/success instead of inline text; friendly error page for API-down (the raw 500 seen in dev).
- [ ] Mobile-first pass — wizard and admin dashboard are untested on small screens.
- [ ] Empty states, 404 page, loading.tsx per route.
- [ ] Accessibility audit (focus traps, aria labels on chip buttons, color contrast).

## 2. Product gaps for real users

- [ ] **Email flows** (blocker): real password reset (current one lets anyone reset any account with just the email — fine for demo, unacceptable in prod), email verification on signup, itinerary-ready notification. Use Resend/SES + signed one-time tokens.
- [ ] **Payments**: plan tiers exist but nothing charges — Stripe Checkout + webhooks to set plan/hits; or drop tiers for launch and use a free quota.
- [ ] **Real pricing data**: Amadeus test tier has sparse coverage; move to Amadeus production (per-call pricing) or Duffel/Kiwi Tequila for flights + a hotel aggregator. Show real booking deep-links (affiliate revenue path).
- [ ] **Attractions quality**: Google Places new Places API (the legacy textsearch API is deprecated-ish); photos, opening hours, price level in results.
- [ ] Itinerary editing/regeneration ("swap day 2", "make it cheaper") — chat-style refinement is a natural Claude fit and a big differentiator.
- [ ] More languages (trivial with Claude — the 3-language limit was an mBART constraint that no longer exists).

## 3. Deployment & infrastructure

- [ ] **Hosting**: simplest solid setup — Vercel (frontend) + Railway/Render/Fly.io (API + Postgres), or a single VPS with the existing docker-compose behind Caddy. Decide based on cost tolerance.
- [ ] **HTTPS + cookies**: set `cookie_secure=True`, `SameSite` review, real `JWT_SECRET` rotation story; CORS locked to the prod origin (or keep the same-origin proxy pattern in prod — Vercel rewrites work the same way).
- [ ] **Managed Postgres** with backups (Neon/Supabase/RDS); run `alembic upgrade` in deploy step, not container CMD (avoids race with multiple replicas).
- [ ] **Secrets management**: env vars in host platform; remove seed-admin defaults in prod.
- [ ] **Rotate the old RDS credentials** still in git history (or scrub history with git-filter-repo before making the repo public).
- [ ] Rate limiting beyond plan quotas: per-IP throttling on auth endpoints (slowapi), bot protection on signup (Turnstile).
- [ ] Caching: current TTLCache is per-process — fine for one instance; move to Redis if scaling horizontally.

## 4. Observability & quality

- [ ] Error tracking (Sentry — both Next.js and FastAPI SDKs); replace the generic 500 handler with logged tracebacks + request IDs.
- [ ] Structured logging + uptime monitoring (healthcheck already exists at `/health`).
- [ ] Analytics for the product itself (PostHog/Plausible) — the admin dashboard only shows in-app trip data.
- [ ] Frontend tests: none exist. Add Playwright smoke covering signup → wizard → itinerary (the manual verification script from this session is the spec).
- [ ] Backend: add tests for account router, admin analytics shape, storage backends; CI already runs pytest + lint/build.
- [ ] LLM cost controls: token budget per generation, per-user daily cap, prompt-injection review of user-supplied place names flowing into prompts.

## 5. Legal/trust (pre-launch checklist)

- [ ] Terms of service + privacy policy pages (itineraries currently end with fake "terms and conditions" text from the prompt — remove or link real ones).
- [ ] Disclaimer that prices are estimates, not bookings.
- [ ] Cookie/GDPR banner if targeting EU.

---

## Suggested order of attack

1. **UI/UX overhaul** (§1) — landing page + wizard polish + itinerary page; adopt shadcn/ui first so everything after is faster.
2. **Email + real password reset** (§2) — the one true security blocker.
3. **Deploy a staging environment** (§3) — get it on real URLs early; everything else iterates against it.
4. Streaming itinerary generation + itinerary refinement chat (§1/§2) — the "wow" features.
5. Payments, real pricing providers, observability as usage justifies.

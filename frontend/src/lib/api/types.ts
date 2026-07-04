import { z } from "zod";

export const userSchema = z.object({
  id: z.number(),
  email: z.string(),
  name: z.string(),
  role: z.string(),
  plan_name: z.string(),
  hits_left: z.number(),
  interests: z.array(z.string()),
});
export type User = z.infer<typeof userSchema>;

export const attractionSchema = z.object({
  name: z.string(),
  rating: z.number().nullable(),
  address: z.string().nullable(),
});
export type Attraction = z.infer<typeof attractionSchema>;

export const dayPlanSchema = z.object({
  day: z.number(),
  places: z.array(z.string()),
  distance_km: z.number().nullable(),
});
export type DayPlan = z.infer<typeof dayPlanSchema>;

export const estimateSchema = z.object({
  start_date: z.string(),
  end_date: z.string(),
  hotel_name: z.string(),
  hotel_price: z.number(),
  airline: z.string(),
  flight_price: z.number(),
  total_cost: z.number(),
  within_budget: z.boolean(),
});
export type Estimate = z.infer<typeof estimateSchema>;

export interface TripRequest {
  origin_iata: string;
  destination_iata: string;
  destination_city: string;
  start_date: string;
  end_date: string;
  num_days: number;
  adults: number;
  rooms: number;
  flight_type: string;
  budget: number;
}

export const itinerarySummarySchema = z.object({
  id: z.number(),
  destination: z.string(),
  language: z.string(),
  created_at: z.string(),
});
export type ItinerarySummary = z.infer<typeof itinerarySummarySchema>;

export const itinerarySchema = itinerarySummarySchema.extend({
  content: z.string(),
  trip: z.record(z.string(), z.unknown()),
});
export type Itinerary = z.infer<typeof itinerarySchema>;

export const analyticsSchema = z.object({
  total_users: z.number(),
  users_by_plan: z.record(z.string(), z.number()),
  trips_by_day: z.array(z.object({ date: z.string(), trips: z.number() })),
  top_destinations: z.array(z.object({ destination: z.string(), trips: z.number() })),
  budget: z.object({
    trips: z.number(),
    avg: z.number(),
    min: z.number(),
    max: z.number(),
  }),
  preferred_start_dates: z.array(z.object({ date: z.string(), travelers: z.number() })),
});
export type Analytics = z.infer<typeof analyticsSchema>;

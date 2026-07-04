import Link from "next/link";
import { cookies } from "next/headers";

export default async function Home() {
  const cookieStore = await cookies();
  const loggedIn = cookieStore.has("access_token") || cookieStore.has("refresh_token");

  return (
    <div className="flex flex-1 flex-col items-center justify-center px-6 py-24 text-center">
      <h1 className="text-5xl font-bold tracking-tight text-slate-900">
        🌎 TravelBud
      </h1>
      <p className="mt-4 max-w-xl text-lg text-slate-600">
        Your all-in-one vacation planner: flights, hotels, and a personalized
        day-by-day itinerary — tailored to your interests and budget.
      </p>
      <div className="mt-8 flex gap-4">
        {loggedIn ? (
          <Link
            href="/plan"
            className="rounded-lg bg-sky-600 px-6 py-3 font-medium text-white hover:bg-sky-700"
          >
            Plan My Trip
          </Link>
        ) : (
          <>
            <Link
              href="/login"
              className="rounded-lg bg-sky-600 px-6 py-3 font-medium text-white hover:bg-sky-700"
            >
              Log in
            </Link>
            <Link
              href="/signup"
              className="rounded-lg border border-slate-300 bg-white px-6 py-3 font-medium text-slate-700 hover:bg-slate-100"
            >
              Sign up
            </Link>
          </>
        )}
      </div>
    </div>
  );
}

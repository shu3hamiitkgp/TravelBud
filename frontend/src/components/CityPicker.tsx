"use client";

import { useMemo, useState } from "react";
import airports from "@/lib/airports.json";
import { Input, Label } from "@/components/ui";

type Airport = { iata: string; city: string; name: string; country: string };

export type CitySelection = { city: string; iata: string };

export default function CityPicker({
  label,
  value,
  onChange,
  excludeIata,
}: {
  label: string;
  value: CitySelection | null;
  onChange: (v: CitySelection | null) => void;
  excludeIata?: string;
}) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (q.length < 2) return [];
    return (airports as Airport[])
      .filter(
        (a) =>
          a.iata !== excludeIata &&
          (a.city.toLowerCase().startsWith(q) || a.iata.toLowerCase() === q)
      )
      .slice(0, 8);
  }, [query, excludeIata]);

  return (
    <div className="relative">
      <Label>{label}</Label>
      <Input
        value={value ? `${value.city} (${value.iata})` : query}
        placeholder="Start typing a city…"
        onChange={(e) => {
          onChange(null);
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
      />
      {open && matches.length > 0 && !value && (
        <ul className="absolute z-10 mt-1 w-full overflow-hidden rounded-lg border border-slate-200 bg-white shadow-lg">
          {matches.map((a) => (
            <li key={a.iata}>
              <button
                type="button"
                className="w-full px-3 py-2 text-left text-sm hover:bg-sky-50"
                onMouseDown={() => {
                  onChange({ city: a.city, iata: a.iata });
                  setQuery("");
                  setOpen(false);
                }}
              >
                <span className="font-medium">{a.city}</span>{" "}
                <span className="text-slate-400">
                  ({a.iata}) · {a.name}, {a.country}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

import { Compass } from "lucide-react";
import Link from "next/link";

export default function Logo({ className = "" }: { className?: string }) {
  return (
    <Link
      href="/"
      className={`inline-flex items-center gap-2 font-bold tracking-tight ${className}`}
    >
      <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
        <Compass className="size-5" />
      </span>
      <span className="text-lg">
        Travel<span className="text-primary">Bud</span>
      </span>
    </Link>
  );
}

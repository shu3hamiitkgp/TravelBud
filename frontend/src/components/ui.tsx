// Thin compatibility layer over shadcn/ui so app pages share one look.
import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
} from "react";
import { Button as ShadButton } from "@/components/ui/button";
import { Card as ShadCard } from "@/components/ui/card";
import { Input as ShadInput } from "@/components/ui/input";

export function Button({
  variant = "primary",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" }) {
  return (
    <ShadButton variant={variant === "primary" ? "default" : "outline"} {...props} />
  );
}

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <ShadInput {...props} />;
}

export function Select({
  className = "",
  ...props
}: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={`border-input focus-visible:ring-ring/50 h-9 w-full rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-[3px] ${className}`}
      {...props}
    />
  );
}

export function Label({ children }: { children: ReactNode }) {
  return (
    <label className="mb-1.5 block text-sm font-medium text-foreground">
      {children}
    </label>
  );
}

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <ShadCard className={`gap-4 p-6 ${className}`}>{children}</ShadCard>;
}

export function ErrorText({ children }: { children: ReactNode }) {
  if (!children) return null;
  return <p className="text-sm text-destructive">{children}</p>;
}

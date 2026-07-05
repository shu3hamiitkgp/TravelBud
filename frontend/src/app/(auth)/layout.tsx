import Logo from "@/components/Logo";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center bg-gradient-to-b from-sky-100/60 via-background to-background px-6 py-16">
      <Logo className="mb-6" />
      <div className="w-full max-w-md">{children}</div>
    </div>
  );
}

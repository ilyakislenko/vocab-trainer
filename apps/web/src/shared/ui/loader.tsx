import { cn } from "@/shared/lib/utils";

export function Loader({ className }: { className?: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className={cn("flex items-center gap-2 text-sm text-muted-foreground", className)}
    >
      <span
        aria-hidden
        className="size-4 shrink-0 animate-spin rounded-full border-2 border-muted-foreground/25 border-t-muted-foreground"
      />
      <span>
        Just a moment
        <span aria-hidden className="inline-flex">
          <span>.</span>
          <span className="dot-fill-2">.</span>
          <span className="dot-fill-3">.</span>
        </span>
      </span>
    </div>
  );
}

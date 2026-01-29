"use client";

import { cn } from "@/lib/utils";

interface LoadingOverlayProps {
  isLoading: boolean;
  message?: string;
  className?: string;
}

export function LoadingOverlay({
  isLoading,
  message = "Loading...",
  className,
}: LoadingOverlayProps) {
  if (!isLoading) return null;

  return (
    <div
      className={cn(
        "absolute inset-0 z-50 flex flex-col items-center justify-center bg-background/80 backdrop-blur-sm",
        className
      )}
    >
      {/* Shimmer skeleton */}
      <div className="flex flex-col gap-4 w-64">
        <div className="h-4 w-full rounded-lg animate-shimmer" />
        <div className="h-4 w-3/4 rounded-lg animate-shimmer" />
        <div className="h-4 w-1/2 rounded-lg animate-shimmer" />
      </div>
      <p className="mt-6 text-sm text-muted-foreground">{message}</p>
    </div>
  );
}

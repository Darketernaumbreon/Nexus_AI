"use client";

import { cn } from "@/lib/utils";

interface SkeletonLoaderProps {
  rows?: number;
  className?: string;
}

export function SkeletonLoader({ rows = 3, className }: SkeletonLoaderProps) {
  return (
    <div className={cn("space-y-3", className)}>
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="h-4 rounded-lg animate-shimmer"
          style={{
            width: `${100 - i * 15}%`,
          }}
        />
      ))}
    </div>
  );
}

export function CardSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-border bg-card p-6 shadow-soft",
        className
      )}
    >
      <div className="h-6 w-1/3 rounded-lg animate-shimmer mb-4" />
      <SkeletonLoader rows={4} />
    </div>
  );
}

export function TableSkeleton({
  rows = 5,
  className,
}: {
  rows?: number;
  className?: string;
}) {
  return (
    <div className={cn("space-y-2", className)}>
      {/* Header */}
      <div className="flex gap-4 p-3 border-b border-border">
        <div className="h-4 w-1/4 rounded-lg animate-shimmer" />
        <div className="h-4 w-1/4 rounded-lg animate-shimmer" />
        <div className="h-4 w-1/4 rounded-lg animate-shimmer" />
        <div className="h-4 w-1/4 rounded-lg animate-shimmer" />
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 p-3">
          <div className="h-4 w-1/4 rounded-lg animate-shimmer" />
          <div className="h-4 w-1/4 rounded-lg animate-shimmer" />
          <div className="h-4 w-1/4 rounded-lg animate-shimmer" />
          <div className="h-4 w-1/4 rounded-lg animate-shimmer" />
        </div>
      ))}
    </div>
  );
}

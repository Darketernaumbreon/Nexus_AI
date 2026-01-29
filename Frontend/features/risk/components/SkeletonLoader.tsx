'use client';

import React from 'react';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent, CardHeader } from '@/components/ui/card';

/**
 * Props for SkeletonLoader component
 */
export interface SkeletonLoaderProps {
  /**
   * Type of skeleton to display
   */
  type?:
    | 'result-card'
    | 'history-list'
    | 'heatmap'
    | 'chart'
    | 'panel'
    | 'table';

  /**
   * Number of items to show
   */
  count?: number;

  /**
   * Custom class name
   */
  className?: string;

  /**
   * Show shimmer animation
   */
  shimmer?: boolean;
}

/**
 * SkeletonLoader Component
 *
 * Loading placeholder components for risk simulation UI
 *
 * **Features**:
 * - Multiple skeleton types
 * - Shimmer animation
 * - Responsive sizing
 * - Accessible placeholders
 *
 * **Types**:
 * - `result-card`: Risk result visualization
 * - `history-list`: Simulation history items
 * - `heatmap`: Map visualization
 * - `chart`: Chart placeholder
 * - `panel`: Control panel
 * - `table`: Data table
 *
 * **Usage**:
 * ```tsx
 * {isLoading ? (
 *   <SkeletonLoader type="result-card" count={3} />
 * ) : (
 *   <ResultCards results={results} />
 * )}
 * ```
 *
 * @reference NEXUS_AI_COMPREHENSIVE_DESIGN.md (Section 7: Loading States)
 */
export const SkeletonLoader = React.memo(
  ({
    type = 'result-card',
    count = 1,
    className = '',
    shimmer = true,
  }: SkeletonLoaderProps) => {
    const shimmerClass = shimmer ? 'animate-pulse' : '';

    const ResultCardSkeleton = () => (
      <Card className={shimmerClass}>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <Skeleton className="h-6 w-2/3 mb-2" />
              <Skeleton className="h-4 w-full" />
            </div>
            <Skeleton className="h-6 w-20" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Skeleton className="h-64 w-full rounded" />
            <div className="grid grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i}>
                  <Skeleton className="h-4 w-3/4 mb-2" />
                  <Skeleton className="h-6 w-full" />
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    );

    const HistoryListSkeleton = () => (
      <div className="space-y-3">
        {Array.from({ length: count }).map((_, i) => (
          <Card key={i} className={shimmerClass}>
            <CardContent className="pt-6">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <Skeleton className="h-6 w-2/3" />
                    <Skeleton className="h-6 w-16 rounded" />
                  </div>
                  <div className="grid grid-cols-4 gap-4 mb-3">
                    {[1, 2, 3, 4].map((j) => (
                      <div key={j}>
                        <Skeleton className="h-4 w-3/4 mb-1" />
                        <Skeleton className="h-5 w-full" />
                      </div>
                    ))}
                  </div>
                  <Skeleton className="h-4 w-1/2" />
                </div>
                <div className="flex gap-2">
                  <Skeleton className="h-10 w-10 rounded" />
                  <Skeleton className="h-10 w-10 rounded" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );

    const HeatmapSkeleton = () => (
      <Card className={shimmerClass}>
        <CardHeader>
          <Skeleton className="h-6 w-2/3 mb-2" />
          <Skeleton className="h-4 w-1/2" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-96 w-full rounded mb-4" />
          <div className="grid grid-cols-3 gap-3">
            {[1, 2, 3].map((i) => (
              <div key={i}>
                <Skeleton className="h-4 w-2/3 mb-2" />
                <Skeleton className="h-8 w-full" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );

    const ChartSkeleton = () => (
      <Card className={shimmerClass}>
        <CardHeader>
          <Skeleton className="h-6 w-2/3 mb-2" />
          <Skeleton className="h-4 w-1/2" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-80 w-full rounded mb-4" />
          <div className="flex gap-3">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="flex-1 h-16 rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    );

    const PanelSkeleton = () => (
      <Card className={shimmerClass}>
        <CardHeader>
          <Skeleton className="h-6 w-1/2 mb-2" />
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i}>
                <Skeleton className="h-4 w-1/3 mb-2" />
                <Skeleton className="h-10 w-full rounded" />
              </div>
            ))}
            <Skeleton className="h-10 w-full rounded" />
          </div>
        </CardContent>
      </Card>
    );

    const TableSkeleton = () => (
      <Card className={shimmerClass}>
        <CardHeader>
          <Skeleton className="h-6 w-2/3" />
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {/* Header */}
            <div className="grid grid-cols-5 gap-4 pb-3 border-b">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-4 w-full" />
              ))}
            </div>
            {/* Rows */}
            {Array.from({ length: count }).map((_, i) => (
              <div key={i} className="grid grid-cols-5 gap-4 py-3">
                {[1, 2, 3, 4, 5].map((j) => (
                  <Skeleton key={j} className="h-4 w-full" />
                ))}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );

    // Select skeleton type
    let skeleton: React.ReactNode;

    switch (type) {
      case 'result-card':
        skeleton = Array.from({ length: count }).map((_, i) => (
          <ResultCardSkeleton key={i} />
        ));
        break;

      case 'history-list':
        skeleton = <HistoryListSkeleton />;
        break;

      case 'heatmap':
        skeleton = <HeatmapSkeleton />;
        break;

      case 'chart':
        skeleton = <ChartSkeleton />;
        break;

      case 'panel':
        skeleton = <PanelSkeleton />;
        break;

      case 'table':
        skeleton = <TableSkeleton />;
        break;

      default:
        skeleton = <ResultCardSkeleton />;
    }

    return (
      <div className={`space-y-4 ${className}`} role="status" aria-label="Loading...">
        {skeleton}
      </div>
    );
  }
);

SkeletonLoader.displayName = 'SkeletonLoader';

export default SkeletonLoader;

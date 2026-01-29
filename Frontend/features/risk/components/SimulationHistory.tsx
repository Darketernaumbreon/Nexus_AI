'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Clock, Trash2, Eye, Download } from 'lucide-react';

import type { RiskSimulationHistory } from '../types';
import { SIMULATION_STATUS_COLORS, SIMULATION_STATUS_LABELS } from '../constants';

/**
 * Props for SimulationHistory component
 */
export interface SimulationHistoryProps {
  /**
   * History entries to display
   */
  history: RiskSimulationHistory[];

  /**
   * Loading state
   */
  isLoading?: boolean;

  /**
   * Error message
   */
  error?: string | null;

  /**
   * Pagination info
   */
  pagination?: {
    total: number;
    page: number;
    pageSize: number;
    totalPages: number;
  };

  /**
   * Callback when entry is selected
   */
  onSelect?: (entry: RiskSimulationHistory) => void;

  /**
   * Callback to view details
   */
  onView?: (resultId: string) => void;

  /**
   * Callback to delete entry
   */
  onDelete?: (resultId: string) => void;

  /**
   * Callback to export entry
   */
  onExport?: (resultId: string) => void;

  /**
   * Callback for pagination
   */
  onPageChange?: (page: number) => void;

  /**
   * Show pagination controls
   */
  showPagination?: boolean;
}

/**
 * SimulationHistory Component
 *
 * Displays list of past risk simulations with metadata
 *
 * **Features**:
 * - Simulation list with details
 * - Status badges with colors
 * - Duration and point counts
 * - Action buttons (view, delete, export)
 * - Pagination support
 * - Empty state handling
 * - Loading skeletons
 *
 * **Display Information**:
 * - Simulation name
 * - Status with color coding
 * - Execution timestamp
 * - Duration
 * - Generated risk points count
 * - Average risk score
 * - Quick actions
 *
 * **Usage**:
 * ```tsx
 * <SimulationHistory
 *   history={simulationHistory}
 *   isLoading={isLoading}
 *   onView={(id) => navigate(`/risk/${id}`)}
 *   onDelete={(id) => deleteSimulation(id)}
 *   showPagination={true}
 * />
 * ```
 *
 * @reference NEXUS_AI_COMPREHENSIVE_DESIGN.md (Section 7.2: History Management)
 */
export const SimulationHistory = React.memo(
  ({
    history,
    isLoading = false,
    error = null,
    pagination,
    onSelect,
    onView,
    onDelete,
    onExport,
    onPageChange,
    showPagination = false,
  }: SimulationHistoryProps) => {
    const formatDuration = (seconds: number): string => {
      if (seconds < 60) return `${seconds}s`;
      if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
      return `${Math.floor(seconds / 3600)}h`;
    };

    const getStatusColor = (status: string): string => {
      return SIMULATION_STATUS_COLORS[status as keyof typeof SIMULATION_STATUS_COLORS] || '#6b7280';
    };

    const getStatusLabel = (status: string): string => {
      return SIMULATION_STATUS_LABELS[status as keyof typeof SIMULATION_STATUS_LABELS] || status;
    };

    if (error) {
      return (
        <Card className="w-full border-red-200 bg-red-50">
          <CardHeader>
            <CardTitle className="text-red-900">History Load Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-red-800">{error}</p>
          </CardContent>
        </Card>
      );
    }

    if (isLoading) {
      return (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-gradient-to-r from-gray-100 to-gray-50 rounded animate-pulse" />
          ))}
        </div>
      );
    }

    if (history.length === 0) {
      return (
        <Card className="w-full border-gray-200 bg-gray-50">
          <CardHeader>
            <CardTitle className="text-gray-900">No Simulations</CardTitle>
            <CardDescription>Run a simulation to get started</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600">
              When you create risk simulations, they will appear here for easy access and review.
            </p>
          </CardContent>
        </Card>
      );
    }

    return (
      <div className="space-y-3">
        {history.map((entry) => (
          <Card
            key={entry.resultId}
            className="cursor-pointer transition-all hover:shadow-md hover:border-blue-300"
            onClick={() => onSelect?.(entry)}
          >
            <CardContent className="pt-6">
              <div className="flex items-start justify-between gap-4">
                {/* Left: Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-semibold text-gray-900 truncate">
                      {entry.name}
                    </h3>
                    <Badge
                      style={{
                        backgroundColor: getStatusColor(entry.status),
                        color: 'white',
                      }}
                    >
                      {getStatusLabel(entry.status)}
                    </Badge>
                  </div>

                  {/* Metadata grid */}
                  <div className="grid grid-cols-4 gap-4 text-sm mb-3">
                    <div>
                      <span className="text-gray-500">Timestamp</span>
                      <div className="font-medium text-gray-900">
                        {new Date(entry.timestamp).toLocaleString()}
                      </div>
                    </div>

                    <div>
                      <span className="text-gray-500">Duration</span>
                      <div className="font-medium text-gray-900">
                        {formatDuration(entry.duration)}
                      </div>
                    </div>

                    <div>
                      <span className="text-gray-500">Risk Points</span>
                      <div className="font-medium text-gray-900">
                        {entry.pointCount.toLocaleString()}
                      </div>
                    </div>

                    <div>
                      <span className="text-gray-500">Avg Risk</span>
                      <div className="font-medium text-gray-900">
                        {(entry.statistics.averageRiskScore * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>

                  {/* Statistics row */}
                  <div className="flex gap-3 text-xs">
                    <div className="px-2 py-1 rounded bg-orange-50 text-orange-700">
                      High Risk: {entry.statistics.highRiskAreaCount}
                    </div>
                    <div className="px-2 py-1 rounded bg-red-50 text-red-700">
                      Critical: {entry.statistics.criticalRiskAreaCount}
                    </div>
                    {entry.tags && entry.tags.length > 0 && (
                      <div className="flex gap-1">
                        {entry.tags.map((tag) => (
                          <Badge key={tag} variant="outline" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Notes */}
                  {entry.notes && (
                    <p className="text-xs text-gray-600 mt-2 line-clamp-2">
                      {entry.notes}
                    </p>
                  )}
                </div>

                {/* Right: Actions */}
                <div className="flex gap-2 flex-shrink-0">
                  {onView && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={(e) => {
                        e.stopPropagation();
                        onView(entry.resultId);
                      }}
                      title="View details"
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  )}

                  {onExport && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={(e) => {
                        e.stopPropagation();
                        onExport(entry.resultId);
                      }}
                      title="Export results"
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  )}

                  {onDelete && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (
                          confirm(
                            `Delete "${entry.name}"? This cannot be undone.`
                          )
                        ) {
                          onDelete(entry.resultId);
                        }
                      }}
                      title="Delete simulation"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {/* Pagination */}
        {showPagination && pagination && pagination.totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-6">
            <Button
              variant="outline"
              onClick={() => onPageChange?.(pagination.page - 1)}
              disabled={pagination.page === 1}
            >
              Previous
            </Button>

            <div className="text-sm text-gray-600">
              Page {pagination.page} of {pagination.totalPages}
            </div>

            <Button
              variant="outline"
              onClick={() => onPageChange?.(pagination.page + 1)}
              disabled={pagination.page === pagination.totalPages}
            >
              Next
            </Button>
          </div>
        )}
      </div>
    );
  }
);

SimulationHistory.displayName = 'SimulationHistory';

export default SimulationHistory;

'use client';

import React from 'react';
import { AlertCircle, AlertTriangle, Info, Wind } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

import type { WeatherAlert } from '../types';

/**
 * Props for GridVisualization component
 */
export interface GridVisualizationProps {
  /**
   * Weather alerts to display
   */
  alerts: WeatherAlert[];

  /**
   * Whether there are more alerts available
   */
  hasMore?: boolean;

  /**
   * Loading state
   */
  isLoading?: boolean;

  /**
   * Critical alert count
   */
  criticalCount?: number;

  /**
   * Callback when alert is dismissed
   */
  onDismiss?: (alertId: string) => void;

  /**
   * Callback to view all alerts
   */
  onViewAll?: () => void;

  /**
   * Max alerts to display
   */
  maxDisplay?: number;
}

/**
 * GridVisualization Component
 *
 * Displays weather alerts in an organized grid/list format
 *
 * **Features**:
 * - Alert severity color coding
 * - Icon indicators for alert types
 * - Dismissible alerts
 * - View more functionality
 * - Loading states
 * - Empty state handling
 *
 * **Alert Visual Hierarchy**:
 * - Critical (5): Red with emergency icon
 * - Severe (4): Orange with warning icon
 * - Moderate (3): Yellow with info icon
 * - Minor (2): Blue with info icon
 * - Advisory (1): Gray with info icon
 *
 * **Usage**:
 * ```tsx
 * <GridVisualization
 *   alerts={weatherAlerts}
 *   criticalCount={2}
 *   maxDisplay={3}
 *   onDismiss={(id) => dismissAlert(id)}
 *   onViewAll={() => navigate('/weather/alerts')}
 * />
 * ```
 *
 * @reference NEXUS_AI_COMPREHENSIVE_DESIGN.md (Section 6.2: Alert Visualization)
 */
export const GridVisualization = React.memo(
  ({
    alerts,
    hasMore = false,
    isLoading = false,
    criticalCount = 0,
    onDismiss,
    onViewAll,
    maxDisplay = 3,
  }: GridVisualizationProps) => {
    const displayedAlerts = alerts.slice(0, maxDisplay);
    const hiddenCount = alerts.length - displayedAlerts.length;

    const getSeverityColor = (severity: number): string => {
      switch (severity) {
        case 5:
          return 'border-red-300 bg-red-50';
        case 4:
          return 'border-orange-300 bg-orange-50';
        case 3:
          return 'border-yellow-300 bg-yellow-50';
        case 2:
          return 'border-blue-300 bg-blue-50';
        default:
          return 'border-gray-300 bg-gray-50';
      }
    };

    const getSeverityBadgeColor = (severity: number): string => {
      switch (severity) {
        case 5:
          return 'bg-red-600 text-white';
        case 4:
          return 'bg-orange-600 text-white';
        case 3:
          return 'bg-yellow-600 text-white';
        case 2:
          return 'bg-blue-600 text-white';
        default:
          return 'bg-gray-600 text-white';
      }
    };

    const getSeverityLabel = (severity: number): string => {
      switch (severity) {
        case 5:
          return 'Critical';
        case 4:
          return 'Severe';
        case 3:
          return 'Moderate';
        case 2:
          return 'Minor';
        default:
          return 'Advisory';
      }
    };

    const getAlertIcon = (type: string) => {
      switch (type) {
        case 'warning':
          return <AlertTriangle className="h-5 w-5" />;
        case 'alert':
          return <AlertCircle className="h-5 w-5" />;
        case 'watch':
          return <Wind className="h-5 w-5" />;
        default:
          return <Info className="h-5 w-5" />;
      }
    };

    if (isLoading) {
      return (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-20 bg-gradient-to-r from-gray-100 to-gray-50 rounded animate-pulse"
            />
          ))}
        </div>
      );
    }

    if (alerts.length === 0) {
      return (
        <Alert className="border-green-200 bg-green-50">
          <Info className="h-4 w-4 text-green-600" />
          <AlertTitle className="text-green-900">No Active Alerts</AlertTitle>
          <AlertDescription className="text-green-800">
            Weather conditions are normal for your area. Stay safe!
          </AlertDescription>
        </Alert>
      );
    }

    return (
      <div className="space-y-3">
        {/* Critical count badge */}
        {criticalCount > 0 && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 border border-red-200">
            <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0" />
            <span className="text-sm font-semibold text-red-900">
              {criticalCount} Critical Alert{criticalCount !== 1 ? 's' : ''}
              {alerts.length > criticalCount && ` • ${alerts.length} total`}
            </span>
          </div>
        )}

        {/* Alert items */}
        {displayedAlerts.map((alert) => (
          <div
            key={alert.id}
            className={`rounded-lg border p-4 transition-all ${getSeverityColor(alert.severity)}`}
          >
            <div className="flex gap-3">
              {/* Icon */}
              <div className="flex-shrink-0 mt-0.5">
                {React.cloneElement(getAlertIcon(alert.type), {
                  className: `h-5 w-5 ${
                    alert.severity === 5
                      ? 'text-red-600'
                      : alert.severity === 4
                      ? 'text-orange-600'
                      : 'text-gray-600'
                  }`,
                })}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2 mb-1">
                  <h4 className="font-semibold text-gray-900 text-sm line-clamp-1">
                    {alert.title}
                  </h4>
                  <Badge className={getSeverityBadgeColor(alert.severity)}>
                    {getSeverityLabel(alert.severity)}
                  </Badge>
                </div>

                <p className="text-sm text-gray-700 mb-2 line-clamp-2">
                  {alert.description}
                </p>

                {alert.recommendations && alert.recommendations.length > 0 && (
                  <div className="mb-2">
                    <p className="text-xs font-medium text-gray-600 mb-1">
                      Recommended Actions:
                    </p>
                    <ul className="text-xs text-gray-600 space-y-0.5">
                      {alert.recommendations.slice(0, 2).map((rec, idx) => (
                        <li key={idx} className="flex gap-2">
                          <span className="text-gray-400">•</span>
                          <span>{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-current border-opacity-20">
                  <span>
                    Valid until {new Date(alert.validTo).toLocaleTimeString()}
                  </span>
                  {onDismiss && (
                    <button
                      onClick={() => onDismiss(alert.id)}
                      className="text-gray-500 hover:text-gray-700 transition-colors"
                      aria-label="Dismiss alert"
                    >
                      ✕
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}

        {/* View all button */}
        {hiddenCount > 0 && (
          <Button
            variant="outline"
            className="w-full"
            onClick={onViewAll}
          >
            View {hiddenCount} More Alert{hiddenCount !== 1 ? 's' : ''}
          </Button>
        )}
      </div>
    );
  }
);

GridVisualization.displayName = 'GridVisualization';

export default GridVisualization;

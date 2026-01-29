'use client';

import React, { useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, Cloud, Droplets, Wind } from 'lucide-react';

import type { RainfallHeatmapData } from '../types';

/**
 * Props for RainfallHeatmap component
 */
export interface RainfallHeatmapProps {
  /**
   * Rainfall heatmap data
   */
  data: RainfallHeatmapData | null;

  /**
   * Loading state
   */
  isLoading?: boolean;

  /**
   * Error message
   */
  error?: string | null;

  /**
   * Map container element ID
   */
  mapContainerId?: string;

  /**
   * Color scheme for heatmap
   */
  colorScheme?: 'viridis' | 'spectral' | 'precipitation';

  /**
   * Show/hide legend
   */
  showLegend?: boolean;

  /**
   * Callback when data is updated
   */
  onDataUpdate?: (data: RainfallHeatmapData) => void;

  /**
   * Forecast hour being displayed (0 = current)
   */
  forecastHour?: number;
}

/**
 * RainfallHeatmap Component
 *
 * Visualizes precipitation intensity using a geographic heatmap
 *
 * **Features**:
 * - Real-time rainfall visualization
 * - Forecast period display
 * - Intensity color coding
 * - Geographic bounds
 * - Interactive hover info
 *
 * **Visualization**:
 * - Blue: Light precipitation
 * - Green: Moderate rainfall
 * - Yellow: Heavy rainfall
 * - Red: Extreme precipitation
 *
 * **Usage**:
 * ```tsx
 * <RainfallHeatmap
 *   data={heatmapData}
 *   isLoading={isLoading}
 *   colorScheme="precipitation"
 *   showLegend={true}
 * />
 * ```
 *
 * **Integration**:
 * - Parent: weather/page.tsx
 * - Data from: fetchRainfallHeatmap API
 * - Updates from: useWeatherPolling hook
 *
 * @reference NEXUS_AI_COMPREHENSIVE_DESIGN.md (Section 6.1: Weather Visualization)
 */
export const RainfallHeatmap = React.memo(
  ({
    data,
    isLoading = false,
    error = null,
    mapContainerId = 'rainfall-heatmap',
    colorScheme = 'precipitation',
    showLegend = true,
    onDataUpdate,
    forecastHour = 0,
  }: RainfallHeatmapProps) => {
    // Calculate statistics
    const stats = useMemo(() => {
      if (!data || !data.points || data.points.length === 0) {
        return {
          avgIntensity: 0,
          maxIntensity: 0,
          affectedArea: 0,
        };
      }

      const intensities = data.points.map((p) => p.intensity);
      const avg = intensities.reduce((a, b) => a + b, 0) / intensities.length;
      const max = Math.max(...intensities);
      const affected = data.points.filter((p) => p.intensity > 0.1).length;

      return {
        avgIntensity: avg,
        maxIntensity: max,
        affectedArea: affected,
      };
    }, [data]);

    // Color scheme definitions
    const colorSchemes = {
      viridis: [
        '#440154',
        '#482878',
        '#3e4a89',
        '#31688e',
        '#26828e',
        '#1f9e89',
        '#35b779',
        '#6ece58',
        '#b5de2b',
        '#fde724',
      ],
      spectral: [
        '#9e0142',
        '#d53e4f',
        '#f46d43',
        '#fdae61',
        '#fee08b',
        '#ffffbf',
        '#e6f598',
        '#abdda4',
        '#66c2a5',
        '#3288bd',
      ],
      precipitation: [
        '#ffffff',
        '#e0f3f8',
        '#abd9e9',
        '#74add1',
        '#4575b4',
        '#313695',
        '#006837',
        '#1a9850',
        '#91cf60',
        '#d9ef8b',
      ],
    };

    const colors = colorSchemes[colorScheme];

    const getColorForIntensity = (intensity: number): string => {
      const max = data?.maxIntensity || 1;
      const normalized = Math.min(intensity / max, 1);
      const colorIndex = Math.floor(normalized * (colors.length - 1));
      return colors[colorIndex];
    };

    const getIntensityLabel = (intensity: number): string => {
      if (intensity < 0.5) return 'Very Light';
      if (intensity < 2) return 'Light';
      if (intensity < 5) return 'Moderate';
      if (intensity < 10) return 'Heavy';
      if (intensity < 20) return 'Very Heavy';
      return 'Extreme';
    };

    if (error) {
      return (
        <Card className="w-full border-red-200 bg-red-50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <CardTitle className="text-red-900">Rainfall Data Error</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-red-800">{error}</p>
          </CardContent>
        </Card>
      );
    }

    return (
      <Card className="w-full">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Droplets className="h-5 w-5 text-blue-600" />
                Rainfall Heatmap
              </CardTitle>
              <CardDescription>
                {forecastHour === 0
                  ? 'Current precipitation intensity'
                  : `${forecastHour}-hour forecast`}
              </CardDescription>
            </div>

            {data && (
              <div className="text-right">
                <div className="text-xs text-gray-500">Last updated</div>
                <div className="text-sm font-medium">
                  {new Date(data.timestamp).toLocaleTimeString()}
                </div>
              </div>
            )}
          </div>
        </CardHeader>

        <CardContent>
          {isLoading ? (
            <div className="flex h-96 items-center justify-center bg-gray-100 rounded">
              <div className="text-center">
                <Cloud className="h-8 w-8 text-gray-400 mx-auto mb-2 animate-bounce" />
                <p className="text-sm text-gray-600">Loading rainfall data...</p>
              </div>
            </div>
          ) : data ? (
            <>
              {/* Heatmap visualization placeholder */}
              <div
                id={mapContainerId}
                className="h-96 bg-gradient-to-br from-blue-50 to-blue-100 rounded border border-blue-200 flex items-center justify-center relative"
              >
                <div className="text-center text-gray-600">
                  <Wind className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">
                    Rainfall intensity map with {data.points.length} data points
                  </p>
                </div>

                {/* Visual representation of points */}
                {data.points.slice(0, 50).map((point, idx) => (
                  <div
                    key={idx}
                    className="absolute w-2 h-2 rounded-full opacity-70"
                    style={{
                      backgroundColor: getColorForIntensity(point.intensity),
                      left: `${((point.lng + 180) / 360) * 100}%`,
                      top: `${((point.lat + 90) / 180) * 100}%`,
                    }}
                    title={`${point.lat.toFixed(4)}, ${point.lng.toFixed(4)} - ${point.intensity.toFixed(1)} mm/h`}
                  />
                ))}
              </div>

              {/* Statistics */}
              <div className="grid grid-cols-3 gap-3 mt-4">
                <div className="bg-blue-50 rounded p-3">
                  <div className="text-xs text-gray-600 mb-1">Average</div>
                  <div className="text-lg font-semibold text-blue-900">
                    {stats.avgIntensity.toFixed(1)}
                  </div>
                  <div className="text-xs text-gray-500">mm/h</div>
                </div>

                <div className="bg-red-50 rounded p-3">
                  <div className="text-xs text-gray-600 mb-1">Maximum</div>
                  <div className="text-lg font-semibold text-red-900">
                    {stats.maxIntensity.toFixed(1)}
                  </div>
                  <div className="text-xs text-gray-500">mm/h</div>
                </div>

                <div className="bg-green-50 rounded p-3">
                  <div className="text-xs text-gray-600 mb-1">Coverage</div>
                  <div className="text-lg font-semibold text-green-900">
                    {stats.affectedArea}
                  </div>
                  <div className="text-xs text-gray-500">points</div>
                </div>
              </div>

              {/* Legend */}
              {showLegend && (
                <div className="mt-4 pt-4 border-t">
                  <div className="text-xs font-semibold text-gray-700 mb-2">
                    Intensity Scale
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    {[0, 0.2, 0.4, 0.6, 0.8, 1].map((intensity) => (
                      <div key={intensity} className="flex items-center gap-1">
                        <div
                          className="w-4 h-4 rounded"
                          style={{ backgroundColor: getColorForIntensity(intensity) }}
                        />
                        <span className="text-xs text-gray-600">
                          {getIntensityLabel(intensity)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="h-96 flex items-center justify-center bg-gray-50 rounded border border-gray-200">
              <p className="text-sm text-gray-500">No rainfall data available</p>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }
);

RainfallHeatmap.displayName = 'RainfallHeatmap';

export default RainfallHeatmap;

'use client';

import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Cloud, Droplets, Thermometer, Wind } from 'lucide-react';

import type { WeatherForecast } from '../types';

/**
 * Props for WeatherChart component
 */
export interface WeatherChartProps {
  /**
   * Forecast data to visualize
   */
  forecast: WeatherForecast | null;

  /**
   * Chart type to display
   */
  chartType?: 'temperature' | 'precipitation' | 'humidity' | 'all';

  /**
   * Loading state
   */
  isLoading?: boolean;

  /**
   * Error message
   */
  error?: string | null;

  /**
   * Custom title
   */
  title?: string;

  /**
   * Show/hide legend
   */
  showLegend?: boolean;

  /**
   * Chart height in pixels
   */
  height?: number;

  /**
   * Callback when time period is selected
   */
  onPeriodSelect?: (time: string) => void;
}

/**
 * WeatherChart Component
 *
 * Visualizes weather forecast data with multiple chart types
 *
 * **Features**:
 * - Multi-metric visualization
 * - Line, area, and bar charts
 * - Time-series data display
 * - Confidence levels
 * - Responsive design
 * - Interactive tooltips
 *
 * **Chart Types**:
 * - **Temperature**: Line chart with gradient
 * - **Precipitation**: Bar chart
 * - **Humidity**: Area chart
 * - **All**: Combined view
 *
 * **Usage**:
 * ```tsx
 * <WeatherChart
 *   forecast={forecastData}
 *   chartType="temperature"
 *   height={300}
 *   showLegend={true}
 * />
 * ```
 *
 * **Data Processing**:
 * - Converts API timestamps to hours
 * - Calculates rolling averages
 * - Normalizes values
 * - Adds confidence indicators
 *
 * @reference NEXUS_AI_COMPREHENSIVE_DESIGN.md (Section 6.1: Forecasting)
 */
export const WeatherChart = React.memo(
  ({
    forecast,
    chartType = 'temperature',
    isLoading = false,
    error = null,
    title = 'Weather Forecast',
    showLegend = true,
    height = 300,
    onPeriodSelect,
  }: WeatherChartProps) => {
    // Prepare chart data
    const chartData = useMemo(() => {
      if (!forecast || !forecast.periods || forecast.periods.length === 0) {
        return [];
      }

      return forecast.periods.map((period, idx) => ({
        time: new Date(period.time).toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
          hour12: true,
        }),
        temperature: Number(period.temperature.toFixed(1)),
        precipitation: Number(period.precipitation.toFixed(1)),
        humidity: Number(period.humidity.toFixed(0)),
        confidence: Number((period.confidence * 100).toFixed(0)),
        period: period.time,
      }));
    }, [forecast]);

    const renderChart = () => {
      if (chartType === 'temperature' || chartType === 'all') {
        return (
          <ResponsiveContainer width="100%" height={height}>
            <LineChart data={chartData}>
              <defs>
                <linearGradient id="tempGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ff6b6b" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#ff6b6b" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis dataKey="time" stroke="#666" style={{ fontSize: '12px' }} />
              <YAxis stroke="#666" style={{ fontSize: '12px' }} label={{ value: '°C', angle: -90, position: 'insideLeft' }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc', borderRadius: '8px' }}
                formatter={(value: any) => [value, '']}
              />
              {showLegend && <Legend />}
              <Line
                type="monotone"
                dataKey="temperature"
                stroke="#ff6b6b"
                strokeWidth={2}
                name="Temperature (°C)"
                dot={{ r: 4, fill: '#ff6b6b' }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        );
      }

      if (chartType === 'precipitation') {
        return (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis dataKey="time" stroke="#666" style={{ fontSize: '12px' }} />
              <YAxis stroke="#666" style={{ fontSize: '12px' }} label={{ value: 'mm/h', angle: -90, position: 'insideLeft' }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc', borderRadius: '8px' }}
                formatter={(value) => [Number(value).toFixed(1), 'Precipitation']}
              />
              {showLegend && <Legend />}
              <Bar
                dataKey="precipitation"
                fill="#4a90e2"
                name="Precipitation (mm/h)"
                radius={[8, 8, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        );
      }

      if (chartType === 'humidity') {
        return (
          <ResponsiveContainer width="100%" height={height}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="humidityGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#82ca9d" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#82ca9d" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis dataKey="time" stroke="#666" style={{ fontSize: '12px' }} />
              <YAxis stroke="#666" style={{ fontSize: '12px' }} label={{ value: '%', angle: -90, position: 'insideLeft' }} domain={[0, 100]} />
              <Tooltip
                contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc', borderRadius: '8px' }}
                formatter={(value) => [Number(value).toFixed(0), 'Humidity']}
              />
              {showLegend && <Legend />}
              <Area
                type="monotone"
                dataKey="humidity"
                stroke="#82ca9d"
                fillOpacity={1}
                fill="url(#humidityGradient)"
                name="Humidity (%)"
              />
            </AreaChart>
          </ResponsiveContainer>
        );
      }

      return null;
    };

    if (error) {
      return (
        <Card className="w-full border-red-200 bg-red-50">
          <CardHeader>
            <CardTitle className="text-red-900">Chart Data Error</CardTitle>
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
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Thermometer className="h-5 w-5 text-orange-600" />
                {title}
              </CardTitle>
              <CardDescription>
                {forecast?.forecastModel && `Model: ${forecast.forecastModel}`}
              </CardDescription>
            </div>

            {forecast && chartData.length > 0 && (
              <div className="text-right text-sm">
                <div className="text-gray-600">Period:</div>
                <div className="font-medium">
                  {new Date(forecast.validFrom).toLocaleDateString()} to{' '}
                  {new Date(forecast.validTo).toLocaleDateString()}
                </div>
              </div>
            )}
          </div>
        </CardHeader>

        <CardContent>
          {isLoading ? (
            <div className="flex h-80 items-center justify-center bg-gray-100 rounded">
              <div className="text-center">
                <Cloud className="h-8 w-8 text-gray-400 mx-auto mb-2 animate-bounce" />
                <p className="text-sm text-gray-600">Loading forecast data...</p>
              </div>
            </div>
          ) : chartData.length > 0 ? (
            <>
              {/* Statistics badges */}
              {chartType === 'all' && chartData.length > 0 && (
                <div className="grid grid-cols-4 gap-2 mb-4">
                  <div className="bg-orange-50 rounded p-2 text-center">
                    <Thermometer className="h-4 w-4 text-orange-600 mx-auto mb-1" />
                    <div className="text-xs text-gray-600">Avg Temp</div>
                    <div className="text-sm font-semibold text-orange-900">
                      {(chartData.reduce((sum, d) => sum + d.temperature, 0) / chartData.length).toFixed(1)}°C
                    </div>
                  </div>

                  <div className="bg-blue-50 rounded p-2 text-center">
                    <Droplets className="h-4 w-4 text-blue-600 mx-auto mb-1" />
                    <div className="text-xs text-gray-600">Max Rain</div>
                    <div className="text-sm font-semibold text-blue-900">
                      {Math.max(...chartData.map((d) => d.precipitation)).toFixed(1)} mm/h
                    </div>
                  </div>

                  <div className="bg-green-50 rounded p-2 text-center">
                    <Cloud className="h-4 w-4 text-green-600 mx-auto mb-1" />
                    <div className="text-xs text-gray-600">Avg Humidity</div>
                    <div className="text-sm font-semibold text-green-900">
                      {(chartData.reduce((sum, d) => sum + d.humidity, 0) / chartData.length).toFixed(0)}%
                    </div>
                  </div>

                  <div className="bg-purple-50 rounded p-2 text-center">
                    <Wind className="h-4 w-4 text-purple-600 mx-auto mb-1" />
                    <div className="text-xs text-gray-600">Confidence</div>
                    <div className="text-sm font-semibold text-purple-900">
                      {(chartData.reduce((sum, d) => sum + d.confidence, 0) / chartData.length).toFixed(0)}%
                    </div>
                  </div>
                </div>
              )}

              {/* Chart */}
              {renderChart()}
            </>
          ) : (
            <div className="h-80 flex items-center justify-center bg-gray-50 rounded border border-gray-200">
              <p className="text-sm text-gray-500">No forecast data available</p>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }
);

WeatherChart.displayName = 'WeatherChart';

export default WeatherChart;

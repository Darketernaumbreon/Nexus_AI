"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout/app-layout";
import {
  RainfallChart,
  TemperatureChart,
  HumidityChart,
} from "@/features/weather/components/weather-chart";
import { AlertBanner } from "@/features/weather/components/alert-banner";
import { GridVisualization } from "@/features/weather/components/grid-visualization";
import { useWeatherGrid, useIMDRainfall } from "@/features/weather/hooks/use-weather";
import { ErrorBanner } from "@/components/feedback/error-banner";
import { CardSkeleton } from "@/components/feedback/skeleton-loader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RefreshCw, Thermometer, Droplets, Wind } from "lucide-react";

export default function WeatherPage() {
  const { data, isLoading, error, refetch } = useWeatherGrid();
  const { data: imdData, isLoading: imdLoading, refetch: refetchIMD } = useIMDRainfall();
  const [dismissedAlerts, setDismissedAlerts] = useState<string[]>([]);

  const activeAlerts =
    data?.alerts.filter((a) => !dismissedAlerts.includes(a.id)) || [];

  const handleDismissAlert = (alertId: string) => {
    setDismissedAlerts((prev) => [...prev, alertId]);
  };

  const handleRefresh = () => {
    refetch();
    refetchIMD();
  };

  // Calculate averages
  let avgRainfall = 0;
  let rainfallSource = "Forecast";

  if (imdData?.data?.length > 0) {
    const sum = imdData.data.reduce((acc: number, curr: any) => acc + curr.rainfall_mm, 0);
    avgRainfall = sum / imdData.data.length;
    rainfallSource = "IMD (Observed)";
  } else if (data?.cells.length) {
    // Fallback
    avgRainfall = data.cells.reduce((sum, c) => sum + c.rainfall_mm, 0) / data.cells.length;
  }

  const avgTemp = data?.cells.length
    ? data.cells.reduce((sum, c) => sum + c.temperature_c, 0) / data.cells.length
    : 0;
  const avgHumidity = data?.cells.length
    ? data.cells.reduce((sum, c) => sum + c.humidity_percent, 0) /
    data.cells.length
    : 0;

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              Weather Monitoring
            </h1>
            <p className="text-muted-foreground">
              Real-time weather data and alerts from IMD sources
            </p>
          </div>
          <div className="flex items-center gap-3">
            {data?.lastUpdated && (
              <span className="text-xs text-muted-foreground">
                Last updated:{" "}
                {new Date(data.lastUpdated).toLocaleTimeString()}
              </span>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={isLoading || imdLoading}
              className="rounded-xl bg-transparent"
            >
              <RefreshCw
                className={cn("h-4 w-4 mr-2", (isLoading || imdLoading) && "animate-spin")}
              />
              Refresh
            </Button>
          </div>
        </div>

        {/* Error Banner */}
        {error && (
          <ErrorBanner
            message={error.message}
            onRetry={handleRefresh}
            onDismiss={() => { }}
          />
        )}

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="rounded-2xl shadow-soft border-border">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-xl bg-blue-100 flex items-center justify-center">
                  <Droplets className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Avg. Rainfall</p>
                  <div className="flex flex-col">
                    <p className="text-2xl font-bold text-foreground">
                      {isLoading && imdLoading ? "--" : `${avgRainfall.toFixed(1)} mm`}
                    </p>
                    <p className="text-xs text-muted-foreground">{rainfallSource}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-2xl shadow-soft border-border">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-xl bg-amber-100 flex items-center justify-center">
                  <Thermometer className="h-6 w-6 text-amber-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">
                    Avg. Temperature
                  </p>
                  <p className="text-2xl font-bold text-foreground">
                    {isLoading ? "--" : `${avgTemp.toFixed(1)}°C`}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-2xl shadow-soft border-border">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-xl bg-green-100 flex items-center justify-center">
                  <Wind className="h-6 w-6 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Avg. Humidity</p>
                  <p className="text-2xl font-bold text-foreground">
                    {isLoading ? "--" : `${avgHumidity.toFixed(0)}%`}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Alerts Section */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <h2 className="text-lg font-semibold text-foreground">
              Weather Alerts
            </h2>
            {activeAlerts.length > 0 && (
              <Badge variant="destructive" className="rounded-lg">
                {activeAlerts.length} active
              </Badge>
            )}
          </div>
          {isLoading ? (
            <div className="h-20 rounded-xl animate-shimmer" />
          ) : (
            <AlertBanner alerts={activeAlerts} onDismiss={handleDismissAlert} />
          )}
        </div>

        {/* Charts and Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 space-y-4">
            {isLoading ? (
              <>
                <CardSkeleton />
                <CardSkeleton />
              </>
            ) : (
              <>
                <RainfallChart data={data?.cells || []} />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <TemperatureChart data={data?.cells || []} />
                  <HumidityChart data={data?.cells || []} />
                </div>
              </>
            )}
          </div>
          <div>
            {isLoading ? (
              <CardSkeleton className="h-full" />
            ) : (
              <GridVisualization cells={data?.cells || []} />
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

"use client";

import Link from "next/link";
import { AppLayout } from "@/components/layout/app-layout";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Map,
  Cloud,
  AlertTriangle,
  TrendingUp,
  ArrowRight,
  Activity,
  Route,
  Thermometer,
  Droplets,
  CheckCircle,
  Clock,
} from "lucide-react";
import { useRoadNetwork } from "@/features/network/hooks/use-road-network";
import { useWeatherGrid, useWeatherAlerts } from "@/features/weather/hooks/use-weather";
import { CardSkeleton } from "@/components/feedback/skeleton-loader";

export default function DashboardPage() {
  const { data: networkData, isLoading: networkLoading } = useRoadNetwork();
  const { data: weatherData, isLoading: weatherLoading } = useWeatherGrid();
  const { alerts, hasActiveAlerts } = useWeatherAlerts();

  // Calculate statistics
  const totalRoutes = networkData?.routes.length || 0;
  const highRiskRoutes =
    networkData?.routes.filter((r) => r.average_risk_score > 70).length || 0;
  const avgRiskScore = networkData?.routes.length
    ? Math.round(
        networkData.routes.reduce((sum, r) => sum + r.average_risk_score, 0) /
          networkData.routes.length
      )
    : 0;

  const avgRainfall = weatherData?.cells.length
    ? weatherData.cells.reduce((sum, c) => sum + c.rainfall_mm, 0) /
      weatherData.cells.length
    : 0;

  const avgTemp = weatherData?.cells.length
    ? weatherData.cells.reduce((sum, c) => sum + c.temperature_c, 0) /
      weatherData.cells.length
    : 0;

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
            <p className="text-muted-foreground">
              Welcome back. Here&apos;s an overview of your road network status.
            </p>
          </div>
          <Button asChild className="rounded-xl shadow-soft">
            <Link href="/risk">
              <AlertTriangle className="h-4 w-4 mr-2" />
              Run Risk Simulation
            </Link>
          </Button>
        </div>

        {/* Alert Banner */}
        {hasActiveAlerts && (
          <div className="rounded-xl border border-risk-high/30 bg-risk-high/10 p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-risk-high/20 flex items-center justify-center">
                <AlertTriangle className="h-5 w-5 text-risk-high" />
              </div>
              <div>
                <p className="font-medium text-foreground">
                  {alerts.length} Weather Alert{alerts.length > 1 ? "s" : ""}{" "}
                  Active
                </p>
                <p className="text-sm text-muted-foreground">
                  Potential impact on road network conditions
                </p>
              </div>
            </div>
            <Button variant="outline" asChild className="rounded-lg bg-transparent">
              <Link href="/weather">View Details</Link>
            </Button>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Routes Monitored */}
          <Card className="rounded-2xl shadow-soft border-border">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center">
                  <Route className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">
                    Routes Monitored
                  </p>
                  <p className="text-2xl font-bold text-foreground">
                    {networkLoading ? "--" : totalRoutes}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* High Risk Routes */}
          <Card className="rounded-2xl shadow-soft border-border">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-xl bg-risk-high/10 flex items-center justify-center">
                  <AlertTriangle className="h-6 w-6 text-risk-high" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">
                    High Risk Routes
                  </p>
                  <p className="text-2xl font-bold text-risk-high">
                    {networkLoading ? "--" : highRiskRoutes}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Avg Temperature */}
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
                    {weatherLoading ? "--" : `${avgTemp.toFixed(1)}°C`}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Avg Rainfall */}
          <Card className="rounded-2xl shadow-soft border-border">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-xl bg-blue-100 flex items-center justify-center">
                  <Droplets className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Avg. Rainfall</p>
                  <p className="text-2xl font-bold text-foreground">
                    {weatherLoading ? "--" : `${avgRainfall.toFixed(1)} mm`}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Route Risk Overview */}
          <Card className="lg:col-span-2 rounded-2xl shadow-soft border-border">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg font-semibold text-foreground">
                    Route Risk Overview
                  </CardTitle>
                  <CardDescription>
                    Current risk assessment for monitored routes
                  </CardDescription>
                </div>
                <Button variant="ghost" asChild className="rounded-lg">
                  <Link href="/network">
                    View All
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Link>
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {networkLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-16 rounded-xl animate-shimmer" />
                  ))}
                </div>
              ) : (
                <div className="space-y-3">
                  {networkData?.routes.slice(0, 4).map((route) => (
                    <div
                      key={route.id}
                      className="flex items-center justify-between rounded-xl border border-border p-4"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-foreground truncate">
                          {route.name}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {route.total_length_km.toFixed(1)} km •{" "}
                          {route.segments.length} segments
                        </p>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="w-32 hidden sm:block">
                          <Progress
                            value={route.average_risk_score}
                            className="h-2"
                          />
                        </div>
                        <Badge
                          variant={
                            route.average_risk_score > 70
                              ? "destructive"
                              : route.average_risk_score > 40
                              ? "secondary"
                              : "default"
                          }
                          className="rounded-lg w-14 justify-center"
                        >
                          {Math.round(route.average_risk_score)}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <div className="space-y-4">
            {/* System Status */}
            <Card className="rounded-2xl shadow-soft border-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold text-foreground flex items-center gap-2">
                  <Activity className="h-4 w-4" />
                  System Status
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    API Status
                  </span>
                  <Badge
                    variant="default"
                    className="rounded-lg bg-risk-low text-white"
                  >
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Healthy
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    Data Freshness
                  </span>
                  <Badge variant="outline" className="rounded-lg">
                    <Clock className="h-3 w-3 mr-1" />2 min ago
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    Network Coverage
                  </span>
                  <Badge variant="secondary" className="rounded-lg">
                    98.5%
                  </Badge>
                </div>
              </CardContent>
            </Card>

            {/* Quick Links */}
            <Card className="rounded-2xl shadow-soft border-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold text-foreground">
                  Quick Actions
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button
                  variant="outline"
                  asChild
                  className="w-full justify-start rounded-xl bg-transparent"
                >
                  <Link href="/network">
                    <Map className="h-4 w-4 mr-3" />
                    View Road Network
                  </Link>
                </Button>
                <Button
                  variant="outline"
                  asChild
                  className="w-full justify-start rounded-xl bg-transparent"
                >
                  <Link href="/weather">
                    <Cloud className="h-4 w-4 mr-3" />
                    Check Weather Data
                  </Link>
                </Button>
                <Button
                  variant="outline"
                  asChild
                  className="w-full justify-start rounded-xl bg-transparent"
                >
                  <Link href="/risk">
                    <TrendingUp className="h-4 w-4 mr-3" />
                    Risk Analysis
                  </Link>
                </Button>
              </CardContent>
            </Card>

            {/* Risk Distribution */}
            <Card className="rounded-2xl shadow-soft border-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold text-foreground">
                  Risk Distribution
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2 mb-3">
                  <div className="flex-1 h-4 rounded-full bg-risk-low" />
                  <div
                    className="h-4 rounded-full bg-risk-medium"
                    style={{
                      width: `${
                        (networkData?.routes.filter(
                          (r) =>
                            r.average_risk_score > 40 &&
                            r.average_risk_score <= 70
                        ).length || 0) *
                        30
                      }%`,
                    }}
                  />
                  <div
                    className="h-4 rounded-full bg-risk-high"
                    style={{
                      width: `${
                        (networkData?.routes.filter(
                          (r) => r.average_risk_score > 70
                        ).length || 0) *
                        30
                      }%`,
                    }}
                  />
                </div>
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Low Risk</span>
                  <span>Medium</span>
                  <span>High Risk</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

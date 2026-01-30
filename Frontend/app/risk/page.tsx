"use client";

import { AppLayout } from "@/components/layout/app-layout";
import { SimulationPanel } from "@/features/risk/components/simulation-panel";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Clock, History, Zap, BarChart3 } from "lucide-react";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";

export default function RiskPage() {
  // State for simulations
  const [recentSimulations, setSimulations] = useState<any[]>([]);

  // Fetch real data on mount
  useEffect(() => {
    async function fetchData() {
      try {
        const res = await api.get('/routing/routes'); // Get all routes
        const routes = res.data;

        // Map routes to simulation format
        const sims = routes.slice(0, 5).map((r: any) => ({
          id: r.id,
          region: r.name || `Route ${r.id}`,
          timestamp: new Date(r.created_at || Date.now()),
          riskScore: Math.round(r.average_risk_score || 0),
          status: "completed"
        }));
        setSimulations(sims);
      } catch (e) {
        console.error("Failed to fetch simulations", e);
      }
    }
    fetchData();
  }, []);

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              Risk Simulation
            </h1>
            <p className="text-muted-foreground">
              Run AI-powered simulations to assess road network workability
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Simulation Panel */}
          <div className="lg:col-span-2">
            <SimulationPanel />
          </div>

          {/* Sidebar */}
          <div className="space-y-4">
            {/* Quick Stats */}
            <Card className="rounded-2xl shadow-soft border-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold text-foreground flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  Quick Stats
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    Simulations Today
                  </span>
                  <Badge variant="secondary" className="rounded-lg">
                    3
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    Avg. Risk Score
                  </span>
                  <Badge variant="secondary" className="rounded-lg">
                    61.7
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    Active Alerts
                  </span>
                  <Badge variant="destructive" className="rounded-lg">
                    2
                  </Badge>
                </div>
              </CardContent>
            </Card>

            {/* Recent Simulations */}
            <Card className="rounded-2xl shadow-soft border-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold text-foreground flex items-center gap-2">
                  <History className="h-4 w-4" />
                  Recent Simulations
                </CardTitle>
                <CardDescription>Previous analysis runs</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {recentSimulations.map((sim) => (
                    <div
                      key={sim.id}
                      className="flex items-center justify-between rounded-lg border border-border p-3"
                    >
                      <div>
                        <p className="font-medium text-foreground text-sm">
                          {sim.region}
                        </p>
                        <p className="text-xs text-muted-foreground flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {sim.timestamp.toLocaleDateString("en-US", {
                            month: "short",
                            day: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </p>
                      </div>
                      <Badge
                        variant={
                          sim.riskScore > 70
                            ? "destructive"
                            : sim.riskScore > 40
                              ? "secondary"
                              : "default"
                        }
                        className="rounded-lg"
                      >
                        {sim.riskScore}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Info Card */}
            <Card className="rounded-2xl shadow-soft border-border bg-secondary/50">
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                    <Zap className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      How it works
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Our AI analyzes weather data, soil saturation levels, and
                      historical patterns to predict road workability and risk
                      factors in real-time.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

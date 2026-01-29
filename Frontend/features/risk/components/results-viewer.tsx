"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import {
  CheckCircle,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight,
  Download,
  FileJson,
  ChevronRight,
} from "lucide-react";
import type { SimulationResult } from "@/types";
import { REGIONS } from "@/types";

interface ResultsViewerProps {
  results: NonNullable<SimulationResult["results"]>;
  regionId: string;
}

function getRiskColor(score: number): string {
  if (score > 70) return "text-risk-high";
  if (score > 40) return "text-risk-medium";
  return "text-risk-low";
}

function getRiskBgColor(score: number): string {
  if (score > 70) return "bg-risk-high";
  if (score > 40) return "bg-risk-medium";
  return "bg-risk-low";
}

function getPriorityBadgeVariant(
  priority: "high" | "medium" | "low"
): "destructive" | "secondary" | "default" {
  switch (priority) {
    case "high":
      return "destructive";
    case "medium":
      return "secondary";
    default:
      return "default";
  }
}

export function ResultsViewer({ results, regionId }: ResultsViewerProps) {
  const region = REGIONS.find((r) => r.id === regionId);
  const regionName = region?.name || regionId;

  const { risk_assessment, recommendations, affected_routes } = results;

  const handleExportJSON = () => {
    const dataStr = JSON.stringify(results, null, 2);
    const blob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `simulation-results-${regionId}-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      {/* Success Banner */}
      <Card className="rounded-2xl shadow-soft border-risk-low/30 bg-risk-low/5">
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-risk-low/20 flex items-center justify-center">
              <CheckCircle className="h-6 w-6 text-risk-low" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-foreground">
                Simulation Complete
              </h3>
              <p className="text-sm text-muted-foreground">
                Risk assessment for {regionName} has been successfully generated
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportJSON}
                className="rounded-lg bg-transparent"
              >
                <FileJson className="h-4 w-4 mr-2" />
                Export JSON
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Risk Assessment Card */}
      <Card className="rounded-2xl shadow-soft border-border">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-foreground">
            Risk Assessment
          </CardTitle>
          <CardDescription>
            Overall risk analysis and contributing factors
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Overall Score */}
          <div className="flex items-center gap-6">
            <div
              className={`h-24 w-24 rounded-2xl flex items-center justify-center ${getRiskBgColor(
                risk_assessment.overall_score
              )}`}
            >
              <span className="text-3xl font-bold text-white">
                {risk_assessment.overall_score}
              </span>
            </div>
            <div className="flex-1">
              <p className="text-sm text-muted-foreground">Overall Risk Score</p>
              <p
                className={`text-2xl font-bold ${getRiskColor(
                  risk_assessment.overall_score
                )}`}
              >
                {risk_assessment.overall_score > 70
                  ? "High Risk"
                  : risk_assessment.overall_score > 40
                  ? "Medium Risk"
                  : "Low Risk"}
              </p>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-sm text-muted-foreground">Confidence:</span>
                <Badge variant="outline" className="rounded-lg">
                  {risk_assessment.confidence}%
                </Badge>
              </div>
            </div>
          </div>

          <Separator />

          {/* Contributing Factors */}
          <div>
            <h4 className="text-sm font-semibold text-foreground mb-3">
              Contributing Factors
            </h4>
            <div className="space-y-3">
              {risk_assessment.factors.map((factor) => (
                <div key={factor.name} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">{factor.name}</span>
                    <span className="font-medium text-foreground">
                      {factor.contribution}% contribution
                    </span>
                  </div>
                  <Progress
                    value={factor.value}
                    className="h-2 rounded-full"
                  />
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recommendations Card */}
      <Card className="rounded-2xl shadow-soft border-border">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-foreground">
            Recommendations
          </CardTitle>
          <CardDescription>
            Suggested actions based on the risk assessment
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {recommendations.map((rec, index) => (
              <div
                key={index}
                className="rounded-xl border border-border p-4 hover:bg-accent transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge
                        variant={getPriorityBadgeVariant(rec.priority)}
                        className="rounded-lg text-xs capitalize"
                      >
                        {rec.priority} priority
                      </Badge>
                    </div>
                    <p className="font-medium text-foreground">{rec.action}</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Impact: {rec.impact}
                    </p>
                  </div>
                  <ChevronRight className="h-5 w-5 text-muted-foreground shrink-0" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Affected Routes Card */}
      <Card className="rounded-2xl shadow-soft border-border">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-foreground">
            Affected Routes
          </CardTitle>
          <CardDescription>
            Routes with changed risk levels based on this simulation
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {affected_routes.map((route) => (
              <div
                key={route.route_id}
                className="flex items-center justify-between rounded-xl border border-border p-3"
              >
                <span className="font-medium text-foreground">{route.name}</span>
                <div className="flex items-center gap-2">
                  {route.risk_change > 0 ? (
                    <>
                      <ArrowUpRight className="h-4 w-4 text-risk-high" />
                      <span className="text-sm text-risk-high">
                        +{route.risk_change}%
                      </span>
                    </>
                  ) : (
                    <>
                      <ArrowDownRight className="h-4 w-4 text-risk-low" />
                      <span className="text-sm text-risk-low">
                        {route.risk_change}%
                      </span>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

"use client";

import { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { Play, RotateCcw, Zap } from "lucide-react";
import { REGIONS } from "@/types";
import { useRiskSimulation } from "../hooks/use-risk-simulation";
import { SimulationStatus } from "./simulation-status";
import { ResultsViewer } from "./results-viewer";

export function SimulationPanel() {
  const [selectedRegion, setSelectedRegion] = useState<string>("");

  const {
    startSimulation,
    isCalculating,
    progress,
    estimatedTimeRemaining,
    results,
    error,
    status,
    resetSimulation,
  } = useRiskSimulation();

  const handleRunSimulation = () => {
    if (!selectedRegion) return;
    startSimulation({ region_id: selectedRegion });
  };

  const handleReset = () => {
    resetSimulation();
    setSelectedRegion("");
  };

  return (
    <div className="space-y-4">
      {/* Main Control Panel */}
      <Card className="rounded-2xl shadow-soft border-border">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center">
              <Zap className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold text-foreground">
                Road Network Risk Simulator
              </CardTitle>
              <CardDescription>
                Run AI-powered risk assessments on road networks
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Region Selection - MANUAL */}
          <div className="space-y-2">
            <Label htmlFor="region-select" className="text-foreground">
              Select Region
            </Label>
            <Select
              value={selectedRegion}
              onValueChange={setSelectedRegion}
              disabled={isCalculating}
            >
              <SelectTrigger
                id="region-select"
                className="rounded-xl shadow-inner-soft"
              >
                <SelectValue placeholder="Choose a region to analyze" />
              </SelectTrigger>
              <SelectContent className="rounded-xl">
                {REGIONS.map((region) => (
                  <SelectItem
                    key={region.id}
                    value={region.id}
                    className="rounded-lg"
                  >
                    {region.name} ({region.code})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Action Buttons - MANUAL */}
          <div className="flex gap-3">
            <Button
              onClick={handleRunSimulation}
              disabled={!selectedRegion || isCalculating}
              className="flex-1 rounded-xl shadow-soft"
            >
              {isCalculating ? (
                <>
                  <Spinner className="mr-2 h-4 w-4" />
                  Processing...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Run Simulation
                </>
              )}
            </Button>
            {(results || error) && (
              <Button
                variant="outline"
                onClick={handleReset}
                className="rounded-xl bg-transparent"
              >
                <RotateCcw className="mr-2 h-4 w-4" />
                Reset
              </Button>
            )}
          </div>

          {/* Error Display */}
          {error && (
            <div className="rounded-xl border border-risk-high/30 bg-risk-high/10 p-4">
              <p className="text-sm text-foreground">{error}</p>
              <Button
                variant="outline"
                size="sm"
                onClick={handleReset}
                className="mt-2 rounded-lg bg-transparent"
              >
                Try Again
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Simulation Status - AUTOMATED polling UI */}
      {isCalculating && (
        <SimulationStatus
          regionId={selectedRegion}
          progress={progress}
          estimatedTimeRemaining={estimatedTimeRemaining}
          status={status}
        />
      )}

      {/* Results Viewer */}
      {results && !isCalculating && (
        <ResultsViewer results={results} regionId={selectedRegion} />
      )}
    </div>
  );
}

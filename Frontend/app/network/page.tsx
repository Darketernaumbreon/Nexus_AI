"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout/app-layout";
import { RoadNetworkMap } from "@/features/network/components/road-network-map";
import { RouteList } from "@/features/network/components/route-list";
import { NodeDetails } from "@/features/network/components/node-details";
import { useRoadNetwork } from "@/features/network/hooks/use-road-network";
import { ErrorBanner } from "@/components/feedback/error-banner";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

export default function NetworkPage() {
  const { data, isLoading, error, refetch } = useRoadNetwork();
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(null);
  const [showWeatherLayer, setShowWeatherLayer] = useState(false);

  const selectedRoute =
    data?.routes.find((r) => r.id === selectedRouteId) || null;

  return (
    <AppLayout>
      <div className="h-full flex flex-col gap-4">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Road Network</h1>
            <p className="text-muted-foreground">
              View and analyze road network data with risk assessments
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Switch
              id="weather-layer"
              checked={showWeatherLayer}
              onCheckedChange={setShowWeatherLayer}
            />
            <Label htmlFor="weather-layer" className="text-sm">
              Weather Layer
            </Label>
          </div>
        </div>

        {/* Error Banner */}
        {error && (
          <ErrorBanner
            message={error.message}
            onRetry={refetch}
            onDismiss={() => {}}
          />
        )}

        {/* Main Content */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-4 min-h-0">
          {/* Route List - Sidebar */}
          <div className="lg:col-span-1 h-full">
            <RouteList
              routes={data?.routes || []}
              selectedRouteId={selectedRouteId}
              onRouteSelect={setSelectedRouteId}
              isLoading={isLoading}
            />
          </div>

          {/* Map - Main Area */}
          <div className="lg:col-span-3 h-full min-h-[400px]">
            <RoadNetworkMap
              routes={data?.routes || []}
              selectedRouteId={selectedRouteId}
              onRouteSelect={setSelectedRouteId}
              showWeatherLayer={showWeatherLayer}
            />
          </div>
        </div>

        {/* Node Details Drawer */}
        <NodeDetails
          route={selectedRoute}
          isOpen={!!selectedRoute}
          onClose={() => setSelectedRouteId(null)}
        />
      </div>
    </AppLayout>
  );
}

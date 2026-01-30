"use client";

import dynamic from "next/dynamic";
import { Card } from "@/components/ui/card";
import type { RoutePolyline } from "@/types";

// Dynamically import the Leaflet component with SSR disabled
const LeafletMap = dynamic(
  () => import("./leaflet-map-internal"),
  {
    loading: () => <div className="h-full w-full bg-slate-100 animate-pulse flex items-center justify-center text-muted-foreground">Loading Map...</div>,
    ssr: false
  }
);

interface RoadNetworkMapProps {
  routes: RoutePolyline[];
  selectedRouteId?: string | null;
  onRouteSelect?: (routeId: string) => void;
  showWeatherLayer?: boolean;
  weatherCells?: any[];
}

export function RoadNetworkMap({
  routes,
  selectedRouteId,
  onRouteSelect,
  showWeatherLayer,
  weatherCells,
}: RoadNetworkMapProps) {
  return (
    <Card className="relative h-full rounded-2xl shadow-soft overflow-hidden border-border z-0">
      <LeafletMap
        routes={routes}
        selectedRouteId={selectedRouteId}
        onRouteSelect={onRouteSelect}
      />

      {/* Overlay: Stats or Region Info */}
      <div className="absolute bottom-4 right-4 bg-white/90 backdrop-blur-sm rounded-lg px-3 py-1.5 shadow-soft z-[1000] border border-slate-200">
        <span className="text-xs font-medium text-slate-700">
          Region: North East (Live)
        </span>
      </div>
    </Card>
  );
}

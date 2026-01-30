"use client";

import { MapContainer } from "@/components/map/MapContainer";
import { FloodLayer } from "@/components/map/FloodLayer";
import { LandslideLayer } from "@/components/map/LandslideLayer";
import { RouteLayer } from "@/components/map/RouteLayer";
import { MapLegend } from "@/components/map/MapLegend";
import { useFloodHazardZones } from "@/hooks/useFloodHazardZones";
import { useLandslideHazardZones } from "@/hooks/useLandslideHazardZones";
import { AlertCircle, Loader2 } from "lucide-react";

export default function MapPage() {
    const floodZones = useFloodHazardZones();
    const landslideZones = useLandslideHazardZones();

    const isLoading = floodZones.isLoading || landslideZones.isLoading;
    const hasError = floodZones.isError || landslideZones.isError;
    const hasNoData = !floodZones.data && !landslideZones.data && !isLoading;

    return (
        <div className="flex flex-col h-full max-w-7xl">
            {/* Page Header */}
            <div className="mb-4">
                <h1 className="text-2xl sm:text-3xl font-bold text-slate-800">
                    Hazard Map
                </h1>
                <p className="text-slate-600 mt-1 text-sm sm:text-base leading-relaxed">
                    Interactive visualization of flood and landslide risk zones
                </p>
            </div>

            {/* Error Banner */}
            {hasError && (
                <div
                    className="mb-4 bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-start gap-3"
                    role="alert"
                >
                    <AlertCircle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
                    <div>
                        <p className="text-sm font-medium text-yellow-800">
                            Unable to Load Hazard Data
                        </p>
                        <p className="text-sm text-yellow-700 mt-1 leading-relaxed">
                            The map is still available, but hazard zones cannot be displayed
                            at this time.
                        </p>
                    </div>
                </div>
            )}

            {/* No Data Banner */}
            {hasNoData && !hasError && (
                <div className="mb-4 bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
                    <AlertCircle className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
                    <div>
                        <p className="text-sm font-medium text-green-800">
                            No Active Hazards Detected
                        </p>
                        <p className="text-sm text-green-700 mt-1 leading-relaxed">
                            The system has not identified any active flood or landslide risk
                            zones in the monitored area.
                        </p>
                    </div>
                </div>
            )}

            {/* Map Container */}
            <div className="flex-1 rounded-lg overflow-hidden border border-slate-200 shadow-sm relative min-h-[400px] sm:min-h-[500px]">
                {/* Loading Overlay */}
                {isLoading && (
                    <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-white rounded-lg shadow-lg border border-slate-200 px-4 py-2 z-20 flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin text-blue-600" aria-hidden="true" />
                        <span className="text-sm text-slate-700">Loading hazard data...</span>
                    </div>
                )}

                <MapContainer>
                    {(map) => (
                        <>
                            <FloodLayer map={map} data={floodZones.data || null} />
                            <LandslideLayer map={map} data={landslideZones.data || null} />
                            <RouteLayer map={map} data={null} />
                            <MapLegend />
                        </>
                    )}
                </MapContainer>
            </div>
        </div>
    );
}

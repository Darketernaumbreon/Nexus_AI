"use client";

import { useState } from "react";
import { useSafeRoute } from "@/hooks/useSafeRoute";
import { RouteRequest } from "@/types/route";
import { RouteSummary } from "@/components/routing/RouteSummary";
import { MapContainer } from "@/components/map/MapContainer";
import { RouteLayer } from "@/components/map/RouteLayer";
import { MapLegend } from "@/components/map/MapLegend";
import { AlertCircle, Loader2, Navigation } from "lucide-react";

export default function RoutingPage() {
    const [originLat, setOriginLat] = useState("");
    const [originLon, setOriginLon] = useState("");
    const [destLat, setDestLat] = useState("");
    const [destLon, setDestLon] = useState("");
    const [routeRequest, setRouteRequest] = useState<RouteRequest | null>(null);

    const { data: routeData, isLoading, isError } = useSafeRoute(routeRequest);

    const handleComputeRoute = () => {
        const origin_lat = parseFloat(originLat);
        const origin_lon = parseFloat(originLon);
        const dest_lat = parseFloat(destLat);
        const dest_lon = parseFloat(destLon);

        if (
            !isNaN(origin_lat) &&
            !isNaN(origin_lon) &&
            !isNaN(dest_lat) &&
            !isNaN(dest_lon)
        ) {
            setRouteRequest({
                origin_lat,
                origin_lon,
                dest_lat,
                dest_lon,
            });
        }
    };

    const isFormValid = originLat && originLon && destLat && destLon;

    return (
        <div className="space-y-4 sm:space-y-6 max-w-6xl">
            {/* Page Header */}
            <div>
                <h1 className="text-2xl sm:text-3xl font-bold text-slate-800">
                    Safe Routing
                </h1>
                <p className="text-slate-600 mt-1 text-sm sm:text-base leading-relaxed">
                    Compute hazard-aware routes between two locations
                </p>
            </div>

            {/* Route Input Form */}
            <div className="bg-white rounded-lg border border-slate-200 p-4 sm:p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
                    {/* Origin */}
                    <div>
                        <label
                            htmlFor="origin-lat"
                            className="block text-sm font-medium text-slate-700 mb-2"
                        >
                            Origin
                        </label>
                        <div className="space-y-2">
                            <input
                                id="origin-lat"
                                type="number"
                                step="any"
                                placeholder="Latitude (e.g., 26.2006)"
                                value={originLat}
                                onChange={(e) => setOriginLat(e.target.value)}
                                className="w-full px-3 py-2.5 text-base border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                aria-label="Origin latitude"
                            />
                            <input
                                id="origin-lon"
                                type="number"
                                step="any"
                                placeholder="Longitude (e.g., 92.9376)"
                                value={originLon}
                                onChange={(e) => setOriginLon(e.target.value)}
                                className="w-full px-3 py-2.5 text-base border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                aria-label="Origin longitude"
                            />
                        </div>
                    </div>

                    {/* Destination */}
                    <div>
                        <label
                            htmlFor="dest-lat"
                            className="block text-sm font-medium text-slate-700 mb-2"
                        >
                            Destination
                        </label>
                        <div className="space-y-2">
                            <input
                                id="dest-lat"
                                type="number"
                                step="any"
                                placeholder="Latitude (e.g., 26.1500)"
                                value={destLat}
                                onChange={(e) => setDestLat(e.target.value)}
                                className="w-full px-3 py-2.5 text-base border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                aria-label="Destination latitude"
                            />
                            <input
                                id="dest-lon"
                                type="number"
                                step="any"
                                placeholder="Longitude (e.g., 91.7500)"
                                value={destLon}
                                onChange={(e) => setDestLon(e.target.value)}
                                className="w-full px-3 py-2.5 text-base border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                aria-label="Destination longitude"
                            />
                        </div>
                    </div>
                </div>

                {/* Compute Button */}
                <div className="mt-6">
                    <button
                        onClick={handleComputeRoute}
                        disabled={!isFormValid || isLoading}
                        className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3 text-base bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                        aria-label="Compute safe route"
                    >
                        {isLoading ? (
                            <>
                                <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
                                Computing Route...
                            </>
                        ) : (
                            <>
                                <Navigation className="h-5 w-5" aria-hidden="true" />
                                Compute Safe Route
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Error State */}
            {isError && (
                <div
                    className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3"
                    role="alert"
                >
                    <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
                    <div>
                        <p className="text-sm font-medium text-red-800">
                            Routing Service Unavailable
                        </p>
                        <p className="text-sm text-red-700 mt-1 leading-relaxed">
                            Unable to compute route at this time. Please try again later.
                        </p>
                    </div>
                </div>
            )}

            {/* BLOCKED Route Warning */}
            {routeData && routeData.route.route_status === "BLOCKED" && (
                <div
                    className="bg-red-600 text-white rounded-lg p-4 sm:p-6"
                    role="alert"
                >
                    <div className="flex items-start gap-3">
                        <AlertCircle className="h-6 w-6 flex-shrink-0 mt-0.5" aria-hidden="true" />
                        <div>
                            <p className="text-lg font-bold mb-1">DO NOT PROCEED</p>
                            <p className="text-sm sm:text-base leading-relaxed">
                                This route passes through active hazard zones and is extremely dangerous.
                                Select an alternative destination immediately.
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Empty State */}
            {!routeRequest && !isLoading && (
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-6 sm:p-8 text-center">
                    <Navigation className="h-12 w-12 text-slate-400 mx-auto mb-3" aria-hidden="true" />
                    <h3 className="text-lg font-semibold text-slate-700 mb-2">
                        No Route Computed
                    </h3>
                    <p className="text-sm text-slate-600 leading-relaxed">
                        Select origin and destination to compute a safe route
                    </p>
                </div>
            )}

            {/* Route Summary */}
            {routeData && !isLoading && <RouteSummary routeData={routeData} />}

            {/* Map with Route */}
            {routeData && !isLoading && (
                <div className="h-[400px] sm:h-[500px] lg:h-[600px] rounded-lg overflow-hidden border border-slate-200 shadow-sm">
                    <MapContainer>
                        {(map) => (
                            <>
                                <RouteLayer
                                    map={map}
                                    data={routeData.route.geometry}
                                    status={routeData.route.route_status}
                                />
                                <MapLegend />
                            </>
                        )}
                    </MapContainer>
                </div>
            )}
        </div>
    );
}

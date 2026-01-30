import { SafeRouteResponse } from "@/types/route";
import { RouteStatusBadge } from "./RouteStatusBadge";
import { MapPin, Clock, AlertTriangle, CheckCircle } from "lucide-react";

interface RouteSummaryProps {
    routeData: SafeRouteResponse;
}

export function RouteSummary({ routeData }: RouteSummaryProps) {
    const { route_status: status, distance_km, eta_minutes, avoided_hazards } = routeData.route;

    return (
        <div className="bg-white rounded-lg border border-slate-200 p-6 space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-slate-800">Route Summary</h3>
                <RouteStatusBadge status={status} />
            </div>

            {/* Route Details */}
            <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-100 rounded-lg">
                        <MapPin className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                        <p className="text-xs text-slate-500">Distance</p>
                        <p className="text-lg font-semibold text-slate-800">
                            {distance_km.toFixed(1)} km
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-100 rounded-lg">
                        <Clock className="h-5 w-5 text-purple-600" />
                    </div>
                    <div>
                        <p className="text-xs text-slate-500">Estimated Time</p>
                        <p className="text-lg font-semibold text-slate-800">
                            {eta_minutes} min
                        </p>
                    </div>
                </div>
            </div>

            {/* Avoided Hazards */}
            {avoided_hazards && avoided_hazards.length > 0 && (
                <div className="pt-4 border-t border-slate-100">
                    <div className="flex items-start gap-2">
                        <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <div>
                            <p className="text-sm font-medium text-slate-700">
                                Hazards Avoided
                            </p>
                            <ul className="mt-1 space-y-1">
                                {avoided_hazards.map((hazard, index) => (
                                    <li key={index} className="text-sm text-slate-600">
                                        • {hazard}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </div>
            )}

            {/* Warning for BLOCKED/PARTIAL routes */}
            {(status === "BLOCKED" || status === "PARTIAL") && (
                <div className="pt-4 border-t border-slate-100">
                    <div className="flex items-start gap-2 bg-red-50 rounded-lg p-3">
                        <AlertTriangle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                        <div>
                            <p className="text-sm font-medium text-red-800">
                                {status === "BLOCKED"
                                    ? "Route Blocked"
                                    : "Route Partially Affected"}
                            </p>
                            <p className="text-sm text-red-700 mt-1">
                                {status === "BLOCKED"
                                    ? "This route passes through active hazard zones and is not recommended. Please select an alternative destination."
                                    : "This route may pass near hazard zones. Exercise extreme caution and monitor conditions."}
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Caution message */}
            {status === "CAUTION" && (
                <div className="pt-4 border-t border-slate-100">
                    <div className="flex items-start gap-2 bg-yellow-50 rounded-lg p-3">
                        <AlertTriangle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                        <div>
                            <p className="text-sm font-medium text-yellow-800">
                                Proceed with Caution
                            </p>
                            <p className="text-sm text-yellow-700 mt-1">
                                This route is near hazard zones. Stay alert and monitor
                                conditions during travel.
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

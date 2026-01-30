"use client";

import { useAlerts } from "@/hooks/useAlerts";
import { AlertCard } from "@/components/alerts/AlertCard";
import { AlertCircle, CheckCircle, Loader2 } from "lucide-react";

export default function AlertsPage() {
    const { data: alerts, isLoading, isError } = useAlerts();

    return (
        <div className="space-y-4 sm:space-y-6 max-w-5xl">
            {/* Page Header */}
            <div>
                <h1 className="text-2xl sm:text-3xl font-bold text-slate-800">
                    Alerts Center
                </h1>
                <p className="text-slate-600 mt-1 text-sm sm:text-base leading-relaxed">
                    Real-time hazard alerts and recommended actions
                </p>
            </div>

            {/* Loading State */}
            {isLoading && (
                <div className="flex items-center justify-center py-12">
                    <div className="flex items-center gap-3">
                        <Loader2 className="h-6 w-6 animate-spin text-blue-600" aria-hidden="true" />
                        <span className="text-slate-600">Loading alerts...</span>
                    </div>
                </div>
            )}

            {/* Error State */}
            {isError && !isLoading && (
                <div
                    className="bg-red-50 border border-red-200 rounded-lg p-4 sm:p-6 flex items-start gap-3"
                    role="alert"
                >
                    <AlertCircle className="h-6 w-6 text-red-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
                    <div>
                        <p className="text-sm font-medium text-red-800">
                            Unable to Load Alerts
                        </p>
                        <p className="text-sm text-red-700 mt-1 leading-relaxed">
                            The alerts system is currently unavailable. Please check back
                            shortly or contact system administrators if this persists.
                        </p>
                    </div>
                </div>
            )}

            {/* Empty State */}
            {!isLoading && !isError && alerts && alerts.length === 0 && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-6 sm:p-8 text-center">
                    <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-3" aria-hidden="true" />
                    <h3 className="text-lg font-semibold text-green-800 mb-2">
                        No Active Hazards Detected
                    </h3>
                    <p className="text-sm text-green-700 leading-relaxed">
                        System is monitoring conditions continuously
                    </p>
                </div>
            )}

            {/* Alerts List */}
            {!isLoading && alerts && alerts.length > 0 && (
                <div className="space-y-4 sm:space-y-6">
                    {/* P0/CRITICAL Alerts Section */}
                    {alerts.some((alert) => alert.priority === "P0" || alert.severity === "CRITICAL") && (
                        <div>
                            <div className="flex items-center gap-2 mb-3">
                                <div className="h-2 w-2 rounded-full bg-red-600 animate-pulse" aria-hidden="true" />
                                <h2 className="text-sm sm:text-base font-bold text-red-600 uppercase tracking-wide">
                                    Critical Alerts
                                </h2>
                            </div>
                            <div className="space-y-3 sm:space-y-4">
                                {alerts
                                    .filter((alert) => alert.priority === "P0" || alert.severity === "CRITICAL")
                                    .map((alert) => (
                                        <AlertCard key={alert.alert_id} alert={alert} />
                                    ))}
                            </div>
                        </div>
                    )}

                    {/* P1-P3 Alerts Section */}
                    {alerts.some((alert) => alert.priority !== "P0" && alert.severity !== "CRITICAL") && (
                        <div>
                            {alerts.some((alert) => alert.priority === "P0" || alert.severity === "CRITICAL") && (
                                <div className="flex items-center gap-2 mb-3 mt-6">
                                    <div className="h-2 w-2 rounded-full bg-slate-400" aria-hidden="true" />
                                    <h2 className="text-sm sm:text-base font-bold text-slate-600 uppercase tracking-wide">
                                        Other Alerts
                                    </h2>
                                </div>
                            )}
                            <div className="space-y-3 sm:space-y-4">
                                {alerts
                                    .filter((alert) => alert.priority !== "P0" && alert.severity !== "CRITICAL")
                                    .map((alert) => (
                                        <AlertCard key={alert.alert_id} alert={alert} />
                                    ))}
                            </div>
                        </div>
                    )}

                    {/* Alert Count */}
                    <div className="pt-4 border-t border-slate-200">
                        <p className="text-sm text-slate-500 text-center">
                            Showing {alerts.length} active {alerts.length === 1 ? "alert" : "alerts"}
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
}

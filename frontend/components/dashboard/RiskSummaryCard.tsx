import { useFloodHazardZones } from "@/hooks/useFloodHazardZones";
import { useLandslideHazardZones } from "@/hooks/useLandslideHazardZones";
import { AlertTriangle, Droplets, Mountain, CheckCircle } from "lucide-react";

export function RiskSummaryCard() {
    const { data: floodZones, isLoading: isLoadingFlood } = useFloodHazardZones();
    const { data: landslideZones, isLoading: isLoadingLandslide } =
        useLandslideHazardZones();

    const isLoading = isLoadingFlood || isLoadingLandslide;

    // Determine risks
    const hasFloodRisk = floodZones && floodZones.features.length > 0;
    const hasLandslideRisk = landslideZones && landslideZones.features.length > 0;

    const overallRisk =
        hasFloodRisk || hasLandslideRisk ? "HIGH" : "LOW";

    return (
        <div className="bg-white rounded-lg border border-slate-200 p-6">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-slate-800">Risk Summary</h3>
                {isLoading ? (
                    <span className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded animate-pulse">
                        Loading...
                    </span>
                ) : (
                    <span
                        className={`text-xs px-2 py-1 rounded font-medium ${overallRisk === "HIGH"
                                ? "bg-red-100 text-red-700"
                                : "bg-green-100 text-green-700"
                            }`}
                    >
                        {overallRisk === "HIGH" ? "Hazardous" : "Safe"}
                    </span>
                )}
            </div>

            <div className="space-y-4">
                {/* Flood Risk */}
                <div
                    className={`flex items-center justify-between p-3 rounded-lg ${hasFloodRisk ? "bg-blue-50" : "bg-slate-50"
                        }`}
                >
                    <div className="flex items-center gap-3">
                        <div
                            className={`p-2 rounded-lg ${hasFloodRisk ? "bg-blue-100" : "bg-slate-200"
                                }`}
                        >
                            <Droplets
                                className={`h-5 w-5 ${hasFloodRisk ? "text-blue-600" : "text-slate-500"
                                    }`}
                            />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-slate-800">Flood Risk</p>
                            <p className="text-xs text-slate-500">
                                {hasFloodRisk
                                    ? `${floodZones?.features.length} active zones`
                                    : "No active zones"}
                            </p>
                        </div>
                    </div>
                    <span
                        className={`text-sm font-bold ${hasFloodRisk ? "text-blue-600" : "text-slate-400"
                            }`}
                    >
                        {hasFloodRisk ? "HIGH" : "LOW"}
                    </span>
                </div>

                {/* Landslide Risk */}
                <div
                    className={`flex items-center justify-between p-3 rounded-lg ${hasLandslideRisk ? "bg-orange-50" : "bg-slate-50"
                        }`}
                >
                    <div className="flex items-center gap-3">
                        <div
                            className={`p-2 rounded-lg ${hasLandslideRisk ? "bg-orange-100" : "bg-slate-200"
                                }`}
                        >
                            <Mountain
                                className={`h-5 w-5 ${hasLandslideRisk
                                        ? "text-orange-600"
                                        : "text-slate-500"
                                    }`}
                            />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-slate-800">
                                Landslide Risk
                            </p>
                            <p className="text-xs text-slate-500">
                                {hasLandslideRisk
                                    ? `${landslideZones?.features.length} active zones`
                                    : "No active zones"}
                            </p>
                        </div>
                    </div>
                    <span
                        className={`text-sm font-bold ${hasLandslideRisk ? "text-orange-600" : "text-slate-400"
                            }`}
                    >
                        {hasLandslideRisk ? "HIGH" : "LOW"}
                    </span>
                </div>

                {/* Overall Risk */}
                <div className="pt-3 border-t border-slate-100">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            {overallRisk === "HIGH" ? (
                                <AlertTriangle className="h-4 w-4 text-red-500" />
                            ) : (
                                <CheckCircle className="h-4 w-4 text-green-500" />
                            )}
                            <span className="text-sm font-medium text-slate-600">
                                Overall Risk Level
                            </span>
                        </div>
                        <span
                            className={`text-lg font-bold ${overallRisk === "HIGH"
                                    ? "text-red-600"
                                    : "text-green-600"
                                }`}
                        >
                            {overallRisk}
                        </span>
                    </div>
                </div>
            </div>

            <div className="mt-4 pt-4 border-t border-slate-100">
                <p className="text-xs text-slate-500 text-center">
                    real-time hazard assessment active
                </p>
            </div>
        </div>
    );
}

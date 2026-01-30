import { useWeather } from "@/hooks/useWeather";
import { Cloud, CloudRain, Database } from "lucide-react";

export function WeatherSummaryCard() {
    const { data: weather, isLoading } = useWeather();

    // Get today's rain (index 0)
    const todayRain = weather?.daily?.precipitation_sum?.[0] ?? 0;

    // Get next 48h rain (index 0 + 1)
    const next48hRain = (weather?.daily?.precipitation_sum?.[0] ?? 0) + (weather?.daily?.precipitation_sum?.[1] ?? 0);

    return (
        <div className="bg-white rounded-lg border border-slate-200 p-6">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-slate-800">
                    Weather Summary
                </h3>
                {isLoading ? (
                    <span className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded animate-pulse">
                        Loading...
                    </span>
                ) : (
                    <span className="text-xs text-green-700 bg-green-100 px-2 py-1 rounded font-medium">
                        Live Data
                    </span>
                )}
            </div>

            <div className="space-y-4">
                {/* Rainfall */}
                <div className="flex items-center justify-between p-3 bg-sky-50 rounded-lg">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-sky-100 rounded-lg">
                            <CloudRain className="h-5 w-5 text-sky-600" />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-slate-800">
                                Rainfall (24h)
                            </p>
                            <p className="text-xs text-slate-500">Cumulative precipitation</p>
                        </div>
                    </div>
                    <span className="text-2xl font-bold text-slate-800">
                        {isLoading ? "—" : `${todayRain.toFixed(1)} mm`}
                    </span>
                </div>

                {/* Forecast Window */}
                <div className="flex items-center justify-between p-3 bg-indigo-50 rounded-lg">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-indigo-100 rounded-lg">
                            <Cloud className="h-5 w-5 text-indigo-600" />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-slate-800">
                                Forecast (48h)
                            </p>
                            <p className="text-xs text-slate-500">Expected rainfall</p>
                        </div>
                    </div>
                    <span className="text-2xl font-bold text-slate-800">
                        {isLoading ? "—" : `${next48hRain.toFixed(1)} mm`}
                    </span>
                </div>

                {/* Data Source */}
                <div className="pt-3 border-t border-slate-100">
                    <div className="flex items-center gap-2 text-sm text-slate-600">
                        <Database className="h-4 w-4" />
                        <span>Data Source:</span>
                        <span className="font-medium">Open-Meteo (Guwahati)</span>
                    </div>
                </div>
            </div>

            <div className="mt-4 pt-4 border-t border-slate-100">
                <p className="text-xs text-slate-500 text-center">
                    Weather data active
                </p>
            </div>
        </div>
    );
}

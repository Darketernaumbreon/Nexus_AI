import { Droplets, Mountain, Route } from "lucide-react";

export function MapLegend() {
    const legendItems = [
        {
            icon: Droplets,
            label: "Flood Zone",
            color: "bg-blue-500",
        },
        {
            icon: Mountain,
            label: "Landslide Zone",
            color: "bg-orange-500",
        },
        {
            icon: Route,
            label: "Safe Route",
            color: "bg-green-500",
        },
    ];

    return (
        <div className="absolute bottom-4 right-4 sm:bottom-6 sm:right-6 bg-white rounded-lg shadow-lg border border-slate-200 p-3 sm:p-4 z-10 max-w-[200px] sm:max-w-none">
            <h4 className="text-xs sm:text-sm font-semibold text-slate-800 mb-2 sm:mb-3">
                Map Legend
            </h4>
            <div className="space-y-1.5 sm:space-y-2">
                {legendItems.map((item) => {
                    const Icon = item.icon;
                    return (
                        <div key={item.label} className="flex items-center gap-2">
                            <div className={`w-3 h-3 sm:w-4 sm:h-4 rounded ${item.color}`} aria-hidden="true" />
                            <Icon className="h-3 w-3 sm:h-3.5 sm:w-3.5 text-slate-600 flex-shrink-0" aria-hidden="true" />
                            <span className="text-xs text-slate-700">{item.label}</span>
                        </div>
                    );
                })}
            </div>
            <div className="mt-2 sm:mt-3 pt-2 sm:pt-3 border-t border-slate-100">
                <p className="text-xs text-slate-500">
                    Data Source: <span className="font-medium">NEXUS-AI</span>
                </p>
                <p className="text-xs text-slate-400 mt-1">Live Predictions</p>
            </div>
        </div>
    );
}

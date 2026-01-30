import { AlertTriangle, Map, Route } from "lucide-react";

export function QuickActions() {
    const actions = [
        {
            icon: Map,
            label: "View Hazard Map",
            description: "Interactive risk visualization",
            disabled: true,
        },
        {
            icon: AlertTriangle,
            label: "Check Alerts",
            description: "Active warnings & notifications",
            disabled: true,
        },
        {
            icon: Route,
            label: "Plan Safe Route",
            description: "Hazard-aware navigation",
            disabled: true,
        },
    ];

    return (
        <div className="bg-white rounded-lg border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">
                Quick Actions
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {actions.map((action) => {
                    const Icon = action.icon;
                    return (
                        <button
                            key={action.label}
                            disabled={action.disabled}
                            className="flex flex-col items-center gap-3 p-4 rounded-lg border-2 border-dashed border-slate-200 bg-slate-50 opacity-50 cursor-not-allowed transition-all"
                            title="Available once system is fully active"
                        >
                            <div className="p-3 bg-slate-100 rounded-lg">
                                <Icon className="h-6 w-6 text-slate-400" />
                            </div>
                            <div className="text-center">
                                <p className="text-sm font-medium text-slate-600">
                                    {action.label}
                                </p>
                                <p className="text-xs text-slate-500 mt-1">
                                    {action.description}
                                </p>
                            </div>
                        </button>
                    );
                })}
            </div>

            <div className="mt-4 pt-4 border-t border-slate-100">
                <p className="text-xs text-slate-500 text-center">
                    Actions will be enabled once all system components are operational
                </p>
            </div>
        </div>
    );
}

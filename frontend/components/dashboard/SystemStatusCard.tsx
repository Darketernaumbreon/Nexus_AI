import { useSystemHealth } from "@/hooks/useSystemHealth";
import { Activity, AlertCircle, CheckCircle, Clock } from "lucide-react";

export function SystemStatusCard() {
    const { data: health, isLoading } = useSystemHealth();

    const getStatusConfig = () => {
        if (isLoading || !health) {
            return {
                icon: Activity,
                color: "text-gray-500",
                bgColor: "bg-gray-100",
                label: "CHECKING...",
            };
        }

        switch (health.status) {
            case "ONLINE":
                return {
                    icon: CheckCircle,
                    color: "text-green-600",
                    bgColor: "bg-green-100",
                    label: "ONLINE",
                };
            case "DEGRADED":
                return {
                    icon: AlertCircle,
                    color: "text-yellow-600",
                    bgColor: "bg-yellow-100",
                    label: "DEGRADED",
                };
            case "OFFLINE":
                return {
                    icon: AlertCircle,
                    color: "text-red-600",
                    bgColor: "bg-red-100",
                    label: "OFFLINE",
                };
        }
    };

    const config = getStatusConfig();
    const Icon = config.icon;

    return (
        <div className="bg-white rounded-lg border border-slate-200 p-6">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-slate-800">System Status</h3>
                <div
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${config.bgColor}`}
                >
                    <Icon className={`h-4 w-4 ${config.color}`} />
                    <span className={`text-sm font-medium ${config.color}`}>
                        {config.label}
                    </span>
                </div>
            </div>

            <div className="space-y-3">
                {/* API Latency */}
                <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-600">API Latency</span>
                    <span className="font-medium text-slate-800">
                        {health?.latencyMs ? `${health.latencyMs}ms` : "—"}
                    </span>
                </div>

                {/* Last Updated */}
                <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-600 flex items-center gap-1">
                        <Clock className="h-3.5 w-3.5" />
                        Last Updated
                    </span>
                    <span className="font-medium text-slate-800">
                        {health?.lastChecked
                            ? new Date(health.lastChecked).toLocaleTimeString()
                            : "—"}
                    </span>
                </div>

                {/* Backend Status */}
                <div className="pt-3 border-t border-slate-100">
                    <p className="text-xs text-slate-500">
                        AI prediction engine is {health?.status === "ONLINE" ? "operational" : "unavailable"}
                    </p>
                </div>
            </div>
        </div>
    );
}

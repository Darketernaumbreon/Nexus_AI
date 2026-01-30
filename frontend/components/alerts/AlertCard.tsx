import { Alert } from "@/types/alert";
import { AlertSeverityBadge } from "./AlertSeverityBadge";
import { Droplets, Mountain, Clock, MapPin } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface AlertCardProps {
    alert: Alert;
}

export function AlertCard({ alert }: AlertCardProps) {
    const isP0 = alert.priority === "P0";
    const isCritical = alert.severity === "CRITICAL";
    const Icon = alert.hazard_type === "flood" ? Droplets : Mountain;

    const validUntilDate = new Date(alert.valid_until);
    const timeRemaining = formatDistanceToNow(validUntilDate, { addSuffix: true });

    return (
        <div
            className={cn(
                "bg-white rounded-lg border-2 p-4 sm:p-5 transition-all",
                isP0 || isCritical
                    ? "border-red-500 shadow-lg shadow-red-500/20"
                    : "border-slate-200 hover:border-slate-300"
            )}
            role={isCritical ? "alert" : undefined}
            aria-live={isP0 ? "assertive" : undefined}
        >
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-3">
                <div className="flex items-center gap-3">
                    <div
                        className={cn(
                            "p-2 rounded-lg flex-shrink-0",
                            alert.hazard_type === "flood" ? "bg-blue-100" : "bg-orange-100"
                        )}
                        aria-hidden="true"
                    >
                        <Icon
                            className={cn(
                                "h-5 w-5",
                                alert.hazard_type === "flood"
                                    ? "text-blue-600"
                                    : "text-orange-600"
                            )}
                        />
                    </div>
                    <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                            <h3 className="font-semibold text-slate-800 capitalize text-base sm:text-lg">
                                {alert.hazard_type} Alert
                            </h3>
                            {isP0 && (
                                <span className="px-2 py-0.5 bg-red-600 text-white text-xs font-bold rounded">
                                    P0
                                </span>
                            )}
                        </div>
                        <p className="text-xs text-slate-500 mt-0.5">
                            Priority: {alert.priority}
                        </p>
                    </div>
                </div>
                <AlertSeverityBadge severity={alert.severity} />
            </div>

            {/* Message */}
            <p className="text-slate-700 mb-4 leading-relaxed text-base">
                {alert.message}
            </p>

            {/* Recommended Action */}
            <div className="bg-slate-50 rounded-lg p-3 mb-4">
                <p className="text-xs font-semibold text-slate-600 mb-1 uppercase tracking-wide">
                    Recommended Action:
                </p>
                <p className="text-sm sm:text-base text-slate-800 leading-relaxed">
                    {alert.recommended_action}
                </p>
            </div>

            {/* Footer */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-xs text-slate-500">
                <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
                    <div className="flex items-center gap-1">
                        <Clock className="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
                        <span>Valid {timeRemaining}</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <MapPin className="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
                        <span>{alert.affected_radius_km} km radius</span>
                    </div>
                </div>
                <span className="text-slate-400">ID: {alert.alert_id.slice(0, 8)}</span>
            </div>
        </div>
    );
}

// Helper function (inline to avoid import issues)
function cn(...classes: (string | boolean | undefined)[]) {
    return classes.filter(Boolean).join(" ");
}

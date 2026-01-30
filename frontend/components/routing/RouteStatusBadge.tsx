import { RouteStatus } from "@/types/route";

interface RouteStatusBadgeProps {
    status: RouteStatus;
}

const STATUS_CONFIG: Record<
    RouteStatus,
    { color: string; bgColor: string; label: string }
> = {
    SAFE: {
        color: "text-green-700",
        bgColor: "bg-green-100",
        label: "SAFE",
    },
    CAUTION: {
        color: "text-yellow-700",
        bgColor: "bg-yellow-100",
        label: "CAUTION",
    },
    PARTIAL: {
        color: "text-orange-700",
        bgColor: "bg-orange-100",
        label: "PARTIAL",
    },
    BLOCKED: {
        color: "text-red-700",
        bgColor: "bg-red-100",
        label: "BLOCKED",
    },
};

export function RouteStatusBadge({ status }: RouteStatusBadgeProps) {
    const config = STATUS_CONFIG[status];

    return (
        <span
            className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${config.bgColor} ${config.color}`}
        >
            {config.label}
        </span>
    );
}

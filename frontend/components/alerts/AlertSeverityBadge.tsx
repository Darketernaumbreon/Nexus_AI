import { SeverityLevel } from "@/types/alert";

interface AlertSeverityBadgeProps {
    severity: SeverityLevel;
}

const SEVERITY_CONFIG: Record<
    SeverityLevel,
    { color: string; bgColor: string; label: string }
> = {
    CRITICAL: {
        color: "text-red-700",
        bgColor: "bg-red-100",
        label: "CRITICAL",
    },
    HIGH: {
        color: "text-orange-700",
        bgColor: "bg-orange-100",
        label: "HIGH",
    },
    MEDIUM: {
        color: "text-yellow-700",
        bgColor: "bg-yellow-100",
        label: "MEDIUM",
    },
    LOW: {
        color: "text-blue-700",
        bgColor: "bg-blue-100",
        label: "LOW",
    },
};

export function AlertSeverityBadge({ severity }: AlertSeverityBadgeProps) {
    const config = SEVERITY_CONFIG[severity];

    return (
        <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bgColor} ${config.color}`}
        >
            {config.label}
        </span>
    );
}

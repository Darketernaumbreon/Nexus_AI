"use client";

import { useSystemHealth } from "@/hooks/useSystemHealth";
import { SystemStatusCard } from "@/components/dashboard/SystemStatusCard";
import { RiskSummaryCard } from "@/components/dashboard/RiskSummaryCard";
import { WeatherSummaryCard } from "@/components/dashboard/WeatherSummaryCard";
import { QuickActions } from "@/components/dashboard/QuickActions";
import { AlertCircle } from "lucide-react";

export default function DashboardPage() {
    const { data: health } = useSystemHealth();

    return (
        <div className="space-y-6">
            {/* Page Header */}
            <div>
                <h1 className="text-3xl font-bold text-slate-800">Dashboard</h1>
                <p className="text-slate-600 mt-1">
                    Multi-hazard decision intelligence system
                </p>
            </div>

            {/* Warning Banner (if backend offline) */}
            {health?.status === "OFFLINE" && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
                    <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                    <div>
                        <p className="text-sm font-medium text-red-800">
                            Backend System Offline
                        </p>
                        <p className="text-sm text-red-700 mt-1">
                            The AI prediction engine is currently unavailable. All prediction
                            features are disabled until the system comes back online.
                        </p>
                    </div>
                </div>
            )}

            {/* System Status Card (full width) */}
            <SystemStatusCard />

            {/* Risk & Weather Cards (2-column grid) */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <RiskSummaryCard />
                <WeatherSummaryCard />
            </div>

            {/* Quick Actions */}
            <QuickActions />
        </div>
    );
}

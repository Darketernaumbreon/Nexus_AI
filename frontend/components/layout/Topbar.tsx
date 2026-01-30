"use client";

import { Menu } from "lucide-react";
import { useUIStore } from "@/store/ui-store";

export function Topbar() {
    const { toggleSidebar } = useUIStore();

    return (
        <div className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-4 lg:px-6">
            {/* Mobile Menu Button */}
            <button
                onClick={toggleSidebar}
                className="p-2 rounded-lg hover:bg-slate-100 transition-colors lg:hidden focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Toggle sidebar menu"
            >
                <Menu className="h-6 w-6 text-slate-700" />
            </button>

            {/* App Title (Mobile) */}
            <h1 className="text-lg font-bold text-slate-800 lg:hidden">
                NEXUS AI
            </h1>

            {/* Desktop Title */}
            <div className="hidden lg:block">
                <h2 className="text-lg font-semibold text-slate-800">
                    Multi-Hazard Decision Dashboard
                </h2>
            </div>

            {/* User Role */}
            <div className="flex items-center gap-2">
                <div className="hidden sm:block text-right">
                    <p className="text-sm font-medium text-slate-700">System Operator</p>
                    <p className="text-xs text-slate-500">Emergency Response</p>
                </div>
                <div className="h-9 w-9 rounded-full bg-blue-600 flex items-center justify-center">
                    <span className="text-sm font-semibold text-white">SO</span>
                </div>
            </div>
        </div>
    );
}

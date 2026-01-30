"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard,
    Map,
    AlertTriangle,
    Route,
    X
} from "lucide-react";
import { useUIStore } from "@/store/ui-store";
import { cn } from "@/lib/utils";
import { useEffect } from "react";

const navigation = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Map", href: "/map", icon: Map },
    { name: "Alerts", href: "/alerts", icon: AlertTriangle },
    { name: "Routing", href: "/routing", icon: Route },
];

export function Sidebar() {
    const pathname = usePathname();
    const { sidebarOpen, closeSidebar } = useUIStore();

    // Close sidebar on mobile when route changes
    useEffect(() => {
        if (window.innerWidth < 1024) {
            closeSidebar();
        }
    }, [pathname, closeSidebar]);

    return (
        <>
            {/* Mobile Overlay */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 lg:hidden"
                    onClick={closeSidebar}
                    aria-hidden="true"
                />
            )}

            {/* Sidebar */}
            <div
                className={cn(
                    "fixed lg:relative inset-y-0 left-0 z-50 flex flex-col bg-slate-900 text-white transition-transform duration-300",
                    "w-64",
                    sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
                )}
            >
                {/* Header */}
                <div className="flex h-16 items-center justify-between px-4 border-b border-slate-800">
                    <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                        NEXUS AI
                    </h1>
                    <button
                        onClick={closeSidebar}
                        className="p-2 rounded-lg hover:bg-slate-800 transition-colors lg:hidden"
                        aria-label="Close sidebar"
                    >
                        <X className="h-5 w-5" />
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-3 py-4 space-y-1" role="navigation" aria-label="Main navigation">
                    {navigation.map((item) => {
                        const isActive = pathname === item.href;
                        const Icon = item.icon;

                        return (
                            <Link
                                key={item.name}
                                href={item.href}
                                className={cn(
                                    "flex items-center gap-3 px-3 py-3 rounded-lg transition-all",
                                    "hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500",
                                    isActive
                                        ? "bg-blue-600 text-white shadow-lg shadow-blue-600/50"
                                        : "text-slate-300"
                                )}
                                aria-current={isActive ? "page" : undefined}
                            >
                                <Icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                                <span className="font-medium text-base">{item.name}</span>
                            </Link>
                        );
                    })}
                </nav>

                {/* Footer */}
                <div className="p-4 border-t border-slate-800">
                    <div className="text-xs text-slate-400">
                        <p className="font-semibold text-slate-300">Multi-Hazard System</p>
                        <p>v1.0.0</p>
                    </div>
                </div>
            </div>
        </>
    );
}

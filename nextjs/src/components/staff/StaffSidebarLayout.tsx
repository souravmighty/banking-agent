"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";
import { usePathname } from "next/navigation";
import { 
  Menu, 
  X,
  Landmark, 
  Sparkles, 
  ClipboardList, 
  UserCheck, 
  LogOut,
  ChevronRight
} from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

interface StaffSidebarLayoutProps {
  children: React.ReactNode;
}

export function StaffSidebarLayout({ children }: StaffSidebarLayoutProps) {
  const { user, loading, logout } = useAuth();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState<boolean>(false);
  const [mounted, setMounted] = useState<boolean>(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Close mobile drawer on route navigation
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  if (!mounted || loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-[#060814] flex items-center justify-center text-slate-500 dark:text-slate-400">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-600 flex items-center justify-center animate-pulse shadow-lg shadow-indigo-500/20">
            <Landmark className="h-5 w-5 text-white" />
          </div>
          <span className="text-xs font-semibold">Loading Business Intelligence...</span>
        </div>
      </div>
    );
  }

  const isCopilotActive =
    pathname.startsWith("/staff/copilot") ||
    pathname.startsWith("/staff/analytics-copilot");

  const isDemoRequestsActive =
    pathname.startsWith("/staff/demo-requests");

  const isDemoCustomersActive =
    pathname.startsWith("/staff/demo-customers");

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#060814] text-slate-900 dark:text-slate-100 flex flex-col font-sans transition-colors duration-200">
      {/* Top Header Navigation Bar */}
      <header className="h-16 border-b border-slate-200 dark:border-slate-800/80 bg-white/90 dark:bg-slate-950/80 backdrop-blur-md px-4 sm:px-6 lg:px-8 flex items-center justify-between sticky top-0 z-40 shadow-sm transition-colors duration-200">
        {/* Left: Brand + Desktop Navigation Tabs */}
        <div className="flex items-center gap-6">
          {/* Brand Logo */}
          <Link
            href="/staff/copilot"
            className="flex items-center gap-3 group focus:outline-none"
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-600 flex items-center justify-center border border-indigo-500/30 shadow-md shadow-indigo-500/20 flex-shrink-0 group-hover:scale-105 transition-transform">
              <Landmark className="h-5 w-5 text-white" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-extrabold tracking-tight text-slate-900 dark:text-white flex items-center gap-1.5">
                BankPilot
                <span className="text-[10px] px-1.5 py-0.5 rounded-md font-bold bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800/60 uppercase tracking-wider">
                  Enterprise
                </span>
              </span>
              <span className="text-[10px] text-slate-500 dark:text-slate-400 font-medium hidden sm:inline">
                Business & Product Intelligence
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Tabs */}
          <nav className="hidden md:flex items-center gap-1.5 p-1 bg-slate-100 dark:bg-slate-900/70 rounded-xl border border-slate-200 dark:border-slate-800 text-xs font-semibold">
            {/* Analytics Copilot (Primary Landing Tab) */}
            <Link
              href="/staff/copilot"
              className={`px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-2 ${
                isCopilotActive
                  ? "bg-indigo-600 text-white shadow-sm font-bold"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-slate-800/60"
              }`}
            >
              <Sparkles className="h-3.5 w-3.5 text-indigo-200" />
              <span>Analytics Copilot</span>
              {isCopilotActive && (
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse ml-0.5" />
              )}
            </Link>

            {/* Demo Requests Tab */}
            <Link
              href="/staff/demo-requests"
              className={`px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-2 ${
                isDemoRequestsActive
                  ? "bg-indigo-600 text-white shadow-sm font-bold"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-slate-800/60"
              }`}
            >
              <ClipboardList className="h-3.5 w-3.5" />
              <span>Demo Requests</span>
            </Link>

            {/* Demo Customers Tab */}
            <Link
              href="/staff/demo-customers"
              className={`px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-2 ${
                isDemoCustomersActive
                  ? "bg-indigo-600 text-white shadow-sm font-bold"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-slate-800/60"
              }`}
            >
              <UserCheck className="h-3.5 w-3.5" />
              <span>Demo Customers</span>
            </Link>
          </nav>
        </div>

        {/* Right: Actions, User Profile & Logout */}
        <div className="flex items-center gap-2.5 sm:gap-3">
          {/* User Email Pill */}
          <span className="hidden lg:inline-flex text-xs text-slate-700 dark:text-slate-300 font-medium bg-slate-100 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 px-3 py-1.5 rounded-xl shadow-inner max-w-[200px] truncate">
            {user?.email || "Staff Admin"}
          </span>

          {/* Sign Out Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => logout()}
            className="border-slate-200 dark:border-slate-800 hover:bg-rose-50 dark:hover:bg-rose-500/10 hover:border-rose-300 dark:hover:border-rose-500/30 text-slate-600 dark:text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 h-9 px-3 text-xs font-semibold rounded-xl transition-colors hidden sm:inline-flex items-center gap-1.5"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span>Sign Out</span>
          </Button>

          {/* Mobile Menu Toggle Button */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 h-9 w-9 rounded-xl border border-slate-200 dark:border-slate-800"
            aria-label="Toggle navigation menu"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>
      </header>

      {/* Mobile Drawer Navigation Menu */}
      {mobileOpen && (
        <div className="md:hidden border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 p-4 space-y-2 shadow-lg transition-all animate-in slide-in-from-top-2 duration-200 z-30">
          <div className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider px-2">
            Operations Navigation
          </div>
          <Link
            href="/staff/copilot"
            className={`flex items-center justify-between p-3 rounded-xl text-sm font-semibold transition-colors ${
              isCopilotActive
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-900"
            }`}
          >
            <div className="flex items-center gap-2.5">
              <Sparkles className="h-4 w-4" />
              <span>Analytics Copilot</span>
            </div>
            <ChevronRight className="h-4 w-4 opacity-70" />
          </Link>

          <Link
            href="/staff/demo-requests"
            className={`flex items-center justify-between p-3 rounded-xl text-sm font-semibold transition-colors ${
              isDemoRequestsActive
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-900"
            }`}
          >
            <div className="flex items-center gap-2.5">
              <ClipboardList className="h-4 w-4" />
              <span>Demo Requests</span>
            </div>
            <ChevronRight className="h-4 w-4 opacity-70" />
          </Link>

          <Link
            href="/staff/demo-customers"
            className={`flex items-center justify-between p-3 rounded-xl text-sm font-semibold transition-colors ${
              isDemoCustomersActive
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-900"
            }`}
          >
            <div className="flex items-center gap-2.5">
              <UserCheck className="h-4 w-4" />
              <span>Demo Customers Pool</span>
            </div>
            <ChevronRight className="h-4 w-4 opacity-70" />
          </Link>

          <div className="pt-2 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
            <div className="text-xs text-slate-500 dark:text-slate-400 truncate max-w-[200px]">
              {user?.email}
            </div>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => logout()}
              className="text-xs rounded-lg h-8 gap-1"
            >
              <LogOut className="h-3.5 w-3.5" />
              <span>Sign Out</span>
            </Button>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col w-full">{children}</main>
    </div>
  );
}

// Export alias for clean imports
export const StaffLayout = StaffSidebarLayout;

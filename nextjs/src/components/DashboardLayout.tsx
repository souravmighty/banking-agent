"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { 
  Landmark, 
  MessageSquare, 
  LayoutDashboard, 
  Wallet, 
  History, 
  CreditCard, 
  TrendingUp, 
  PiggyBank, 
  LogOut, 
  User, 
  CheckCircle, 
  AlertTriangle 
} from "lucide-react";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, customerContext, loading, logout } = useAuth();
  const pathname = usePathname();

  if (loading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-[#f7f8fc]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-[#1a1f71] text-white flex items-center justify-center animate-bounce shadow-xl">
            <Landmark className="h-7 w-7" />
          </div>
          <p className="text-sm font-bold text-slate-500 animate-pulse">Initializing Secure Session...</p>
        </div>
      </div>
    );
  }

  if (!user || !customerContext) {
    return null; // AuthProvider handles redirect
  }

  const navItems = [
    { name: "AI Assistant", href: "/", icon: MessageSquare },
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Accounts", href: "/accounts", icon: Wallet },
    { name: "Transactions", href: "/transactions", icon: History },
    { name: "Credit Cards", href: "/credit-cards", icon: CreditCard },
    { name: "Loans", href: "/loans", icon: TrendingUp },
    { name: "Fixed Deposits", href: "/fixed-deposits", icon: PiggyBank },
  ];

  // Helper for segment badge color styling
  const getSegmentColor = (segment: string) => {
    switch (segment?.toUpperCase()) {
      case "WEALTH":
        return "bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-purple-100 ring-2 ring-purple-100";
      case "PREMIUM":
        return "bg-gradient-to-r from-amber-500 to-yellow-600 text-white shadow-amber-100 ring-2 ring-amber-100";
      default:
        return "bg-slate-100 text-slate-700 ring-1 ring-slate-200";
    }
  };

  return (
    <div className="flex h-screen bg-[#f7f8fc] overflow-hidden text-slate-900 font-sans">
      {/* Sidebar navigation */}
      <aside className="hidden md:flex flex-col w-72 bg-[#1a1f71] text-white shrink-0 shadow-2xl relative z-20">
        {/* Sidebar Header branding */}
        <div className="flex items-center gap-3 p-6 border-b border-blue-900/30">
          <div className="w-10 h-10 rounded-xl bg-white text-[#1a1f71] flex items-center justify-center shadow-lg ring-1 ring-white/10">
            <Landmark className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white leading-tight">ABC Bank</h1>
            <p className="text-[10px] font-bold text-[#f0a500] uppercase tracking-widest">Portal & Copilot</p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center gap-3.5 px-4 py-3.5 rounded-xl text-sm font-semibold transition-all duration-200 group relative ${
                  isActive
                    ? "bg-[#f0a500] text-[#1a1f71] shadow-lg shadow-yellow-500/10 scale-[1.02]"
                    : "text-blue-100/70 hover:text-white hover:bg-blue-900/20"
                }`}
              >
                <Icon className={`w-5 h-5 transition-transform group-hover:scale-110 ${isActive ? "text-[#1a1f71]" : "text-blue-200/50 group-hover:text-blue-100"}`} />
                {item.name}
                {isActive && (
                  <div className="absolute right-3 w-1.5 h-1.5 rounded-full bg-[#1a1f71]" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Sidebar Footer context & controls */}
        <div className="p-4 border-t border-blue-900/30 bg-blue-950/20 space-y-4">
          <div className="bg-[#1e237e]/60 p-4 rounded-2xl border border-blue-900/20">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-8 h-8 rounded-full bg-blue-800/80 flex items-center justify-center">
                <User className="h-4 w-4 text-blue-200" />
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-bold text-white truncate">{customerContext.name}</p>
                <p className="text-[10px] text-blue-200/60 truncate font-mono">ID: {customerContext.customer_id}</p>
              </div>
            </div>
            
            {/* Segment badge */}
            <div className="mt-2.5">
              <span className={`inline-flex px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wider uppercase shadow-sm ${getSegmentColor(customerContext.customer_segment)}`}>
                {customerContext.customer_segment}
              </span>
            </div>
          </div>

          <button
            onClick={logout}
            className="w-full flex items-center justify-center gap-2.5 px-4 py-3 bg-red-500/10 hover:bg-red-500/20 text-red-200 hover:text-white rounded-xl text-sm font-bold transition-all border border-red-500/10"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main content viewport */}
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Top Header */}
        <header className="bg-white border-b border-slate-100 h-16 shrink-0 flex items-center justify-between px-6 md:px-8 relative z-10 shadow-sm shadow-slate-100/10">
          {/* Mobile hamburger placeholder / Title */}
          <div className="flex items-center gap-4">
            <div className="md:hidden w-8 h-8 rounded-lg bg-[#1a1f71] text-white flex items-center justify-center">
              <Landmark className="h-5 w-5" />
            </div>
            <span className="text-md font-bold text-[#1a1f71] capitalize md:text-lg">
              {pathname === "/" ? "AI Banking Copilot" : pathname.replace("/", "").replace("-", " ")}
            </span>
          </div>

          {/* KYC Status & Controls */}
          <div className="flex items-center gap-4">
            {customerContext.kyc_status === "VERIFIED" ? (
              <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-100 text-xs font-semibold">
                <CheckCircle className="w-3.5 h-3.5" />
                KYC Verified
              </div>
            ) : (
              <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-100 text-xs font-semibold animate-pulse">
                <AlertTriangle className="w-3.5 h-3.5" />
                KYC Pending
              </div>
            )}

            <div className="md:hidden flex items-center gap-3">
              <span className="text-xs font-bold text-slate-700 max-w-[80px] truncate">{customerContext.name}</span>
              <button onClick={logout} className="p-1.5 text-slate-400 hover:text-red-500 transition-colors">
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </header>

        {/* Content view */}
        <main className="flex-1 overflow-y-auto bg-[#f7f8fc] relative">
          {children}
        </main>
      </div>
    </div>
  );
}

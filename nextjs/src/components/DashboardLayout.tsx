"use client";

/* eslint-disable @next/next/no-img-element */

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { AuthLoader } from "@/components/AuthProvider";
import { 
  Landmark, 
  MessageSquare, 
  LayoutDashboard, 
  LogOut, 
  ChevronDown,
  User
} from "lucide-react";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, customerContext, loading, logout } = useAuth();
  const pathname = usePathname();
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [navbarImgError, setNavbarImgError] = useState(false);
  const [dropdownImgError, setDropdownImgError] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const isValidPhotoURL = (url: string | null | undefined): boolean => {
    if (!url) return false;
    const trimmed = url.trim();
    if (trimmed === "" || trimmed === "undefined" || trimmed === "null") return false;
    
    // Check if it's a default Google initials avatar
    // If the URL is from googleusercontent.com and contains '/a/' but NOT '/a-/', it is a default initials avatar
    if (trimmed.includes("googleusercontent.com") && trimmed.includes("/a/") && !trimmed.includes("/a-/")) {
      return false;
    }
    
    return trimmed.startsWith("http://") || trimmed.startsWith("https://") || trimmed.startsWith("/");
  };

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsProfileOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (loading) {
    return <AuthLoader />;
  }

  if (!user || !customerContext) {
    return null; // AuthProvider handles redirect
  }

  // Segment badge color styling helper
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

  // Get user initials for avatar
  const getInitials = (name: string) => {
    if (!name) return "U";
    return name
      .split(" ")
      .map((n) => n[0])
      .slice(0, 2)
      .join("")
      .toUpperCase();
  };

  const isChatActive = pathname === "/";
  const isDashboardActive = pathname !== "/";

  return (
    <div className="flex flex-col h-screen bg-[#f7f8fc] text-slate-900 font-sans overflow-hidden">
      {/* Global Top Navbar */}
      <header className="bg-white border-b border-slate-200 h-16 shrink-0 flex items-center justify-between px-4 md:px-8 relative z-30 shadow-sm shadow-slate-100/10">
        {/* Left Side: Brand Logo */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-[#1a1f71] text-white flex items-center justify-center shadow-md shrink-0">
            <Landmark className="h-5 w-5" />
          </div>
          <div className="hidden sm:block">
            <h1 className="text-sm font-bold tracking-tight text-[#1a1f71] leading-tight">ABC Bank</h1>
            <p className="text-[9px] font-bold text-[#f0a500] uppercase tracking-widest">Premium Portal</p>
          </div>
        </div>

        {/* Center Side: Option 1 Segmented Pill Switcher */}
        <div className="bg-slate-100 p-1 rounded-full flex items-center gap-0.5 border border-slate-200/50 shadow-inner">
          <Link
            href="/"
            className={`flex items-center gap-2 px-3 sm:px-4 py-1.5 rounded-full text-xs font-bold tracking-wide transition-all duration-200 ${
              isChatActive
                ? "bg-[#1a1f71] text-white shadow-md scale-[1.02]"
                : "text-slate-600 hover:text-slate-950 hover:bg-slate-200/50"
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">AI Assistant</span>
          </Link>
          <Link
            href="/dashboard"
            className={`flex items-center gap-2 px-3 sm:px-4 py-1.5 rounded-full text-xs font-bold tracking-wide transition-all duration-200 ${
              isDashboardActive
                ? "bg-[#1a1f71] text-white shadow-md scale-[1.02]"
                : "text-slate-600 hover:text-slate-950 hover:bg-slate-200/50"
            }`}
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Dashboard</span>
          </Link>
        </div>

        {/* Right Side: User Menu & Profile Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setIsProfileOpen(!isProfileOpen)}
            className="flex items-center gap-2 p-1.5 rounded-full hover:bg-slate-100 transition-all duration-200 border border-transparent hover:border-slate-200/60"
            aria-label="User profile menu"
          >
            <div className="w-8 h-8 rounded-full overflow-hidden bg-blue-100 text-[#1a1f71] flex items-center justify-center font-bold text-xs shadow-inner shrink-0 border border-slate-200/50">
              {isValidPhotoURL(user?.photoURL) && !navbarImgError ? (
                <img
                  src={user!.photoURL!}
                  alt={customerContext.name}
                  className="w-full h-full object-cover"
                  onError={() => setNavbarImgError(true)}
                />
              ) : customerContext?.name ? (
                getInitials(customerContext.name)
              ) : (
                <User className="w-4 h-4 text-[#1a1f71]" />
              )}
            </div>
            <span className="hidden md:inline text-xs font-bold text-slate-700 truncate max-w-[120px]">
              {customerContext.name}
            </span>
            <ChevronDown className="w-4 h-4 text-slate-400" />
          </button>

          {/* Profile Dropdown Card */}
          {isProfileOpen && (
            <div className="absolute right-0 mt-2 w-64 bg-white rounded-2xl shadow-2xl border border-slate-100 py-3 z-50 animate-in fade-in slide-in-from-top-3 duration-200">
              {/* User Profile Context */}
              <div className="px-4 py-3 flex items-center gap-3">
                <div className="w-12 h-12 rounded-full overflow-hidden bg-blue-100 text-[#1a1f71] flex items-center justify-center font-extrabold text-sm shadow-inner shrink-0 border border-slate-100">
                  {isValidPhotoURL(user?.photoURL) && !dropdownImgError ? (
                    <img
                      src={user!.photoURL!}
                      alt={customerContext.name}
                      className="w-full h-full object-cover"
                      onError={() => setDropdownImgError(true)}
                    />
                  ) : customerContext?.name ? (
                    getInitials(customerContext.name)
                  ) : (
                    <User className="w-6 h-6 text-[#1a1f71]" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-[10px] font-bold text-[#f0a500] uppercase tracking-wider">Secure Account</p>
                  <p className="text-sm font-extrabold text-slate-800 truncate" title={customerContext.name}>
                    {customerContext.name}
                  </p>
                  <p className="text-[9px] text-slate-400 font-mono">ID: {customerContext.customer_id}</p>
                </div>
              </div>

              {/* Segment badge */}
              <div className="px-4 py-2">
                <span className={`inline-flex px-3 py-1 rounded-full text-[10px] font-bold tracking-wider uppercase shadow-sm ${getSegmentColor(customerContext.customer_segment)}`}>
                  {customerContext.customer_segment}
                </span>
              </div>

              <div className="border-t border-slate-100 my-2"></div>

              {/* Sign Out Item */}
              <div className="px-2">
                <button
                  onClick={logout}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-bold text-red-600 hover:bg-red-50 hover:text-red-700 transition-all duration-150"
                >
                  <LogOut className="w-4 h-4 text-red-500" />
                  <span>Sign Out Securely</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Main Viewport Container */}
      <main className="flex-1 overflow-hidden bg-[#f7f8fc]">
        {children}
      </main>
    </div>
  );
}

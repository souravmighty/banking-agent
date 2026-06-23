"use client";

import React from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { useAuth } from "@/hooks/useAuth";
import { 
  CheckCircle, 
  PiggyBank, 
  Landmark, 
  CreditCard, 
  Home, 
  ShoppingBag, 
  Briefcase, 
  Utensils, 
  Zap,
  DollarSign
} from "lucide-react";

export default function DashboardPage() {
  const { customerContext } = useAuth();

  if (!customerContext) return null;

  const firstName = customerContext.name ? customerContext.name.split(" ")[0] : "Casey";

  // Indian Rupee formatting helper
  const formatRupee = (value: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2
    }).format(value);
  };

  return (
    <DashboardLayout>
      <div className="p-6 md:p-8 space-y-6 max-w-7xl mx-auto animate-fade-in bg-[#f7f8fc]">
        
        {/* Header Greeting & Last Login */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-2xl md:text-3xl font-extrabold text-[#1a1f71] tracking-tight">
              Good morning, {firstName}
            </h2>
          </div>
          <div className="text-xs sm:text-sm font-semibold text-slate-400">
            Last login: today, 9:14 AM
          </div>
        </div>

        {/* KYC & Account Standing Status Bar */}
        <div className="flex items-center gap-3 p-4 bg-amber-50/50 border border-amber-200 rounded-2xl text-amber-800 text-xs sm:text-sm font-medium shadow-sm">
          <CheckCircle className="w-5 h-5 text-amber-600 shrink-0" />
          <span>
            KYC verified &middot; Risk profile: <strong className="font-bold">Low</strong> &middot; Account in good standing
          </span>
        </div>

        {/* YOUR ACCOUNTS Section */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500">Your Accounts</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Savings Account */}
            <div className="bg-white border border-slate-100 shadow-lg shadow-slate-100/50 rounded-3xl p-6 relative overflow-hidden flex flex-col justify-between h-44 hover:shadow-xl transition-shadow duration-200">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-3.5">
                  <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-[#1a1f71] flex items-center justify-center shrink-0">
                    <PiggyBank className="h-6 w-6" />
                  </div>
                  <div>
                    <h4 className="font-extrabold text-slate-800 text-md">Savings account</h4>
                    <p className="text-xs font-bold text-slate-400 font-mono">&bull;&bull; 7890</p>
                  </div>
                </div>
                <span className="inline-flex px-3 py-1 rounded-full text-[11px] font-bold tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-100">
                  Active
                </span>
              </div>
              <div className="space-y-0.5">
                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Available balance</p>
                <p className="text-3xl font-extrabold text-[#1a1f71] tracking-tight">{formatRupee(284650.50)}</p>
              </div>
              <div className="text-[11px] font-semibold text-slate-400 border-t border-slate-50 pt-2.5">
                Central Square, Mumbai &middot; ABCB0001234
              </div>
            </div>

            {/* Current Account */}
            <div className="bg-white border border-slate-100 shadow-lg shadow-slate-100/50 rounded-3xl p-6 relative overflow-hidden flex flex-col justify-between h-44 hover:shadow-xl transition-shadow duration-200">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-3.5">
                  <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-[#1a1f71] flex items-center justify-center shrink-0">
                    <Landmark className="h-6 w-6" />
                  </div>
                  <div>
                    <h4 className="font-extrabold text-slate-800 text-md">Current account</h4>
                    <p className="text-xs font-bold text-slate-400 font-mono">&bull;&bull; 4521</p>
                  </div>
                </div>
                <span className="inline-flex px-3 py-1 rounded-full text-[11px] font-bold tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-100">
                  Active
                </span>
              </div>
              <div className="space-y-0.5">
                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Available balance</p>
                <p className="text-3xl font-extrabold text-[#1a1f71] tracking-tight">{formatRupee(64200.00)}</p>
              </div>
              <div className="text-[11px] font-semibold text-slate-400 border-t border-slate-50 pt-2.5">
                MG Road, Bengaluru &middot; ABCB0005678
              </div>
            </div>

          </div>
        </div>

        {/* YOUR PRODUCTS Section */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500">Your Products</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

            {/* Credit Card Card */}
            <div className="bg-white border border-slate-100 shadow-lg shadow-slate-100/50 rounded-3xl p-6 flex flex-col justify-between h-44 hover:shadow-xl transition-shadow duration-200">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-50 text-[#1a1f71] flex items-center justify-center shrink-0">
                  <CreditCard className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <h4 className="font-extrabold text-slate-800 text-sm">Credit card</h4>
                  <div className="flex justify-between items-baseline mt-2">
                    <span className="text-xs font-semibold text-slate-400">Outstanding</span>
                    <span className="font-extrabold text-slate-800 text-sm">{formatRupee(15000)}</span>
                  </div>
                  <div className="flex justify-between items-baseline mt-1">
                    <span className="text-xs font-semibold text-slate-400">Min due - 5 Jul</span>
                    <span className="font-extrabold text-slate-800 text-sm">{formatRupee(600)}</span>
                  </div>
                </div>
              </div>
              <div className="space-y-1.5">
                <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-purple-600 h-full rounded-full" style={{ width: "15%" }} />
                </div>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                  15% utilization &middot; Limit {formatRupee(1000000)}
                </p>
              </div>
            </div>

            {/* Personal Loan Card */}
            <div className="bg-white border border-slate-100 shadow-lg shadow-slate-100/50 rounded-3xl p-6 flex flex-col justify-between h-44 hover:shadow-xl transition-shadow duration-200">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-50 text-[#1a1f71] flex items-center justify-center shrink-0">
                  <Home className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <h4 className="font-extrabold text-slate-800 text-sm">Personal loan</h4>
                  <div className="flex justify-between items-baseline mt-2">
                    <span className="text-xs font-semibold text-slate-400">Outstanding</span>
                    <span className="font-extrabold text-slate-800 text-sm">{formatRupee(450000)}</span>
                  </div>
                  <div className="flex justify-between items-baseline mt-1">
                    <span className="text-xs font-semibold text-slate-400">Next EMI - 1 Jul</span>
                    <span className="font-extrabold text-slate-800 text-sm">{formatRupee(12500)}</span>
                  </div>
                </div>
              </div>
              <div className="space-y-1.5">
                <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-[#f0a500] h-full rounded-full" style={{ width: "75%" }} />
                </div>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                  48 of 60 months remaining
                </p>
              </div>
            </div>

            {/* Fixed Deposit Card */}
            <div className="bg-white border border-slate-100 shadow-lg shadow-slate-100/50 rounded-3xl p-6 flex flex-col justify-between h-44 hover:shadow-xl transition-shadow duration-200">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-50 text-[#1a1f71] flex items-center justify-center shrink-0">
                  <DollarSign className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <h4 className="font-extrabold text-slate-800 text-sm">Fixed deposit</h4>
                  <div className="flex justify-between items-baseline mt-2">
                    <span className="text-xs font-semibold text-slate-400">Current value</span>
                    <span className="font-extrabold text-slate-800 text-sm">{formatRupee(105500)}</span>
                  </div>
                  <div className="flex justify-between items-baseline mt-1">
                    <span className="text-xs font-semibold text-slate-400">Rate</span>
                    <span className="font-extrabold text-slate-800 text-sm">6.5% p.a.</span>
                  </div>
                </div>
              </div>
              <div className="space-y-1.5">
                <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-[#1a1f71] h-full rounded-full" style={{ width: "100%" }} />
                </div>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                  Matures 1 Jan 2026
                </p>
              </div>
            </div>

          </div>
        </div>

        {/* BOTTOM ROW GRID */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* RECENT TRANSACTIONS Card */}
          <div className="lg:col-span-2 bg-white border border-slate-100 shadow-lg shadow-slate-100/50 rounded-3xl p-6 space-y-4 hover:shadow-xl transition-shadow duration-200">
            <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500 pb-2 border-b border-slate-50">
              Recent Transactions
            </h3>
            <div className="divide-y divide-slate-50">
              
              {/* Row 1: Amazon */}
              <div className="flex items-center justify-between py-3.5 first:pt-0 last:pb-0">
                <div className="flex items-center gap-3.5">
                  <div className="w-10 h-10 rounded-xl bg-slate-50 text-slate-600 flex items-center justify-center shrink-0">
                    <ShoppingBag className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="font-bold text-slate-700 text-sm">Amazon</p>
                    <p className="text-xs text-slate-400">Shopping &bull; Today</p>
                  </div>
                </div>
                <p className="font-extrabold text-sm text-slate-800">
                  -{formatRupee(2450)}
                </p>
              </div>

              {/* Row 2: Salary */}
              <div className="flex items-center justify-between py-3.5 first:pt-0 last:pb-0">
                <div className="flex items-center gap-3.5">
                  <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
                    <Briefcase className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="font-bold text-slate-700 text-sm">Salary credit</p>
                    <p className="text-xs text-slate-400">Income &bull; Yesterday</p>
                  </div>
                </div>
                <p className="font-extrabold text-sm text-emerald-600">
                  +{formatRupee(85000)}
                </p>
              </div>

              {/* Row 3: Swiggy */}
              <div className="flex items-center justify-between py-3.5 first:pt-0 last:pb-0">
                <div className="flex items-center gap-3.5">
                  <div className="w-10 h-10 rounded-xl bg-slate-50 text-slate-600 flex items-center justify-center shrink-0">
                    <Utensils className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="font-bold text-slate-700 text-sm">Swiggy</p>
                    <p className="text-xs text-slate-400">Food &bull; 2 days ago</p>
                  </div>
                </div>
                <p className="font-extrabold text-sm text-slate-800">
                  -{formatRupee(540)}
                </p>
              </div>

              {/* Row 4: Electricity Bill */}
              <div className="flex items-center justify-between py-3.5 first:pt-0 last:pb-0">
                <div className="flex items-center gap-3.5">
                  <div className="w-10 h-10 rounded-xl bg-slate-50 text-slate-600 flex items-center justify-center shrink-0">
                    <Zap className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="font-bold text-slate-700 text-sm">Electricity bill</p>
                    <p className="text-xs text-slate-400">Utilities &bull; 3 days ago</p>
                  </div>
                </div>
                <p className="font-extrabold text-sm text-slate-800">
                  -{formatRupee(1820)}
                </p>
              </div>

            </div>
          </div>

          {/* RIGHT PANELS COLUMN */}
          <div className="flex flex-col gap-6">

            {/* CREDIT SCORE Card */}
            <div className="bg-white border border-slate-100 shadow-lg shadow-slate-100/50 rounded-3xl p-6 flex flex-col justify-between hover:shadow-xl transition-shadow duration-200">
              <div className="flex justify-between items-center pb-3 border-b border-slate-50">
                <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500">
                  Credit Score
                </h3>
                <span className="inline-flex px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-50 text-emerald-700 border border-emerald-100 uppercase tracking-wider">
                  Excellent
                </span>
              </div>
              <div className="py-4">
                <p className="text-5xl font-extrabold text-[#1a1f71] tracking-tight">750</p>
              </div>
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                Experian &middot; Updated 1 Dec 2024
              </div>
            </div>

            {/* BENEFICIARIES Card */}
            <div className="bg-white border border-slate-100 shadow-lg shadow-slate-100/50 rounded-3xl p-6 space-y-4 hover:shadow-xl transition-shadow duration-200 flex-1 flex flex-col justify-between">
              <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500 pb-2 border-b border-slate-50">
                Beneficiaries
              </h3>
              <div className="space-y-4 flex-1 flex flex-col justify-center">
                
                {/* Beneficiary 1: Mom's account */}
                <div className="flex items-center gap-3.5">
                  <div className="w-9 h-9 rounded-full bg-indigo-600 text-white text-xs font-bold flex items-center justify-center shrink-0">
                    MA
                  </div>
                  <div>
                    <p className="font-extrabold text-slate-700 text-sm leading-snug">Mom&apos;s account</p>
                    <p className="text-[11px] font-semibold text-slate-400 leading-none">HDFC Bank</p>
                  </div>
                </div>

                {/* Beneficiary 2: Raj Sharma */}
                <div className="flex items-center gap-3.5">
                  <div className="w-9 h-9 rounded-full bg-blue-900 text-white text-xs font-bold flex items-center justify-center shrink-0">
                    RS
                  </div>
                  <div>
                    <p className="font-extrabold text-slate-700 text-sm leading-snug">Raj Sharma</p>
                    <p className="text-[11px] font-semibold text-slate-400 leading-none">ICICI Bank</p>
                  </div>
                </div>

              </div>
            </div>

          </div>

        </div>

      </div>
    </DashboardLayout>
  );
}

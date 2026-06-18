"use client";

import React from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { useAuth } from "@/hooks/useAuth";
import { Award, Calendar, Sparkles } from "lucide-react";

export default function FixedDepositsPage() {
  const { customerContext } = useAuth();

  if (!customerContext) return null;

  const isPremium = customerContext.customer_segment?.toUpperCase() === "PREMIUM" || customerContext.customer_segment?.toUpperCase() === "WEALTH";

  const fdDetails = {
    fdNum: "FD-4491-0029-45",
    depositAmount: isPremium ? "$150,000.00" : "$20,000.00",
    interestRate: isPremium ? "5.45% p.a." : "4.90% p.a.",
    maturityAmount: isPremium ? "$166,350.00" : "$21,960.00",
    interestEarned: isPremium ? "$16,350.00" : "$1,960.00",
    tenure: "24 Months",
    maturityDate: "November 15, 2027",
    status: "ACTIVE",
  };

  return (
    <DashboardLayout>
      <div className="p-6 md:p-8 space-y-8 animate-fade-in">
        <div>
          <h2 className="text-3xl font-extrabold text-[#1a1f71] tracking-tight">Fixed Deposits</h2>
          <p className="text-sm text-slate-500">View and track your high-yield fixed deposit investment portfolios.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main FD investment summary */}
          <div className="lg:col-span-2 bg-white border border-slate-100 shadow-xl shadow-slate-100/30 rounded-3xl p-6 md:p-8 space-y-6">
            <div className="flex justify-between items-center border-b border-slate-50 pb-4">
              <div>
                <span className="text-[10px] font-extrabold uppercase tracking-widest px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-100">
                  {fdDetails.status}
                </span>
                <p className="text-xs font-semibold text-slate-400 mt-2 font-mono">Certificate: {fdDetails.fdNum}</p>
              </div>
              <div className="text-right">
                <span className="inline-flex items-center gap-1 text-xs bg-yellow-400/10 text-yellow-700 px-2.5 py-1 rounded-full font-bold">
                  <Sparkles className="w-3 h-3 text-[#1a1f71]" />
                  Compounded Monthly
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-4">
              <div className="space-y-1">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Principal Deposit Amount</p>
                <p className="text-2xl font-extrabold text-slate-800">{fdDetails.depositAmount}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Interest Yield Rate</p>
                <p className="text-2xl font-extrabold text-emerald-600">{fdDetails.interestRate}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Interest to Earn</p>
                <p className="text-2xl font-extrabold text-slate-800">{fdDetails.interestEarned}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Estimated Maturity Amount</p>
                <p className="text-2xl font-extrabold text-[#1a1f71]">{fdDetails.maturityAmount}</p>
              </div>
            </div>

            {/* maturity progress */}
            <div className="space-y-2 pt-4 border-t border-slate-50">
              <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-slate-400">
                <span>Tenure Duration Progress</span>
                <span className="text-[#1a1f71]">12 of 24 Months</span>
              </div>
              <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                <div className="bg-[#1a1f71] h-full" style={{ width: "50%" }}></div>
              </div>
            </div>
          </div>

          {/* Maturity specifics panel */}
          <div className="bg-white border border-[#d0d3ea] shadow-xl shadow-slate-100/30 rounded-3xl p-6 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-xl bg-blue-50 text-[#1a1f71] flex items-center justify-center">
                <Calendar className="h-6 w-6" />
              </div>
              <h4 className="font-extrabold text-slate-800 text-base font-sans">Maturity Details</h4>
              <p className="text-xs text-slate-400">Your Fixed Deposit will mature and credit automatically back to your primary savings account.</p>
              
              <div className="pt-4 space-y-2 text-xs font-semibold text-slate-600">
                <div className="flex justify-between py-1 border-b border-slate-50">
                  <span className="text-slate-400">Maturity Date</span>
                  <span className="text-slate-800 font-bold">{fdDetails.maturityDate}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-50">
                  <span className="text-slate-400">Compounding tenure</span>
                  <span className="text-slate-800 font-bold">{fdDetails.tenure}</span>
                </div>
              </div>
            </div>

            <button className="w-full mt-6 flex items-center justify-center gap-2 px-4 py-3.5 border border-slate-200 hover:bg-slate-50 font-bold text-slate-700 rounded-xl text-sm transition-colors">
              <Award className="w-4 h-4 text-slate-400" />
              Premature Withdrawal Policy
            </button>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

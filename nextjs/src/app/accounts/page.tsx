"use client";

import React from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { useAuth } from "@/hooks/useAuth";
import { Wallet, ShieldCheck } from "lucide-react";

export default function AccountsPage() {
  const { customerContext } = useAuth();

  if (!customerContext) return null;

  const isPremium = customerContext.customer_segment?.toUpperCase() === "PREMIUM" || customerContext.customer_segment?.toUpperCase() === "WEALTH";

  const accounts = [
    {
      accNum: "ACC-5982-1049-33",
      type: "Savings Account",
      balance: isPremium ? "$42,500.80" : "$4,250.20",
      status: "ACTIVE",
      interest: "3.5% p.a.",
      holder: customerContext.name,
    },
    {
      accNum: "ACC-1102-3958-88",
      type: "Checking Account",
      balance: isPremium ? "$12,400.00" : "$1,120.50",
      status: "ACTIVE",
      interest: "0.0% p.a.",
      holder: customerContext.name,
    },
    {
      accNum: "ACC-9923-8847-12",
      type: "Salary Account",
      balance: isPremium ? "$8,210.00" : "$500.00",
      status: "ACTIVE",
      interest: "4.0% p.a.",
      holder: customerContext.name,
    }
  ];

  return (
    <DashboardLayout>
      <div className="p-6 md:p-8 space-y-8 animate-fade-in">
        <div>
          <h2 className="text-3xl font-extrabold text-[#1a1f71] tracking-tight">Core Accounts</h2>
          <p className="text-sm text-slate-500">Manage and audit your linked banking accounts.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {accounts.map((acc, i) => (
            <div key={i} className="bg-white border border-slate-100 shadow-xl shadow-slate-100/30 rounded-3xl p-6 relative overflow-hidden group hover:scale-[1.01] transition-transform duration-200">
              <div className="flex justify-between items-start mb-6">
                <div className="w-12 h-12 rounded-xl bg-blue-50 text-[#1a1f71] flex items-center justify-center">
                  <Wallet className="h-6 w-6" />
                </div>
                <span className="text-[10px] font-extrabold uppercase tracking-widest px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-100">
                  {acc.status}
                </span>
              </div>

              <div className="space-y-4">
                <div>
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">{acc.type}</p>
                  <p className="text-2xl font-extrabold text-[#1a1f71] tracking-tight">{acc.balance}</p>
                </div>

                <div className="pt-4 border-t border-slate-50 space-y-2">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-slate-400">Account Number</span>
                    <span className="text-slate-700 font-mono">{acc.accNum}</span>
                  </div>
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-slate-400">Interest Rate</span>
                    <span className="text-slate-700">{acc.interest}</span>
                  </div>
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-slate-400">Primary Holder</span>
                    <span className="text-slate-700">{acc.holder}</span>
                  </div>
                </div>
              </div>

              {/* Accent border highlight on group hover */}
              <div className="absolute bottom-0 left-0 right-0 h-1.5 bg-[#1a1f71] transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left" />
            </div>
          ))}
        </div>

        {/* Account Controls Panel */}
        <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-xl shadow-slate-100/30">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-yellow-400/10 text-[#1a1f71] flex items-center justify-center shrink-0">
                <ShieldCheck className="h-6 w-6 text-[#1a1f71]" />
              </div>
              <div>
                <h4 className="font-extrabold text-slate-800 text-base">Authorized Views Configured</h4>
                <p className="text-sm text-slate-400">These accounts are connected to secure BigQuery views for AI Copilot queries.</p>
              </div>
            </div>
            <button className="px-5 py-2.5 bg-[#1a1f71] hover:bg-[#2a2f81] text-white rounded-xl text-sm font-bold shadow-lg transition-transform hover:scale-[1.02]">
              Audit Identity Logs
            </button>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

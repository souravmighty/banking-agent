"use client";

import React from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { useAuth } from "@/hooks/useAuth";
import { Eye, ShieldCheck, Cpu } from "lucide-react";

export default function CreditCardsPage() {
  const { customerContext } = useAuth();

  if (!customerContext) return null;

  const isPremium = customerContext.customer_segment?.toUpperCase() === "PREMIUM" || customerContext.customer_segment?.toUpperCase() === "WEALTH";

  const cardDetails = {
    cardNumber: isPremium ? "•••• •••• •••• 9012" : "•••• •••• •••• 4512",
    cardHolder: customerContext.name,
    expiry: "09/31",
    cvv: "•••",
    limit: isPremium ? "$25,000.00" : "$5,000.00",
    balance: isPremium ? "$3,420.50" : "$890.10",
    availableLimit: isPremium ? "$21,579.50" : "$4,109.90",
    utilization: isPremium ? "13.6%" : "17.8%",
    dueDate: "July 01, 2026",
    minimumDue: isPremium ? "$150.00" : "$35.00",
  };

  return (
    <DashboardLayout>
      <div className="p-6 md:p-8 space-y-8 animate-fade-in">
        <div>
          <h2 className="text-3xl font-extrabold text-[#1a1f71] tracking-tight">Credit Cards</h2>
          <p className="text-sm text-slate-500">Track and pay your credit card balances and limits.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Visual Digital Card */}
          <div className="lg:col-span-1 space-y-6">
            <div className={`relative h-56 rounded-3xl p-6 text-white shadow-2xl overflow-hidden flex flex-col justify-between hover:rotate-1 hover:scale-[1.02] transition-all duration-300 ${
              isPremium 
                ? "bg-gradient-to-br from-[#1e237e] via-[#11144c] to-[#05061c]" 
                : "bg-gradient-to-br from-indigo-600 via-blue-700 to-indigo-900"
            }`}>
              <div className="flex justify-between items-start relative z-10">
                <div>
                  <p className="text-[10px] font-bold text-blue-200 uppercase tracking-widest">
                    {isPremium ? "ABC Bank Infinite" : "ABC Bank Platinum"}
                  </p>
                  <p className="text-sm font-extrabold mt-1">Credit Card</p>
                </div>
                <Cpu className="h-10 w-10 text-yellow-400 shrink-0" />
              </div>

              <div className="relative z-10">
                <p className="text-lg font-mono tracking-widest font-semibold">{cardDetails.cardNumber}</p>
              </div>

              <div className="flex justify-between items-end relative z-10">
                <div>
                  <p className="text-[9px] text-blue-200/50 uppercase tracking-wider">Card Holder</p>
                  <p className="text-xs font-bold font-mono tracking-wide">{cardDetails.cardHolder}</p>
                </div>
                <div>
                  <p className="text-[9px] text-blue-200/50 uppercase tracking-wider">Expires</p>
                  <p className="text-xs font-bold font-mono">{cardDetails.expiry}</p>
                </div>
              </div>

              {/* Decorative design curves */}
              <div className="absolute top-[-40%] right-[-20%] w-72 h-72 rounded-full bg-yellow-400/5 blur-3xl" />
              <div className="absolute bottom-[-30%] left-[-10%] w-60 h-60 rounded-full bg-blue-500/10 blur-2xl" />
            </div>

            <button className="w-full flex items-center justify-center gap-2 px-4 py-3 border border-slate-200 bg-white hover:bg-slate-50 font-bold rounded-2xl text-sm transition-colors text-slate-700">
              <Eye className="w-4 h-4 text-slate-400" />
              Reveal Card Credentials
            </button>
          </div>

          {/* Card utilization & billing info */}
          <div className="lg:col-span-2 bg-white border border-slate-100 shadow-xl shadow-slate-100/30 rounded-3xl p-6 md:p-8 space-y-6">
            <h3 className="font-extrabold text-[#1a1f71] text-lg border-b border-slate-50 pb-4">Limits & Billing Summary</h3>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div className="space-y-1">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Credit Limit</p>
                <p className="text-2xl font-extrabold text-slate-800">{cardDetails.limit}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Current Balance Due</p>
                <p className="text-2xl font-extrabold text-slate-800">{cardDetails.balance}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Available Credit Limit</p>
                <p className="text-2xl font-extrabold text-[#1a1f71]">{cardDetails.availableLimit}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Credit Card Utilization</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xl font-extrabold text-slate-800">{cardDetails.utilization}</span>
                  <span className="text-xs font-semibold text-slate-400">(Healthy)</span>
                </div>
              </div>
            </div>

            {/* Bill Payment Progress bar */}
            <div className="space-y-2 pt-4 border-t border-slate-50">
              <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-slate-400">
                <span>Card Utilization Limit Progress</span>
                <span className="text-[#1a1f71]">{cardDetails.utilization}</span>
              </div>
              <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                <div className="bg-[#1a1f71] h-full" style={{ width: cardDetails.utilization }}></div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-slate-50 text-xs font-semibold text-slate-600">
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-400">Next Payment Due Date</span>
                <span className="text-slate-800 font-bold">{cardDetails.dueDate}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-400">Minimum Due Amount</span>
                <span className="text-slate-800 font-bold">{cardDetails.minimumDue}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Card Security info */}
        <div className="bg-emerald-50/40 rounded-2xl p-5 border border-emerald-100 flex gap-4">
          <ShieldCheck className="w-6 h-6 text-emerald-600 shrink-0" />
          <div className="space-y-1">
            <h5 className="font-extrabold text-emerald-800 text-sm">Tokenized Security & Encryption</h5>
            <p className="text-xs text-emerald-800/70 leading-relaxed">
              Your digital card details and credential storage are highly protected. Transaction requests executed through our AI Copilot are subjected to multi-factor transaction validation and require verified email context.
            </p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

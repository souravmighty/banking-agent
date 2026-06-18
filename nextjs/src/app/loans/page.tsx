"use client";

import React from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { useAuth } from "@/hooks/useAuth";
import { FileText, Calendar, CheckCircle2 } from "lucide-react";

export default function LoansPage() {
  const { customerContext } = useAuth();

  if (!customerContext) return null;

  const isPremium = customerContext.customer_segment?.toUpperCase() === "PREMIUM" || customerContext.customer_segment?.toUpperCase() === "WEALTH";

  const loanDetails = {
    loanNum: "LN-3850-1120-19",
    type: "Home Loan Portfolio",
    sanctionedAmount: isPremium ? "$150,000.00" : "$45,000.00",
    outstandingAmount: isPremium ? "$80,000.00" : "$15,000.00",
    emiAmount: isPremium ? "$1,200.00" : "$350.00",
    tenureLeft: isPremium ? "72 Months" : "48 Months",
    interestRate: "6.75% Fixed",
    nextDueDate: "July 01, 2026",
  };

  return (
    <DashboardLayout>
      <div className="p-6 md:p-8 space-y-8 animate-fade-in">
        <div>
          <h2 className="text-3xl font-extrabold text-[#1a1f71] tracking-tight">Active Loans</h2>
          <p className="text-sm text-slate-500">Track EMI schedules, sanctioned limits, and outstanding loan obligations.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Loan Outstanding Display */}
          <div className="lg:col-span-2 bg-white border border-slate-100 shadow-xl shadow-slate-100/30 rounded-3xl p-6 md:p-8 space-y-6">
            <div className="flex justify-between items-center border-b border-slate-50 pb-4">
              <div>
                <span className="text-[10px] font-extrabold uppercase tracking-widest px-2.5 py-1 rounded-full bg-blue-50 text-[#1a1f71] border border-blue-100">
                  {loanDetails.type}
                </span>
                <p className="text-xs font-semibold text-slate-400 mt-2 font-mono">Reference: {loanDetails.loanNum}</p>
              </div>
              <div className="text-right">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Interest Rate</p>
                <p className="font-extrabold text-slate-800 text-sm">{loanDetails.interestRate}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-4">
              <div className="space-y-1">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Sanctioned Amount</p>
                <p className="text-2xl font-extrabold text-slate-800">{loanDetails.sanctionedAmount}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Current Outstanding</p>
                <p className="text-2xl font-extrabold text-red-500">{loanDetails.outstandingAmount}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Monthly EMI Due</p>
                <p className="text-2xl font-extrabold text-[#1a1f71]">{loanDetails.emiAmount}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Remaining Tenure</p>
                <p className="text-2xl font-extrabold text-slate-800">{loanDetails.tenureLeft}</p>
              </div>
            </div>

            {/* Loan repayment progress */}
            <div className="space-y-2 pt-4 border-t border-slate-50">
              <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-slate-400">
                <span>Principal Repayment Progress</span>
                <span className="text-[#1a1f71]">47% Repaid</span>
              </div>
              <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                <div className="bg-[#1a1f71] h-full" style={{ width: "47%" }}></div>
              </div>
            </div>
          </div>

          {/* EMI billing calendar panel */}
          <div className="bg-white border border-slate-100 shadow-xl shadow-slate-100/30 rounded-3xl p-6 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-xl bg-blue-50 text-[#1a1f71] flex items-center justify-center">
                <Calendar className="h-6 w-6" />
              </div>
              <h4 className="font-extrabold text-slate-800 text-base">Next EMI Payment</h4>
              <p className="text-xs text-slate-400">Your EMI is configured for automated payment from your checking account.</p>
              
              <div className="pt-4 space-y-2 text-xs font-semibold text-slate-600">
                <div className="flex justify-between py-1 border-b border-slate-50">
                  <span className="text-slate-400">Due Date</span>
                  <span className="text-slate-800 font-bold">{loanDetails.nextDueDate}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-50">
                  <span className="text-slate-400">EMI Due</span>
                  <span className="text-slate-800 font-bold">{loanDetails.emiAmount}</span>
                </div>
              </div>
            </div>

            <button className="w-full mt-6 flex items-center justify-center gap-2 px-4 py-3 bg-[#1a1f71] hover:bg-[#2a2f81] font-bold text-white rounded-xl text-sm transition-transform hover:scale-[1.02] shadow-md shadow-blue-900/10">
              <FileText className="w-4 h-4" />
              Download Statement
            </button>
          </div>
        </div>

        {/* Security / Terms banner */}
        <div className="bg-slate-50/50 rounded-2xl p-5 border border-slate-200 flex gap-4">
          <CheckCircle2 className="w-6 h-6 text-slate-600 shrink-0" />
          <div className="space-y-1">
            <h5 className="font-extrabold text-slate-800 text-sm">Regulatory Compliance & Transparency</h5>
            <p className="text-xs text-slate-400 leading-relaxed">
              Loans and interest calculations strictly conform to central banking regulation mandates. Statements can be audited or reviewed by downloading certified PDFs directly or requesting interest certificate summaries from the AI Assistant.
            </p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

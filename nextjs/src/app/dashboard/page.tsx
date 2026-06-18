"use client";

import React from "react";
import Link from "next/link";
import { DashboardLayout } from "@/components/DashboardLayout";
import { useAuth } from "@/hooks/useAuth";
import { 
  Wallet, 
  CreditCard, 
  TrendingUp, 
  PiggyBank, 
  ArrowUpRight, 
  ArrowDownLeft, 
  ShieldCheck, 
  Sparkles,
  ArrowRight
} from "lucide-react";

export default function DashboardPage() {
  const { customerContext } = useAuth();

  if (!customerContext) return null;

  // Let's create gorgeous mock data customized by customer segment
  const isPremium = customerContext.customer_segment?.toUpperCase() === "PREMIUM" || customerContext.customer_segment?.toUpperCase() === "WEALTH";
  const savingsBalance = isPremium ? "$42,500.80" : "$4,250.20";
  const creditLimit = isPremium ? "$25,000.00" : "$5,000.00";
  const creditBalance = isPremium ? "$3,420.50" : "$890.10";
  const loanBalance = isPremium ? "$80,000.00" : "$15,000.00";
  const fixedDepositBalance = isPremium ? "$150,000.00" : "$20,000.00";

  const cards = [
    {
      title: "Total Balance",
      value: savingsBalance,
      sub: "Savings Account",
      change: "+2.4% this month",
      icon: Wallet,
      color: "from-blue-600 to-indigo-700 text-white",
    },
    {
      title: "Credit Utilization",
      value: creditBalance,
      sub: `of ${creditLimit} limit`,
      change: "13.6% used",
      icon: CreditCard,
      color: "from-purple-600 to-pink-600 text-white",
    },
    {
      title: "Active Investments",
      value: fixedDepositBalance,
      sub: "Fixed Deposit Portfolio",
      change: "5.4% p.a. interest",
      icon: PiggyBank,
      color: "from-emerald-500 to-teal-600 text-white",
    },
    {
      title: "Outstanding Loans",
      value: loanBalance,
      sub: "Home & Personal Loans",
      change: "EMI $1,200 due in 12 days",
      icon: TrendingUp,
      color: "from-slate-800 to-slate-900 text-white",
    },
  ];

  const recentTransactions = [
    { merchant: "Whole Foods", category: "Groceries", amount: "-$124.50", date: "Today, 2:45 PM", status: "Completed", type: "debit" },
    { merchant: "Salary Inward", category: "Income", amount: isPremium ? "+$8,500.00" : "+$3,200.00", date: "Yesterday, 9:00 AM", status: "Completed", type: "credit" },
    { merchant: "Starbucks Coffee", category: "Dining", amount: "-$6.75", date: "Yesterday, 8:15 AM", status: "Completed", type: "debit" },
    { merchant: "Netflix Premium", category: "Entertainment", amount: "-$22.99", date: "June 15, 2026", status: "Completed", type: "debit" },
    { merchant: "Apple Store", category: "Electronics", amount: "-$1,299.00", date: "June 12, 2026", status: "Completed", type: "debit" },
  ];

  return (
    <DashboardLayout>
      <div className="p-6 md:p-8 space-y-8 animate-fade-in">
        {/* Welcome Banner */}
        <div className="relative overflow-hidden bg-gradient-to-r from-[#1a1f71] to-[#2a2f81] rounded-3xl p-6 md:p-8 text-white shadow-xl">
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md text-yellow-400 text-xs font-bold">
                <Sparkles className="w-3.5 h-3.5" />
                {customerContext.customer_segment} Customer Tier
              </div>
              <h2 className="text-3xl font-extrabold tracking-tight">
                Good evening, {customerContext.name}!
              </h2>
              <p className="text-blue-100/70 text-sm max-w-md">
                Welcome to your secure financial portal. Your account looks healthy. We detected no suspicious logins or transfers.
              </p>
            </div>
            
            <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-2xl p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-yellow-400/20 text-yellow-400 flex items-center justify-center shrink-0">
                <ShieldCheck className="h-6 w-6" />
              </div>
              <div>
                <p className="text-xs text-blue-100/60 font-semibold uppercase tracking-wider">Security Status</p>
                <p className="text-sm font-bold">256-Bit SSL Protected</p>
              </div>
            </div>
          </div>

          {/* Decorative shapes */}
          <div className="absolute top-[-20%] right-[-5%] w-80 h-80 rounded-full bg-blue-500/10 blur-3xl" />
          <div className="absolute bottom-[-40%] left-[20%] w-96 h-96 rounded-full bg-yellow-500/5 blur-3xl" />
        </div>

        {/* Core Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {cards.map((card, i) => {
            const Icon = card.icon;
            return (
              <div key={i} className={`bg-gradient-to-br ${card.color} p-6 rounded-3xl shadow-xl flex flex-col justify-between h-48 hover:scale-[1.02] transition-transform duration-200 cursor-pointer`}>
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider opacity-70">{card.title}</p>
                    <h3 className="text-2xl font-extrabold mt-1 tracking-tight">{card.value}</h3>
                  </div>
                  <div className="w-10 h-10 rounded-xl bg-white/10 backdrop-blur-md flex items-center justify-center text-white shrink-0">
                    <Icon className="h-5 w-5" />
                  </div>
                </div>
                <div>
                  <p className="text-xs font-medium opacity-80">{card.sub}</p>
                  <p className="text-[11px] font-bold mt-1 inline-flex items-center gap-1 bg-white/10 px-2 py-0.5 rounded-full">
                    {card.change}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Dashboard Bottom Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Recent transactions */}
          <div className="lg:col-span-2 bg-white rounded-3xl p-6 border border-slate-100 shadow-xl shadow-slate-100/30 space-y-6">
            <div className="flex items-center justify-between border-b border-slate-50 pb-4">
              <div>
                <h4 className="font-extrabold text-lg text-slate-800">Recent Transactions</h4>
                <p className="text-xs text-slate-400">Live ledger records in banking database</p>
              </div>
              <button className="text-xs font-bold text-[#1a1f71] hover:underline">View All Records</button>
            </div>

            <div className="divide-y divide-slate-50">
              {recentTransactions.map((tx, idx) => (
                <div key={idx} className="flex items-center justify-between py-4 first:pt-0 last:pb-0">
                  <div className="flex items-center gap-3.5">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                      tx.type === "credit" ? "bg-emerald-50 text-emerald-600" : "bg-rose-50 text-red-500"
                    }`}>
                      {tx.type === "credit" ? <ArrowDownLeft className="w-5 h-5" /> : <ArrowUpRight className="w-5 h-5" />}
                    </div>
                    <div>
                      <p className="font-bold text-slate-700 text-sm">{tx.merchant}</p>
                      <p className="text-xs text-slate-400">{tx.category} • {tx.date}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`font-extrabold text-sm ${tx.type === "credit" ? "text-emerald-600" : "text-slate-800"}`}>
                      {tx.amount}
                    </p>
                    <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">{tx.status}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Side panel: Copilot prompt helper */}
          <div className="bg-[#1a1f71] text-white rounded-3xl p-6 shadow-xl relative overflow-hidden flex flex-col justify-between">
            <div className="relative z-10 space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-white/10 flex items-center justify-center text-yellow-400">
                <Sparkles className="h-6 w-6" />
              </div>
              <h4 className="font-extrabold text-xl tracking-tight leading-tight">Ask your AI Copilot!</h4>
              <p className="text-blue-100/70 text-sm leading-relaxed">
                Your AI Banking Assistant is connected directly to your authorized BigQuery views. You can ask queries like:
              </p>
              <div className="space-y-2 pt-2">
                <p className="text-xs bg-white/5 border border-white/10 p-3 rounded-xl italic text-blue-100">
                  &ldquo;Check if my Whole Foods transactions are normal.&rdquo;
                </p>
                <p className="text-xs bg-white/5 border border-white/10 p-3 rounded-xl italic text-blue-100">
                  &ldquo;How much did I spend in Groceries this week?&rdquo;
                </p>
              </div>
            </div>
            
            <div className="relative z-10 pt-6">
              <Link
                href="/"
                className="w-full inline-flex items-center justify-center gap-2 px-4 py-3.5 bg-yellow-400 hover:bg-yellow-500 text-[#1a1f71] font-bold rounded-2xl text-sm shadow-lg transition-transform hover:scale-[1.02]"
              >
                Go to AI Copilot
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            <div className="absolute top-[-30%] right-[-10%] w-48 h-48 rounded-full bg-blue-500/10 blur-2xl" />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

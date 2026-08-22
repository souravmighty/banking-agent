"use client";

import React from "react";
import {
  Sparkles,
  PieChart,
  CreditCard,
  TrendingUp,
  Users,
  ShoppingBag,
  Landmark,
  ArrowRight,
} from "lucide-react";

interface StaffEmptyStateProps {
  onSelectPrompt: (prompt: string) => void;
  inputComponent?: React.ReactNode;
}

export function StaffEmptyState({ onSelectPrompt, inputComponent }: StaffEmptyStateProps) {
  const suggestedQueries = [
    {
      title: "Deposit Portfolio & Risk Tiers",
      query: "What is the total deposit balance distribution across customer risk segments and account types?",
      icon: Landmark,
      category: "Portfolio Health",
    },
    {
      title: "Credit Card Utilization & Limits",
      query: "Compare average credit card utilization rates and credit limits across risk tiers.",
      icon: CreditCard,
      category: "Product Performance",
    },
    {
      title: "Loan Exposure & Distribution",
      query: "What is our total outstanding loan balance and risk distribution across Personal and Home loans?",
      icon: TrendingUp,
      category: "Lending & Risk",
    },
    {
      title: "High-Balance Cross-Sell",
      query: "Identify customer segments with high deposit balances who do not hold an active credit card or loan.",
      icon: Users,
      category: "Growth & Retention",
    },
    {
      title: "Merchant Category Spend Trends",
      query: "Analyze transaction volumes and total customer spend across merchant categories like Travel, Retail, and Dining.",
      icon: ShoppingBag,
      category: "Spend Velocity",
    },
    {
      title: "Fixed Deposit Tenure & Yield",
      query: "Show the distribution of fixed deposits by tenure length and average interest rates.",
      icon: PieChart,
      category: "Deposits & Yield",
    },
  ];

  return (
    <div className="flex flex-col items-center justify-center my-auto py-4 px-2 sm:px-4 max-w-4xl mx-auto w-full">
      {/* Hero Header */}
      <div className="text-center max-w-2xl mx-auto mb-6 sm:mb-8 flex flex-col items-center">
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight bg-gradient-to-r from-indigo-600 via-violet-600 to-cyan-600 dark:from-indigo-400 dark:via-violet-400 dark:to-cyan-400 bg-clip-text text-transparent pb-1.5 leading-tight">
          Analytics Copilot
        </h1>

        <div className="mt-2 mb-3.5 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-50/90 dark:bg-indigo-950/80 border border-indigo-200/80 dark:border-indigo-500/30 text-indigo-700 dark:text-indigo-300 text-xs font-semibold shadow-sm">
          <Sparkles className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400" />
          <span>Product & Portfolio Intelligence</span>
        </div>

        <p className="text-slate-500 dark:text-slate-400 text-xs sm:text-sm leading-relaxed max-w-lg mx-auto">
          Ask natural business questions to analyze customer segments, deposit trends, card usage, loan exposure, and product adoption.
        </p>
      </div>

      {/* Hero Chat Input Box in the middle */}
      {inputComponent && (
        <div className="w-full max-w-3xl mx-auto mb-6 sm:mb-8">
          {inputComponent}
        </div>
      )}

      {/* Suggested Inquiries / Deep Dives */}
      <div className="w-full max-w-3xl mx-auto">
        <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-3 px-1 flex items-center justify-between">
          <span>Suggested Deep Dives & Inquiries</span>
          <span className="text-[10px] font-normal text-slate-400 dark:text-slate-500">Click any prompt to analyze</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-3.5">
          {suggestedQueries.map((item, index) => {
            const Icon = item.icon;
            return (
              <button
                key={index}
                type="button"
                onClick={() => onSelectPrompt(item.query)}
                className="group flex flex-col justify-between p-3.5 sm:p-4 text-left rounded-xl bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 hover:border-indigo-500/50 hover:bg-indigo-50/20 dark:hover:bg-slate-900 transition-all text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white shadow-sm hover:shadow-md"
              >
                <div>
                  <div className="flex items-center justify-between mb-2.5">
                    <div className="p-1.5 rounded-lg bg-indigo-50 dark:bg-slate-950 text-indigo-600 dark:text-indigo-400 border border-indigo-100 dark:border-slate-800 group-hover:bg-indigo-600 group-hover:text-white transition-colors shrink-0">
                      <Icon className="h-4 w-4" />
                    </div>
                    <span className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800/80">
                      {item.category}
                    </span>
                  </div>

                  <div className="text-xs font-bold text-slate-900 dark:text-slate-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-300 transition-colors leading-snug">
                    {item.title}
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1.5 line-clamp-2 leading-relaxed">
                    {item.query}
                  </div>
                </div>

                <div className="flex items-center gap-1 text-[10px] font-semibold text-indigo-600 dark:text-indigo-400 mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800/60 opacity-80 group-hover:opacity-100">
                  <span>Explore analysis</span>
                  <ArrowRight className="h-3 w-3 group-hover:translate-x-1 transition-transform" />
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

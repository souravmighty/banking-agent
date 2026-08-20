"use client";

import React from "react";
import {
  Sparkles,
  BarChart3,
  Database,
  ArrowRight,
  PieChart,
  ShieldAlert,
  Users2,
  TrendingUp,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

interface StaffEmptyStateProps {
  onSelectPrompt: (prompt: string) => void;
}

export function StaffEmptyState({ onSelectPrompt }: StaffEmptyStateProps) {
  const suggestedQueries = [
    {
      label: "Portfolio Distribution",
      query: "What is the total balance distribution across customer risk segments?",
      icon: PieChart,
    },
    {
      label: "Credit Card Debt & Payoff",
      query: "Which customer segments have the highest average credit card balances and default risks?",
      icon: TrendingUp,
    },
    {
      label: "High-Value Wealth Accounts",
      query: "Show me all high-value customers with low credit card utilization and high deposit balance.",
      icon: Users2,
    },
    {
      label: "Demo Operations Velocity",
      query: "Summarize current pending demo access requests, pool capacity, and approval velocity.",
      icon: ShieldAlert,
    },
  ];

  return (
    <div className="flex flex-col items-center justify-center min-h-full py-8 px-4 max-w-5xl mx-auto w-full">
      {/* Hero Header */}
      <div className="text-center max-w-2xl mx-auto mb-8 space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-50 dark:bg-indigo-950/80 border border-indigo-200 dark:border-indigo-500/30 text-indigo-700 dark:text-indigo-300 text-xs font-bold shadow-sm dark:shadow-lg dark:shadow-indigo-950/50">
          <Sparkles className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400 animate-pulse" />
          <span>Enterprise Operations Intelligence</span>
        </div>

        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
          BankPilot{" "}
          <span className="bg-gradient-to-r from-indigo-600 via-violet-600 to-cyan-500 dark:from-indigo-400 dark:via-violet-400 dark:to-cyan-400 bg-clip-text text-transparent">
            Analytics Copilot
          </span>
        </h1>

        <p className="text-slate-600 dark:text-slate-400 text-xs sm:text-sm leading-relaxed max-w-lg mx-auto">
          Autonomous hypothesis formulation, BigQuery analytical intelligence,
          and deep customer portfolio insights for bank operations staff.
        </p>
      </div>

      {/* Capability Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full mb-8">
        {/* Card 1 */}
        <Card className="bg-white dark:bg-slate-900/60 border-slate-200 dark:border-slate-800 hover:border-indigo-500/40 transition-all hover:bg-slate-50 dark:hover:bg-slate-900/90 shadow-sm dark:shadow-md">
          <CardContent className="p-4 space-y-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-600/20 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-500/30 flex items-center justify-center">
              <BarChart3 className="h-4 w-4" />
            </div>
            <h3 className="text-xs font-bold text-slate-900 dark:text-slate-100">
              Portfolio & Risk Analytics
            </h3>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
              Examine segment deposits, loan delinquency risk tiers, and credit
              card payoff rates with automated synthesis.
            </p>
          </CardContent>
        </Card>

        {/* Card 2 */}
        <Card className="bg-white dark:bg-slate-900/60 border-slate-200 dark:border-slate-800 hover:border-violet-500/40 transition-all hover:bg-slate-50 dark:hover:bg-slate-900/90 shadow-sm dark:shadow-md">
          <CardContent className="p-4 space-y-2.5">
            <div className="w-8 h-8 rounded-lg bg-violet-50 dark:bg-violet-600/20 text-violet-600 dark:text-violet-400 border border-violet-200 dark:border-violet-500/30 flex items-center justify-center">
              <Users2 className="h-4 w-4" />
            </div>
            <h3 className="text-xs font-bold text-slate-900 dark:text-slate-100">
              Demo Operations & Auditing
            </h3>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
              Monitor demo requests approval velocity, customer pool allocation
              capacity, and audit active staff accounts.
            </p>
          </CardContent>
        </Card>

        {/* Card 3 */}
        <Card className="bg-white dark:bg-slate-900/60 border-slate-200 dark:border-slate-800 hover:border-cyan-500/40 transition-all hover:bg-slate-50 dark:hover:bg-slate-900/90 shadow-sm dark:shadow-md">
          <CardContent className="p-4 space-y-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-50 dark:bg-cyan-600/20 text-cyan-600 dark:text-cyan-400 border border-cyan-200 dark:border-cyan-500/30 flex items-center justify-center">
              <Database className="h-4 w-4" />
            </div>
            <h3 className="text-xs font-bold text-slate-900 dark:text-slate-100">
              BigQuery NL2SQL Engine
            </h3>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
              Deconstruct natural language inquiries into verified BigQuery
              queries, aggregation views, and diagnostic tables.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Suggested Questions Section */}
      <div className="w-full max-w-3xl">
        <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-3 px-1 flex items-center gap-1.5">
          <span>Suggested Operational Inquiries</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {suggestedQueries.map((item, index) => {
            const Icon = item.icon;
            return (
              <button
                key={index}
                onClick={() => onSelectPrompt(item.query)}
                className="group flex items-start gap-3 p-3 text-left rounded-xl bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 hover:border-indigo-500/50 hover:bg-slate-50 dark:hover:bg-slate-900 transition-all text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white shadow-sm"
              >
                <div className="mt-0.5 p-1.5 rounded-lg bg-slate-100 dark:bg-slate-950 text-indigo-600 dark:text-indigo-400 border border-slate-200 dark:border-slate-800 group-hover:bg-indigo-600 group-hover:text-white transition-colors shrink-0">
                  <Icon className="h-3.5 w-3.5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-bold text-slate-900 dark:text-slate-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-300 transition-colors">
                    {item.label}
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-2 leading-snug">
                    {item.query}
                  </div>
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400 dark:text-slate-600 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-transform group-hover:translate-x-1 shrink-0 mt-1" />
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

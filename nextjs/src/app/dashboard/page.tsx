"use client";

import React, { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { useAuth } from "@/hooks/useAuth";
import { customerDataService, DashboardResponse } from "@/lib/services/customerDataService";
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
  DollarSign,
  Loader2,
  AlertCircle
} from "lucide-react";

export default function DashboardPage() {
  const { user, customerContext } = useAuth();
  const [dashboardData, setDashboardData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [greeting, setGreeting] = useState<string>("Good morning");

  useEffect(() => {
    const hr = new Date().getHours();
    if (hr < 12) {
      setGreeting("Good morning");
    } else if (hr < 17) {
      setGreeting("Good afternoon");
    } else {
      setGreeting("Good evening");
    }
  }, []);

  useEffect(() => {
    async function loadDashboard() {
      if (!user) return;
      try {
        setLoading(true);
        const token = await user.getIdToken();
        const data = await customerDataService.getDashboard(token);
        setDashboardData(data);
        setError(null);
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
        const errMsg = err instanceof Error ? err.message : "Failed to retrieve your financial profile.";
        setError(errMsg);
      } finally {
        setLoading(false);
      }
    }
    
    loadDashboard();
  }, [user]);

  if (!customerContext) return null;

  // Indian Rupee formatting helper
  const formatRupee = (value: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2
    }).format(value);
  };

  const getTransactionIcon = (type: string, category?: string) => {
    const cat = (category || "").toUpperCase();
    const tType = type.toUpperCase();
    
    if (cat === "SHOPPING") return <ShoppingBag className="w-5 h-5 text-slate-600" />;
    if (cat === "FOOD") return <Utensils className="w-5 h-5 text-slate-600" />;
    if (cat === "SALARY") return <Briefcase className="w-5 h-5 text-emerald-600" />;
    if (cat === "UTILITIES") return <Zap className="w-5 h-5 text-slate-600" />;
    if (tType.includes("LOAN") || cat === "LOAN") return <Home className="w-5 h-5 text-slate-600" />;
    if (tType.includes("FD") || cat === "INVESTMENT") return <DollarSign className="w-5 h-5 text-slate-600" />;
    
    return <Landmark className="w-5 h-5 text-slate-600" />;
  };

  const getTransactionBg = (type: string, category?: string) => {
    const cat = (category || "").toUpperCase();
    if (cat === "SALARY") return "bg-emerald-50";
    return "bg-slate-50";
  };

  const name = dashboardData?.customer?.name || customerContext.name || "Casey";
  const firstName = name.split(" ")[0];

  const segment = dashboardData?.customer?.segment || customerContext.customer_segment || "RETAIL";
  const risk = dashboardData?.customer?.risk_profile || "LOW";
  const kyc = dashboardData?.customer?.kyc_status || customerContext.kyc_status || "VERIFIED";

  // Card, Loan, Investment extracts
  const card = dashboardData?.cards?.[0];
  const loan = dashboardData?.loans?.[0];
  const investment = dashboardData?.investments?.[0];

  return (
    <DashboardLayout>
      <div className="p-6 md:p-8 space-y-6 max-w-7xl mx-auto animate-fade-in bg-[#f7f8fc] min-h-[calc(100vh-70px)]">
        
        {/* Header Greeting & Last Login */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-2xl md:text-3xl font-extrabold text-[#1a1f71] tracking-tight">
              {greeting}, {firstName}
            </h2>
          </div>
          <div className="text-xs sm:text-sm font-semibold text-slate-400">
            Last login: today, {new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })}
          </div>
        </div>

        {/* Error State Banner */}
        {error && (
          <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-2xl text-red-800 text-xs sm:text-sm font-medium shadow-sm">
            <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
            <span>
              <strong>Service Alert:</strong> {error} &middot; Using offline cached profiles.
            </span>
          </div>
        )}

        {/* Loading Spinner Overlays */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <Loader2 className="w-10 h-10 animate-spin text-[#1a1f71]" />
            <p className="text-xs font-bold text-slate-500 animate-pulse uppercase tracking-wider">
              Securing session & retrieving bank ledgers...
            </p>
          </div>
        ) : (
          <>
            {/* KYC & Account Standing Status Bar */}
            <div className="flex items-center gap-3 p-4 bg-amber-50/50 border border-amber-200 rounded-2xl text-amber-800 text-xs sm:text-sm font-medium shadow-sm">
              <CheckCircle className="w-5 h-5 text-amber-600 shrink-0" />
              <span>
                KYC: <strong className="font-bold">{kyc}</strong> &middot; Risk profile: <strong className="font-bold capitalize">{risk.toLowerCase()}</strong> &middot; Segment: <strong className="font-bold capitalize">{segment.toLowerCase()}</strong> &middot; Account in good standing
              </span>
            </div>

            {/* YOUR ACCOUNTS Section */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500">Your Accounts</h3>
              {dashboardData?.accounts && dashboardData.accounts.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {dashboardData.accounts.map((acc) => (
                    <div key={acc.account_number} className="bg-white border border-slate-100 shadow-lg shadow-slate-100/50 rounded-3xl p-6 relative overflow-hidden flex flex-col justify-between h-44 hover:shadow-xl transition-shadow duration-200">
                      <div className="flex justify-between items-start">
                        <div className="flex items-center gap-3.5">
                          <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-[#1a1f71] flex items-center justify-center shrink-0">
                            {acc.account_type.toUpperCase().includes("SAVINGS") || acc.account_type.toUpperCase().includes("SALARY") ? (
                              <PiggyBank className="h-6 w-6" />
                            ) : (
                              <Landmark className="h-6 w-6" />
                            )}
                          </div>
                          <div>
                            <h4 className="font-extrabold text-slate-800 text-md capitalize">{acc.account_type.toLowerCase()} account</h4>
                            <p className="text-xs font-bold text-slate-400 font-mono">&bull;&bull;&bull;&bull; {acc.account_number.slice(-4)}</p>
                          </div>
                        </div>
                        <span className={`inline-flex px-3 py-1 rounded-full text-[11px] font-bold tracking-wider ${
                          acc.account_status === "ACTIVE" 
                            ? "bg-emerald-50 text-emerald-700 border border-emerald-100" 
                            : "bg-amber-50 text-amber-700 border border-amber-100"
                        }`}>
                          {acc.account_status}
                        </span>
                      </div>
                      <div className="space-y-0.5">
                        <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Available balance</p>
                        <p className="text-3xl font-extrabold text-[#1a1f71] tracking-tight">{formatRupee(acc.balance)}</p>
                      </div>
                      <div className="text-[11px] font-semibold text-slate-400 border-t border-slate-50 pt-2.5">
                        {acc.branch_name} &middot; {acc.ifsc_code}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="bg-white border border-slate-100 shadow-lg shadow-slate-100/50 rounded-3xl p-10 text-center text-slate-400 font-medium">
                  <PiggyBank className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                  <p className="text-sm font-bold">No active deposit accounts found</p>
                </div>
              )}
            </div>

            {/* YOUR PRODUCTS Section */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500">Your Products</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

                {/* Credit Card Card */}
                {card ? (
                  <div className="bg-white border border-slate-100 shadow-lg shadow-slate-100/50 rounded-3xl p-6 flex flex-col justify-between h-44 hover:shadow-xl transition-shadow duration-200">
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-xl bg-indigo-50 text-[#1a1f71] flex items-center justify-center shrink-0">
                        <CreditCard className="h-5 w-5" />
                      </div>
                      <div className="flex-1">
                        <h4 className="font-extrabold text-slate-800 text-sm">Credit card</h4>
                        <div className="flex justify-between items-baseline mt-2">
                          <span className="text-xs font-semibold text-slate-400">Outstanding</span>
                          <span className="font-extrabold text-slate-800 text-sm">{formatRupee(card.outstanding_balance)}</span>
                        </div>
                        <div className="flex justify-between items-baseline mt-1">
                          <span className="text-xs font-semibold text-slate-400">
                            Min due - {card.payment_due_date ? new Date(card.payment_due_date).toLocaleDateString("en-IN", { day: "numeric", month: "short" }) : "N/A"}
                          </span>
                          <span className="font-extrabold text-slate-800 text-sm">{formatRupee(card.minimum_due_amount)}</span>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-1.5">
                      <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                        <div className="bg-purple-600 h-full rounded-full" style={{ width: `${Math.min(100, Math.round((card.outstanding_balance / card.credit_limit) * 100))}%` }} />
                      </div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                        {Math.round((card.outstanding_balance / card.credit_limit) * 100)}% utilization &middot; Limit {formatRupee(card.credit_limit)}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="bg-white border border-slate-100 shadow-lg shadow-slate-100/50 rounded-3xl p-6 flex flex-col justify-center items-center h-44 text-center text-slate-400">
                    <CreditCard className="w-8 h-8 text-slate-300 mb-2" />
                    <p className="text-xs font-bold">No active credit cards</p>
                  </div>
                )}

                {/* Personal Loan Card */}
                {loan ? (
                  <div className="bg-white border border-slate-100 shadow-lg shadow-slate-100/50 rounded-3xl p-6 flex flex-col justify-between h-44 hover:shadow-xl transition-shadow duration-200">
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-xl bg-indigo-50 text-[#1a1f71] flex items-center justify-center shrink-0">
                        <Home className="h-5 w-5" />
                      </div>
                      <div className="flex-1">
                        <h4 className="font-extrabold text-slate-800 text-sm capitalize">{loan.loan_type.toLowerCase()} loan</h4>
                        <div className="flex justify-between items-baseline mt-2">
                          <span className="text-xs font-semibold text-slate-400">Outstanding</span>
                          <span className="font-extrabold text-slate-800 text-sm">{formatRupee(loan.outstanding_amount)}</span>
                        </div>
                        <div className="flex justify-between items-baseline mt-1">
                          <span className="text-xs font-semibold text-slate-400">Next EMI</span>
                          <span className="font-extrabold text-slate-800 text-sm">{formatRupee(loan.emi_amount)}</span>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-1.5">
                      <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                        <div className="bg-[#f0a500] h-full rounded-full" style={{ width: `${Math.round((loan.remaining_tenure_months / loan.original_tenure_months) * 100)}%` }} />
                      </div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                        {loan.remaining_tenure_months} of {loan.original_tenure_months} months remaining
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="bg-white border border-slate-100 shadow-lg shadow-slate-100/50 rounded-3xl p-6 flex flex-col justify-center items-center h-44 text-center text-slate-400">
                    <Home className="w-8 h-8 text-slate-300 mb-2" />
                    <p className="text-xs font-bold">No active loan accounts</p>
                  </div>
                )}

                {/* Fixed Deposit Card */}
                {investment ? (
                  <div className="bg-white border border-slate-100 shadow-lg shadow-slate-100/50 rounded-3xl p-6 flex flex-col justify-between h-44 hover:shadow-xl transition-shadow duration-200">
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-xl bg-indigo-50 text-[#1a1f71] flex items-center justify-center shrink-0">
                        <DollarSign className="h-5 w-5" />
                      </div>
                      <div className="flex-1">
                        <h4 className="font-extrabold text-slate-800 text-sm">Fixed deposit</h4>
                        <div className="flex justify-between items-baseline mt-2">
                          <span className="text-xs font-semibold text-slate-400">Current value</span>
                          <span className="font-extrabold text-slate-800 text-sm">{formatRupee(investment.current_value)}</span>
                        </div>
                        <div className="flex justify-between items-baseline mt-1">
                          <span className="text-xs font-semibold text-slate-400">Rate</span>
                          <span className="font-extrabold text-slate-800 text-sm">{investment.interest_rate}% p.a.</span>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-1.5">
                      <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                        <div className="bg-[#1a1f71] h-full rounded-full" style={{ width: "100%" }} />
                      </div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                        Matures {investment.maturity_date ? new Date(investment.maturity_date).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" }) : "N/A"}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="bg-white border border-slate-100 shadow-lg shadow-slate-100/50 rounded-3xl p-6 flex flex-col justify-center items-center h-44 text-center text-slate-400">
                    <DollarSign className="w-8 h-8 text-slate-300 mb-2" />
                    <p className="text-xs font-bold">No active fixed deposits</p>
                  </div>
                )}

              </div>
            </div>

            {/* BOTTOM ROW GRID */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

              {/* RECENT TRANSACTIONS Card */}
              <div className="lg:col-span-2 bg-white border border-slate-100 shadow-lg shadow-slate-100/50 rounded-3xl p-6 space-y-4 hover:shadow-xl transition-shadow duration-200">
                <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500 pb-2 border-b border-slate-50">
                  Recent Transactions
                </h3>
                {dashboardData?.recent_transactions && dashboardData.recent_transactions.length > 0 ? (
                  <div className="divide-y divide-slate-50">
                    {dashboardData.recent_transactions.slice(0, 5).map((tx) => (
                      <div key={tx.transaction_id} className="flex items-center justify-between py-3.5 first:pt-0 last:pb-0">
                        <div className="flex items-center gap-3.5">
                          <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${getTransactionBg(tx.transaction_type, tx.category)}`}>
                            {getTransactionIcon(tx.transaction_type, tx.category)}
                          </div>
                          <div>
                            <p className="font-bold text-slate-700 text-sm leading-snug">{tx.description}</p>
                            <p className="text-xs text-slate-400 capitalize">
                              {tx.category ? tx.category.toLowerCase() : tx.transaction_type.toLowerCase().replace("_", " ")} &bull; {tx.transaction_timestamp ? new Date(tx.transaction_timestamp).toLocaleString("en-IN", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }) : "Today"}
                            </p>
                          </div>
                        </div>
                        <p className={`font-extrabold text-sm ${tx.direction === "CREDIT" ? "text-emerald-600" : "text-slate-800"}`}>
                          {tx.direction === "CREDIT" ? "+" : "-"}{formatRupee(tx.amount)}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-8 text-center text-slate-400 font-medium text-sm">
                    No recent transactions found
                  </div>
                )}
              </div>

              {/* RIGHT PANELS COLUMN */}
              <div className="flex flex-col gap-6">

                {/* CREDIT SCORE Card */}
                <div className="bg-white border border-slate-100 shadow-lg shadow-slate-100/50 rounded-3xl p-6 flex flex-col justify-between hover:shadow-xl transition-shadow duration-200">
                  <div className="flex justify-between items-center pb-3 border-b border-slate-50">
                    <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500">
                      Credit Score
                    </h3>
                    <span className={`inline-flex px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider ${
                      (dashboardData?.summary?.credit_score || 750) >= 750
                        ? "bg-emerald-50 text-emerald-700 border border-emerald-100"
                        : (dashboardData?.summary?.credit_score || 750) >= 650
                          ? "bg-amber-50 text-amber-700 border border-amber-100"
                          : "bg-red-50 text-red-700 border border-red-100"
                    }`}>
                      {(dashboardData?.summary?.credit_score || 750) >= 750 ? "Excellent" : (dashboardData?.summary?.credit_score || 750) >= 650 ? "Good" : "Fair"}
                    </span>
                  </div>
                  <div className="py-4">
                    <p className="text-5xl font-extrabold text-[#1a1f71] tracking-tight">
                      {dashboardData?.summary?.credit_score || 750}
                    </p>
                  </div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    Experian &middot; Updated recently
                  </div>
                </div>

                {/* BENEFICIARIES Card */}
                <div className="bg-white border border-slate-100 shadow-lg shadow-slate-100/50 rounded-3xl p-6 space-y-4 hover:shadow-xl transition-shadow duration-200 flex-1 flex flex-col justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500 pb-2 border-b border-slate-50">
                    Beneficiaries
                  </h3>
                  <div className="space-y-4 flex-1 flex flex-col justify-center">
                    {dashboardData?.beneficiaries && dashboardData.beneficiaries.length > 0 ? (
                      dashboardData.beneficiaries.slice(0, 3).map((ben) => {
                        const initials = ben.beneficiary_name ? ben.beneficiary_name.split(" ").map((n: string) => n[0]).join("").toUpperCase().slice(0, 2) : "BA";
                        return (
                          <div key={ben.beneficiary_id || ben.beneficiary_account_number} className="flex items-center gap-3.5">
                            <div className="w-9 h-9 rounded-full bg-indigo-600 text-white text-xs font-bold flex items-center justify-center shrink-0">
                              {initials}
                            </div>
                            <div>
                              <p className="font-extrabold text-slate-700 text-sm leading-snug">{ben.beneficiary_name}</p>
                              <p className="text-[11px] font-semibold text-slate-400 leading-none">{ben.bank_name}</p>
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <div className="py-4 text-center text-slate-400 text-xs font-medium">
                        No beneficiaries added yet
                      </div>
                    )}
                  </div>
                </div>

              </div>

            </div>
          </>
        )}

      </div>
    </DashboardLayout>
  );
}

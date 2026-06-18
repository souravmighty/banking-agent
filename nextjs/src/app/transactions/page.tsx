"use client";

import React, { useState } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { useAuth } from "@/hooks/useAuth";
import { ArrowUpRight, ArrowDownLeft, Search, Filter, HelpCircle } from "lucide-react";

export default function TransactionsPage() {
  const { customerContext } = useAuth();
  const [searchTerm, setSearchTerm] = useState("");

  if (!customerContext) return null;

  const isPremium = customerContext.customer_segment?.toUpperCase() === "PREMIUM" || customerContext.customer_segment?.toUpperCase() === "WEALTH";

  const rawTransactions = [
    { id: "TX-10029", merchant: "Whole Foods", category: "Groceries", amount: "-$124.50", date: "June 18, 2026", status: "COMPLETED", type: "debit", method: "Checking ...88" },
    { id: "TX-10028", merchant: "Salary Inward", category: "Income", amount: isPremium ? "+$8,500.00" : "+$3,200.00", date: "June 17, 2026", status: "COMPLETED", type: "credit", method: "Savings ...33" },
    { id: "TX-10027", merchant: "Starbucks Coffee", category: "Dining", amount: "-$6.75", date: "June 17, 2026", status: "COMPLETED", type: "debit", method: "Checking ...88" },
    { id: "TX-10026", merchant: "Netflix Premium", category: "Entertainment", amount: "-$22.99", date: "June 15, 2026", status: "COMPLETED", type: "debit", method: "Credit Card ...45" },
    { id: "TX-10025", merchant: "Apple Store", category: "Electronics", amount: "-$1,299.00", date: "June 12, 2026", status: "COMPLETED", type: "debit", method: "Credit Card ...45" },
    { id: "TX-10024", merchant: "Chevron Fuel", category: "Transport", amount: "-$45.00", date: "June 10, 2026", status: "COMPLETED", type: "debit", method: "Checking ...88" },
    { id: "TX-10023", merchant: "Uber Ride", category: "Transport", amount: "-$18.50", date: "June 08, 2026", status: "COMPLETED", type: "debit", method: "Credit Card ...45" },
  ];

  const filteredTransactions = rawTransactions.filter(
    (tx) =>
      tx.merchant.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tx.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tx.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <DashboardLayout>
      <div className="p-6 md:p-8 space-y-8 animate-fade-in">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-3xl font-extrabold text-[#1a1f71] tracking-tight">Ledger Transactions</h2>
            <p className="text-sm text-slate-500">View detailed, real-time records of your cash inflows and outflows.</p>
          </div>
          
          <div className="flex gap-3">
            <div className="relative">
              <Search className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search merchant, category..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2.5 h-11 w-64 bg-white border border-slate-200 focus:border-[#1a1f71] focus:ring-[#1a1f71]/5 transition-all rounded-xl text-sm"
              />
            </div>
            <button className="h-11 px-4 border border-slate-200 bg-white hover:bg-slate-50 rounded-xl flex items-center gap-2 text-sm font-semibold text-slate-600 transition-colors">
              <Filter className="w-4 h-4 text-slate-400" />
              Filter
            </button>
          </div>
        </div>

        {/* Transactions Table Card */}
        <div className="bg-white rounded-3xl border border-slate-100 shadow-xl shadow-slate-100/30 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-100 text-slate-400 text-xs font-bold uppercase tracking-wider">
                  <th className="p-4 pl-6">Reference ID</th>
                  <th className="p-4">Merchant / Flow</th>
                  <th className="p-4">Category</th>
                  <th className="p-4">Payment Method</th>
                  <th className="p-4">Date</th>
                  <th className="p-4">Status</th>
                  <th className="p-4 pr-6 text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50 text-sm font-semibold text-slate-700">
                {filteredTransactions.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="p-4 pl-6 font-mono text-xs text-[#1a1f71]">{tx.id}</td>
                    <td className="p-4">
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                          tx.type === "credit" ? "bg-emerald-50 text-emerald-600" : "bg-rose-50 text-red-500"
                        }`}>
                          {tx.type === "credit" ? <ArrowDownLeft className="w-4 h-4" /> : <ArrowUpRight className="w-4 h-4" />}
                        </div>
                        <span className="font-bold text-slate-800">{tx.merchant}</span>
                      </div>
                    </td>
                    <td className="p-4 text-slate-500">{tx.category}</td>
                    <td className="p-4 text-slate-500 font-medium">{tx.method}</td>
                    <td className="p-4 text-slate-400 text-xs font-medium">{tx.date}</td>
                    <td className="p-4">
                      <span className="inline-flex px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wide bg-emerald-50 text-emerald-700 border border-emerald-100">
                        {tx.status}
                      </span>
                    </td>
                    <td className={`p-4 pr-6 text-right font-extrabold ${tx.type === "credit" ? "text-emerald-600" : "text-slate-800"}`}>
                      {tx.amount}
                    </td>
                  </tr>
                ))}
                {filteredTransactions.length === 0 && (
                  <tr>
                    <td colSpan={7} className="p-12 text-center text-slate-400 font-medium">
                      No transactions found matching your criteria.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Ledger Guidance Note */}
        <div className="bg-blue-50/50 rounded-2xl p-5 border border-blue-100 flex gap-4">
          <HelpCircle className="w-6 h-6 text-[#1a1f71] shrink-0" />
          <div className="space-y-1">
            <h5 className="font-extrabold text-[#1a1f71] text-sm">RAG & Audit Synchronization</h5>
            <p className="text-xs text-blue-900/60 leading-relaxed">
              These entries represent live immutable records on the Google Cloud BigQuery database ledger. If you perform transfers or payments via the AI Banking Assistant, your ledger updates dynamically in real-time.
            </p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/hooks/useAuth";
import { customerIdentityService, DemoCustomer, DemoSummary } from "@/lib/services/customerIdentityService";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { 
  Landmark, 
  Search, 
  LogOut, 
  RefreshCw, 
  Trash2, 
  CheckCircle, 
  Loader2, 
  Inbox, 
  Calendar,
  Lock,
  User,
  Mail,
  ShieldCheck,
  Power
} from "lucide-react";
import { toast } from "sonner";
import Link from "next/link";

export default function DemoCustomersDashboard() {
  const { user, logout } = useAuth();
  const [customers, setCustomers] = useState<DemoCustomer[]>([]);
  const [summary, setSummary] = useState<DemoSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<number | null>(null); // holds customer_id of row being released
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "AVAILABLE" | "ALLOCATED">("ALL");

  const loadData = useCallback(async () => {
    if (!user) return;
    try {
      setLoading(true);
      const token = await user.getIdToken();
      
      const [custList, summaryData] = await Promise.all([
        customerIdentityService.getDemoCustomers(token),
        customerIdentityService.getDemoSummary(token)
      ]);
      
      setCustomers(custList);
      setSummary(summaryData);
    } catch (err) {
      console.error("Failed to load customer parameters:", err);
      toast.error("Failed to load customer parameters.");
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Handle Release Customer Allocation
  const handleRelease = async (customerId: number) => {
    if (!user) return;
    
    setActionLoading(customerId);
    try {
      const token = await user.getIdToken();
      const res = await customerIdentityService.releaseDemoCustomer(token, customerId.toString());
      
      toast.success(`Demo customer ${customerId} released successfully. Deleted ${res.deleted_views_count} BigQuery views.`);
      await loadData();
    } catch (err) {
      console.error("Failed to release demo customer:", err);
      toast.error((err as Error).message || "Failed to release demo customer.");
    } finally {
      setActionLoading(null);
    }
  };

  // Filter list
  const filteredCustomers = customers.filter((cust) => {
    const matchesSearch = 
      cust.customer_id.toString().includes(searchTerm) ||
      (cust.demo_name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (cust.demo_email || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      cust.original_email.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = 
      statusFilter === "ALL" ||
      (statusFilter === "AVAILABLE" && cust.status === "AVAILABLE") ||
      (statusFilter === "ALLOCATED" && cust.status !== "AVAILABLE");

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="min-h-screen bg-[#060814] text-slate-100 flex flex-col font-sans">
      {/* Dashboard Header Banner */}
      <header className="border-b border-slate-900 bg-slate-950/60 backdrop-blur-md px-6 py-4 flex items-center justify-between sticky top-0 z-20">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-600 flex items-center justify-center border border-indigo-500/20 shadow-md">
            <Landmark className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-md font-extrabold tracking-tight">BankPilot Operations</h1>
            <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">Administrative Console</p>
          </div>
        </div>

        <nav className="hidden md:flex items-center gap-6 text-sm font-semibold text-slate-400">
          <Link href="/staff/demo-requests" className="hover:text-white transition-colors pb-1 border-b border-transparent">
            Demo Requests
          </Link>
          <Link href="/staff/demo-customers" className="text-white hover:text-white transition-colors pb-1 border-b border-indigo-500">
            Demo Customers Pool
          </Link>
        </nav>

        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400 font-medium bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-full">
            {user?.email || "Admin Session"}
          </span>
          <Button 
            variant="outline" 
            onClick={() => logout()}
            className="border-slate-800 hover:bg-slate-900 hover:text-white text-slate-400 h-9 px-3 text-xs font-semibold gap-1.5"
          >
            <LogOut className="h-3.5 w-3.5" />
            Sign Out
          </Button>
        </div>
      </header>

      {/* Sub-nav mobile */}
      <div className="md:hidden flex items-center justify-center gap-6 bg-slate-950 px-4 py-2.5 border-b border-slate-900 text-xs font-bold text-slate-400">
        <Link href="/staff/demo-requests">
          Requests
        </Link>
        <Link href="/staff/demo-customers" className="text-white">
          Customers Pool
        </Link>
      </div>

      <main className="flex-1 p-6 md:p-10 max-w-7xl w-full mx-auto space-y-8">
        {/* Metric Cards Grid */}
        <section className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            {
              title: "Total Pool Capacity",
              value: customers.length || 20,
              icon: Landmark,
              color: "text-slate-400",
              bgColor: "bg-slate-900/30 border-slate-900"
            },
            {
              title: "Allocated Active Demo Users",
              value: summary?.allocated_customers ?? 0,
              icon: ShieldCheck,
              color: "text-indigo-400",
              bgColor: "bg-indigo-500/10 border-indigo-500/20"
            },
            {
              title: "Available Free Customers",
              value: summary?.available_customers ?? 20,
              icon: CheckCircle,
              color: "text-emerald-400",
              bgColor: "bg-emerald-500/10 border-emerald-500/20"
            }
          ].map((card, idx) => (
            <Card key={idx} className={`border ${card.bgColor} bg-slate-900/40 backdrop-blur-md`}>
              <CardContent className="p-4 md:p-5 flex items-center justify-between">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">{card.title}</p>
                  <h3 className="text-2xl md:text-3xl font-black text-white">{loading ? "..." : card.value}</h3>
                </div>
                <div className="w-10 h-10 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center justify-center text-slate-400">
                  <card.icon className={`h-5 w-5 ${card.color}`} />
                </div>
              </CardContent>
            </Card>
          ))}
        </section>

        {/* Filters and List */}
        <section className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-4 items-stretch sm:items-center justify-between">
            {/* Search Input */}
            <div className="relative max-w-sm flex-1">
              <Search className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
              <Input
                type="text"
                placeholder="Search Customer ID, demo email, or base name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 bg-slate-900/60 border-slate-800/80 text-white rounded-xl focus:border-indigo-500 focus:ring-indigo-500/30 text-xs h-10"
              />
            </div>

            {/* Filter Buttons */}
            <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-900 text-[11px] font-bold text-slate-400 overflow-x-auto">
              {[
                { filter: "ALL", label: "All Customers" },
                { filter: "AVAILABLE", label: "Available Pool" },
                { filter: "ALLOCATED", label: "Allocated Active" }
              ].map((item) => (
                <button
                  key={item.filter}
                  onClick={() => setStatusFilter(item.filter as "ALL" | "AVAILABLE" | "ALLOCATED")}
                  className={`px-3.5 py-1.5 rounded-lg whitespace-nowrap transition-all ${
                    statusFilter === item.filter 
                      ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/10" 
                      : "hover:text-white"
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          {/* Table Container */}
          <Card className="border-slate-900 bg-slate-950/30 overflow-hidden">
            <CardContent className="p-0">
              {loading ? (
                <div className="flex flex-col items-center justify-center py-20 text-slate-500 gap-3">
                  <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
                  <p className="text-xs font-semibold">Scanning BigQuery demo tables...</p>
                </div>
              ) : filteredCustomers.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-slate-500 text-center px-4">
                  <Inbox className="h-10 w-10 text-slate-700 mb-3" />
                  <p className="text-sm font-bold text-slate-400">No matching demo customers found</p>
                  <p className="text-xs text-slate-600 mt-1">There are no records matching your current criteria.</p>
                </div>
              ) : (
                <div className="overflow-x-auto w-full">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="border-b border-slate-900 text-slate-500 font-bold uppercase tracking-wider bg-slate-950/50">
                        <th className="px-5 py-3.5">Customer ID</th>
                        <th className="px-5 py-3.5">Allocation Status</th>
                        <th className="px-5 py-3.5">Allocated Demo User</th>
                        <th className="px-5 py-3.5">Firebase UID / Google Email</th>
                        <th className="px-5 py-3.5">Expires At</th>
                        <th className="px-5 py-3.5 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-900/60">
                      {filteredCustomers.map((cust) => {
                        const isAllocated = cust.status !== "AVAILABLE";
                        return (
                          <tr 
                            key={cust.customer_id}
                            className="hover:bg-slate-900/20 group transition-colors"
                          >
                            <td className="px-5 py-4 font-mono font-bold text-slate-300">
                              {cust.customer_id}
                            </td>
                            <td className="px-5 py-4">
                              <span className={`inline-flex px-2 py-0.5 rounded text-[9px] font-extrabold tracking-wider ${
                                cust.status === "AVAILABLE" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
                                cust.status === "APPROVED" ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" :
                                "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"
                              }`}>
                                {cust.status}
                              </span>
                            </td>
                            <td className="px-5 py-4">
                              {isAllocated ? (
                                <div>
                                  <p className="font-bold text-white">{cust.demo_name}</p>
                                  <p className="text-slate-500 font-medium text-[11px]">{cust.demo_email}</p>
                                </div>
                              ) : (
                                <span className="text-slate-600 italic">Unallocated Pool Customer</span>
                              )}
                            </td>
                            <td className="px-5 py-4">
                              {isAllocated ? (
                                <div className="space-y-0.5 text-[11px]">
                                  <div className="flex items-center gap-1 text-slate-400">
                                    <Lock className="h-3.5 w-3.5 text-slate-600" />
                                    <span className="font-mono">{cust.firebase_uid || "No Login Yet"}</span>
                                  </div>
                                  <div className="flex items-center gap-1 text-slate-500">
                                    <Mail className="h-3.5 w-3.5 text-slate-700" />
                                    <span>{cust.demo_email}</span>
                                  </div>
                                </div>
                              ) : (
                                <span className="text-slate-700 font-medium font-mono text-[10px]">Restored Base State</span>
                              )}
                            </td>
                            <td className="px-5 py-4 text-slate-400">
                              {isAllocated && cust.expires_at ? (
                                <div className="flex items-center gap-1.5 text-amber-500/80 font-semibold">
                                  <Calendar className="h-3.5 w-3.5 text-slate-600" />
                                  {new Date(cust.expires_at).toLocaleString("en-US", {
                                    month: "short",
                                    day: "numeric",
                                    hour: "2-digit",
                                    minute: "2-digit"
                                  })}
                                </div>
                              ) : (
                                <span className="text-slate-700">—</span>
                              )}
                            </td>
                            <td className="px-5 py-4 text-right">
                              {isAllocated ? (
                                <Button
                                  size="sm"
                                  onClick={() => handleRelease(cust.customer_id)}
                                  disabled={actionLoading !== null}
                                  className="bg-rose-950/20 hover:bg-rose-950/40 text-rose-400 border border-rose-900/30 font-bold h-8 px-3 rounded-lg text-xs gap-1.5"
                                >
                                  {actionLoading === cust.customer_id ? (
                                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                  ) : (
                                    <>
                                      <Power className="h-3.5 w-3.5" />
                                      Release Customer
                                    </>
                                  )}
                                </Button>
                              ) : (
                                <span className="text-[10px] text-slate-600 font-bold uppercase tracking-wider mr-3">Available</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </section>
      </main>

      {/* Footer */}
      <footer className="mt-12 border-t border-slate-950 py-6 text-center text-xs text-slate-600">
        <p>© 2026 BankPilot Systems. Operations control layer. Confidential.</p>
      </footer>
    </div>
  );
}

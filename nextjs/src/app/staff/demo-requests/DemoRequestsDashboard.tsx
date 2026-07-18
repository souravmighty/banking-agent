"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/hooks/useAuth";
import { customerIdentityService, DemoRequest, DemoSummary } from "@/lib/services/customerIdentityService";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { 
  Landmark, 
  Search, 
  LogOut, 
  Check, 
  X, 
  Eye, 
  Clock, 
  Inbox, 
  CheckCircle2, 
  XCircle, 
  Calendar,
  AlertTriangle,
  Loader2,
  Linkedin,
  Building,
  User,
  ExternalLink,
  ChevronRight
} from "lucide-react";
import { toast } from "sonner";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

export function DemoRequestsDashboard({ requestId }: { requestId?: string }) {
  const { user, logout } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // Dashboard states
  const [requests, setRequests] = useState<DemoRequest[]>([]);
  const [summary, setDemoSummary] = useState<DemoSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null); // holds request_id if processing
  
  // Filtering and Searching
  const [searchTerm, setSearchTerm] = useState("");
  const [activeTab, setActiveTab] = useState<"ALL" | "PENDING" | "ALLOCATED" | "REJECTED" | "EXPIRED">("PENDING");
  
  // Detail Drawer state
  const [selectedRequest, setSelectedRequest] = useState<DemoRequest | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [rejectRemarks, setRejectRemarks] = useState("");
  const [isRejectModalOpen, setIsRejectModalOpen] = useState(false);
 
  // Load dashboard data
  const loadDashboardData = useCallback(async () => {
    if (!user) return;
    try {
      setLoading(true);
      const token = await user.getIdToken();
      
      const [reqList, summaryData] = await Promise.all([
        customerIdentityService.getDemoRequests(token),
        customerIdentityService.getDemoSummary(token)
      ]);
      
      setRequests(reqList);
      setDemoSummary(summaryData);
 
      // Handle deep-link request ID parameter if provided in path params or query params
      const deepLinkId = requestId || searchParams.get("requestId");
      if (deepLinkId) {
        const matched = reqList.find(r => r.request_id === deepLinkId);
        if (matched) {
          setSelectedRequest(matched);
          setIsDrawerOpen(true);
          
          // Check action parameter in URL
          const action = searchParams.get("action");
          if (action === "approve" && matched.status === "PENDING") {
            toast.info(`Pre-authorized intent: Approve request for ${matched.name}`);
          } else if (action === "reject" && matched.status === "PENDING") {
            setRejectRemarks("Auto-loaded reject intent");
            setIsRejectModalOpen(true);
          }
        } else {
          toast.error("Deep-linked request not found.");
        }
      }
    } catch (err) {
      console.error("Failed to load dashboard parameters:", err);
      toast.error("Failed to load dashboard parameters.");
    } finally {
      setLoading(false);
    }
  }, [user, requestId, searchParams]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // Handle Approve Action
  const handleApprove = async (request: DemoRequest) => {
    if (!user) return;
    setActionLoading(request.request_id);
    try {
      const token = await user.getIdToken();
      const res = await customerIdentityService.approveDemoRequest(token, request.request_id);
      
      toast.success(res.message || `Demo request approved! Allocated customer ${res.customer_id}`);
      
      // Close drawer and reload dashboard
      setIsDrawerOpen(false);
      setSelectedRequest(null);
      await loadDashboardData();
    } catch (err) {
      console.error("Approval execution failed:", err);
      toast.error((err as Error).message || "Failed to approve demo request.");
    } finally {
      setActionLoading(null);
    }
  };

  // Handle Reject Action
  const handleReject = async () => {
    if (!user || !selectedRequest) return;
    setActionLoading(selectedRequest.request_id);
    setIsRejectModalOpen(false);
    try {
      const token = await user.getIdToken();
      await customerIdentityService.rejectDemoRequest(token, selectedRequest.request_id, rejectRemarks);
      
      toast.success("Demo request rejected.");
      setRejectRemarks("");
      setIsDrawerOpen(false);
      setSelectedRequest(null);
      await loadDashboardData();
    } catch (err) {
      console.error("Rejection execution failed:", err);
      toast.error((err as Error).message || "Failed to reject demo request.");
    } finally {
      setActionLoading(null);
    }
  };

  // Filter lists based on tab and search
  const filteredRequests = requests.filter((req) => {
    const matchesSearch = 
      req.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      req.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (req.company || "").toLowerCase().includes(searchTerm.toLowerCase());

    if (activeTab === "ALL") return matchesSearch;
    if (activeTab === "PENDING") return matchesSearch && req.status === "PENDING";
    if (activeTab === "ALLOCATED") return matchesSearch && req.status === "ALLOCATED";
    if (activeTab === "REJECTED") return matchesSearch && req.status === "REJECTED";
    if (activeTab === "EXPIRED") return matchesSearch && req.status === "EXPIRED";
    return matchesSearch;
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
          <Link href="/staff/demo-requests" className="text-white hover:text-white transition-colors pb-1 border-b border-indigo-500">
            Demo Requests
          </Link>
          <Link href="/staff/demo-customers" className="hover:text-white transition-colors pb-1 border-b border-transparent">
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
        <Link href="/staff/demo-requests" className="text-white">
          Requests
        </Link>
        <Link href="/staff/demo-customers">
          Customers Pool
        </Link>
      </div>

      <main className="flex-1 p-6 md:p-10 max-w-7xl w-full mx-auto space-y-8">
        {/* Metric Cards Grid */}
        <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            {
              title: "Pending Requests",
              value: summary?.pending_requests ?? 0,
              icon: Clock,
              color: "text-amber-400",
              bgColor: "bg-amber-500/10 border-amber-500/20"
            },
            {
              title: "Allocated Customers",
              value: summary?.allocated_customers ?? 0,
              icon: CheckCircle2,
              color: "text-indigo-400",
              bgColor: "bg-indigo-500/10 border-indigo-500/20"
            },
            {
              title: "Available Pool",
              value: summary?.available_customers ?? 0,
              icon: Landmark,
              color: "text-emerald-400",
              bgColor: "bg-emerald-500/10 border-emerald-500/20"
            },
            {
              title: "Expired Today",
              value: summary?.expired_today ?? 0,
              icon: XCircle,
              color: "text-rose-400",
              bgColor: "bg-rose-500/10 border-rose-500/20"
            }
          ].map((card, idx) => (
            <Card key={idx} className={`border ${card.bgColor} bg-slate-900/40 backdrop-blur-md`}>
              <CardContent className="p-4 md:p-5 flex items-center justify-between">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">{card.title}</p>
                  <h3 className="text-2xl md:text-3xl font-black text-white">{loading ? "..." : card.value}</h3>
                </div>
                <div className={`w-10 h-10 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center justify-center ${card.color}`}>
                  <card.icon className="h-5 w-5" />
                </div>
              </CardContent>
            </Card>
          ))}
        </section>

        {/* Filters and Table Section */}
        <section className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-4 items-stretch sm:items-center justify-between">
            {/* Search Input */}
            <div className="relative max-w-sm flex-1">
              <Search className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
              <Input
                type="text"
                placeholder="Search name, email, or company..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 bg-slate-900/60 border-slate-800/80 text-white rounded-xl focus:border-indigo-500 focus:ring-indigo-500/30 text-xs h-10"
              />
            </div>

            {/* Filter Tabs */}
            <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-900 text-[11px] font-bold text-slate-400 overflow-x-auto">
              {(["PENDING", "ALLOCATED", "REJECTED", "EXPIRED", "ALL"] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-3.5 py-1.5 rounded-lg whitespace-nowrap transition-all ${
                    activeTab === tab 
                      ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/10" 
                      : "hover:text-white"
                  }`}
                >
                  {tab === "ALL" ? "All Requests" : tab.charAt(0) + tab.slice(1).toLowerCase()}
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
                  <p className="text-xs font-semibold">Retrieving database state...</p>
                </div>
              ) : filteredRequests.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-slate-500 text-center px-4">
                  <Inbox className="h-10 w-10 text-slate-700 mb-3" />
                  <p className="text-sm font-bold text-slate-400">No matching requests found</p>
                  <p className="text-xs text-slate-600 mt-1">There are no records matching your current filter parameter sets.</p>
                </div>
              ) : (
                <div className="overflow-x-auto w-full">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="border-b border-slate-900 text-slate-500 font-bold uppercase tracking-wider bg-slate-950/50">
                        <th className="px-5 py-3.5">Requester Details</th>
                        <th className="px-5 py-3.5">Business / Role</th>
                        <th className="px-5 py-3.5">Requested At</th>
                        <th className="px-5 py-3.5">Status</th>
                        <th className="px-5 py-3.5 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-900/60">
                      {filteredRequests.map((req) => (
                        <tr 
                          key={req.request_id}
                          className="hover:bg-slate-900/20 group transition-colors"
                        >
                          <td className="px-5 py-4">
                            <div>
                              <p className="font-bold text-white group-hover:text-indigo-400 transition-colors">{req.name}</p>
                              <p className="text-slate-500 font-medium text-[11px]">{req.email}</p>
                            </div>
                          </td>
                          <td className="px-5 py-4">
                            <div>
                              <p className="font-semibold text-slate-300">{req.company || "Individual/Independent"}</p>
                              <p className="text-slate-500 text-[11px]">{req.role || "N/A"}</p>
                            </div>
                          </td>
                          <td className="px-5 py-4 text-slate-400">
                            <div className="flex items-center gap-1.5">
                              <Calendar className="h-3.5 w-3.5 text-slate-600" />
                              {req.created_at ? new Date(req.created_at).toLocaleDateString("en-US", {
                                month: "short",
                                day: "numeric",
                                hour: "2-digit",
                                minute: "2-digit"
                              }) : "N/A"}
                            </div>
                          </td>
                          <td className="px-5 py-4">
                            <span className={`inline-flex px-2 py-1 rounded-md text-[10px] font-bold ${
                              req.status === "PENDING" ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" :
                              req.status === "ALLOCATED" ? "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20" :
                              req.status === "REJECTED" ? "bg-rose-500/10 text-rose-400 border border-rose-500/20" :
                              "bg-slate-800 text-slate-400"
                            }`}>
                              {req.status}
                            </span>
                          </td>
                          <td className="px-5 py-4 text-right">
                            <div className="flex items-center justify-end gap-2 opacity-90 group-hover:opacity-100">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                  setSelectedRequest(req);
                                  setIsDrawerOpen(true);
                                }}
                                className="border-slate-800 hover:bg-slate-900 hover:text-white text-slate-400 h-8 px-2.5 rounded-lg text-xs"
                              >
                                <Eye className="h-3.5 w-3.5" />
                              </Button>

                              {req.status === "PENDING" && (
                                <>
                                  <Button
                                    size="sm"
                                    onClick={() => handleApprove(req)}
                                    disabled={actionLoading !== null}
                                    className="bg-indigo-600 hover:bg-indigo-500 text-white h-8 px-2.5 rounded-lg text-xs"
                                  >
                                    {actionLoading === req.request_id ? (
                                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                    ) : (
                                      <Check className="h-3.5 w-3.5" />
                                    )}
                                  </Button>
                                  <Button
                                    size="sm"
                                    onClick={() => {
                                      setSelectedRequest(req);
                                      setRejectRemarks("");
                                      setIsRejectModalOpen(true);
                                    }}
                                    disabled={actionLoading !== null}
                                    className="bg-rose-950/20 hover:bg-rose-950/40 text-rose-400 border border-rose-900/30 h-8 px-2.5 rounded-lg text-xs"
                                  >
                                    <X className="h-3.5 w-3.5" />
                                  </Button>
                                </>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </section>
      </main>

      {/* Slide-out Detail Drawer */}
      {isDrawerOpen && selectedRequest && (
        <div className="fixed inset-0 z-50 flex justify-end">
          {/* Backdrop */}
          <div 
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setIsDrawerOpen(false)}
          />
          
          {/* Drawer Panel */}
          <div className="relative w-full max-w-md bg-[#0a0d1d] h-full shadow-2xl border-l border-slate-900 p-6 flex flex-col justify-between overflow-y-auto animate-slide-in">
            <div className="space-y-6">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-[9px] font-extrabold tracking-wider ${
                    selectedRequest.status === "PENDING" ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" :
                    selectedRequest.status === "ALLOCATED" ? "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20" :
                    selectedRequest.status === "REJECTED" ? "bg-rose-500/10 text-rose-400 border border-rose-500/20" :
                    "bg-slate-800 text-slate-400"
                  }`}>
                    {selectedRequest.status}
                  </span>
                  <p className="text-[10px] text-slate-500 font-bold">Request Detail</p>
                </div>
                <button 
                  onClick={() => setIsDrawerOpen(false)}
                  className="p-1 rounded-lg hover:bg-slate-900 text-slate-500 hover:text-white"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              {/* Profile Overview */}
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-indigo-500/10 to-violet-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20 font-bold text-lg">
                  {selectedRequest.name.charAt(0)}
                </div>
                <div>
                  <h2 className="text-lg font-extrabold text-white">{selectedRequest.name}</h2>
                  <p className="text-xs text-slate-500 font-semibold">{selectedRequest.email}</p>
                </div>
              </div>

              <hr className="border-slate-900" />

              {/* Metadata Fields */}
              <div className="space-y-4">
                {[
                  { label: "Company", value: selectedRequest.company, icon: Building },
                  { label: "Role / Title", value: selectedRequest.role, icon: User }
                ].map((item, idx) => (
                  <div key={idx} className="flex gap-3">
                    <div className="mt-0.5 text-slate-600">
                      <item.icon className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{item.label}</p>
                      <p className="text-xs font-semibold text-slate-300">{item.value || "Not Specified"}</p>
                    </div>
                  </div>
                ))}

                {/* LinkedIn Link */}
                <div className="flex gap-3">
                  <div className="mt-0.5 text-slate-600">
                    <Linkedin className="h-4 w-4" />
                  </div>
                  <div className="flex-1">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">LinkedIn Profile</p>
                    {selectedRequest.linkedin ? (
                      <a 
                        href={selectedRequest.linkedin} 
                        target="_blank" 
                        rel="noreferrer"
                        className="text-xs font-semibold text-indigo-400 hover:underline flex items-center gap-1 mt-0.5"
                      >
                        View Profile
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    ) : (
                      <p className="text-xs font-semibold text-slate-500">Not Specified</p>
                    )}
                  </div>
                </div>

                {/* Purpose Field */}
                <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-900 space-y-1.5">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-indigo-400">Statement of Purpose</p>
                  <p className="text-xs text-slate-300 leading-normal font-medium">
                    {selectedRequest.purpose || "No evaluation description was submitted with this request."}
                  </p>
                </div>
              </div>

              <hr className="border-slate-900" />

              {/* Technical / Log details */}
              <div className="space-y-3.5 text-xs text-slate-400">
                <div className="flex justify-between">
                  <span>Created At:</span>
                  <span className="font-semibold text-slate-300">
                    {selectedRequest.created_at ? new Date(selectedRequest.created_at).toLocaleString() : "N/A"}
                  </span>
                </div>
                {selectedRequest.status !== "PENDING" && (
                  <>
                    <div className="flex justify-between">
                      <span>Reviewed By:</span>
                      <span className="font-semibold text-slate-300">{selectedRequest.approved_by || "Admin"}</span>
                    </div>
                    {selectedRequest.updated_at && (
                      <div className="flex justify-between">
                        <span>Reviewed At:</span>
                        <span className="font-semibold text-slate-300">{new Date(selectedRequest.updated_at).toLocaleString()}</span>
                      </div>
                    )}
                  </>
                )}
                {selectedRequest.status === "ALLOCATED" && (
                  <>
                    <div className="flex justify-between text-indigo-400">
                      <span>Allocated Customer:</span>
                      <span className="font-bold">{selectedRequest.customer_id}</span>
                    </div>
                    <div className="flex justify-between text-amber-500">
                      <span>Access Expiry:</span>
                      <span className="font-semibold">
                        {selectedRequest.expires_at ? new Date(selectedRequest.expires_at).toLocaleString() : "N/A"}
                      </span>
                    </div>
                  </>
                )}
                {selectedRequest.remarks && (
                  <div className="p-3 bg-slate-950/20 border border-slate-900/60 rounded-lg text-slate-500 mt-1">
                    <span className="font-bold text-[10px] uppercase text-slate-400 block mb-0.5">Admin Remarks</span>
                    {selectedRequest.remarks}
                  </div>
                )}
              </div>
            </div>

            {/* Bottom Actions inside Drawer */}
            {selectedRequest.status === "PENDING" && (
              <div className="grid grid-cols-2 gap-3 pt-6 border-t border-slate-900">
                <Button
                  onClick={() => handleApprove(selectedRequest)}
                  disabled={actionLoading !== null}
                  className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold h-10 rounded-xl border border-indigo-500/20 flex items-center justify-center gap-1.5"
                >
                  {actionLoading === selectedRequest.request_id ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <>
                      <Check className="h-4 w-4" />
                      Approve Request
                    </>
                  )}
                </Button>
                <Button
                  onClick={() => {
                    setRejectRemarks("");
                    setIsRejectModalOpen(true);
                  }}
                  disabled={actionLoading !== null}
                  className="w-full bg-rose-950/20 hover:bg-rose-950/40 text-rose-400 border border-rose-900/30 font-bold h-10 rounded-xl flex items-center justify-center gap-1.5"
                >
                  <X className="h-4 w-4" />
                  Reject Request
                </Button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Reject Modal dialog */}
      {isRejectModalOpen && selectedRequest && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setIsRejectModalOpen(false)} />
          
          <Card className="relative w-full max-w-md border-rose-900/40 bg-slate-950 shadow-2xl rounded-2xl overflow-hidden border z-10 p-6 animate-scale-in">
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-rose-400">
                <AlertTriangle className="h-5 w-5" />
                <h3 className="font-bold text-md">Reject Demo Request</h3>
              </div>
              <p className="text-xs text-slate-400 leading-normal">
                Please enter a reason or remarks for rejecting <span className="text-white font-semibold">{selectedRequest.name}</span>&apos;s request. An automated notification will be compiled and printed.
              </p>
              
              <textarea
                placeholder="Reason for rejection (e.g. invalid profile)..."
                value={rejectRemarks}
                onChange={(e) => setRejectRemarks(e.target.value)}
                rows={3}
                className="w-full p-3 bg-slate-900/60 border border-slate-800 text-white rounded-xl focus:border-rose-500 focus:ring-1 focus:ring-rose-500/30 text-xs focus:outline-none placeholder:text-slate-600"
              />

              <div className="flex items-center justify-end gap-3 pt-2">
                <Button
                  variant="outline"
                  onClick={() => setIsRejectModalOpen(false)}
                  className="border-slate-800 text-slate-400 hover:bg-slate-900 hover:text-white text-xs h-9 px-4 rounded-lg"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleReject}
                  className="bg-rose-600 hover:bg-rose-500 text-white text-xs h-9 px-4 rounded-lg font-bold"
                >
                  Confirm Rejection
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

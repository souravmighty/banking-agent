"use client";

import React, { useState, useEffect, useCallback } from "react";
import { StaffSidebarLayout } from "@/components/staff/StaffSidebarLayout";
import { useAuth } from "@/hooks/useAuth";
import {
  customerIdentityService,
  KnowledgeDocument,
  KnowledgeVersion,
  KnowledgeAuditLog,
} from "@/lib/services/customerIdentityService";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  BookOpen,
  UploadCloud,
  RefreshCw,
  Search,
  CheckCircle2,
  AlertCircle,
  Archive,
  History,
  FileText,
  Layers,
  X,
  ShieldCheck,
  Calendar,
} from "lucide-react";

export default function KnowledgeManagementPage() {
  const { user } = useAuth();
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string>("ALL");
  const [productFilter, setProductFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [accessScopeFilter, setAccessScopeFilter] = useState<string>("ALL");

  // Modals & Drawers
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false);
  const [selectedDoc, setSelectedDoc] = useState<KnowledgeDocument | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);
  const [versions, setVersions] = useState<KnowledgeVersion[]>([]);
  const [auditLogs, setAuditLogs] = useState<KnowledgeAuditLog[]>([]);
  const [loadingDrawer, setLoadingDrawer] = useState<boolean>(false);

  // Upload Form State
  const [file, setFile] = useState<File | null>(null);
  const [formLogicalId, setFormLogicalId] = useState<string>("");
  const [formDocName, setFormDocName] = useState<string>("");
  const [formDocType, setFormDocType] = useState<string>("PRODUCT");
  const [formProductType, setFormProductType] = useState<string>("CREDIT_CARD");
  const [formProductId, setFormProductId] = useState<string>("");
  const [formProductName, setFormProductName] = useState<string>("");
  const [formVersion, setFormVersion] = useState<string>("v1.0.0");
  const [formEffectiveFrom, setFormEffectiveFrom] = useState<string>(
    new Date().toISOString().split("T")[0]
  );
  const [formEffectiveTo, setFormEffectiveTo] = useState<string>("");
  const [formRegion, setFormRegion] = useState<string>("IN");
  const [formAudience, setFormAudience] = useState<string>("ALL");
  const [formAccessControl, setFormAccessControl] = useState<string[]>(["CUSTOMER", "STAFF"]);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Load documents
  const fetchDocuments = useCallback(async () => {
    if (!user) return;
    try {
      setError(null);
      const token = await user.getIdToken();
      if (!token) return;

      const filters: {
        document_type?: string;
        product_type?: string;
        status?: string;
        access_scope?: string;
      } = {};
      if (typeFilter !== "ALL") filters.document_type = typeFilter;
      if (productFilter !== "ALL") filters.product_type = productFilter;
      if (statusFilter !== "ALL") filters.status = statusFilter;
      if (accessScopeFilter !== "ALL") filters.access_scope = accessScopeFilter;

      const res = await customerIdentityService.getKnowledgeDocuments(token, filters);
      setDocuments(res.documents || []);
    } catch (err: unknown) {
      console.error("Failed to load documents:", err);
      const msg = err instanceof Error ? err.message : "Failed to load knowledge documents";
      setError(msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [user, typeFilter, productFilter, statusFilter, accessScopeFilter]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  // Auto-poll when documents are indexing in background
  useEffect(() => {
    const hasPending = documents.some(
      (d) =>
        d.status === "PROCESSING" ||
        d.ingestion_status === "INDEXING" ||
        d.ingestion_status === "PENDING"
    );
    if (!hasPending) return;

    const intervalId = setInterval(() => {
      fetchDocuments();
    }, 3000);

    return () => clearInterval(intervalId);
  }, [documents, fetchDocuments]);

  // Auto-dismiss toast after 6 seconds
  useEffect(() => {
    if (!toastMessage) return;
    const timer = setTimeout(() => setToastMessage(null), 6000);
    return () => clearTimeout(timer);
  }, [toastMessage]);

  // Open Version History Drawer
  const handleOpenDrawer = async (doc: KnowledgeDocument) => {
    setSelectedDoc(doc);
    setIsDrawerOpen(true);
    setLoadingDrawer(true);
    try {
      const token = await user?.getIdToken();
      if (!token) return;

      const [vers, logs] = await Promise.all([
        customerIdentityService.getKnowledgeDocumentVersions(token, doc.document_id),
        customerIdentityService.getKnowledgeDocumentAuditLogs(token, doc.document_id),
      ]);
      setVersions(vers || []);
      setAuditLogs(logs || []);
    } catch (err) {
      console.error("Error fetching version/audit history:", err);
    } finally {
      setLoadingDrawer(false);
    }
  };

  // Upload handler
  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setUploadError("Please select a document file (.pdf, .docx, .txt, .md)");
      return;
    }
    if (!formLogicalId || !formDocName || !formVersion || !formEffectiveFrom) {
      setUploadError("Please fill in all required fields.");
      return;
    }
    if (!formAccessControl || formAccessControl.length === 0) {
      setUploadError("Please select at least one Access Scope (CUSTOMER or STAFF).");
      return;
    }

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(false);

    try {
      const token = await user?.getIdToken();
      if (!token) throw new Error("Authentication token expired");

      const formData = new FormData();
      formData.append("file", file);
      formData.append("logical_document_id", formLogicalId.trim());
      formData.append("document_name", formDocName.trim());
      formData.append("document_type", formDocType);
      formData.append("version", formVersion.trim());
      formData.append("effective_from", formEffectiveFrom);
      if (formDocType === "PRODUCT") {
        formData.append("product_type", formProductType);
        if (formProductId) formData.append("product_id", formProductId.trim());
        if (formProductName) formData.append("product_name", formProductName.trim());
      }
      if (formEffectiveTo) formData.append("effective_to", formEffectiveTo);
      formData.append("region", formRegion);
      formData.append("audience", formAudience);
      formData.append("access_control", formAccessControl.join(","));

      await customerIdentityService.uploadKnowledgeDocument(token, formData);
      
      // Close popup modal and display success banner
      setIsUploadOpen(false);
      setFile(null);
      setToastMessage({
        type: "success",
        text: `Document '${formDocName.trim()}' uploaded successfully to Cloud Storage! Vertex AI RAG Vector DB indexing is running in the background.`,
      });
      fetchDocuments();
    } catch (err: unknown) {
      console.error("Upload error:", err);
      const msg = err instanceof Error ? err.message : "Document upload failed.";
      setUploadError(msg);
    } finally {
      setUploading(false);
    }
  };

  // Retry handler
  const handleRetry = async (documentId: string) => {
    try {
      const token = await user?.getIdToken();
      if (!token) return;
      await customerIdentityService.retryKnowledgeDocument(token, documentId);
      fetchDocuments();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Retry failed";
      alert("Retry failed: " + msg);
    }
  };

  // Archive handler
  const handleArchive = async (documentId: string) => {
    if (!confirm("Are you sure you want to archive this document version? Active customers will no longer retrieve it.")) {
      return;
    }
    try {
      const token = await user?.getIdToken();
      if (!token) return;
      await customerIdentityService.archiveKnowledgeDocument(token, documentId);
      fetchDocuments();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Archive failed";
      alert("Archive failed: " + msg);
    }
  };

  // Pre-fill modal for creating a new version of existing document
  const handleCreateNewVersion = (doc: KnowledgeDocument) => {
    setFormLogicalId(doc.logical_document_id);
    setFormDocName(doc.document_name);
    setFormDocType(doc.document_type);
    if (doc.product_type) setFormProductType(doc.product_type);
    if (doc.product_id) setFormProductId(doc.product_id);
    if (doc.product_name) setFormProductName(doc.product_name);
    setFormRegion(doc.region || "IN");
    setFormAudience(doc.audience || "ALL");
    setFormAccessControl(
      doc.access_control && doc.access_control.length > 0
        ? doc.access_control
        : ["CUSTOMER", "STAFF"]
    );
    setFormVersion("v" + (parseFloat(doc.version.replace(/[^0-9.]/g, "")) + 1.0).toFixed(1));
    setFile(null);
    setUploadError(null);
    setIsUploadOpen(true);
  };

  // Search filter
  const filteredDocs = documents.filter((doc) => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return true;
    return (
      doc.document_name.toLowerCase().includes(q) ||
      doc.logical_document_id.toLowerCase().includes(q) ||
      (doc.product_name && doc.product_name.toLowerCase().includes(q)) ||
      (doc.original_filename && doc.original_filename.toLowerCase().includes(q))
    );
  });

  return (
    <StaffSidebarLayout>
      <div className="flex-1 space-y-6 p-6 lg:p-8 max-w-7xl mx-auto w-full">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-indigo-100 dark:bg-indigo-950/70 border border-indigo-200 dark:border-indigo-800 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
                <BookOpen className="h-5 w-5" />
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                Enterprise Knowledge Base
              </h1>
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Governed document repository and Vertex AI RAG Engine grounding pipeline for banking products, policies, and terms.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setRefreshing(true);
                fetchDocuments();
              }}
              disabled={refreshing || loading}
              className="gap-1.5 h-9"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </Button>

            <Button
              onClick={() => {
                setFormLogicalId("");
                setFormDocName("");
                setFormDocType("PRODUCT");
                setFormProductType("CREDIT_CARD");
                setFormProductId("");
                setFormProductName("");
                setFormVersion("v1.0.0");
                setFile(null);
                setUploadError(null);
                setIsUploadOpen(true);
              }}
              className="bg-indigo-600 hover:bg-indigo-700 text-white gap-2 h-9 shadow-sm shadow-indigo-600/20"
            >
              <UploadCloud className="h-4 w-4" />
              <span>Upload Document</span>
            </Button>
          </div>
        </div>

        {/* Live Notification Toast */}
        {toastMessage && (
          <div
            className={`p-4 rounded-xl border flex items-center justify-between shadow-sm animate-in fade-in duration-200 ${
              toastMessage.type === "success"
                ? "bg-emerald-50/90 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300"
                : "bg-rose-50/90 dark:bg-rose-950/40 border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-300"
            }`}
          >
            <div className="flex items-center gap-3">
              {toastMessage.type === "success" ? (
                <CheckCircle2 className="h-5 w-5 text-emerald-600 dark:text-emerald-400 shrink-0" />
              ) : (
                <AlertCircle className="h-5 w-5 text-rose-600 dark:text-rose-400 shrink-0" />
              )}
              <span className="text-xs md:text-sm font-medium">{toastMessage.text}</span>
            </div>
            <button
              onClick={() => setToastMessage(null)}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 ml-4"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Filters Bar */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          {/* Search Input */}
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search by title, ID, product..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 h-9 text-xs"
            />
          </div>

          {/* Doc Type Filter */}
          <div>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="w-full h-9 px-3 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs font-medium text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="ALL">All Document Types</option>
              <option value="PRODUCT">Products</option>
              <option value="POLICY">Policies</option>
              <option value="FAQ">FAQs</option>
              <option value="TERMS_AND_CONDITIONS">Terms & Conditions</option>
              <option value="SERVICE_INFORMATION">Service Info</option>
            </select>
          </div>

          {/* Product Type Filter */}
          <div>
            <select
              value={productFilter}
              onChange={(e) => setProductFilter(e.target.value)}
              className="w-full h-9 px-3 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs font-medium text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="ALL">All Product Categories</option>
              <option value="CREDIT_CARD">Credit Cards</option>
              <option value="LOAN">Loans</option>
              <option value="SAVINGS">Savings Accounts</option>
              <option value="INVESTMENT">Investments</option>
              <option value="ACCOUNT">Accounts</option>
              <option value="OTHER">Other</option>
            </select>
          </div>

          {/* Access Scope Filter */}
          <div>
            <select
              value={accessScopeFilter}
              onChange={(e) => setAccessScopeFilter(e.target.value)}
              className="w-full h-9 px-3 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs font-medium text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="ALL">All Access Scopes</option>
              <option value="CUSTOMER">Customer Assistant (CUSTOMER)</option>
              <option value="STAFF">Analytics Copilot (STAFF)</option>
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full h-9 px-3 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs font-medium text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="ACTIVE">Active (In Production)</option>
              <option value="PROCESSING">Indexing / Processing</option>
              <option value="ARCHIVED">Archived (Old Versions)</option>
              <option value="FAILED">Failed Ingestion</option>
            </select>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800/60 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Documents Table */}
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-sm text-slate-500 flex flex-col items-center justify-center gap-3">
              <RefreshCw className="h-6 w-6 animate-spin text-indigo-600" />
              <span>Loading enterprise knowledge documents...</span>
            </div>
          ) : filteredDocs.length === 0 ? (
            <div className="p-12 text-center text-sm text-slate-500 flex flex-col items-center justify-center gap-2">
              <Layers className="h-8 w-8 text-slate-400 mb-1" />
              <p className="font-semibold text-slate-700 dark:text-slate-300">No documents found</p>
              <p className="text-xs text-slate-400">
                {searchQuery || typeFilter !== "ALL" || statusFilter !== "ALL" || accessScopeFilter !== "ALL"
                  ? "Try clearing or adjusting your filters."
                  : "Upload your first product or policy document to index into Vertex AI RAG."}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-950/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 uppercase tracking-wider font-semibold">
                  <tr>
                    <th className="py-3 px-4">Document Title & ID</th>
                    <th className="py-3 px-4">Type / Product</th>
                    <th className="py-3 px-4">Access Control</th>
                    <th className="py-3 px-4">Version</th>
                    <th className="py-3 px-4">Effective Range</th>
                    <th className="py-3 px-4">RAG Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/70">
                  {filteredDocs.map((doc) => {
                    const isActive = doc.status === "ACTIVE" && doc.is_active;
                    const isFailed = doc.status === "FAILED" || doc.ingestion_status === "FAILED";
                    const isProcessing = doc.status === "PROCESSING" || doc.ingestion_status === "INDEXING";
                    const accessList = doc.access_control && doc.access_control.length > 0
                      ? doc.access_control
                      : (doc.audience === "STAFF" ? ["STAFF"] : doc.audience === "CUSTOMER" ? ["CUSTOMER"] : ["CUSTOMER", "STAFF"]);

                    return (
                      <tr
                        key={doc.document_id}
                        className="hover:bg-slate-50/70 dark:hover:bg-slate-800/30 transition-colors"
                      >
                        {/* Title & Logical ID */}
                        <td className="py-3.5 px-4">
                          <div className="flex items-start gap-2.5">
                            <FileText className="h-4 w-4 text-indigo-500 mt-0.5 shrink-0" />
                            <div>
                              <div className="font-semibold text-slate-900 dark:text-white">
                                {doc.document_name}
                              </div>
                              <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                                {doc.logical_document_id} • {doc.original_filename}
                              </div>
                            </div>
                          </div>
                        </td>

                        {/* Type & Product */}
                        <td className="py-3.5 px-4">
                          <div className="flex flex-col gap-1">
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 w-fit">
                              {doc.document_type}
                            </span>
                            {doc.product_name && (
                              <span className="text-[11px] font-medium text-indigo-600 dark:text-indigo-400">
                                {doc.product_name}
                              </span>
                            )}
                          </div>
                        </td>

                        {/* Access Control */}
                        <td className="py-3.5 px-4">
                          <div className="flex flex-wrap gap-1">
                            {accessList.includes("CUSTOMER") && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                                CUSTOMER
                              </span>
                            )}
                            {accessList.includes("STAFF") && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-purple-100 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800">
                                STAFF
                              </span>
                            )}
                          </div>
                        </td>

                        {/* Version */}
                        <td className="py-3.5 px-4 font-mono font-bold text-slate-700 dark:text-slate-300">
                          {doc.version}
                        </td>

                        {/* Effective Range */}
                        <td className="py-3.5 px-4 text-slate-600 dark:text-slate-400">
                          <div className="flex items-center gap-1">
                            <Calendar className="h-3 w-3 text-slate-400" />
                            <span>{doc.effective_from}</span>
                            <span>→</span>
                            <span>{doc.effective_to || "Ongoing"}</span>
                          </div>
                        </td>

                        {/* Status Badge */}
                        <td className="py-3.5 px-4">
                          {isActive && (
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/60">
                              <CheckCircle2 className="h-3 w-3" />
                              ACTIVE
                            </span>
                          )}
                          {isProcessing && (
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800/60">
                              <RefreshCw className="h-3 w-3 animate-spin" />
                              INDEXING
                            </span>
                          )}
                          {isFailed && (
                            <span
                              title={doc.ingestion_error || "Ingestion error"}
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-800/60 cursor-help"
                            >
                              <AlertCircle className="h-3 w-3" />
                              FAILED
                            </span>
                          )}
                          {doc.status === "ARCHIVED" && (
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                              <Archive className="h-3 w-3" />
                              ARCHIVED
                            </span>
                          )}
                        </td>

                        {/* Actions */}
                        <td className="py-3.5 px-4 text-right">
                          <div className="inline-flex items-center gap-1.5">
                            {isFailed && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleRetry(doc.document_id)}
                                className="h-7 px-2 text-[11px] text-amber-600 border-amber-300 hover:bg-amber-50"
                              >
                                Retry
                              </Button>
                            )}

                            {isActive && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleCreateNewVersion(doc)}
                                className="h-7 px-2 text-[11px] text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-950/50"
                                title="Upload new version"
                              >
                                New Version
                              </Button>
                            )}

                            {isActive && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleArchive(doc.document_id)}
                                className="h-7 px-2 text-[11px] text-slate-500 hover:text-rose-600 hover:bg-rose-50"
                                title="Archive version"
                              >
                                Archive
                              </Button>
                            )}

                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleOpenDrawer(doc)}
                              className="h-7 px-2 text-[11px] text-slate-600 hover:text-slate-900 dark:text-slate-300"
                            >
                              <History className="h-3.5 w-3.5 mr-1" />
                              History
                            </Button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Upload Document Modal */}
        {isUploadOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
              {/* Modal Header */}
              <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <UploadCloud className="h-5 w-5 text-indigo-600" />
                  <h3 className="font-bold text-slate-900 dark:text-white">
                    Upload Knowledge Document
                  </h3>
                </div>
                <button
                  onClick={() => setIsUploadOpen(false)}
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Form Body */}
              <form onSubmit={handleUploadSubmit} className="p-6 space-y-4 overflow-y-auto">
                {uploadError && (
                  <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    <span>{uploadError}</span>
                  </div>
                )}
                {uploadSuccess && (
                  <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 shrink-0" />
                    <span>Document uploaded and indexed successfully!</span>
                  </div>
                )}

                {/* File input */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Select File (PDF, DOCX, TXT, MD, max 25MB) *
                  </label>
                  <input
                    type="file"
                    accept=".pdf,.docx,.txt,.md,.html"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    className="block w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 dark:file:bg-indigo-950 dark:file:text-indigo-300 cursor-pointer"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  {/* Logical Document ID */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                      Logical Document ID *
                    </label>
                    <Input
                      placeholder="e.g. platinum-card-terms"
                      value={formLogicalId}
                      onChange={(e) => setFormLogicalId(e.target.value)}
                      required
                      className="h-8 text-xs font-mono"
                    />
                  </div>

                  {/* Version */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                      Version *
                    </label>
                    <Input
                      placeholder="e.g. v1.0.0"
                      value={formVersion}
                      onChange={(e) => setFormVersion(e.target.value)}
                      required
                      className="h-8 text-xs font-mono"
                    />
                  </div>
                </div>

                {/* Document Name */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Document Title *
                  </label>
                  <Input
                    placeholder="e.g. BankPilot Platinum Credit Card Overview & Rewards"
                    value={formDocName}
                    onChange={(e) => setFormDocName(e.target.value)}
                    required
                    className="h-8 text-xs"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  {/* Document Type */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                      Document Type *
                    </label>
                    <select
                      value={formDocType}
                      onChange={(e) => setFormDocType(e.target.value)}
                      className="w-full h-8 px-2 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs text-slate-800 dark:text-slate-200"
                    >
                      <option value="PRODUCT">PRODUCT</option>
                      <option value="POLICY">POLICY</option>
                      <option value="FAQ">FAQ</option>
                      <option value="TERMS_AND_CONDITIONS">TERMS_AND_CONDITIONS</option>
                      <option value="SERVICE_INFORMATION">SERVICE_INFORMATION</option>
                    </select>
                  </div>

                  {/* Product Type (if Product) */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                      Product Category
                    </label>
                    <select
                      value={formProductType}
                      onChange={(e) => setFormProductType(e.target.value)}
                      disabled={formDocType !== "PRODUCT"}
                      className="w-full h-8 px-2 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs text-slate-800 dark:text-slate-200 disabled:opacity-50"
                    >
                      <option value="CREDIT_CARD">Credit Card</option>
                      <option value="LOAN">Loan</option>
                      <option value="SAVINGS">Savings</option>
                      <option value="INVESTMENT">Investment</option>
                      <option value="ACCOUNT">Account</option>
                      <option value="OTHER">Other</option>
                    </select>
                  </div>
                </div>

                {/* Product Name & ID */}
                {formDocType === "PRODUCT" && (
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                        Product Name
                      </label>
                      <Input
                        placeholder="e.g. Platinum Card"
                        value={formProductName}
                        onChange={(e) => setFormProductName(e.target.value)}
                        className="h-8 text-xs"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                        Product ID
                      </label>
                      <Input
                        placeholder="e.g. CARD_PLATINUM_01"
                        value={formProductId}
                        onChange={(e) => setFormProductId(e.target.value)}
                        className="h-8 text-xs font-mono"
                      />
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-3">
                  {/* Effective From */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                      Effective From *
                    </label>
                    <Input
                      type="date"
                      value={formEffectiveFrom}
                      onChange={(e) => setFormEffectiveFrom(e.target.value)}
                      required
                      className="h-8 text-xs"
                    />
                  </div>

                  {/* Effective To */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                      Effective To (Optional)
                    </label>
                    <Input
                      type="date"
                      value={formEffectiveTo}
                      onChange={(e) => setFormEffectiveTo(e.target.value)}
                      className="h-8 text-xs"
                    />
                  </div>
                </div>

                {/* Access Control (Governed Scope) */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Access Control (Target Agents) *
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 p-3 bg-slate-50 dark:bg-slate-950 rounded-lg border border-slate-200 dark:border-slate-800">
                    <label className="flex items-center gap-2.5 cursor-pointer text-xs font-medium text-slate-700 dark:text-slate-300">
                      <input
                        type="checkbox"
                        checked={formAccessControl.includes("CUSTOMER")}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFormAccessControl([...formAccessControl, "CUSTOMER"]);
                          } else {
                            setFormAccessControl(formAccessControl.filter((x) => x !== "CUSTOMER"));
                          }
                        }}
                        className="rounded text-indigo-600 focus:ring-indigo-500 h-4 w-4"
                      />
                      <span>Customer AI Assistant (<span className="font-mono text-[11px] font-bold text-blue-600 dark:text-blue-400">CUSTOMER</span>)</span>
                    </label>

                    <label className="flex items-center gap-2.5 cursor-pointer text-xs font-medium text-slate-700 dark:text-slate-300">
                      <input
                        type="checkbox"
                        checked={formAccessControl.includes("STAFF")}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFormAccessControl([...formAccessControl, "STAFF"]);
                          } else {
                            setFormAccessControl(formAccessControl.filter((x) => x !== "STAFF"));
                          }
                        }}
                        className="rounded text-indigo-600 focus:ring-indigo-500 h-4 w-4"
                      />
                      <span>Analytics Copilot (<span className="font-mono text-[11px] font-bold text-purple-600 dark:text-purple-400">STAFF</span>)</span>
                    </label>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">
                    Select both to share across customer retail assistance and internal staff analytics.
                  </p>
                </div>

                {/* Modal Footer */}
                <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-end gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setIsUploadOpen(false)}
                    disabled={uploading}
                    className="h-9"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={uploading}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white gap-2 h-9"
                  >
                    {uploading ? (
                      <>
                        <RefreshCw className="h-4 w-4 animate-spin" />
                        <span>Uploading to Cloud Storage...</span>
                      </>
                    ) : (
                      <>
                        <UploadCloud className="h-4 w-4" />
                        <span>Upload Document</span>
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Version History & Audit Drawer */}
        {isDrawerOpen && selectedDoc && (
          <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/60 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 w-full max-w-2xl h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
              {/* Drawer Header */}
              <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-slate-900 dark:text-white text-base">
                    {selectedDoc.document_name}
                  </h3>
                  <p className="text-xs text-slate-400 font-mono mt-0.5">
                    {selectedDoc.logical_document_id}
                  </p>
                </div>
                <button
                  onClick={() => setIsDrawerOpen(false)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Drawer Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {loadingDrawer ? (
                  <div className="py-12 text-center text-xs text-slate-500 flex flex-col items-center gap-2">
                    <RefreshCw className="h-5 w-5 animate-spin text-indigo-600" />
                    <span>Loading version history and audit log...</span>
                  </div>
                ) : (
                  <>
                    {/* Version History Section */}
                    <div>
                      <div className="flex items-center gap-2 font-bold text-xs uppercase tracking-wider text-slate-500 mb-3">
                        <Layers className="h-4 w-4" />
                        <span>Version History ({versions.length})</span>
                      </div>

                      <div className="space-y-3">
                        {versions.map((ver) => {
                          const isActive = ver.is_active;
                          const verAccess = ver.access_control && ver.access_control.length > 0
                            ? ver.access_control
                            : (selectedDoc.access_control || ["CUSTOMER", "STAFF"]);
                          return (
                            <div
                              key={ver.document_id}
                              className={`p-4 rounded-xl border transition-all ${
                                isActive
                                  ? "bg-indigo-50/50 dark:bg-indigo-950/20 border-indigo-200 dark:border-indigo-800/80 shadow-sm"
                                  : "bg-slate-50/60 dark:bg-slate-950/40 border-slate-200 dark:border-slate-800"
                              }`}
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <span className="font-mono font-bold text-sm text-slate-900 dark:text-white">
                                    {ver.version}
                                  </span>
                                  {isActive && (
                                    <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                                      CURRENT ACTIVE
                                    </span>
                                  )}
                                  {ver.status === "ARCHIVED" && (
                                    <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-400">
                                      ARCHIVED
                                    </span>
                                  )}
                                  <div className="flex items-center gap-1 ml-1">
                                    {verAccess.includes("CUSTOMER") && (
                                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300">
                                        CUSTOMER
                                      </span>
                                    )}
                                    {verAccess.includes("STAFF") && (
                                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300">
                                        STAFF
                                      </span>
                                    )}
                                  </div>
                                </div>
                                <span className="text-[11px] text-slate-400">
                                  {new Date(ver.uploaded_at).toLocaleDateString()}
                                </span>
                              </div>

                              <div className="mt-2 text-xs text-slate-500 space-y-1">
                                <div>
                                  <span className="font-medium text-slate-700 dark:text-slate-300">
                                    Uploaded By:
                                  </span>{" "}
                                  {ver.uploaded_by}
                                </div>
                                <div>
                                  <span className="font-medium text-slate-700 dark:text-slate-300">
                                    Effective Range:
                                  </span>{" "}
                                  {ver.effective_from} → {ver.effective_to || "Ongoing"}
                                </div>
                                <div className="font-mono text-[10px] truncate text-slate-400">
                                  GCS: {ver.gcs_uri}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Audit Logs Section */}
                    <div>
                      <div className="flex items-center gap-2 font-bold text-xs uppercase tracking-wider text-slate-500 mb-3">
                        <ShieldCheck className="h-4 w-4" />
                        <span>Audit Trail ({auditLogs.length})</span>
                      </div>

                      <div className="space-y-2.5">
                        {auditLogs.map((log) => (
                          <div
                            key={log.audit_id}
                            className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs"
                          >
                            <div className="flex items-center justify-between font-mono">
                              <span className="font-bold text-indigo-600 dark:text-indigo-400">
                                {log.action}
                              </span>
                              <span
                                className={`font-semibold ${
                                  log.result === "SUCCESS"
                                    ? "text-emerald-600"
                                    : "text-rose-600"
                                }`}
                              >
                                {log.result}
                              </span>
                            </div>
                            <div className="text-[11px] text-slate-400 mt-1 flex items-center justify-between">
                              <span>User: {log.user_id}</span>
                              <span>{new Date(log.timestamp).toLocaleString()}</span>
                            </div>
                            {log.details && (
                              <p className="text-slate-600 dark:text-slate-300 text-[11px] mt-1.5 bg-slate-50 dark:bg-slate-950 p-2 rounded">
                                {log.details}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </StaffSidebarLayout>
  );
}

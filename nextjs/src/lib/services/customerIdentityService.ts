
export interface CheckEmailResponse {
  customer_exists: boolean;
  already_registered?: boolean;
  is_staff?: boolean;
  customer_id?: number | null;
}

export interface LinkUserResponse {
  customer_id: number;
  firebase_uid: string;
  registration_completed: boolean;
}

export interface CustomerMeResponse {
  customer_id: number;
  name: string;
  email: string;
  kyc_status: string;
  customer_segment: string;
}

export interface DemoRequest {
  request_id: string;
  name: string;
  email: string;
  company?: string;
  role?: string;
  linkedin?: string;
  purpose?: string;
  status: string; // PENDING, APPROVED, ALLOCATED, REJECTED, EXPIRED
  created_at: string;
  updated_at?: string;
  approved_by?: string;
  remarks?: string;
  customer_id?: string;
  expires_at?: string;
}

export interface DemoSummary {
  pending_requests: number;
  allocated_customers: number;
  available_customers: number;
  expired_today: number;
}

export interface DemoCustomer {
  demo_customer_id: string;
  customer_id: number;
  original_name: string;
  original_email: string;
  demo_name?: string;
  demo_email?: string;
  firebase_uid?: string;
  status: string;
  allocated_at?: string;
  expires_at?: string;
  released_at?: string;
  allocated_by?: string;
  remarks?: string;
}

class CustomerIdentityService {
  private getBaseUrl(): string {
    return process.env.NEXT_PUBLIC_IDENTITY_SERVICE_URL || "http://localhost:8001";
  }

  /**
   * Check if a customer email exists in the bank's pre-authorized database
   * and if they are already registered with Firebase.
   */
  async checkEmail(email: string): Promise<CheckEmailResponse> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/registration/check-email`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to check email with identity service.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in checkEmail:", error);
      throw error;
    }
  }

  /**
   * Links a verified Firebase user to their pre-authorized bank customer mapping.
   * Creates necessary BigQuery authorized views.
   */
  async linkUser(idToken: string): Promise<LinkUserResponse> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/registration/link-user`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to link Firebase account with bank customer.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in linkUser:", error);
      throw error;
    }
  }

  /**
   * Links a verified Firebase user to their pre-authorized bank staff mapping in BigQuery.
   */
  async linkStaff(idToken: string): Promise<{ email: string; firebase_uid: string; registration_completed: boolean }> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/registration/link-staff`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to link Firebase account with bank staff.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in linkStaff:", error);
      throw error;
    }
  }

  /**
   * Retrieves the current authenticated customer's profile context.
   */
  async getMe(idToken: string): Promise<CustomerMeResponse> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/auth/me`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to fetch customer profile context.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in getMe:", error);
      throw error;
    }
  }

  /**
   * Submit a new demo request (Public endpoint)
   */
  async submitDemoRequest(payload: {
    name: string;
    email: string;
    company?: string;
    role?: string;
    linkedin?: string;
    purpose?: string;
  }): Promise<DemoRequest> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/demo/request`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to submit demo request.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in submitDemoRequest:", error);
      throw error;
    }
  }

  /**
   * Get all demo requests (Admin/Staff only)
   */
  async getDemoRequests(idToken: string): Promise<DemoRequest[]> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/demo/requests`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to retrieve demo requests.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in getDemoRequests:", error);
      throw error;
    }
  }

  /**
   * Get a single demo request details (Admin/Staff only)
   */
  async getDemoRequestDetails(idToken: string, requestId: string): Promise<DemoRequest> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/demo/requests/${requestId}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to retrieve demo request details.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in getDemoRequestDetails:", error);
      throw error;
    }
  }

  /**
   * Get dashboard summary cards data (Admin/Staff only)
   */
  async getDemoSummary(idToken: string): Promise<DemoSummary> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/demo/summary`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to fetch dashboard summary metrics.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in getDemoSummary:", error);
      throw error;
    }
  }

  /**
   * Approve a demo request (Admin/Staff only)
   */
  async approveDemoRequest(idToken: string, requestId: string): Promise<{ customer_id: number; expires_at: string; status: string; message?: string }> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/demo/approve/${requestId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to approve demo request.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in approveDemoRequest:", error);
      throw error;
    }
  }

  /**
   * Reject a demo request (Admin/Staff only)
   */
  async rejectDemoRequest(idToken: string, requestId: string, remarks?: string): Promise<{ status: string; message: string }> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/demo/reject/${requestId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify({ remarks }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to reject demo request.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in rejectDemoRequest:", error);
      throw error;
    }
  }

  /**
   * Get all demo customers (Admin/Staff only)
   */
  async getDemoCustomers(idToken: string): Promise<DemoCustomer[]> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/demo/customers`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to fetch demo customer pool.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in getDemoCustomers:", error);
      throw error;
    }
  }

  /**
   * Release a demo customer allocation (Admin/Staff only)
   */
  /**
   * Release a demo customer allocation (Admin/Staff only)
   */
  async releaseDemoCustomer(idToken: string, customerId: string): Promise<{ customer_id: number; status: string; released_at: string; deleted_views_count: number }> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/demo/release/${customerId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to release demo customer.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in releaseDemoCustomer:", error);
      throw error;
    }
  }

  /**
   * List Knowledge Documents with optional filters (Staff only)
   */
  async getKnowledgeDocuments(
    idToken: string,
    filters?: {
      document_type?: string;
      product_type?: string;
      status?: string;
      is_active?: boolean;
      access_scope?: string;
    }
  ): Promise<{ documents: KnowledgeDocument[]; total: number }> {
    try {
      const params = new URLSearchParams();
      if (filters?.document_type) params.append("document_type", filters.document_type);
      if (filters?.product_type) params.append("product_type", filters.product_type);
      if (filters?.status) params.append("status", filters.status);
      if (filters?.is_active !== undefined) params.append("is_active", String(filters.is_active));
      if (filters?.access_scope) params.append("access_scope", filters.access_scope);

      const url = `${this.getBaseUrl()}/api/v1/knowledge/documents${params.toString() ? `?${params.toString()}` : ""}`;
      const response = await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to fetch knowledge documents.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in getKnowledgeDocuments:", error);
      throw error;
    }
  }

  /**
   * Get Single Knowledge Document details (Staff only)
   */
  async getKnowledgeDocument(idToken: string, documentId: string): Promise<KnowledgeDocument> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/knowledge/documents/${documentId}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to fetch document details.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in getKnowledgeDocument:", error);
      throw error;
    }
  }

  /**
   * Get Version History for a Document (Staff only)
   */
  async getKnowledgeDocumentVersions(idToken: string, documentId: string): Promise<KnowledgeVersion[]> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/knowledge/documents/${documentId}/versions`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to fetch version history.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in getKnowledgeDocumentVersions:", error);
      throw error;
    }
  }

  /**
   * Get Audit Logs for a Document (Staff only)
   */
  async getKnowledgeDocumentAuditLogs(idToken: string, documentId: string): Promise<KnowledgeAuditLog[]> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/knowledge/documents/${documentId}/audit-logs`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to fetch document audit logs.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in getKnowledgeDocumentAuditLogs:", error);
      throw error;
    }
  }

  /**
   * Upload a new Knowledge Document or new Version (Staff only)
   */
  async uploadKnowledgeDocument(idToken: string, formData: FormData): Promise<KnowledgeDocument> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/knowledge/documents`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${idToken}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to upload knowledge document.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in uploadKnowledgeDocument:", error);
      throw error;
    }
  }

  /**
   * Retry failed RAG indexing for a document (Staff only)
   */
  async retryKnowledgeDocument(idToken: string, documentId: string): Promise<KnowledgeDocument> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/knowledge/documents/${documentId}/retry`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to retry document indexing.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in retryKnowledgeDocument:", error);
      throw error;
    }
  }

  /**
   * Manually archive a document version (Staff only)
   */
  async archiveKnowledgeDocument(idToken: string, documentId: string): Promise<KnowledgeDocument> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/knowledge/documents/${documentId}/archive`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to archive document.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in archiveKnowledgeDocument:", error);
      throw error;
    }
  }
}

export interface KnowledgeDocument {
  document_id: string;
  logical_document_id: string;
  document_name: string;
  original_filename: string;
  document_type: "PRODUCT" | "POLICY" | "FAQ" | "TERMS_AND_CONDITIONS" | "SERVICE_INFORMATION";
  product_type?: "CREDIT_CARD" | "LOAN" | "SAVINGS" | "INVESTMENT" | "ACCOUNT" | "OTHER";
  product_id?: string;
  product_name?: string;
  version: string;
  status: "DRAFT" | "PROCESSING" | "ACTIVE" | "ARCHIVED" | "FAILED";
  effective_from: string;
  effective_to?: string;
  region: string;
  audience?: string;
  access_control: string[];
  gcs_uri: string;
  rag_file_id?: string;
  rag_corpus_name?: string;
  uploaded_by: string;
  uploaded_at: string;
  updated_at: string;
  ingestion_status: "PENDING" | "UPLOADING" | "INDEXING" | "COMPLETED" | "FAILED";
  ingestion_error?: string;
  is_active: boolean;
}

export interface KnowledgeVersion {
  document_id: string;
  logical_document_id: string;
  version: string;
  document_name: string;
  status: string;
  ingestion_status: string;
  is_active: boolean;
  uploaded_by: string;
  uploaded_at: string;
  effective_from: string;
  effective_to?: string;
  access_control?: string[];
  gcs_uri: string;
}

export interface KnowledgeAuditLog {
  audit_id: string;
  document_id: string;
  logical_document_id: string;
  version: string;
  action: string;
  result: string;
  user_id: string;
  timestamp: string;
  details?: string;
}

export const customerIdentityService = new CustomerIdentityService();

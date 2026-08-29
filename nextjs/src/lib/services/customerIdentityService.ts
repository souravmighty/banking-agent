
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
}

export const customerIdentityService = new CustomerIdentityService();

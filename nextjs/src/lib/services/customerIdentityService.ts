
export interface CheckEmailResponse {
  customer_exists: boolean;
  already_registered?: boolean;
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

class CustomerIdentityService {
  private getBaseUrl() {
    return process.env.NEXT_PUBLIC_IDENTITY_SERVICE_URL || "http://localhost:8080";
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
}

export const customerIdentityService = new CustomerIdentityService();

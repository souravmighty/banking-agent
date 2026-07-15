export interface CustomerProfile {
  customer_id: number;
  name: string;
  email: string;
  segment: string;
  kyc_status: string;
  risk_profile: string;
}

export interface FinancialSummary {
  total_balance: number;
  monthly_spend: number;
  credit_score: number;
}

export interface AccountDetail {
  account_number: string;
  account_type: string;
  account_status: string;
  balance: number;
  currency: string;
  ifsc_code: string;
  branch_name: string;
  created_at: string;
}

export interface CardDetail {
  card_account_number: string;
  card_number: string;
  card_type: string;
  credit_limit: number;
  available_credit: number;
  outstanding_balance: number;
  statement_amount: number;
  minimum_due_amount: number;
  payment_due_date: string;
  statement_date: string;
}

export interface LoanDetail {
  loan_account_number: string;
  loan_type: string;
  loan_amount: number;
  outstanding_amount: number;
  interest_rate: number;
  emi_amount: number;
  remaining_tenure_months: number;
  original_tenure_months: number;
}

export interface InvestmentDetail {
  fd_account_number: string;
  principal_amount: number;
  current_value: number;
  interest_rate: number;
  start_date: string;
  maturity_date: string;
  tenure_months: number;
  status: string;
}

export interface TransactionDetail {
  transaction_id: string;
  reference_id: string;
  account_number: string;
  counterparty_account_number?: string;
  transaction_type: string;
  currency: string;
  direction: "DEBIT" | "CREDIT";
  amount: number;
  merchant_name?: string;
  category?: string;
  description: string;
  transaction_timestamp: string;
}

export interface BeneficiaryDetail {
  beneficiary_id?: number;
  beneficiary_name: string;
  beneficiary_account_number: string;
  bank_name: string;
  ifsc_code: string;
  status: string;
}

export interface DashboardResponse {
  customer: CustomerProfile;
  summary: FinancialSummary;
  accounts: AccountDetail[];
  cards: CardDetail[];
  loans: LoanDetail[];
  investments: InvestmentDetail[];
  recent_transactions: TransactionDetail[];
  beneficiaries: BeneficiaryDetail[];
}

class CustomerDataService {
  private getBaseUrl() {
    return process.env.NEXT_PUBLIC_CUSTOMER_DATA_SERVICE_URL || "http://localhost:8081";
  }

  /**
   * Fetches the aggregated dashboard details.
   */
  async getDashboard(idToken: string): Promise<DashboardResponse> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/dashboard`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to retrieve customer dashboard data.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in getDashboard:", error);
      throw error;
    }
  }

  /**
   * Fetches the granular customer accounts list.
   */
  async getAccounts(idToken: string): Promise<AccountDetail[]> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/accounts`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to retrieve accounts.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in getAccounts:", error);
      throw error;
    }
  }

  /**
   * Fetches the credit cards list.
   */
  async getCards(idToken: string): Promise<CardDetail[]> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/cards`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to retrieve credit cards.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in getCards:", error);
      throw error;
    }
  }

  /**
   * Fetches the active loans list.
   */
  async getLoans(idToken: string): Promise<LoanDetail[]> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/loans`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to retrieve loans.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in getLoans:", error);
      throw error;
    }
  }

  /**
   * Fetches the investments (fixed deposits) list.
   */
  async getInvestments(idToken: string): Promise<InvestmentDetail[]> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/investments`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to retrieve investments.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in getInvestments:", error);
      throw error;
    }
  }

  /**
   * Fetches the complete transaction log list.
   */
  async getTransactions(idToken: string): Promise<TransactionDetail[]> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v1/transactions`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to retrieve transactions.");
      }

      return await response.json();
    } catch (error) {
      console.error("Error in getTransactions:", error);
      throw error;
    }
  }
}

export const customerDataService = new CustomerDataService();

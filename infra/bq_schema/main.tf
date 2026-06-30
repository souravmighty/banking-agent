terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  credentials = file(var.credentials)
  project     = var.project_id
  region      = var.region
}


# Create BigQuery dataset
resource "google_bigquery_dataset" "banking_dataset" {
  dataset_id                 = var.dataset_id
  friendly_name              = "Banking Data"
  description                = "Dataset for banking customer, account, and transaction data"
  location                   = var.location
  delete_contents_on_destroy = true
}

# Customers table (SCD Type 2)
resource "google_bigquery_table" "customers" {
  dataset_id          = google_bigquery_dataset.banking_dataset.dataset_id
  table_id            = "customers"
  deletion_protection = false

  description = "Business Purpose: Stores customer master records and customer profile information. Contains customer demographics, segmentation, KYC information, risk profile, and customer lifecycle status.\nPrimary Business Key: customer_id\nRelationship Information: One customer can own multiple accounts, loans, fixed deposits, credit cards, and beneficiaries.\nTypical Usage Examples: Filter by customer_id or email to retrieve demographic or segment data for personalization or marketing analytics.\nSCD Type 2 Status: This table is a Slowly Changing Dimension Type 2 (SCD Type 2) table. Historical customer changes are preserved.\nSCD Column Explanations:\n- eff_start_ts: Timestamp when this version became effective.\n- eff_end_ts: Timestamp when this version expired. NULL indicates current version.\n- is_current: Indicates whether record is the current active version.\n- record_version: Version number of the customer record.\nAI Usage Guidance: Use is_current = TRUE unless historical analysis is requested.\nTypical AI Questions:\n- What segment does the customer belong to?\n- What is the customer's risk profile?\n- Is the customer active?\n- Has the customer recently upgraded to Premium?"

  schema = jsonencode([
    {
      name        = "customer_id"
      type        = "INTEGER"
      mode        = "REQUIRED"
      description = "Business meaning: Unique 16-digit customer identifier. Primary key for customer entities. Relationship information: Joined with accounts, credit_cards, loans, fixed_deposits, credit_scores, beneficiaries, and identity mapping tables. Nullability: Never null."
    },
    {
      name        = "name"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Full legal name of the customer. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "email"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Primary email address used for contact and identity matching. Relationship information: Matches email_id in customer_identity_mapping. Nullability: Never null."
    },
    {
      name        = "phone"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Mobile phone number. Contact method for alerts and verification. Relationship information: None. Nullability: Nullable if not provided."
    },
    {
      name        = "address"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Current residential address. Physical location for mailing or KYC. Relationship information: None. Nullability: Nullable."
    },
    {
      name        = "customer_status"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Operational status of the customer. Allowed values: ACTIVE, DORMANT, BLOCKED, CLOSED. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "customer_segment"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Customer tier used for targeted marketing and personalization. Allowed values: RETAIL, PREMIUM, WEALTH, STUDENT, SENIOR_CITIZEN. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "risk_profile"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Internal credit and compliance risk rating. Allowed values: LOW, MEDIUM, HIGH. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "kyc_status"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Know Your Customer identity verification status. Allowed values: VERIFIED, PENDING, REJECTED. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "created_at"
      type        = "DATE"
      mode        = "REQUIRED"
      description = "Business meaning: Original date when the customer was onboarded. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "eff_start_ts"
      type        = "TIMESTAMP"
      mode        = "REQUIRED"
      description = "Business meaning: SCD Type 2 Effective Start Timestamp. When this version of the customer record became active. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "eff_end_ts"
      type        = "TIMESTAMP"
      mode        = "NULLABLE"
      description = "Business meaning: SCD Type 2 Effective End Timestamp. When this version stopped being effective. NULL means currently active. Relationship information: None. Nullability: Nullable."
    },
    {
      name        = "is_current"
      type        = "BOOLEAN"
      mode        = "REQUIRED"
      description = "Business meaning: SCD Type 2 Flag indicating if this is the latest active version. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "record_version"
      type        = "INTEGER"
      mode        = "REQUIRED"
      description = "Business meaning: Incremental version number for this customer business key. Relationship information: None. Nullability: Never null."
    }
  ])
}

# Customer Identity Mapping table
resource "google_bigquery_table" "customer_identity_mapping" {
  dataset_id          = google_bigquery_dataset.banking_dataset.dataset_id
  table_id            = "customer_identity_mapping"
  deletion_protection = false

  description = "Business Purpose: Maps authenticated Firebase users to banking customers. Used for authentication, authorization, and digital onboarding tracking.\nPrimary Business Key: customer_id\nRelationship Information: Links firebase_uid to customer_id. Foreign key reference to customers.customer_id.\nTypical Usage Examples: Retrieve customer_id for a given Firebase UID during user authentication or context loading.\nSCD Type 2 Status: Not an SCD Type 2 table.\nAI Usage Guidance: Used by Customer Identity Service, Google ADK, and MCP Transaction Service for identity resolution. Do not treat as historical."

  schema = jsonencode([
    {
      name        = "customer_id"
      type        = "INTEGER"
      mode        = "REQUIRED"
      description = "Business meaning: Unique internal customer identifier. Relationship information: Foreign key referencing customers.customer_id. Nullability: Never null."
    },
    {
      name        = "email_id"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Digital identity email address. Relationship information: Corresponds to customers.email. Nullability: Never null."
    },
    {
      name        = "firebase_uid"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Unique identifier provided by Firebase Auth. Relationship information: Identifies authenticated user. Nullability: Nullable if customer is NOT_REGISTERED."
    },
    {
      name        = "registration_status"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Stage in digital onboarding. Allowed values: NOT_REGISTERED, REGISTERED. Relationship information: None. Nullability: Nullable."
    },
    {
      name        = "linked_at"
      type        = "TIMESTAMP"
      mode        = "NULLABLE"
      description = "Business meaning: Point-in-time when the digital identity was linked to customer record. Relationship information: None. Nullability: Nullable for unregistered customers."
    }
  ])
}

# Accounts table (SCD Type 2)
resource "google_bigquery_table" "accounts" {
  dataset_id          = google_bigquery_dataset.banking_dataset.dataset_id
  table_id            = "accounts"
  deletion_protection = false

  description = "Business Purpose: Stores customer bank account information, including balances, account type, branch routing, and account lifecycle status.\nPrimary Business Key: account_number\nRelationship Information: Many accounts belong to one customer (customer_id). Join key for transactions, loans, and beneficiaries.\nTypical Usage Examples: Query to find available balance, branch, or types of accounts owned by a customer.\nSCD Type 2 Status: This table is a Slowly Changing Dimension Type 2 (SCD Type 2) table. Historical account changes (status, branch, tier) are preserved.\nSCD Column Explanations:\n- eff_start_ts: Timestamp when this version became effective.\n- eff_end_ts: Timestamp when this version expired. NULL indicates current version.\n- is_current: Indicates whether record is the current active version.\n- record_version: Version number of the account configuration.\nAI Usage Guidance: Use is_current = TRUE unless historical analysis is requested. Check balance before allowing debits.\nTypical AI Questions:\n- What is my balance?\n- How many accounts do I have?\n- Which account is active?"

  schema = jsonencode([
    {
      name        = "account_number"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Unique business key for the bank account. Primary identifier exposed to users. Relationship information: Joined with transactions.account_number and beneficiaries.beneficiary_account_number. Nullability: Never null."
    },
    {
      name        = "customer_id"
      type        = "INTEGER"
      mode        = "REQUIRED"
      description = "Business meaning: Internal identifier of the account owner. Relationship information: Foreign key to customers.customer_id. Nullability: Never null."
    },
    {
      name        = "account_type"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Type of deposit account. Allowed values: SAVINGS, CURRENT, SALARY. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "account_status"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Lifecycle state of the account. Allowed values: ACTIVE, DORMANT, FROZEN, CLOSED. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "balance"
      type        = "FLOAT"
      mode        = "REQUIRED"
      description = "Business meaning: Current available funds or balance. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "currency"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Base currency code of the account. Allowed values: INR, USD, EUR. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "ifsc_code"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Indian Financial System Code for branch routing. Relationship information: Identifies the branch in beneficiaries. Nullability: Never null."
    },
    {
      name        = "branch_name"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Name of the bank branch where the account is held. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "created_at"
      type        = "DATE"
      mode        = "REQUIRED"
      description = "Business meaning: Date when the account was initially opened. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "eff_start_ts"
      type        = "TIMESTAMP"
      mode        = "REQUIRED"
      description = "Business meaning: SCD Type 2 Effective Start Timestamp. When this account configuration version became active. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "eff_end_ts"
      type        = "TIMESTAMP"
      mode        = "NULLABLE"
      description = "Business meaning: SCD Type 2 Effective End Timestamp. When this account configuration version expired. NULL for active version. Relationship information: None. Nullability: Nullable."
    },
    {
      name        = "is_current"
      type        = "BOOLEAN"
      mode        = "REQUIRED"
      description = "Business meaning: SCD Type 2 Flag indicating if this is the current active configuration of the account. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "record_version"
      type        = "INTEGER"
      mode        = "REQUIRED"
      description = "Business meaning: Incremental version number of the account configuration. Relationship information: None. Nullability: Never null."
    }
  ])
}

# Beneficiaries table
resource "google_bigquery_table" "beneficiaries" {
  dataset_id          = google_bigquery_dataset.banking_dataset.dataset_id
  table_id            = "beneficiaries"
  deletion_protection = false

  description = "Business Purpose: Stores transfer beneficiaries configured by customers. Used in money transfer workflows, MCP transaction tools, and beneficiary management.\nPrimary Business Key: beneficiary_id\nRelationship Information: Many beneficiaries belong to one customer (customer_id). Link to payee's bank account.\nTypical Usage Examples: Fetch a list of verified payees for a customer before a fund transfer.\nSCD Type 2 Status: Not an SCD Type 2 table.\nAI Usage Guidance: Query to retrieve beneficiary accounts or verify payee names during transfer workflows.\nTypical AI Questions:\n- Show my beneficiaries\n- Transfer money to Raj"

  schema = jsonencode([
    {
      name        = "beneficiary_id"
      type        = "INTEGER"
      mode        = "REQUIRED"
      description = "Business meaning: Unique internal identifier for the saved contact. Relationship information: Primary key. Nullability: Never null."
    },
    {
      name        = "customer_id"
      type        = "INTEGER"
      mode        = "REQUIRED"
      description = "Business meaning: Identifier of the customer who saved this beneficiary. Relationship information: Foreign key to customers.customer_id. Nullability: Never null."
    },
    {
      name        = "beneficiary_name"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Nickname or full name of the payee. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "beneficiary_account_number"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Bank account number of the payee. Relationship information: Target account in transfer transactions. Nullability: Never null."
    },
    {
      name        = "bank_name"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Name of the payee's bank. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "ifsc_code"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Branch routing code for the payee bank. Relationship information: Route code for payments. Nullability: Never null."
    },
    {
      name        = "status"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Safety or activation status of the beneficiary. Allowed values: ACTIVE, BLOCKED. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "created_at"
      type        = "TIMESTAMP"
      mode        = "REQUIRED"
      description = "Business meaning: Point-in-time when contact was added. Relationship information: None. Nullability: Never null."
    }
  ])
}

# Transactions table
resource "google_bigquery_table" "transactions" {
  dataset_id          = google_bigquery_dataset.banking_dataset.dataset_id
  table_id            = "transactions"
  deletion_protection = false

  description = "Business Purpose: Stores account-level transaction history. Tracks fund movements (inflows and outflows) for balance updates, spend analysis, and fraud prevention.\nPrimary Business Key: transaction_id\nRelationship Information: Many transactions belong to one account (account_number). Related transactions share a reference_id. For money transfers, a dual-entry debit and credit pair is generated, sharing the same reference_id.\nTypical Usage Examples: Calculate total monthly spend by category, or retrieve the recent ledger entries for an account.\nSCD Type 2 Status: Not an SCD Type 2 table.\nAI Usage Guidance: Always filter or sum transactions using the 'direction' and 'amount' fields. Use reference_id to group transfer pairs.\nTypical AI Questions:\n- Show recent transactions\n- What are my biggest expenses?\n- How much did I spend on food?"

  schema = jsonencode([
    {
      name        = "transaction_id"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Unique transaction identifier. Relationship information: Primary key. Nullability: Never null."
    },
    {
      name        = "reference_id"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Logical transaction reference linking debit/credit entries for transfers. Relationship information: Shared across transfer leg records. Nullability: Never null."
    },
    {
      name        = "account_number"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: The bank account on which this entry is recorded. This can include account numbers of different account types such as credit card, savings/current account, loans, or fixed deposits. Relationship information: Foreign key to accounts.account_number, credit_cards.card_account_number, fixed_deposits.fd_account_number, loans.loan_account_number. Nullability: Never null."
    },
    {
      name        = "counterparty_account_number"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: The other party's bank account in transfers. Relationship information: Target or source account. Nullability: Null for non-transfer transactions."
    },
    {
      name        = "transaction_type"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Financial category of the transaction. Allowed values: TRANSFER, UPI, CARD_PAYMENT, ATM_WITHDRAWAL, ATM_DEPOSIT, SALARY_CREDIT, INTEREST_CREDIT, LOAN_EMI, FD_DEPOSIT, FD_MATURITY, BILL_PAYMENT. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "currency"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Base currency of the transaction. Allowed values: INR, USD, EUR. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "direction"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Balance change direction (inflow vs. outflow). Allowed values: DEBIT (outflow), CREDIT (inflow). Relationship information: None. Nullability: Never null."
    },
    {
      name        = "amount"
      type        = "FLOAT"
      mode        = "REQUIRED"
      description = "Business meaning: Absolute value of the transaction. Always positive. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "merchant_name"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Commercial name of the retailer or receiver. Relationship information: None. Nullability: Null for bank transfers or interest credits."
    },
    {
      name        = "category"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: High-level classification of merchant or purpose for spending analysis. Allowed values: GROCERY, FOOD, TRAVEL, SHOPPING, ENTERTAINMENT, UTILITIES, HEALTHCARE, EDUCATION, BANKING, SALARY, INVESTMENT, LOAN, OTHER. Relationship information: None. Nullability: Nullable."
    },
    {
      name        = "description"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Detailed transaction narration/memo. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "transaction_timestamp"
      type        = "TIMESTAMP"
      mode        = "REQUIRED"
      description = "Business meaning: Point-in-time when transaction occurred. Relationship information: None. Nullability: Never null."
    }
  ])

  time_partitioning {
    type  = "DAY"
    field = "transaction_timestamp"
  }

  clustering = ["transaction_type", "direction"]
}

# Credit Cards table (SCD Type 2)
resource "google_bigquery_table" "credit_cards" {
  dataset_id          = google_bigquery_dataset.banking_dataset.dataset_id
  table_id            = "credit_cards"
  deletion_protection = false

  description = "Business Purpose: Stores customer credit card profiles, credit limits, and detailed billing metrics (outstanding balance, statements, utilization).\nPrimary Business Key: card_account_number\nRelationship Information: Many credit cards belong to one customer (customer_id).\nTypical Usage Examples: Get outstanding balances, utilization stats, or payment due dates.\nSCD Type 2 Status: This table is a Slowly Changing Dimension Type 2 (SCD Type 2) table. Historical card changes (credit limit updates, status changes) are preserved.\nSCD Column Explanations:\n- eff_start_ts: Timestamp when this version became effective.\n- eff_end_ts: Timestamp when this version expired. NULL indicates current version.\n- is_current: Indicates whether record is the current active version.\n- record_version: Version number of the card record.\nAI Usage Guidance: Use is_current = TRUE unless historical analysis is requested. Helpful for calculating credit utilization.\nTypical AI Questions:\n- What is my current outstanding balance?\n- What is my minimum due amount?\n- What is my credit utilization?"

  schema = jsonencode([
    {
      name        = "card_account_number"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Unique credit card account business key. Relationship information: Primary key. Nullability: Never null."
    },
    {
      name        = "customer_id"
      type        = "INTEGER"
      mode        = "REQUIRED"
      description = "Business meaning: Customer ID of the credit card holder. Relationship information: Foreign key referencing customers.customer_id. Nullability: Never null."
    },
    {
      name        = "card_number"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Masked/full card identification number. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "card_type"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Card processing network and tier. Allowed values: VISA, MASTERCARD, RUPAY. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "credit_limit"
      type        = "FLOAT"
      mode        = "REQUIRED"
      description = "Business meaning: Maximum credit limit approved on the card. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "available_credit"
      type        = "FLOAT"
      mode        = "REQUIRED"
      description = "Business meaning: Remaining spending power on the card. Relationship information: Calculated as credit_limit - outstanding_balance. Nullability: Never null."
    },
    {
      name        = "outstanding_balance"
      type        = "FLOAT"
      mode        = "REQUIRED"
      description = "Business meaning: Total unpaid statement and unbilled balances. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "statement_amount"
      type        = "FLOAT"
      mode        = "REQUIRED"
      description = "Business meaning: Total due balance from the last billing cycle. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "minimum_due_amount"
      type        = "FLOAT"
      mode        = "REQUIRED"
      description = "Business meaning: Minimum required payment to avoid late penalties. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "payment_due_date"
      type        = "DATE"
      mode        = "REQUIRED"
      description = "Business meaning: Deadline for paying the minimum or full statement amount. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "statement_date"
      type        = "DATE"
      mode        = "REQUIRED"
      description = "Business meaning: Date when the monthly billing statement was compiled. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "utilization_percentage"
      type        = "FLOAT"
      mode        = "REQUIRED"
      description = "Business meaning: Card credit utilization ratio. Relationship information: Calculated as (outstanding_balance / credit_limit) * 100. Nullability: Never null."
    },
    {
      name        = "status"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Activation state of the credit card. Allowed values: ACTIVE, BLOCKED, CLOSED. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "created_at"
      type        = "DATE"
      mode        = "REQUIRED"
      description = "Business meaning: Date when the credit card was issued. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "eff_start_ts"
      type        = "TIMESTAMP"
      mode        = "REQUIRED"
      description = "Business meaning: SCD Type 2 Effective Start Timestamp. When this card record version became effective. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "eff_end_ts"
      type        = "TIMESTAMP"
      mode        = "NULLABLE"
      description = "Business meaning: SCD Type 2 Effective End Timestamp. When this card record version expired. NULL means current active version. Relationship information: None. Nullability: Nullable."
    },
    {
      name        = "is_current"
      type        = "BOOLEAN"
      mode        = "REQUIRED"
      description = "Business meaning: SCD Type 2 Flag indicating if this is the current active profile. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "record_version"
      type        = "INTEGER"
      mode        = "REQUIRED"
      description = "Business meaning: Incremental version count for this credit card configuration. Relationship information: None. Nullability: Never null."
    }
  ])
}

# Loans table
resource "google_bigquery_table" "loans" {
  dataset_id          = google_bigquery_dataset.banking_dataset.dataset_id
  table_id            = "loans"
  deletion_protection = false

  description = "Business Purpose: Stores customer loan accounts and detailed repayment metrics (principal, outstanding amounts, EMIs, tenure, interest rate).\nPrimary Business Key: loan_account_number\nRelationship Information: Many loans belong to one customer (customer_id).\nTypical Usage Examples: Retrieve active loan tenure, next EMI dates, or outstanding balances.\nSCD Type 2 Status: Not an SCD Type 2 table.\nAI Usage Guidance: Query to answer active loan repayments or remaining debt queries.\nTypical AI Questions:\n- What is my next EMI amount?\n- How much loan balance remains?"

  schema = jsonencode([
    {
      name        = "loan_account_number"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Unique loan account business key. Relationship information: Primary key. Nullability: Never null."
    },
    {
      name        = "customer_id"
      type        = "INTEGER"
      mode        = "REQUIRED"
      description = "Business meaning: Customer ID of the borrower. Relationship information: Foreign key referencing customers.customer_id. Nullability: Never null."
    },
    {
      name        = "loan_type"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Classification of the loan product. Allowed values: PERSONAL, HOME, AUTO, EDUCATION. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "loan_amount"
      type        = "FLOAT"
      mode        = "REQUIRED"
      description = "Business meaning: Total sanctioned principal loan amount. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "outstanding_amount"
      type        = "FLOAT"
      mode        = "REQUIRED"
      description = "Business meaning: Current unpaid loan amount including accrued interest. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "interest_rate"
      type        = "FLOAT"
      mode        = "REQUIRED"
      description = "Business meaning: Annual percentage rate (APR) of interest on the loan. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "emi_amount"
      type        = "FLOAT"
      mode        = "REQUIRED"
      description = "Business meaning: Equated Monthly Installment to be repaid. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "remaining_tenure_months"
      type        = "INTEGER"
      mode        = "REQUIRED"
      description = "Business meaning: Number of months/repayments left. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "original_tenure_months"
      type        = "INTEGER"
      mode        = "REQUIRED"
      description = "Business meaning: Total scheduled tenure of the loan in months. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "next_emi_date"
      type        = "DATE"
      mode        = "REQUIRED"
      description = "Business meaning: Date of the next scheduled EMI payment. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "status"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Current status of the loan account. Allowed values: ACTIVE, CLOSED. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "start_date"
      type        = "DATE"
      mode        = "REQUIRED"
      description = "Business meaning: Date when the loan was disbursed. Relationship information: None. Nullability: Never null."
    }
  ])
}

# Fixed Deposits table
resource "google_bigquery_table" "fixed_deposits" {
  dataset_id          = google_bigquery_dataset.banking_dataset.dataset_id
  table_id            = "fixed_deposits"
  deletion_protection = false

  description = "Business Purpose: Stores fixed deposit (FD) accounts, principal investments, interest rates, and maturity details.\nPrimary Business Key: fd_account_number\nRelationship Information: Many fixed deposits belong to one customer (customer_id).\nTypical Usage Examples: Check investment value, maturity dates, or yield rates on deposits.\nSCD Type 2 Status: Not an SCD Type 2 table.\nAI Usage Guidance: Query to retrieve current investment details or interest rates.\nTypical AI Questions:\n- What is my FD value?\n- When will my FD mature?"

  schema = jsonencode([
    {
      name        = "fd_account_number"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Unique FD account business key. Relationship information: Primary key. Nullability: Never null."
    },
    {
      name        = "customer_id"
      type        = "INTEGER"
      mode        = "REQUIRED"
      description = "Business meaning: Internal customer ID of the depositor. Relationship information: Foreign key to customers.customer_id. Nullability: Never null."
    },
    {
      name        = "principal_amount"
      type        = "FLOAT"
      mode        = "REQUIRED"
      description = "Business meaning: Initial principal amount deposited. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "current_value"
      type        = "FLOAT"
      mode        = "REQUIRED"
      description = "Business meaning: Current value of the FD including accrued compound interest. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "interest_rate"
      type        = "FLOAT"
      mode        = "REQUIRED"
      description = "Business meaning: Annual interest rate agreed at inception. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "start_date"
      type        = "DATE"
      mode        = "REQUIRED"
      description = "Business meaning: Creation date of the fixed deposit. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "maturity_date"
      type        = "DATE"
      mode        = "REQUIRED"
      description = "Business meaning: Date when the FD matures and funds are released. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "tenure_months"
      type        = "INTEGER"
      mode        = "REQUIRED"
      description = "Business meaning: Total length of the deposit term in months. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "status"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Current status of the deposit. Allowed values: ACTIVE, MATURED. Relationship information: None. Nullability: Never null."
    }
  ])
}

# Credit Scores table
resource "google_bigquery_table" "credit_scores" {
  dataset_id          = google_bigquery_dataset.banking_dataset.dataset_id
  table_id            = "credit_scores"
  deletion_protection = false

  description = "Business Purpose: Stores customer credit scores and bureau origin details.\nPrimary Business Key: customer_id\nRelationship Information: Links directly to customers (customer_id).\nTypical Usage Examples: Get customer's credit score to determine loan or card eligibility.\nSCD Type 2 Status: Not an SCD Type 2 table.\nAI Usage Guidance: Retrieve to check overall creditworthiness. Range is 300 to 850.\nTypical AI Questions:\n- What is my credit score?\n- Which bureau provided the score?"

  schema = jsonencode([
    {
      name        = "customer_id"
      type        = "INTEGER"
      mode        = "REQUIRED"
      description = "Business meaning: Internal customer ID of the record. Relationship information: Foreign key to customers.customer_id. Nullability: Never null."
    },
    {
      name        = "score"
      type        = "INTEGER"
      mode        = "REQUIRED"
      description = "Business meaning: Numeric credit score value between 300 and 850. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "last_updated"
      type        = "DATE"
      mode        = "REQUIRED"
      description = "Business meaning: Date when the credit score was retrieved or refreshed. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "bureau_source"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Business meaning: Credit bureau supplying the credit data. Allowed values: EXPERIAN, EQUIFAX, TRANSUNION, CIBIL. Relationship information: None. Nullability: Never null."
    }
  ])
}

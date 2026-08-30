# Analytics Dataset for Analytical Mart Views
resource "google_bigquery_dataset" "analytics_dataset" {
  dataset_id                 = var.analytics_dataset_id
  friendly_name              = "Analytics Marts"
  description                = "Dataset containing curated analytical views, metrics marts, and customer 360 models"
  location                   = var.location
  delete_contents_on_destroy = true
}

# 1. Analytics Customer 360 View
resource "google_bigquery_table" "analytics_customer_360" {
  dataset_id          = google_bigquery_dataset.analytics_dataset.dataset_id
  table_id            = "analytics_customer_360"
  deletion_protection = false

  description = "Business Purpose: Curated 360-degree customer analytical view aggregating demographics, employment, geography, acquisition channels, product adoption flags, lifecycle stages, credit score, and financial balances across deposit, loan, investment, and card lines.\nPrimary Business Key: customer_id\nRelationship Information: Enriched view joining customers (SCD2 current version), accounts, fixed_deposits, loans, credit_cards, and credit_scores. Primary dimension referenced by analytics_customer_acquisition, analytics_transactions, analytics_products, and analytics_balances.\nTypical Usage Examples: Customer segmentation, lifetime value analysis, cross-sell/up-sell targeting, and credit risk assessment.\nAI Usage Guidance: Preferred single-pane analytical source for any customer-level profiling or portfolio aggregation questions. All underlying tables are pre-filtered for active and current records.\nTypical AI Questions:\n- What is the total relationship balance and product count for a customer?\n- What percentage of High Value customers hold both a credit card and a loan?\n- Which customer age cohorts hold the highest average deposit balance?\n- What is the distribution of customers across lifecycle stages and risk segments?"

  schema = jsonencode([
    {
      name        = "customer_id"
      type        = "INTEGER"
      mode        = "NULLABLE"
      description = "Business meaning: Unique 16-digit customer identifier. Primary key for customer entities. Relationship information: Joined with accounts, credit_cards, loans, fixed_deposits, credit_scores, beneficiaries, and identity mapping tables. Nullability: Never null."
    },
    {
      name        = "customer_status"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Operational status of the customer. Allowed values: ACTIVE, DORMANT, BLOCKED, CLOSED. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "customer_since_date"
      type        = "DATE"
      mode        = "NULLABLE"
      description = "Business meaning: Original date when the customer was onboarded. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "age"
      type        = "INTEGER"
      mode        = "NULLABLE"
      description = "Business meaning: Current age of the customer in completed years, calculated dynamically from date_of_birth. Aggregations: AVG, MIN, MAX."
    },
    {
      name        = "age_band"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Standard demographic age cohort for segmentation. Allowed values: '<25', '25-34', '35-49', '50-64', '65+', 'UNKNOWN'."
    },
    {
      name        = "gender"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Customer gender. Allowed values: MALE, FEMALE, OTHER. Nullability: Nullable."
    },
    {
      name        = "employment_status"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Customer employment status. Allowed values: EMPLOYED, SELF_EMPLOYED, STUDENT, RETIRED, UNEMPLOYED. Nullability: Nullable."
    },
    {
      name        = "occupation"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Customer job title or profession. Nullability: Nullable."
    },
    {
      name        = "industry"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Industry domain of customer employment. Nullability: Nullable."
    },
    {
      name        = "annual_income"
      type        = "FLOAT"
      mode        = "NULLABLE"
      description = "Business meaning: Total estimated annual earnings or salary. Nullability: Nullable."
    },
    {
      name        = "income_band"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Standard income bracket tier. Allowed values: '< 5L', '5L-15L', '15L-30L', '30L-50L', '50L+', 'UNKNOWN'."
    },
    {
      name        = "region"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Geographic territory or zone. Allowed values: NORTH, SOUTH, EAST, WEST, CENTRAL. Nullability: Nullable."
    },
    {
      name        = "state"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: State or province of residential location. Nullability: Nullable."
    },
    {
      name        = "city"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: City or metro area of residence. Nullability: Nullable."
    },
    {
      name        = "branch_id"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Primary assigned branch identifier for servicing. Nullability: Nullable."
    },
    {
      name        = "acquisition_date"
      type        = "DATE"
      mode        = "NULLABLE"
      description = "Business meaning: Original date when the customer was onboarded. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "acquisition_channel"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Marketing channel through which customer was onboarded. Allowed values: ORGANIC_DIGITAL, BRANCH, REFERRAL, PAID_SEARCH, PARTNER. Nullability: Nullable."
    },
    {
      name        = "acquisition_source"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Specific digital touchpoint or campaign source. Nullability: Nullable."
    },
    {
      name        = "customer_segment"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Customer tier used for targeted marketing and personalization. Allowed values: RETAIL, PREMIUM, WEALTH, STUDENT, SENIOR_CITIZEN. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "customer_tier"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Commercial relationship tier. Allowed values: BRONZE, SILVER, GOLD, PLATINUM, DIAMOND. Nullability: Nullable."
    },
    {
      name        = "value_segment"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Relationship balance value tier based on total deposits and fixed deposits. Allowed values: HIGH_VALUE (>= 10L), MEDIUM_VALUE (>= 2L), MASS_MARKET (< 2L)."
    },
    {
      name        = "risk_segment"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Composite credit risk category formatted as LOW_RISK, MEDIUM_RISK, or HIGH_RISK."
    },
    {
      name        = "risk_profile"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Internal credit and compliance risk rating. Allowed values: LOW, MEDIUM, HIGH. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "lifecycle_stage"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Customer relationship lifecycle phase. Allowed values: ONBOARDING (< 90 days), GROWTH (< 3 products), MATURE (>= 3 products), DORMANT (inactive)."
    },
    {
      name        = "has_credit_card"
      type        = "BOOLEAN"
      mode        = "NULLABLE"
      description = "Business meaning: Boolean indicator showing whether customer currently holds at least one active credit card."
    },
    {
      name        = "has_loan"
      type        = "BOOLEAN"
      mode        = "NULLABLE"
      description = "Business meaning: Boolean indicator showing whether customer currently holds at least one active loan account."
    },
    {
      name        = "has_investment"
      type        = "BOOLEAN"
      mode        = "NULLABLE"
      description = "Business meaning: Boolean indicator showing whether customer currently holds at least one active fixed deposit investment."
    },
    {
      name        = "product_count"
      type        = "INTEGER"
      mode        = "NULLABLE"
      description = "Business meaning: Total number of active distinct product lines held by customer (accounts + fixed deposits + loans + credit cards). Range: 0 to 4."
    },
    {
      name        = "active_product_count"
      type        = "INTEGER"
      mode        = "NULLABLE"
      description = "Business meaning: Aggregate count of open, active financial products held. Used for product penetration and cross-sell ratio analytics."
    },
    {
      name        = "total_deposit_balance"
      type        = "FLOAT"
      mode        = "NULLABLE"
      description = "Business meaning: Total combined liquid balance in INR across all active savings and current accounts owned by customer. Aggregations: SUM, AVG, MIN, MAX."
    },
    {
      name        = "total_fd_balance"
      type        = "FLOAT"
      mode        = "NULLABLE"
      description = "Business meaning: Total active principal amount in INR locked in fixed deposits. Aggregations: SUM, AVG, MIN, MAX."
    },
    {
      name        = "total_loan_outstanding"
      type        = "FLOAT"
      mode        = "NULLABLE"
      description = "Business meaning: Total remaining outstanding loan principal balance in INR across all active loans. Aggregations: SUM, AVG, MIN, MAX."
    },
    {
      name        = "total_card_outstanding"
      type        = "FLOAT"
      mode        = "NULLABLE"
      description = "Business meaning: Total current outstanding debt balance in INR across all active credit cards. Aggregations: SUM, AVG, MIN, MAX."
    },
    {
      name        = "credit_score"
      type        = "INTEGER"
      mode        = "NULLABLE"
      description = "Business meaning: Numeric credit score value between 300 and 850. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "effective_from"
      type        = "TIMESTAMP"
      mode        = "NULLABLE"
      description = "Business meaning: SCD Type 2 Effective Start Timestamp. When this customer record version became effective. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "effective_to"
      type        = "TIMESTAMP"
      mode        = "NULLABLE"
      description = "Business meaning: SCD Type 2 Effective End Timestamp. When this customer record version expired. NULL means current active version. Relationship information: None. Nullability: Nullable."
    },
    {
      name        = "is_current"
      type        = "BOOLEAN"
      mode        = "NULLABLE"
      description = "Business meaning: SCD Type 2 Flag indicating if this is the current active version. Relationship information: None. Nullability: Never null."
    }
  ])

  view {
    query          = <<-SQL
      SELECT
        c.customer_id,
        c.customer_status,
        c.created_at AS customer_since_date,
        
        -- Age and Demographics
        DATE_DIFF(CURRENT_DATE(), c.date_of_birth, YEAR) AS age,
        CASE
          WHEN DATE_DIFF(CURRENT_DATE(), c.date_of_birth, YEAR) < 25 THEN '<25'
          WHEN DATE_DIFF(CURRENT_DATE(), c.date_of_birth, YEAR) BETWEEN 25 AND 34 THEN '25-34'
          WHEN DATE_DIFF(CURRENT_DATE(), c.date_of_birth, YEAR) BETWEEN 35 AND 49 THEN '35-49'
          WHEN DATE_DIFF(CURRENT_DATE(), c.date_of_birth, YEAR) BETWEEN 50 AND 64 THEN '50-64'
          WHEN DATE_DIFF(CURRENT_DATE(), c.date_of_birth, YEAR) >= 65 THEN '65+'
          ELSE 'UNKNOWN'
        END AS age_band,
        c.gender,
        
        -- Employment & Income
        c.employment_status,
        c.occupation,
        c.industry,
        c.annual_income,
        CASE
          WHEN c.annual_income < 500000 THEN '< 5L'
          WHEN c.annual_income BETWEEN 500000 AND 1500000 THEN '5L-15L'
          WHEN c.annual_income BETWEEN 1500001 AND 3000000 THEN '15L-30L'
          WHEN c.annual_income BETWEEN 3000001 AND 5000000 THEN '30L-50L'
          WHEN c.annual_income > 5000000 THEN '50L+'
          ELSE 'UNKNOWN'
        END AS income_band,
        
        -- Geography & Servicing Branch
        c.region,
        c.state,
        c.city,
        c.branch_id,
        
        -- Acquisition
        c.created_at AS acquisition_date,
        c.acquisition_channel,
        c.acquisition_source,
        
        -- Segmentation & Lifecycle
        c.customer_segment,
        c.customer_tier,
        CASE
          WHEN (COALESCE(acc.total_deposit_balance, 0.0) + COALESCE(fd.total_fd_balance, 0.0)) >= 1000000.0 THEN 'HIGH_VALUE'
          WHEN (COALESCE(acc.total_deposit_balance, 0.0) + COALESCE(fd.total_fd_balance, 0.0)) >= 200000.0 THEN 'MEDIUM_VALUE'
          ELSE 'MASS_MARKET'
        END AS value_segment,
        CONCAT(c.risk_profile, '_RISK') AS risk_segment,
        c.risk_profile,
        CASE
          WHEN DATE_DIFF(CURRENT_DATE(), c.created_at, DAY) < 90 THEN 'ONBOARDING'
          WHEN c.customer_status = 'DORMANT' THEN 'DORMANT'
          WHEN (
            (CASE WHEN acc.acc_count > 0 THEN 1 ELSE 0 END) +
            (CASE WHEN fd.fd_count > 0 THEN 1 ELSE 0 END) +
            (CASE WHEN ln.loan_count > 0 THEN 1 ELSE 0 END) +
            (CASE WHEN cc.cc_count > 0 THEN 1 ELSE 0 END)
          ) >= 3 THEN 'MATURE'
          ELSE 'GROWTH'
        END AS lifecycle_stage,
        
        -- Product Holdings Flags & Counts
        (COALESCE(cc.cc_count, 0) > 0) AS has_credit_card,
        (COALESCE(ln.loan_count, 0) > 0) AS has_loan,
        (COALESCE(fd.fd_count, 0) > 0) AS has_investment,
        (
          (CASE WHEN acc.acc_count > 0 THEN 1 ELSE 0 END) +
          (CASE WHEN fd.fd_count > 0 THEN 1 ELSE 0 END) +
          (CASE WHEN ln.loan_count > 0 THEN 1 ELSE 0 END) +
          (CASE WHEN cc.cc_count > 0 THEN 1 ELSE 0 END)
        ) AS product_count,
        (
          (CASE WHEN acc.acc_count > 0 THEN 1 ELSE 0 END) +
          (CASE WHEN fd.fd_count > 0 THEN 1 ELSE 0 END) +
          (CASE WHEN ln.loan_count > 0 THEN 1 ELSE 0 END) +
          (CASE WHEN cc.cc_count > 0 THEN 1 ELSE 0 END)
        ) AS active_product_count,
        
        -- Financial Balances & Bureau Scores
        COALESCE(acc.total_deposit_balance, 0.0) AS total_deposit_balance,
        COALESCE(fd.total_fd_balance, 0.0) AS total_fd_balance,
        COALESCE(ln.total_loan_outstanding, 0.0) AS total_loan_outstanding,
        COALESCE(cc.total_card_outstanding, 0.0) AS total_card_outstanding,
        cs.score AS credit_score,
        
        -- SCD Type 2 Audit
        c.eff_start_ts AS effective_from,
        c.eff_end_ts AS effective_to,
        c.is_current
      FROM
        `${var.project_id}.${var.dataset_id}.customers` c
      LEFT JOIN (
        SELECT
          customer_id,
          SUM(balance) AS total_deposit_balance,
          COUNT(1) AS acc_count
        FROM `${var.project_id}.${var.dataset_id}.accounts`
        WHERE is_current = TRUE AND account_status = 'ACTIVE'
        GROUP BY customer_id
      ) acc ON c.customer_id = acc.customer_id
      LEFT JOIN (
        SELECT
          customer_id,
          SUM(principal_amount) AS total_fd_balance,
          COUNT(1) AS fd_count
        FROM `${var.project_id}.${var.dataset_id}.fixed_deposits`
        WHERE status = 'ACTIVE'
        GROUP BY customer_id
      ) fd ON c.customer_id = fd.customer_id
      LEFT JOIN (
        SELECT
          customer_id,
          SUM(outstanding_amount) AS total_loan_outstanding,
          COUNT(1) AS loan_count
        FROM `${var.project_id}.${var.dataset_id}.loans`
        WHERE status = 'ACTIVE'
        GROUP BY customer_id
      ) ln ON c.customer_id = ln.customer_id
      LEFT JOIN (
        SELECT
          customer_id,
          SUM(outstanding_balance) AS total_card_outstanding,
          COUNT(1) AS cc_count
        FROM `${var.project_id}.${var.dataset_id}.credit_cards`
        WHERE is_current = TRUE AND status = 'ACTIVE'
        GROUP BY customer_id
      ) cc ON c.customer_id = cc.customer_id
      LEFT JOIN (
        SELECT
          customer_id,
          score,
          ROW_NUMBER() OVER(PARTITION BY customer_id ORDER BY last_updated DESC) AS rn
        FROM `${var.project_id}.${var.dataset_id}.credit_scores`
      ) cs ON c.customer_id = cs.customer_id AND cs.rn = 1
      WHERE
        c.is_current = TRUE
    SQL
    use_legacy_sql = false
  }

  depends_on = [
    google_bigquery_table.customers,
    google_bigquery_table.accounts,
    google_bigquery_table.fixed_deposits,
    google_bigquery_table.loans,
    google_bigquery_table.credit_cards,
    google_bigquery_table.credit_scores,
  ]
}

# 2. Analytics Customer Acquisition View
resource "google_bigquery_table" "analytics_customer_acquisition" {
  dataset_id          = google_bigquery_dataset.analytics_dataset.dataset_id
  table_id            = "analytics_customer_acquisition"
  deletion_protection = false

  description = "Business Purpose: Curated customer acquisition and onboarding funnel mart tracking acquisition channels, initial account funding, conversion status, and estimated customer acquisition cost (CAC).\nPrimary Business Key: acquisition_id\nRelationship Information: Joined with analytics_customer_360 and customers via customer_id. Enriched with initial account funding balance from accounts.\nTypical Usage Examples: Marketing attribution, channel CAC vs. LTV analysis, and branch onboarding performance analytics.\nAI Usage Guidance: Use this view when analyzing how customers joined the bank, comparing channel effectiveness, or calculating customer acquisition cost trends.\nTypical AI Questions:\n- What is the total acquisition cost and volume by channel (Branch vs. Digital)?\n- Which marketing channel produces customers with the highest initial deposit amount?\n- How has customer onboarding volume grown month-over-month by segment?"

  schema = jsonencode([
    {
      name        = "acquisition_id"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Unique synthetic identifier for the customer onboarding/acquisition event. Primary key for acquisition mart."
    },
    {
      name        = "customer_id"
      type        = "INTEGER"
      mode        = "NULLABLE"
      description = "Business meaning: Unique 16-digit customer identifier. Primary key for customer entities. Relationship information: Joined with accounts, credit_cards, loans, fixed_deposits, credit_scores, beneficiaries, and identity mapping tables. Nullability: Never null."
    },
    {
      name        = "acquisition_channel"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Marketing channel through which customer was onboarded. Allowed values: ORGANIC_DIGITAL, BRANCH, REFERRAL, PAID_SEARCH, PARTNER. Nullability: Nullable."
    },
    {
      name        = "acquisition_source"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Specific digital touchpoint or campaign source. Nullability: Nullable."
    },
    {
      name        = "customer_segment"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Customer tier used for targeted marketing and personalization. Allowed values: RETAIL, PREMIUM, WEALTH, STUDENT, SENIOR_CITIZEN. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "customer_tier"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Commercial relationship tier. Allowed values: BRONZE, SILVER, GOLD, PLATINUM, DIAMOND. Nullability: Nullable."
    },
    {
      name        = "region"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Geographic territory or zone. Allowed values: NORTH, SOUTH, EAST, WEST, CENTRAL. Nullability: Nullable."
    },
    {
      name        = "state"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: State or province of residential location. Nullability: Nullable."
    },
    {
      name        = "city"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: City or metro area of residence. Nullability: Nullable."
    },
    {
      name        = "branch_id"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Primary assigned branch identifier for servicing. Nullability: Nullable."
    },
    {
      name        = "acquisition_date"
      type        = "DATE"
      mode        = "NULLABLE"
      description = "Business meaning: Original date when the customer was onboarded. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "application_status"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Status of the onboarding application. Allowed values: APPROVED, DORMANT, CLOSED, PENDING."
    },
    {
      name        = "initial_deposit_amount"
      type        = "FLOAT"
      mode        = "NULLABLE"
      description = "Business meaning: Initial opening funding amount in INR deposited into the primary account at version 1. Aggregations: SUM, AVG, MIN, MAX."
    },
    {
      name        = "acquisition_cost"
      type        = "FLOAT"
      mode        = "NULLABLE"
      description = "Business meaning: Standard estimated Customer Acquisition Cost (CAC) in INR assigned based on channel model (e.g., Branch: 150.00, Paid Search: 120.00, Partner: 85.00, Referral: 45.00, Digital: 25.00). Aggregations: SUM, AVG."
    }
  ])

  view {
    query          = <<-SQL
      SELECT
        CONCAT('ACQ-', CAST(c.customer_id AS STRING)) AS acquisition_id,
        c.customer_id,
        COALESCE(c.acquisition_channel, 'ORGANIC_DIGITAL') AS acquisition_channel,
        c.acquisition_source,
        c.customer_segment,
        c.customer_tier,
        c.region,
        c.state,
        c.city,
        c.branch_id,
        c.created_at AS acquisition_date,
        CASE WHEN c.customer_status = 'ACTIVE' THEN 'APPROVED' ELSE c.customer_status END AS application_status,
        COALESCE(acc.initial_deposit_amount, 0.0) AS initial_deposit_amount,
        CASE 
          WHEN c.acquisition_channel = 'BRANCH' THEN 150.00
          WHEN c.acquisition_channel = 'PAID_SEARCH' THEN 120.00
          WHEN c.acquisition_channel = 'PARTNER' THEN 85.00
          WHEN c.acquisition_channel = 'REFERRAL' THEN 45.00
          ELSE 25.00
        END AS acquisition_cost
      FROM
        `${var.project_id}.${var.dataset_id}.customers` c
      LEFT JOIN (
        SELECT
          customer_id,
          MIN(balance) AS initial_deposit_amount
        FROM `${var.project_id}.${var.dataset_id}.accounts`
        WHERE record_version = 1
        GROUP BY customer_id
      ) acc ON c.customer_id = acc.customer_id
      WHERE
        c.is_current = TRUE
    SQL
    use_legacy_sql = false
  }

  depends_on = [
    google_bigquery_table.customers,
    google_bigquery_table.accounts,
  ]
}

# 3. Analytics Transactions View
resource "google_bigquery_table" "analytics_transactions" {
  dataset_id          = google_bigquery_dataset.analytics_dataset.dataset_id
  table_id            = "analytics_transactions"
  deletion_protection = false

  description = "Business Purpose: Curated analytical transaction mart enriched with customer demographics, geographic dimensions, merchant categories, and temporal attributes.\nPrimary Business Key: transaction_id\nRelationship Information: Sourced from transactions, enriched with accounts and customers dimensions. Linked to customer_id.\nTypical Usage Examples: Monthly spend trend analysis, merchant category profiling, debit vs. credit cashflow analytics, and geographic transaction volume comparisons.\nAI Usage Guidance: Preferred source for transaction and spend analysis. For spend analysis, filter direction = 'DEBIT'. Use transaction_date or month for time slicing.\nTypical AI Questions:\n- What is the total transaction volume and average spend by merchant category for Premium customers?\n- How did debit transaction volume change between Q1 and Q2?\n- Which geographic regions generate the highest transaction spend?"

  schema = jsonencode([
    {
      name        = "transaction_id"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Unique 16-digit transaction identifier. Primary key for transaction entities. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "customer_id"
      type        = "INTEGER"
      mode        = "NULLABLE"
      description = "Business meaning: Unique 16-digit customer identifier. Primary key for customer entities. Relationship information: Joined with accounts, credit_cards, loans, fixed_deposits, credit_scores, beneficiaries, and identity mapping tables. Nullability: Never null."
    },
    {
      name        = "account_number"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: 16-digit account number associated with the transaction. Relationship information: Joined with accounts.account_number. Nullability: Never null."
    },
    {
      name        = "customer_segment"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Customer tier used for targeted marketing and personalization. Allowed values: RETAIL, PREMIUM, WEALTH, STUDENT, SENIOR_CITIZEN. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "region"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Geographic territory or zone. Allowed values: NORTH, SOUTH, EAST, WEST, CENTRAL. Nullability: Nullable."
    },
    {
      name        = "state"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: State or province of residential location. Nullability: Nullable."
    },
    {
      name        = "city"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: City or metro area of residence. Nullability: Nullable."
    },
    {
      name        = "merchant_category"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: High-level classification of merchant or purpose for spending analysis. Allowed values: GROCERY, FOOD, TRAVEL, SHOPPING, ENTERTAINMENT, UTILITIES, HEALTHCARE, EDUCATION, BANKING, SALARY, INVESTMENT, LOAN, OTHER. Relationship information: None. Nullability: Nullable."
    },
    {
      name        = "direction"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Balance change direction (inflow vs. outflow). Allowed values: DEBIT (outflow), CREDIT (inflow). Relationship information: None. Nullability: Never null."
    },
    {
      name        = "amount"
      type        = "FLOAT"
      mode        = "NULLABLE"
      description = "Business meaning: Absolute value of the transaction. Always positive. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "transaction_timestamp"
      type        = "TIMESTAMP"
      mode        = "NULLABLE"
      description = "Business meaning: Point-in-time when transaction occurred. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "transaction_date"
      type        = "DATE"
      mode        = "NULLABLE"
      description = "Business meaning: Calendar date of transaction in YYYY-MM-DD format."
    },
    {
      name        = "month"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Reporting period month formatted as YYYY-MM (e.g., '2026-03')."
    }
  ])

  view {
    query          = <<-SQL
      SELECT
        t.transaction_id,
        acc.customer_id,
        t.account_number,
        c.customer_segment,
        c.region,
        c.state,
        c.city,
        COALESCE(t.category, 'GENERAL') AS merchant_category,
        t.direction,
        t.amount,
        t.transaction_timestamp,
        DATE(t.transaction_timestamp) AS transaction_date,
        FORMAT_DATE('%Y-%m', DATE(t.transaction_timestamp)) AS month
      FROM
        `${var.project_id}.${var.dataset_id}.transactions` t
      LEFT JOIN (
        SELECT account_number, customer_id
        FROM `${var.project_id}.${var.dataset_id}.accounts`
        WHERE is_current = TRUE
      ) acc ON t.account_number = acc.account_number
      LEFT JOIN (
        SELECT customer_id, customer_segment, region, state, city
        FROM `${var.project_id}.${var.dataset_id}.customers`
        WHERE is_current = TRUE
      ) c ON acc.customer_id = c.customer_id
    SQL
    use_legacy_sql = false
  }

  depends_on = [
    google_bigquery_table.transactions,
    google_bigquery_table.accounts,
    google_bigquery_table.customers,
  ]
}

# 4. Analytics Products View
resource "google_bigquery_table" "analytics_products" {
  dataset_id          = google_bigquery_dataset.analytics_dataset.dataset_id
  table_id            = "analytics_products"
  deletion_protection = false

  description = "Business Purpose: Unified product holdings mart consolidating all active customer accounts, credit cards, loans, and fixed deposits into a standardized product adoption schema.\nPrimary Business Key: holding_id\nRelationship Information: Unioned view combining accounts, credit_cards, loans, and fixed_deposits, enriched with customer segment and geography from customers.\nTypical Usage Examples: Product penetration rates, multi-holding analysis, portfolio cross-sell tracking, and product line growth comparison.\nAI Usage Guidance: Use this view when asked about how many products customers hold, which product lines are growing fastest, or product penetration by customer segment.\nTypical AI Questions:\n- What is the total number of active product holdings across SAVINGS, CREDIT_CARD, and LOAN categories?\n- Which customer segment has the highest proportion of credit card holders?\n- How many new product holdings were opened per month by product type?"

  schema = jsonencode([
    {
      name        = "holding_id"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Unified unique product holding identifier prefixed by product type code (e.g., 'ACC-1001', 'CC-5001', 'LN-2001', 'FD-3001')."
    },
    {
      name        = "customer_id"
      type        = "INTEGER"
      mode        = "NULLABLE"
      description = "Business meaning: Unique 16-digit customer identifier. Primary key for customer entities. Relationship information: Joined with accounts, credit_cards, loans, fixed_deposits, credit_scores, beneficiaries, and identity mapping tables. Nullability: Never null."
    },
    {
      name        = "product_type"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Standardized product category code. Allowed values: SAVINGS, CURRENT, SALARY, CREDIT_CARD, LOAN, FIXED_DEPOSIT."
    },
    {
      name        = "product_name"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Commercial product name, card product name, or loan type description (e.g., 'SAVINGS Account', 'Premier', 'Taj', 'Travel One', 'Live+', 'Visa Platinum', 'HOME_LOAN', 'Fixed Deposit')."
    },
    {
      name        = "customer_segment"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Customer tier used for targeted marketing and personalization. Allowed values: RETAIL, PREMIUM, WEALTH, STUDENT, SENIOR_CITIZEN. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "region"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Geographic territory or zone. Allowed values: NORTH, SOUTH, EAST, WEST, CENTRAL. Nullability: Nullable."
    },
    {
      name        = "state"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: State or province of residential location. Nullability: Nullable."
    },
    {
      name        = "city"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: City or metro area of residence. Nullability: Nullable."
    },
    {
      name        = "is_active"
      type        = "BOOLEAN"
      mode        = "NULLABLE"
      description = "Business meaning: Boolean flag indicating if the product holding is currently active and open."
    },
    {
      name        = "opened_date"
      type        = "DATE"
      mode        = "NULLABLE"
      description = "Business meaning: Date when the account, card, loan, or deposit was officially created or opened."
    }
  ])

  view {
    query          = <<-SQL
      WITH product_holdings AS (
        SELECT
          CONCAT('ACC-', account_number) AS holding_id,
          customer_id,
          account_type AS product_type,
          CONCAT(account_type, ' Account') AS product_name,
          CASE WHEN account_status = 'ACTIVE' THEN TRUE ELSE FALSE END AS is_active,
          created_at AS opened_date
        FROM `${var.project_id}.${var.dataset_id}.accounts`
        WHERE is_current = TRUE

        UNION ALL

        SELECT
          CONCAT('CC-', card_account_number) AS holding_id,
          customer_id,
          'CREDIT_CARD' AS product_type,
          card_product_name AS product_name,
          CASE WHEN status = 'ACTIVE' THEN TRUE ELSE FALSE END AS is_active,
          created_at AS opened_date
        FROM `${var.project_id}.${var.dataset_id}.credit_cards`
        WHERE is_current = TRUE

        UNION ALL

        SELECT
          CONCAT('LN-', loan_account_number) AS holding_id,
          customer_id,
          'LOAN' AS product_type,
          loan_type AS product_name,
          CASE WHEN status = 'ACTIVE' THEN TRUE ELSE FALSE END AS is_active,
          start_date AS opened_date
        FROM `${var.project_id}.${var.dataset_id}.loans`

        UNION ALL

        SELECT
          CONCAT('FD-', fd_account_number) AS holding_id,
          customer_id,
          'FIXED_DEPOSIT' AS product_type,
          'Fixed Deposit' AS product_name,
          CASE WHEN status = 'ACTIVE' THEN TRUE ELSE FALSE END AS is_active,
          start_date AS opened_date
        FROM `${var.project_id}.${var.dataset_id}.fixed_deposits`
      )
      SELECT
        p.holding_id,
        p.customer_id,
        p.product_type,
        p.product_name,
        c.customer_segment,
        c.region,
        c.state,
        c.city,
        p.is_active,
        p.opened_date
      FROM
        product_holdings p
      LEFT JOIN (
        SELECT customer_id, customer_segment, region, state, city
        FROM `${var.project_id}.${var.dataset_id}.customers`
        WHERE is_current = TRUE
      ) c ON p.customer_id = c.customer_id
    SQL
    use_legacy_sql = false
  }

  depends_on = [
    google_bigquery_table.accounts,
    google_bigquery_table.credit_cards,
    google_bigquery_table.loans,
    google_bigquery_table.fixed_deposits,
    google_bigquery_table.customers,
  ]
}

# 5. Analytics Balances View
resource "google_bigquery_table" "analytics_balances" {
  dataset_id          = google_bigquery_dataset.analytics_dataset.dataset_id
  table_id            = "analytics_balances"
  deletion_protection = false

  description = "Business Purpose: Curated snapshot balance mart providing daily balance positions across deposit and savings accounts, segmented by account type, customer tier, and geographic regions.\nPrimary Business Key: snapshot_id\nRelationship Information: Sourced from active records in accounts, joined with customers for demographic segmentation.\nTypical Usage Examples: Total deposit balance trends, average balance per account by segment, regional liquidity tracking, and customer wealth tier analysis.\nAI Usage Guidance: Preferred source for calculating total deposit balances, account-level balance distributions, and customer liquidity metrics.\nTypical AI Questions:\n- What is the total and average savings account balance by customer segment?\n- Which branch regions have the highest concentration of high-balance accounts?\n- What is the distribution of deposit balances across Wealth vs. Retail customer tiers?"

  schema = jsonencode([
    {
      name        = "snapshot_id"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Unique daily balance snapshot record identifier formatted as 'BAL-{account_number}-{YYYYMMDD}'."
    },
    {
      name        = "customer_id"
      type        = "INTEGER"
      mode        = "NULLABLE"
      description = "Business meaning: Unique 16-digit customer identifier. Primary key for customer entities. Relationship information: Joined with accounts, credit_cards, loans, fixed_deposits, credit_scores, beneficiaries, and identity mapping tables. Nullability: Never null."
    },
    {
      name        = "account_number"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Unique 16-digit bank account number. Primary business key for account entities. Relationship information: Joined with transactions, beneficiaries, and identity mapping tables. Nullability: Never null."
    },
    {
      name        = "account_type"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Type of bank account. Allowed values: SAVINGS, CURRENT, SALARY, NRI. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "customer_segment"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Customer tier used for targeted marketing and personalization. Allowed values: RETAIL, PREMIUM, WEALTH, STUDENT, SENIOR_CITIZEN. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "region"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: Geographic territory or zone. Allowed values: NORTH, SOUTH, EAST, WEST, CENTRAL. Nullability: Nullable."
    },
    {
      name        = "state"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: State or province of residential location. Nullability: Nullable."
    },
    {
      name        = "city"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Business meaning: City or metro area of residence. Nullability: Nullable."
    },
    {
      name        = "balance"
      type        = "FLOAT"
      mode        = "NULLABLE"
      description = "Business meaning: Available balance in the account. Relationship information: None. Nullability: Never null."
    },
    {
      name        = "snapshot_date"
      type        = "DATE"
      mode        = "NULLABLE"
      description = "Business meaning: Calendar snapshot date of balance calculation in YYYY-MM-DD format."
    }
  ])

  view {
    query          = <<-SQL
      SELECT
        CONCAT('BAL-', a.account_number, '-', FORMAT_DATE('%Y%m%d', CURRENT_DATE())) AS snapshot_id,
        a.customer_id,
        a.account_number,
        a.account_type,
        c.customer_segment,
        c.region,
        c.state,
        c.city,
        a.balance AS balance,
        CURRENT_DATE() AS snapshot_date
      FROM
        `${var.project_id}.${var.dataset_id}.accounts` a
      LEFT JOIN (
        SELECT customer_id, customer_segment, region, state, city
        FROM `${var.project_id}.${var.dataset_id}.customers`
        WHERE is_current = TRUE
      ) c ON a.customer_id = c.customer_id
      WHERE
        a.is_current = TRUE
    SQL
    use_legacy_sql = false
  }

  depends_on = [
    google_bigquery_table.accounts,
    google_bigquery_table.customers,
  ]
}

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

  description = "Curated 360-degree customer analytical view aggregating demographics, employment, geography, acquisition channels, product adoption flags, lifecycle stages, credit score, and financial balances."

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

  description = "Curated customer acquisition and application funnel dataset tracking onboarding channels, campaigns, conversion rates, and acquisition dates."

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

  description = "Curated analytical transaction mart enriched with customer demographics, merchant categories, and temporal dimensions."

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

  description = "Curated product holdings mart tracking customer product adoption, product lines, and open dates."

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
          card_type AS product_name,
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

  description = "Curated balance snapshot mart tracking customer account balances across asset and liability classes."

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

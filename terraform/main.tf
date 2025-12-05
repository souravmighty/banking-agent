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
  project = var.project_id
  region  = var.region
}


# Create BigQuery dataset
resource "google_bigquery_dataset" "banking_dataset" {
  dataset_id                 = var.dataset_id
  friendly_name              = "Banking Data"
  description                = "Dataset for banking customer, account, and transaction data"
  location                   = var.location
  delete_contents_on_destroy = true
}

# Customers table
resource "google_bigquery_table" "customers" {
  dataset_id          = google_bigquery_dataset.banking_dataset.dataset_id
  table_id            = "customers"
  deletion_protection = false

  schema = jsonencode([
    {
      name = "customer_id"
      type = "INTEGER"
      mode = "REQUIRED"
    },
    {
      name = "name"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "email"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "phone"
      type = "STRING"
      mode = "NULLABLE"
    },
    {
      name = "address"
      type = "STRING"
      mode = "NULLABLE"
    },
    {
      name = "kyc_status"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "created_at"
      type = "TIMESTAMP"
      mode = "REQUIRED"
    },
    {
      name = "has_credit_card"
      type = "BOOLEAN"
      mode = "REQUIRED"
    },
    {
      name = "has_personal_loan"
      type = "BOOLEAN"
      mode = "REQUIRED"
    },
    {
      name = "has_td"
      type = "BOOLEAN"
      mode = "REQUIRED"
    },
    {
      name = "has_dd"
      type = "BOOLEAN"
      mode = "REQUIRED"
    }
  ])
}

# Accounts table
resource "google_bigquery_table" "accounts" {
  dataset_id          = google_bigquery_dataset.banking_dataset.dataset_id
  table_id            = "accounts"
  deletion_protection = false

  schema = jsonencode([
    {
      name = "account_id"
      type = "INTEGER"
      mode = "REQUIRED"
    },
    {
      name = "customer_id"
      type = "INTEGER"
      mode = "REQUIRED"
    },
    {
      name = "account_type"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "balance"
      type = "FLOAT"
      mode = "REQUIRED"
    },
    {
      name = "currency"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "status"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "created_at"
      type = "TIMESTAMP"
      mode = "REQUIRED"
    }
  ])
}

# Transactions table
resource "google_bigquery_table" "transactions" {
  dataset_id          = google_bigquery_dataset.banking_dataset.dataset_id
  table_id            = "transactions"
  deletion_protection = false

  schema = jsonencode([
    {
      name = "transaction_id"
      type = "INTEGER"
      mode = "REQUIRED"
    },
    {
      name = "from_account_id"
      type = "INTEGER"
      mode = "REQUIRED"
    },
    {
      name = "to_account_id"
      type = "INTEGER"
      mode = "NULLABLE"
    },
    {
      name = "amount"
      type = "FLOAT"
      mode = "REQUIRED"
    },
    {
      name = "type"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "status"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "merchant_name"
      type = "STRING"
      mode = "NULLABLE"
    },
    {
      name = "mcc"
      type = "STRING"
      mode = "NULLABLE"
    },
    {
      name = "merchant_location"
      type = "STRING"
      mode = "NULLABLE"
    },
    {
      name = "timestamp"
      type = "TIMESTAMP"
      mode = "REQUIRED"
    }
  ])

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  clustering = ["type", "status"]
}

# Products table
resource "google_bigquery_table" "products" {
  dataset_id          = google_bigquery_dataset.banking_dataset.dataset_id
  table_id            = "products"
  deletion_protection = false

  schema = jsonencode([
    {
      name = "product_id"
      type = "INTEGER"
      mode = "REQUIRED"
    },
    {
      name = "product_type"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "name"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "interest_rate"
      type = "FLOAT"
      mode = "REQUIRED"
    },
    {
      name = "eligibility_criteria"
      type = "STRING"
      mode = "NULLABLE"
    }
  ])
}

# Customer Products table
resource "google_bigquery_table" "customer_products" {
  dataset_id          = google_bigquery_dataset.banking_dataset.dataset_id
  table_id            = "customer_products"
  deletion_protection = false

  schema = jsonencode([
    {
      name = "id"
      type = "INTEGER"
      mode = "REQUIRED"
    },
    {
      name = "customer_id"
      type = "INTEGER"
      mode = "REQUIRED"
    },
    {
      name = "product_id"
      type = "INTEGER"
      mode = "REQUIRED"
    },
    {
      name = "application_date"
      type = "TIMESTAMP"
      mode = "REQUIRED"
    },
    {
      name = "status"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "approval_date"
      type = "TIMESTAMP"
      mode = "NULLABLE"
    }
  ])
}

# Credit Scores table
resource "google_bigquery_table" "credit_scores" {
  dataset_id          = google_bigquery_dataset.banking_dataset.dataset_id
  table_id            = "credit_scores"
  deletion_protection = false

  schema = jsonencode([
    {
      name = "customer_id"
      type = "INTEGER"
      mode = "REQUIRED"
    },
    {
      name = "score"
      type = "INTEGER"
      mode = "REQUIRED"
    },
    {
      name = "last_updated"
      type = "TIMESTAMP"
      mode = "REQUIRED"
    },
    {
      name = "bureau_source"
      type = "STRING"
      mode = "REQUIRED"
    }
  ])
}
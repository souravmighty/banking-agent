import random
import json
import os
from datetime import datetime, timedelta
from faker import Faker
import pandas as pd

fake = Faker()
Faker.seed(42)
random.seed(42)

# Configuration
NUM_CUSTOMERS = 1000
NUM_ACCOUNTS_PER_CUSTOMER = (1, 3)
NUM_TRANSACTIONS = 50000

# Create data directory if it doesn't exist
DATA_DIR = '../data'
os.makedirs(DATA_DIR, exist_ok=True)

# Helper functions
def random_date(start, end):
    return start + timedelta(days=random.randint(0, (end - start).days))

def generate_customers(n):
    customers = []
    customer_ids = set()
    while len(customer_ids) < n:
        # Generate a 16-digit number starting with a non-zero digit
        cid = str(random.randint(10**15, 10**16 - 1))
        if cid not in customer_ids:
            customer_ids.add(cid)
    customer_ids = list(customer_ids)
    for i in range(n):
        has_cc = random.choice([True, False])
        has_pl = random.choice([True, False])
        has_td = random.choice([True, False])
        has_dd = random.choice([True, False])
        
        customers.append({
            'customer_id': customer_ids[i],
            'name': fake.name(),
            'email': fake.email(),
            'phone': fake.phone_number()[:15],
            'address': fake.address().replace('\n', ', '),
            'kyc_status': random.choice(['VERIFIED', 'PENDING', 'REJECTED']),
            'created_at': random_date(datetime(2020, 1, 1), datetime(2024, 12, 1)),
            'has_credit_card': has_cc,
            'has_personal_loan': has_pl,
            'has_td': has_td,
            'has_dd': has_dd
        })
    return pd.DataFrame(customers)

def generate_accounts(customers_df):
    accounts = []
    account_ids = set()
    total_accounts = 0
    for _, customer in customers_df.iterrows():
        num_accounts = random.randint(*NUM_ACCOUNTS_PER_CUSTOMER)
        total_accounts += num_accounts
    # Generate unique 16-digit account IDs
    while len(account_ids) < total_accounts:
        aid = str(random.randint(10**15, 10**16 - 1))
        if aid not in account_ids:
            account_ids.add(aid)
    account_ids = list(account_ids)
    idx = 0
    for _, customer in customers_df.iterrows():
        num_accounts = random.randint(*NUM_ACCOUNTS_PER_CUSTOMER)
        for _ in range(num_accounts):
            account_type = random.choice(['SAVINGS', 'CHECKING', 'CREDIT', 'LOAN'])
            balance = round(random.uniform(100, 100000), 2)
            accounts.append({
                'account_id': account_ids[idx],
                'customer_id': customer['customer_id'],
                'account_type': account_type,
                'balance': balance,
                'currency': random.choice(['USD', 'EUR', 'GBP', 'INR']),
                'status': random.choice(['ACTIVE', 'INACTIVE', 'FROZEN']),
                'created_at': random_date(customer['created_at'], datetime(2024, 12, 1))
            })
            idx += 1
    
    return pd.DataFrame(accounts)

def generate_transactions(accounts_df, n):
    transactions = []
    active_accounts = accounts_df[accounts_df['status'] == 'ACTIVE']['account_id'].tolist()
    
    mcc_codes = {
        '5411': 'Grocery Stores',
        '5812': 'Restaurants',
        '5541': 'Gas Stations',
        '5311': 'Department Stores',
        '4121': 'Taxi/Rideshare',
        '5912': 'Pharmacies',
        '7832': 'Movie Theaters',
        '5999': 'Online Shopping'
    }
    
    for i in range(1, n + 1):
        from_account = random.choice(active_accounts)
        transaction_type = random.choice(['DEBIT', 'CREDIT', 'TRANSFER', 'WITHDRAWAL'])
        
        if transaction_type == 'TRANSFER':
            to_account = random.choice([acc for acc in active_accounts if acc != from_account])
        else:
            to_account = None
        
        mcc = random.choice(list(mcc_codes.keys()))
        
        transactions.append({
            'transaction_id': i,
            'from_account_id': from_account,
            'to_account_id': to_account,
            'amount': round(random.uniform(5, 5000), 2),
            'type': transaction_type,
            'status': random.choice(['COMPLETED', 'PENDING', 'FAILED']),
            'merchant_name': mcc_codes[mcc] if transaction_type == 'DEBIT' else None,
            'mcc': mcc if transaction_type == 'DEBIT' else None,
            'merchant_location': fake.city() if transaction_type == 'DEBIT' else None,
            'timestamp': random_date(datetime(2023, 1, 1), datetime(2024, 12, 1))
        })
    
    return pd.DataFrame(transactions)

def generate_products():
    products = [
        {
            'product_id': 1,
            'product_type': 'CREDIT_CARD',
            'name': 'Premium Rewards Card',
            'interest_rate': 18.99,
            'eligibility_criteria': json.dumps({'min_credit_score': 700, 'min_income': 50000})
        },
        {
            'product_id': 2,
            'product_type': 'CREDIT_CARD',
            'name': 'Basic Card',
            'interest_rate': 24.99,
            'eligibility_criteria': json.dumps({'min_credit_score': 600, 'min_income': 25000})
        },
        {
            'product_id': 3,
            'product_type': 'PERSONAL_LOAN',
            'name': 'Personal Loan',
            'interest_rate': 12.5,
            'eligibility_criteria': json.dumps({'min_credit_score': 650, 'min_income': 40000})
        },
        {
            'product_id': 4,
            'product_type': 'TERM_DEPOSIT',
            'name': '1-Year Fixed Deposit',
            'interest_rate': 5.5,
            'eligibility_criteria': json.dumps({'min_deposit': 1000})
        },
        {
            'product_id': 5,
            'product_type': 'DEMAND_DEPOSIT',
            'name': 'Premium Savings Account',
            'interest_rate': 3.0,
            'eligibility_criteria': json.dumps({'min_balance': 5000})
        }
    ]
    return pd.DataFrame(products)

def generate_customer_products(customers_df, products_df):
    customer_products = []
    cp_id = 1
    
    for _, customer in customers_df.iterrows():
        # Apply for products based on customer flags
        if customer['has_credit_card']:
            product_id = random.choice([1, 2])
            app_date = random_date(customer['created_at'], datetime(2024, 12, 1))
            status = random.choice(['APPROVED', 'PENDING', 'REJECTED'])
            
            customer_products.append({
                'id': cp_id,
                'customer_id': customer['customer_id'],
                'product_id': product_id,
                'application_date': app_date,
                'status': status,
                'approval_date': app_date + timedelta(days=random.randint(1, 30)) if status == 'APPROVED' else None
            })
            cp_id += 1
        
        if customer['has_personal_loan']:
            app_date = random_date(customer['created_at'], datetime(2024, 12, 1))
            status = random.choice(['APPROVED', 'PENDING', 'REJECTED'])
            
            customer_products.append({
                'id': cp_id,
                'customer_id': customer['customer_id'],
                'product_id': 3,
                'application_date': app_date,
                'status': status,
                'approval_date': app_date + timedelta(days=random.randint(1, 30)) if status == 'APPROVED' else None
            })
            cp_id += 1
        
        if customer['has_td']:
            app_date = random_date(customer['created_at'], datetime(2024, 12, 1))
            customer_products.append({
                'id': cp_id,
                'customer_id': customer['customer_id'],
                'product_id': 4,
                'application_date': app_date,
                'status': 'APPROVED',
                'approval_date': app_date + timedelta(days=1)
            })
            cp_id += 1
    
    return pd.DataFrame(customer_products)

def generate_credit_scores(customers_df):
    credit_scores = []
    
    for _, customer in customers_df.iterrows():
        credit_scores.append({
            'customer_id': customer['customer_id'],
            'score': random.randint(300, 850),
            'last_updated': random_date(datetime(2024, 1, 1), datetime(2024, 12, 1)),
            'bureau_source': random.choice(['EXPERIAN', 'EQUIFAX', 'TRANSUNION', 'CIBIL'])
        })
    
    return pd.DataFrame(credit_scores)

def generate_customer_identity_mapping(customers_df):
    mapping = []
    
    for _, customer in customers_df.iterrows():
        mapping.append({
            'customer_id': customer['customer_id'],
            'email_id': customer['email'],
            'firebase_uid': None
        })
    
    return pd.DataFrame(mapping)

# Generate all data
print("Generating customers...")
customers_df = generate_customers(NUM_CUSTOMERS)

print("Generating accounts...")
accounts_df = generate_accounts(customers_df)

print("Generating transactions...")
transactions_df = generate_transactions(accounts_df, NUM_TRANSACTIONS)

print("Generating products...")
products_df = generate_products()

print("Generating customer products...")
customer_products_df = generate_customer_products(customers_df, products_df)

print("Generating credit scores...")
credit_scores_df = generate_credit_scores(customers_df)

print("Generating customer identity mapping...")
customer_identity_mapping_df = generate_customer_identity_mapping(customers_df)

# Save to CSV files in data directory
print(f"\nSaving to CSV files in {DATA_DIR}...")
customers_df.to_csv(f'{DATA_DIR}/customers.csv', index=False)
accounts_df.to_csv(f'{DATA_DIR}/accounts.csv', index=False)
transactions_df.to_csv(f'{DATA_DIR}/transactions.csv', index=False)
products_df.to_csv(f'{DATA_DIR}/products.csv', index=False)
customer_products_df.to_csv(f'{DATA_DIR}/customer_products.csv', index=False)
credit_scores_df.to_csv(f'{DATA_DIR}/credit_scores.csv', index=False)
customer_identity_mapping_df.to_csv(f'{DATA_DIR}/customer_identity_mapping.csv', index=False)

print("\nData generation complete!")
print(f"Customers: {len(customers_df)}")
print(f"Accounts: {len(accounts_df)}")
print(f"Transactions: {len(transactions_df)}")
print(f"Products: {len(products_df)}")
print(f"Customer Products: {len(customer_products_df)}")
print(f"Credit Scores: {len(credit_scores_df)}")
print(f"Customer Identity Mapping: {len(customer_identity_mapping_df)}")
print(f"\nAll files saved to: {DATA_DIR}/")
import random
import json
import os
from datetime import datetime, timedelta, date
from faker import Faker
import pandas as pd
import numpy as np

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

# Configuration
NUM_CUSTOMERS = 1000
DATA_DIR = '../../data'
os.makedirs(DATA_DIR, exist_ok=True)

# Constants & Enums
SEGMENTS = ['RETAIL', 'PREMIUM', 'WEALTH', 'STUDENT', 'SENIOR_CITIZEN']
SEGMENT_DIST = [0.60, 0.20, 0.05, 0.10, 0.05]

RISK_PROFILES = ['LOW', 'MEDIUM', 'HIGH']
RISK_DIST = [0.70, 0.25, 0.05]

TX_TYPES = [
    'TRANSFER', 'UPI', 'CARD_PAYMENT', 'ATM_WITHDRAWAL', 'ATM_DEPOSIT', 
    'SALARY_CREDIT', 'INTEREST_CREDIT', 'LOAN_EMI', 'FD_DEPOSIT', 
    'FD_MATURITY', 'BILL_PAYMENT'
]

CATEGORIES = [
    'GROCERY', 'FOOD', 'TRAVEL', 'SHOPPING', 'ENTERTAINMENT', 
    'UTILITIES', 'HEALTHCARE', 'EDUCATION', 'BANKING', 'SALARY', 
    'INVESTMENT', 'LOAN', 'OTHER'
]

CURRENCIES = ['INR', 'USD', 'EUR']
BANKS = ['ABC Bank', 'HDFC Bank', 'ICICI Bank', 'SBI', 'Axis Bank']

# Map of merchants to their correct category
MERCHANT_CATEGORY_MAP = {
    'Amazon': 'SHOPPING',
    'Flipkart': 'SHOPPING',
    'Swiggy': 'FOOD',
    'Zomato': 'FOOD',
    'Uber': 'TRAVEL',
    'IRCTC': 'TRAVEL',
    'Reliance Fresh': 'GROCERY',
    'D-Mart': 'GROCERY',
    'Starbucks': 'FOOD',
    'Netflix': 'ENTERTAINMENT',
}

UTILITY_MERCHANTS = ['Tata Power', 'Airtel Broadband', 'Indraprastha Gas', 'Reliance Energy', 'Jio Fiber']

MERCHANTS = list(MERCHANT_CATEGORY_MAP.keys())

# Helper functions
def random_date(start, end):
    return start + timedelta(days=random.randint(0, (end - start).days))

def generate_account_number(prefix=""):
    return f"{prefix}{random.randint(10**11, 10**12 - 1)}"

def generate_scd_fields(version, start_ts, is_current=True):
    end_ts = None if is_current else start_ts + timedelta(days=random.randint(30, 180))
    return {
        'eff_start_ts': start_ts,
        'eff_end_ts': end_ts,
        'is_current': is_current,
        'record_version': version
    }

# --- DATA GENERATION FUNCTIONS ---

def generate_customers_scd():
    customers = []
    identity_mapping = []
    
    # Generate unique 16-digit customer IDs
    customer_ids = set()
    while len(customer_ids) < NUM_CUSTOMERS:
        cid = random.randint(10**15, 10**16 - 1)
        customer_ids.add(cid)
    customer_ids = list(customer_ids)
    
    for i in range(NUM_CUSTOMERS):
        cid = customer_ids[i]
        segment = np.random.choice(SEGMENTS, p=SEGMENT_DIST)
        risk = np.random.choice(RISK_PROFILES, p=RISK_DIST)
        onboard_date = random_date(datetime(2020, 1, 1), datetime(2023, 1, 1))
        
        # Base version
        name = fake.name()
        email = fake.email()
        base_record = {
            'customer_id': cid,
            'name': name,
            'email': email,
            'phone': fake.phone_number()[:15],
            'address': fake.address().replace('\n', ', '),
            'customer_status': 'ACTIVE',
            'customer_segment': segment,
            'risk_profile': risk,
            'kyc_status': 'VERIFIED',
            'created_at': onboard_date.date()
        }
        
        # Identity Mapping (Initialize as NOT REGISTERED)
        identity_mapping.append({
            'customer_id': cid,
            'email_id': email,
            'firebase_uid': None,
            'registration_status': 'NOT REGISTERED',
            'linked_at': None
        })

        # Versioning: Simulate a change (e.g., segment upgrade or address change)
        if random.random() < 0.3:
            # Historical Version
            v1_start = onboard_date
            v1_scd = generate_scd_fields(1, v1_start, is_current=False)
            customers.append({**base_record, **v1_scd})
            
            # Current Version
            v2_start = v1_scd['eff_end_ts'] + timedelta(seconds=1)
            # Change something
            updated_record = base_record.copy()
            if random.random() < 0.5:
                updated_record['customer_segment'] = 'PREMIUM' if segment == 'RETAIL' else 'WEALTH'
            else:
                updated_record['address'] = fake.address().replace('\n', ', ')
                
            v2_scd = generate_scd_fields(2, v2_start, is_current=True)
            customers.append({**updated_record, **v2_scd})
        else:
            # Only one version
            scd = generate_scd_fields(1, onboard_date, is_current=True)
            customers.append({**base_record, **scd})
            
    return pd.DataFrame(customers), pd.DataFrame(identity_mapping)

def generate_accounts_scd(customers_df):
    accounts = []
    # Use only current customer records to link accounts
    current_customers = customers_df[customers_df['is_current'] == True]
    
    for _, customer in current_customers.iterrows():
        # Determine number of accounts based on segment
        seg = customer['customer_segment']
        num_accounts = 1
        if seg == 'PREMIUM': num_accounts = 2
        elif seg == 'WEALTH': num_accounts = random.randint(2, 3)
        elif seg == 'STUDENT': num_accounts = 1
        
        for i in range(num_accounts):
            acc_num = generate_account_number("100")
            acc_type = 'SAVINGS' if i == 0 else random.choice(['CURRENT', 'SALARY'])
            onboard_date = datetime.combine(customer['created_at'], datetime.min.time()) + timedelta(days=random.randint(1, 30))
            
            base_record = {
                'account_number': acc_num,
                'customer_id': customer['customer_id'],
                'account_type': acc_type,
                'account_status': 'ACTIVE',
                'balance': round(random.uniform(5000, 500000 if seg != 'WEALTH' else 2000000), 2),
                'currency': 'INR',
                'ifsc_code': f"ABCB000{random.randint(1000, 9999)}",
                'branch_name': f"{fake.city()} Branch",
                'created_at': onboard_date.date()
            }
            
            # Versioning: Simulate status changes
            if random.random() < 0.2:
                v1_scd = generate_scd_fields(1, onboard_date, is_current=False)
                accounts.append({**base_record, **v1_scd})
                
                v2_start = v1_scd['eff_end_ts'] + timedelta(seconds=1)
                updated_record = base_record.copy()
                updated_record['account_status'] = random.choice(['DORMANT', 'FROZEN'])
                v2_scd = generate_scd_fields(2, v2_start, is_current=True)
                accounts.append({**updated_record, **v2_scd})
            else:
                scd = generate_scd_fields(1, onboard_date, is_current=True)
                accounts.append({**base_record, **scd})
                
    return pd.DataFrame(accounts)

def generate_credit_cards_scd(customers_df):
    cards = []
    eligible_segments = ['PREMIUM', 'WEALTH', 'RETAIL']
    current_customers = customers_df[(customers_df['is_current'] == True) & (customers_df['customer_segment'].isin(eligible_segments))]
    
    for _, customer in current_customers.iterrows():
        if random.random() < (0.8 if customer['customer_segment'] == 'WEALTH' else 0.4):
            card_acc_num = generate_account_number("CC")
            limit = 100000.0 if customer['customer_segment'] == 'RETAIL' else (500000.0 if customer['customer_segment'] == 'PREMIUM' else 1000000.0)
            outstanding = round(random.uniform(0, limit * 0.4), 2)
            created_at = datetime.combine(customer['created_at'], datetime.min.time()) + timedelta(days=random.randint(60, 200))
            
            base_record = {
                'card_account_number': card_acc_num,
                'customer_id': customer['customer_id'],
                'card_number': fake.credit_card_number(card_type='visa'),
                'card_type': random.choice(['VISA', 'MASTERCARD', 'RUPAY']),
                'credit_limit': limit,
                'available_credit': limit - outstanding,
                'outstanding_balance': outstanding,
                'statement_amount': round(outstanding * 0.8, 2),
                'minimum_due_amount': round(outstanding * 0.05, 2),
                'payment_due_date': (datetime.now() + timedelta(days=15)).date(),
                'statement_date': (datetime.now() - timedelta(days=15)).date(),
                'utilization_percentage': round((outstanding / limit) * 100, 2),
                'status': 'ACTIVE',
                'created_at': created_at.date()
            }
            
            # Simple SCD: Single version for most
            scd = generate_scd_fields(1, created_at, is_current=True)
            cards.append({**base_record, **scd})
            
    return pd.DataFrame(cards)

def generate_beneficiaries(customers_df):
    beneficiaries = []
    current_customers = customers_df[customers_df['is_current'] == True]
    
    bid = 5001
    for _, customer in current_customers.iterrows():
        num_ben = random.randint(0, 10)
        for _ in range(num_ben):
            beneficiaries.append({
                'beneficiary_id': bid,
                'customer_id': customer['customer_id'],
                'beneficiary_name': fake.name(),
                'beneficiary_account_number': generate_account_number("99"),
                'bank_name': random.choice(BANKS),
                'ifsc_code': f"BANK000{random.randint(1000, 9999)}",
                'status': 'ACTIVE',
                'created_at': datetime.now() - timedelta(days=random.randint(10, 100))
            })
            bid += 1
    return pd.DataFrame(beneficiaries)

def generate_loans(customers_df):
    loans = []
    # Loans for Retail, Premium, Wealth
    current_customers = customers_df[(customers_df['is_current'] == True) & (customers_df['customer_segment'] != 'STUDENT')]
    
    for _, customer in current_customers.iterrows():
        if random.random() < 0.3:
            loan_amt = round(random.uniform(100000, 5000000), 2)
            tenure = random.choice([12, 24, 36, 60, 120])
            emi = round(loan_amt / tenure * 1.1, 2)
            loans.append({
                'loan_account_number': generate_account_number("LN"),
                'customer_id': customer['customer_id'],
                'loan_type': random.choice(['PERSONAL', 'HOME', 'AUTO']),
                'loan_amount': loan_amt,
                'outstanding_amount': round(loan_amt * 0.8, 2),
                'interest_rate': round(random.uniform(8.5, 15.0), 2),
                'emi_amount': emi,
                'remaining_tenure_months': tenure - 6,
                'original_tenure_months': tenure,
                'next_emi_date': (datetime.now() + timedelta(days=20)).date(),
                'status': 'ACTIVE',
                'start_date': (datetime.now() - timedelta(days=180)).date()
            })
    return pd.DataFrame(loans)

def generate_fds(customers_df):
    fds = []
    # FDs for Wealth and Senior Citizens primarily
    current_customers = customers_df[customers_df['is_current'] == True]
    
    for _, customer in current_customers.iterrows():
        prob = 0.1
        if customer['customer_segment'] == 'WEALTH': prob = 0.8
        elif customer['customer_segment'] == 'SENIOR_CITIZEN': prob = 0.6
        
        if random.random() < prob:
            principal = round(random.uniform(50000, 1000000), 2)
            fds.append({
                'fd_account_number': generate_account_number("FD"),
                'customer_id': customer['customer_id'],
                'principal_amount': principal,
                'current_value': round(principal * 1.05, 2),
                'interest_rate': round(random.uniform(6.0, 7.5), 2),
                'start_date': (datetime.now() - timedelta(days=180)).date(),
                'maturity_date': (datetime.now() + timedelta(days=180)).date(),
                'tenure_months': 12,
                'status': 'ACTIVE'
            })
    return pd.DataFrame(fds)

def generate_transactions(accounts_df, cards_df=None):
    transactions = []
    # Only generate transactions for CURRENT active versions of accounts
    active_accounts = accounts_df[accounts_df['is_current'] == True]
    account_list = active_accounts['account_number'].tolist()
    
    tx_id_pool = 1
    for _, account in active_accounts.iterrows():
        num_tx = random.randint(50, 500)
        acc_num = account['account_number']
        
        for _ in range(num_tx):
            ref_id = f"REF_{random.randint(10**9, 10**10-1)}"
            tx_type = random.choice(TX_TYPES)
            amount = round(random.uniform(10, 5000), 2)
            ts = random_date(datetime(2024, 1, 1), datetime(2024, 6, 17))
            
            if tx_type == 'TRANSFER':
                # Double Entry
                counterparty = random.choice([a for a in account_list if a != acc_num])
                
                # Row 1 (This Account)
                transactions.append({
                    'transaction_id': f"TXN_{tx_id_pool}",
                    'reference_id': ref_id,
                    'account_number': acc_num,
                    'counterparty_account_number': counterparty,
                    'transaction_type': 'TRANSFER',
                    'currency': 'INR',
                    'direction': 'DEBIT',
                    'amount': amount,
                    'merchant_name': None,
                    'category': 'BANKING',
                    'description': f"Transfer to {counterparty}",
                    'transaction_timestamp': ts
                })
                tx_id_pool += 1
                
                # Row 2 (Counterparty)
                transactions.append({
                    'transaction_id': f"TXN_{tx_id_pool}",
                    'reference_id': ref_id,
                    'account_number': counterparty,
                    'counterparty_account_number': acc_num,
                    'transaction_type': 'TRANSFER',
                    'currency': 'INR',
                    'direction': 'CREDIT',
                    'amount': amount,
                    'merchant_name': None,
                    'category': 'BANKING',
                    'description': f"Transfer from {acc_num}",
                    'transaction_timestamp': ts
                })
                tx_id_pool += 1
            else:
                # Single Entry
                direction = 'CREDIT' if tx_type in ['SALARY_CREDIT', 'INTEREST_CREDIT', 'ATM_DEPOSIT', 'FD_MATURITY'] else 'DEBIT'
                
                # Align merchant and category based on transaction type
                if tx_type == 'CARD_PAYMENT':
                    merchant = random.choice(list(MERCHANT_CATEGORY_MAP.keys()))
                    category = MERCHANT_CATEGORY_MAP[merchant]
                elif tx_type == 'UPI':
                    # UPI can be merchant payment or P2P transfer
                    if random.random() < 0.75:
                        merchant = random.choice(list(MERCHANT_CATEGORY_MAP.keys()))
                        category = MERCHANT_CATEGORY_MAP[merchant]
                    else:
                        merchant = None
                        category = 'BANKING'
                elif tx_type == 'BILL_PAYMENT':
                    merchant = random.choice(UTILITY_MERCHANTS)
                    category = 'UTILITIES'
                elif tx_type == 'SALARY_CREDIT':
                    merchant = None
                    category = 'SALARY'
                elif tx_type == 'LOAN_EMI':
                    merchant = None
                    category = 'LOAN'
                elif tx_type in ['FD_DEPOSIT', 'FD_MATURITY']:
                    merchant = None
                    category = 'INVESTMENT'
                elif tx_type == 'INTEREST_CREDIT':
                    merchant = None
                    category = 'BANKING'
                elif tx_type in ['ATM_WITHDRAWAL', 'ATM_DEPOSIT']:
                    merchant = None
                    category = 'BANKING'
                else:
                    merchant = None
                    category = 'OTHER'
                
                desc = f"{tx_type} {f'at {merchant}' if merchant else ''}"
                if tx_type == 'UPI' and merchant is None:
                    desc = "UPI P2P Transfer"
                
                transactions.append({
                    'transaction_id': f"TXN_{tx_id_pool}",
                    'reference_id': ref_id,
                    'account_number': acc_num,
                    'counterparty_account_number': None,
                    'transaction_type': tx_type,
                    'currency': 'INR',
                    'direction': direction,
                    'amount': amount,
                    'merchant_name': merchant,
                    'category': category,
                    'description': desc,
                    'transaction_timestamp': ts
                })
                tx_id_pool += 1
                
    if cards_df is not None and len(cards_df) > 0:
        active_cards = cards_df[cards_df['is_current'] == True]
        for _, card in active_cards.iterrows():
            num_tx = random.randint(20, 100)
            card_acc_num = card['card_account_number']
            
            for _ in range(num_tx):
                ref_id = f"REF_{random.randint(10**9, 10**10-1)}"
                ts = random_date(datetime(2024, 1, 1), datetime(2024, 6, 17))
                
                # 85% card spend (DEBIT), 15% payment of card bill (CREDIT)
                if random.random() < 0.85:
                    tx_type = 'CARD_PAYMENT'
                    direction = 'DEBIT'
                    amount = round(random.uniform(50, 10000), 2)
                    merchant = random.choice(list(MERCHANT_CATEGORY_MAP.keys()))
                    category = MERCHANT_CATEGORY_MAP[merchant]
                    desc = f"CARD_PAYMENT at {merchant}"
                else:
                    tx_type = 'BILL_PAYMENT'
                    direction = 'CREDIT'
                    amount = round(random.uniform(500, 20000), 2)
                    merchant = None
                    category = 'BANKING'
                    desc = f"Credit Card Bill Payment"
                
                transactions.append({
                    'transaction_id': f"TXN_{tx_id_pool}",
                    'reference_id': ref_id,
                    'account_number': card_acc_num,
                    'counterparty_account_number': None,
                    'transaction_type': tx_type,
                    'currency': 'INR',
                    'direction': direction,
                    'amount': amount,
                    'merchant_name': merchant,
                    'category': category,
                    'description': desc,
                    'transaction_timestamp': ts
                })
                tx_id_pool += 1
                
    return pd.DataFrame(transactions)

def generate_credit_scores(customers_df):
    scores = []
    current_customers = customers_df[customers_df['is_current'] == True]
    for _, customer in current_customers.iterrows():
        scores.append({
            'customer_id': customer['customer_id'],
            'score': random.randint(300, 850),
            'last_updated': date.today(),
            'bureau_source': random.choice(['EXPERIAN', 'EQUIFAX', 'TRANSUNION', 'CIBIL'])
        })
    return pd.DataFrame(scores)

# --- EXECUTION ---

def format_timestamps(df, columns):
    for col in columns:
        if col in df.columns:
            # Convert to datetime if not already, then format as string
            # This handles both datetime objects and None/NaN values
            df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%d %H:%M:%S')
            # Replace 'NaT' with None so it's empty in CSV
            df[col] = df[col].replace('NaT', None)
    return df

print("🚀 Starting enhanced data generation...")

print("Generating Customers (SCD Type 2) & Identity Mapping...")
customers_df, identity_df = generate_customers_scd()

print("Generating Accounts (SCD Type 2)...")
accounts_df = generate_accounts_scd(customers_df)

print("Generating Credit Cards (SCD Type 2)...")
cards_df = generate_credit_cards_scd(customers_df)

print("Generating Beneficiaries...")
beneficiaries_df = generate_beneficiaries(customers_df)

print("Generating Loans...")
loans_df = generate_loans(customers_df)

print("Generating Fixed Deposits...")
fds_df = generate_fds(customers_df)

print("Generating Transactions (Ledger Model)...")
transactions_df = generate_transactions(accounts_df, cards_df)

print("Generating Credit Scores...")
scores_df = generate_credit_scores(customers_df)

# Format TIMESTAMP columns for BigQuery
print("Formatting timestamps for BigQuery...")
customers_df = format_timestamps(customers_df, ['eff_start_ts', 'eff_end_ts'])
identity_df = format_timestamps(identity_df, ['linked_at'])
accounts_df = format_timestamps(accounts_df, ['eff_start_ts', 'eff_end_ts'])
cards_df = format_timestamps(cards_df, ['eff_start_ts', 'eff_end_ts'])
beneficiaries_df = format_timestamps(beneficiaries_df, ['created_at'])
transactions_df = format_timestamps(transactions_df, ['transaction_timestamp'])

# Save to CSV
print(f"\n💾 Saving data to {DATA_DIR}...")
customers_df.to_csv(f'{DATA_DIR}/customers.csv', index=False)
identity_df.to_csv(f'{DATA_DIR}/customer_identity_mapping.csv', index=False)
accounts_df.to_csv(f'{DATA_DIR}/accounts.csv', index=False)
cards_df.to_csv(f'{DATA_DIR}/credit_cards.csv', index=False)
beneficiaries_df.to_csv(f'{DATA_DIR}/beneficiaries.csv', index=False)
loans_df.to_csv(f'{DATA_DIR}/loans.csv', index=False)
fds_df.to_csv(f'{DATA_DIR}/fixed_deposits.csv', index=False)
transactions_df.to_csv(f'{DATA_DIR}/transactions.csv', index=False)
scores_df.to_csv(f'{DATA_DIR}/credit_scores.csv', index=False)

print("\n✅ Data generation complete!")
print(f"Total Transactions: {len(transactions_df)}")
print(f"Total Customers (Versions): {len(customers_df)}")

import csv
import os
import random
from datetime import datetime, timedelta
import numpy as np

# Seed for reproducibility
random.seed(42)
np.random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)

CITIES_STATE = [
    ("Mumbai", "Maharashtra"),
    ("Bengaluru", "Karnataka"),
    ("Delhi NCR", "Delhi"),
    ("Pune", "Maharashtra"),
    ("Hyderabad", "Telangana"),
    ("Chennai", "Tamil Nadu"),
    ("Kolkata", "West Bengal"),
    ("Ahmedabad", "Gujarat"),
    ("Jaipur", "Rajasthan"),
]

CATEGORIES = [
    "Grocery",
    "Restaurants",
    "Electronics",
    "Fashion",
    "Pharmacy",
    "Bill Payment",
    "Fuel",
    "Retail"
]

CATEGORY_AMOUNT_RANGES = {
    "Grocery": (50, 2500),
    "Restaurants": (100, 3500),
    "Electronics": (1500, 45000),
    "Fashion": (400, 8000),
    "Pharmacy": (80, 1800),
    "Bill Payment": (200, 5000),
    "Fuel": (100, 4000),
    "Retail": (150, 5000)
}

PAYMENT_TYPES = ["UPI", "CREDIT_CARD", "DEBIT_CARD", "WALLET", "NET_BANKING"]
PAYMENT_TYPE_WEIGHTS = [0.65, 0.15, 0.10, 0.06, 0.04]

FAILURE_REASONS = [
    "BANK_SERVER_DOWN",
    "INSUFFICIENT_FUNDS",
    "NETWORK_TIMEOUT",
    "WRONG_PIN",
    "LIMIT_EXCEEDED"
]

NAME_PREFIXES = ["Sri", "New", "Royal", "Apex", "City", "Global", "Metro", "Prime", "Star", "Urban", "Super", "Golden", "Express", "Vibrant"]
NAME_SUFFIXES = ["Store", "Enterprises", "Mart", "Traders", "Emporium", "Hub", "Zone", "Point", "Outlet", "Corner", "Bazaar", "World"]

COHORTS = ["HIGH_GROWTH", "HEALTHY", "STABLE", "DECLINING", "AT_RISK", "NEW_GROWTH"]
COHORT_WEIGHTS = [0.15, 0.30, 0.25, 0.15, 0.10, 0.05]

START_DATE = datetime(2025, 8, 1)
END_DATE = datetime(2026, 8, 15)
TOTAL_DAYS = (END_DATE - START_DATE).days

def generate_merchant_name(category, idx):
    prefix = random.choice(NAME_PREFIXES)
    suffix = random.choice(NAME_SUFFIXES)
    return f"{prefix} {category} {suffix} #{idx+1}"

def generate_merchants(num_merchants=500):
    merchants = []
    for i in range(num_merchants):
        m_id = f"MCH{i+1:04d}"
        city, state = random.choice(CITIES_STATE)
        category = random.choice(CATEGORIES)
        name = generate_merchant_name(category, i)
        cohort = random.choices(COHORTS, weights=COHORT_WEIGHTS)[0]
        
        # Onboarding date based on cohort
        if cohort == "NEW_GROWTH":
            days_ago = random.randint(10, 55)
            onboard_date = END_DATE - timedelta(days=days_ago)
        else:
            days_ago = random.randint(180, 360)
            onboard_date = START_DATE + timedelta(days=random.randint(0, 90))
            
        merchants.append({
            "merchant_id": m_id,
            "merchant_name": name,
            "merchant_category": category,
            "city": city,
            "state": state,
            "onboarding_date": onboard_date.strftime("%Y-%m-%d"),
            "cohort": cohort
        })
    return merchants

def generate_users(num_users=5000):
    users = []
    device_types = ["Android", "iOS", "Web"]
    device_weights = [0.72, 0.23, 0.05]
    
    for i in range(num_users):
        u_id = f"USR{i+1:05d}"
        city, _ = random.choice(CITIES_STATE)
        device = random.choices(device_types, weights=device_weights)[0]
        signup_offset = random.randint(0, TOTAL_DAYS - 30)
        signup_date = START_DATE + timedelta(days=signup_offset)
        
        users.append({
            "user_id": u_id,
            "city": city,
            "device_type": device,
            "signup_date": signup_date.strftime("%Y-%m-%d")
        })
    return users

def generate_transactions(merchants, users, target_txns=75000):
    transactions = []
    txn_count = 0
    
    user_ids = [u["user_id"] for u in users]
    
    # Calculate txn targets per merchant based on cohort
    merchant_profiles = []
    for m in merchants:
        cohort = m["cohort"]
        m_id = m["merchant_id"]
        category = m["merchant_category"]
        onboard_dt = datetime.strptime(m["onboarding_date"], "%Y-%m-%d")
        
        if cohort == "HIGH_GROWTH":
            base_daily = random.uniform(0.5, 1.5)
            growth_factor = random.uniform(3.0, 5.0) # volume multiplies by 3-5x
            fail_prob = 0.03
        elif cohort == "HEALTHY":
            base_daily = random.uniform(2.5, 5.0)
            growth_factor = random.uniform(1.0, 1.2)
            fail_prob = 0.02
        elif cohort == "STABLE":
            base_daily = random.uniform(1.2, 2.5)
            growth_factor = random.uniform(0.9, 1.1)
            fail_prob = 0.04
        elif cohort == "DECLINING":
            base_daily = random.uniform(3.5, 6.0)
            growth_factor = random.uniform(0.15, 0.35) # drops by 65-85%
            fail_prob = 0.07
        elif cohort == "AT_RISK":
            base_daily = random.uniform(1.0, 3.0)
            growth_factor = random.uniform(0.3, 0.6)
            fail_prob = random.uniform(0.18, 0.32) # High failure rate!
        elif cohort == "NEW_GROWTH":
            base_daily = random.uniform(2.0, 6.0)
            growth_factor = random.uniform(2.0, 4.0)
            fail_prob = 0.03
            
        merchant_profiles.append({
            "merchant_id": m_id,
            "category": category,
            "onboard_dt": onboard_dt,
            "cohort": cohort,
            "base_daily": base_daily,
            "growth_factor": growth_factor,
            "fail_prob": fail_prob
        })

    # Generate transactions day by day
    current_date = START_DATE
    while current_date <= END_DATE:
        day_progress = (current_date - START_DATE).days / TOTAL_DAYS
        is_recent_period = (END_DATE - current_date).days <= 45
        
        for mp in merchant_profiles:
            if current_date < mp["onboard_dt"]:
                continue
                
            # If AT_RISK and recent, some merchants have total inactivity
            if mp["cohort"] == "AT_RISK" and is_recent_period and random.random() < 0.40:
                continue # skip generating txns to simulate drop in recency
                
            # Interpolate daily count based on growth factor
            if mp["cohort"] == "HIGH_GROWTH" or mp["cohort"] == "NEW_GROWTH":
                daily_rate = mp["base_daily"] * (1 + (mp["growth_factor"] - 1) * day_progress)
            elif mp["cohort"] == "DECLINING":
                daily_rate = mp["base_daily"] * (1 - (1 - mp["growth_factor"]) * day_progress)
            else:
                daily_rate = mp["base_daily"] * (1 + (mp["growth_factor"] - 1) * (day_progress - 0.5))
                
            # Add day-of-week seasonality (weekend spike)
            if current_date.weekday() in (5, 6):
                daily_rate *= 1.25
                
            num_txns_today = np.random.poisson(max(0.1, daily_rate))
            
            for _ in range(num_txns_today):
                txn_count += 1
                t_id = f"TXN{txn_count:08d}"
                u_id = random.choice(user_ids)
                
                # Timestamp random offset in day
                seconds_offset = random.randint(0, 86399)
                txn_datetime = current_date + timedelta(seconds=seconds_offset)
                
                # Amount calculation
                min_amt, max_amt = CATEGORY_AMOUNT_RANGES[mp["category"]]
                # Log-normal distribution for amounts
                amt = round(float(np.random.uniform(min_amt, max_amt)), 2)
                
                # Status & failure reason
                if random.random() < mp["fail_prob"]:
                    status = "FAILED"
                    fail_reason = random.choice(FAILURE_REASONS)
                else:
                    if random.random() < 0.01:
                        status = "PENDING"
                        fail_reason = "NONE"
                    else:
                        status = "SUCCESS"
                        fail_reason = "NONE"
                        
                pay_type = random.choices(PAYMENT_TYPES, weights=PAYMENT_TYPE_WEIGHTS)[0]
                
                transactions.append({
                    "transaction_id": t_id,
                    "merchant_id": mp["merchant_id"],
                    "user_id": u_id,
                    "transaction_date": txn_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    "transaction_amount": amt,
                    "transaction_status": status,
                    "payment_type": pay_type,
                    "failure_reason": fail_reason
                })
                
        current_date += timedelta(days=1)
        
    print(f"Generated total {len(transactions)} transactions.")
    return transactions

def main():
    print("Generating synthetic digital payment dataset...")
    
    merchants = generate_merchants(500)
    users = generate_users(5000)
    transactions = generate_transactions(merchants, users)
    
    # Save merchants (exclude internal cohort key from final CSV)
    merchant_csv_path = os.path.join(DATA_DIR, "merchants.csv")
    with open(merchant_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["merchant_id", "merchant_name", "merchant_category", "city", "state", "onboarding_date"])
        writer.writeheader()
        for m in merchants:
            writer.writerow({k: v for k, v in m.items() if k != "cohort"})
            
    # Save users
    user_csv_path = os.path.join(DATA_DIR, "users.csv")
    with open(user_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["user_id", "city", "device_type", "signup_date"])
        writer.writeheader()
        writer.writerows(users)
        
    # Save transactions
    transaction_csv_path = os.path.join(DATA_DIR, "transactions.csv")
    with open(transaction_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "transaction_id", "merchant_id", "user_id", "transaction_date",
            "transaction_amount", "transaction_status", "payment_type", "failure_reason"
        ])
        writer.writeheader()
        writer.writerows(transactions)
        
    print("Dataset generation complete!")
    print(f"- Merchants: {len(merchants)} -> {merchant_csv_path}")
    print(f"- Users: {len(users)} -> {user_csv_path}")
    print(f"- Transactions: {len(transactions)} -> {transaction_csv_path}")

if __name__ == "__main__":
    main()

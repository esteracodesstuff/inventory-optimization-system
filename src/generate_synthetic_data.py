import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Set seed for reproducibility (crucial for scientific projects!)
np.random.seed(42)

# --- Configuration ---
NUM_SKUS = 500
NUM_WAREHOUSES = 3
NUM_SUPPLIERS = 10
DAYS_OF_HISTORY = 730 # 2 years of daily data

# --- 1. Generate Warehouses ---
warehouses = pd.DataFrame({
    'warehouse_id': [f'WH-{i:03d}' for i in range(1, NUM_WAREHOUSES + 1)],
    'location': ['New York, NY', 'Los Angeles, CA', 'Chicago, IL'],
    'capacity_units': np.random.randint(50000, 200000, NUM_WAREHOUSES),
    'operating_cost_daily': np.random.uniform(1000, 5000, NUM_WAREHOUSES).round(2)
})

# --- 2. Generate Suppliers ---
suppliers = pd.DataFrame({
    'supplier_id': [f'SUP-{i:03d}' for i in range(1, NUM_SUPPLIERS + 1)],
    'name': [f'Supplier_{chr(65+i)}' for i in range(NUM_SUPPLIERS)],
    'lead_time_mean_days': np.random.uniform(3, 15, NUM_SUPPLIERS).round(1),
    'lead_time_std_days': np.random.uniform(0.5, 3, NUM_SUPPLIERS).round(1),
    'reliability_score': np.random.uniform(0.85, 0.99, NUM_SUPPLIERS).round(3)
})

# --- 3. Generate SKUs ---
# We use a log-normal distribution for unit costs to simulate real-world pricing 
# (many cheap items, few expensive - Pareto principle)
unit_costs = np.random.lognormal(mean=2.5, sigma=1.0, size=NUM_SKUS).round(2)
holding_costs = (unit_costs * 0.20 / 365).round(4) # ~20% annual holding cost

# ABC Classification based on value
abc_class = pd.cut(unit_costs, bins=[0, 10, 50, np.inf], labels=['C', 'B', 'A'])

skus = pd.DataFrame({
    'sku_id': [f'SKU-{i:05d}' for i in range(1, NUM_SKUS + 1)],
    'description': [f'Product_{i}' for i in range(1, NUM_SKUS + 1)],
    'category': np.random.choice(['Electronics', 'Apparel', 'Home Goods', 'Groceries'], NUM_SKUS),
    'unit_cost': unit_costs,
    'holding_cost_daily': holding_costs,
    'abc_class': abc_class,
    'supplier_id': np.random.choice(suppliers['supplier_id'], NUM_SKUS)
})

# --- 4. Generate Demand History (The Stochastic Part) ---
# We will generate daily demand for each SKU. 
# To make it realistic, we'll use a Poisson distribution for discrete items, 
# adding a weekly seasonality factor.

dates = [datetime(2024, 10, 6) - timedelta(days=i) for i in range(DAYS_OF_HISTORY)]
dates.reverse()

demand_records = []

for _, sku in skus.iterrows():
    # Base demand rate depends on ABC class
    if sku['abc_class'] == 'A':
        base_demand = np.random.uniform(50, 200)
    elif sku['abc_class'] == 'B':
        base_demand = np.random.uniform(10, 50)
    else:
        base_demand = np.random.uniform(1, 10)
        
    for date in dates:
        # Add weekly seasonality (e.g., higher demand on weekends)
        day_of_week = date.weekday()
        seasonality_factor = 1.2 if day_of_week >= 5 else 1.0
        
        # Add slight trend and random noise
        trend = 1 + (DAYS_OF_HISTORY - dates.index(date)) * 0.0001 # Very slight upward trend
        
        # Generate demand (Poisson for discrete items)
        lambda_param = base_demand * seasonality_factor * trend
        daily_demand = np.random.poisson(lambda_param)
        
        demand_records.append({
            'date': date,
            'sku_id': sku['sku_id'],
            'quantity': daily_demand,
            'is_weekend': 1 if day_of_week >= 5 else 0
        })

demand_df = pd.DataFrame(demand_records)

# --- 5. Save to CSV ---
print("Saving synthetic data to data/synthetic/...")
skus.to_csv('data/synthetic/skus.csv', index=False)
warehouses.to_csv('data/synthetic/warehouses.csv', index=False)
suppliers.to_csv('data/synthetic/suppliers.csv', index=False)
demand_df.to_csv('data/synthetic/demand_history.csv', index=False)

print(f"Generated {len(skus)} SKUs, {len(warehouses)} Warehouses, {len(suppliers)} Suppliers.")
print(f"Generated {len(demand_df)} daily demand records.")
print("Done!")
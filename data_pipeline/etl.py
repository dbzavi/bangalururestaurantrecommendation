import os
import pandas as pd
from datasets import load_dataset
from sqlalchemy import create_engine
import re

# Database connection settings (Using SQLite for local development)
DB_PATH = os.path.join(os.getcwd(), 'zomato.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"

def clean_cost(cost_str):
    if pd.isna(cost_str):
        return None
    # Remove commas and non-numeric characters except for digits
    cleaned = re.sub(r'[^\d]', '', str(cost_str))
    if cleaned:
        return int(cleaned)
    return None

def clean_rate(rate_str):
    if pd.isna(rate_str) or rate_str == 'NEW' or rate_str == '-':
        return 0.0
    # Extract the numeric part before '/5'
    cleaned = str(rate_str).split('/')[0].strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def run_etl():
    print("Loading dataset from Hugging Face...")
    ds = load_dataset('ManikaSaini/zomato-restaurant-recommendation')
    df = ds['train'].to_pandas()
    print(f"Loaded {len(df)} records. Starting data cleaning...")

    # Data Cleaning & Transformation
    
    # 1. Handle missing values
    df['approx_cost(for two people)'] = df['approx_cost(for two people)'].apply(clean_cost)
    df['rate'] = df['rate'].apply(clean_rate)
    
    # Fill remaining missing numericals with 0
    df['approx_cost(for two people)'] = df['approx_cost(for two people)'].fillna(0)
    df['votes'] = df['votes'].fillna(0)

    # 2. Handle missing categorical values
    df['cuisines'] = df['cuisines'].fillna("Unknown")
    df['rest_type'] = df['rest_type'].fillna("Unknown")
    df['dish_liked'] = df['dish_liked'].fillna("None")

    # 3. Rename columns for easier access
    df.rename(columns={
        'approx_cost(for two people)': 'cost_for_two',
        'listed_in(type)': 'listed_type',
        'listed_in(city)': 'listed_city',
        'url': 'zomato_url'
    }, inplace=True)

    # Drop massive columns not needed for AI inference to shrink DB
    df.drop(columns=['reviews_list', 'menu_item'], inplace=True, errors='ignore')

    # 4. Standardize text fields (lowercase tags)
    df['cuisines'] = df['cuisines'].astype(str).str.lower()
    
    # Optional: Deduplicate (using zomato_url which should be unique if scraped well)
    df.drop_duplicates(subset=['zomato_url'], inplace=True)
    
    print(f"Cleaned data successfully. {len(df)} records remaining.")
    
    # Load into SQLite
    print("Connecting to SQLite database...")
    engine = create_engine(DATABASE_URL)
    
    print("Inserting data into database (this may take a minute)...")
    # Using chunksize to avoid memory issues and if_exists='replace' for initial setup
    df.to_sql('restaurants', engine, if_exists='replace', index=False, chunksize=2000)
    print(f"ETL complete! Data inserted into 'restaurants' table in {DB_PATH}")

if __name__ == "__main__":
    run_etl()

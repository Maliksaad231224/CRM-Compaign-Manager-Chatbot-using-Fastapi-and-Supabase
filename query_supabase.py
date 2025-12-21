import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TABLE_NAME = "term_deposit_campaigns"  # replace with your table name

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def query_table():
    try:
        response = supabase.table(TABLE_NAME).select("*").execute()
        data = response.data
        if data:
            print(f"✅ Retrieved {len(data)} rows from {TABLE_NAME}")
            # Optional: save to file
            import json
            with open("supabase_data.json", "w") as f:
                json.dump(data, f, indent=4)
            print("✅ Data saved to supabase_data.json")
        else:
            print("⚠️ No data found in the table")
    except Exception as e:
        print(f"❌ Error querying Supabase: {e}")

if __name__ == "__main__":
    query_table()

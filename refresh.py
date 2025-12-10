from supabase import create_client, Client
import os


SUPABASE_URL="https://ahvzujttyrpwqefxbhkf.supabase.co"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFodnp1anR0eXJwd3FlZnhiaGtmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUyODI4NzEsImV4cCI6MjA4MDg1ODg3MX0.g6tnAtt1kD1-YlohgjnHlg-lUyIpo9ltTOR92afdUrA"
url: str =SUPABASE_URL
key: str =SUPABASE_KEY
supabase: Client = create_client(url, key)
table_name = "term_deposit_campaigns"

rows = supabase.table(table_name).select("*").execute().data

print(rows)

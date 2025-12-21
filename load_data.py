import pandas as pd
df = pd.read_csv('client_leads_cleaned.csv')
df.dropna(subset=['email','company','website'], inplace=True)
print(df.shape)
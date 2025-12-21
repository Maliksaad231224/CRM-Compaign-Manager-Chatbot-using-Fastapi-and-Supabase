import pandas as pd
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
import os

load_dotenv()

PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
index_name = 'crm-chatbot'

pc = Pinecone(api_key=PINECONE_API_KEY)

# Load embeddings
embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def load_csv_structured(csv_path):
    df = pd.read_csv(csv_path)
    docs = []

    for _, row in df.iterrows():
        content = f"""
Lead from {row['company']} located in {row['location']}.
Client company: {row['client_company_name']}
Status: {row['status']} | Milestone: {row['milestone']}

Enriched Info:
{row['enriched_info']}

Notes:
{row['notes']}
"""

        metadata = {
            "id": str(row["id"]) if pd.notna(row["id"]) else "",
            "first_name": row["first_name"] if pd.notna(row["first_name"]) else "",
            "last_name": row["last_name"] if pd.notna(row["last_name"]) else "",
            "email": row["email"] if pd.notna(row["email"]) else "",
            "company": row["company"] if pd.notna(row["company"]) else "",
            "website": row["website"] if pd.notna(row["website"]) else "",
            "status": row["status"] if pd.notna(row["status"]) else "",
            "milestone": row["milestone"] if pd.notna(row["milestone"]) else "",
            "owner": row["owner"] if pd.notna(row["owner"]) else "",
            "location": row["location"] if pd.notna(row["location"]) else "",
            "last_contact_date": str(row["last_contact_date"]) if pd.notna(row["last_contact_date"]) else "",
            "follow_up_date": str(row["follow_up_date"]) if pd.notna(row["follow_up_date"]) else "",
            "client_company_name": row["client_company_name"] if pd.notna(row["client_company_name"]) else "",
        }

        docs.append(Document(page_content=content, metadata=metadata))

    return docs

# Load data
extracted = load_csv_structured(r'D:\University\knowledge representation\CRM Chatbot\client_leads_cleaned.csv')

# Split text
text_splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=20)
test_chunks = text_splitter.split_documents(extracted)

print(f"Loaded {len(test_chunks)} chunks")

# Create vector store
docsearch = PineconeVectorStore.from_documents(
    documents=test_chunks,
    embedding=embedding,
    index_name=index_name,
    namespace='leads-v1'
)

print("Data loaded into Pinecone successfully!")
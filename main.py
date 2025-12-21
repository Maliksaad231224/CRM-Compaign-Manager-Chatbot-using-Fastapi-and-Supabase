from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
from dotenv import load_dotenv
from openai import OpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_pinecone import PineconeVectorStore
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import os
from langchain_community.embeddings import HuggingFaceEmbeddings
import ast
import numpy as np
import openai
import json
from openai import OpenAI
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
import asyncio
from langchain_pinecone import PineconeVectorStore

app = FastAPI(title="Lead CRM API", version="1.0.0")
load_dotenv()
index_name='crm-chatbot'

# Initialize Pinecone
PINECONE_API_KEY=os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
os.environ['PINECONE_API_KEY'] = PINECONE_API_KEY
# Load sentence transformer model
embedding = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
    
vectorstore = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embedding,
        
       
    )

print('✅ Model loaded successfully')

def query_rag(query, top_k=10):
    """
    Query RAG using Pinecone vector similarity search
    """
    try:
        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": top_k})
        
        # Get relevant documents
        docs = retriever.invoke(query)
        
        # Extract content from documents
        results = [doc.page_content for doc in docs]
        
        return results
        
    except Exception as e:
        print(f"❌ Error in query_rag: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Data Models
class Message(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime

class ChatMessage(BaseModel):
    message: str
    chat_id: Optional[str] = None
    timestamp: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    chat_id: str
    timestamp: datetime

class ChatSession(BaseModel):
    id: str
    title: str
    messages: List[Message]
    created_at: datetime
    updated_at: datetime

chat_sessions = {}

# API Endpoints

@app.get("/")
async def read_root():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")

@app.post("/api/chat/new")
async def create_new_chat():

    chat_id = str(uuid.uuid4())
    chat_sessions[chat_id] = {
        "id": chat_id,
        "title": f"Chat {len(chat_sessions) + 1}",
        "messages": [],
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    return {"chat_id": chat_id, "message": "New chat created"}

@app.post("/api/chat", response_model=ChatResponse)
async def send_message(chat_message: ChatMessage):
 
    # Create new chat if chat_id not provided
    if not chat_message.chat_id or chat_message.chat_id not in chat_sessions:
        chat_id = str(uuid.uuid4())
        chat_sessions[chat_id] = {
            "id": chat_id,
            "title": chat_message.message[:50],
            "messages": [],
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    else:
        chat_id = chat_message.chat_id
    
    # Store user message
    user_message = {
        "role": "user",
        "content": chat_message.message,
        "timestamp": datetime.now()
    }
    chat_sessions[chat_id]["messages"].append(user_message)
    
    # Initialize OpenAI client
    client = openai.OpenAI(
        base_url="https://api.llm7.io/v1",
        api_key="unused"  # Or get it for free at https://token.llm7.io/ for higher rate limits.
    )
    
    query = chat_message.message
    top_rows = query_rag(query, top_k=5)

    context = "\n".join([str(r) for r in top_rows])

    prompt = f"""
You are an expert CRM data analyst with deep knowledge of customer relationship management, sales patterns, and business intelligence. Your role is to analyze customer data, identify trends, and provide actionable insights.

IMPORTANT INSTRUCTIONS:
1. Answer using the information provided in the "Retrieved Data" below as your primary source
2. ANALYZE and REASON about the data - don't just list records
3. Identify patterns, trends, correlations, and insights from the data
4. Provide business intelligence and actionable recommendations
5. Compare and contrast different records when relevant
6. Calculate metrics, percentages, or aggregations when appropriate
7. Explain WHY certain patterns exist and WHAT they mean for business decisions
8. Suggest next steps or strategies based on the data analysis
9. Use markdown tables for structured data presentation
10. For visualizations, use chart format: [CHART:type|labels:label1,label2|data:value1,value2] where type can be bar, line, pie, etc.
11. If the data is insufficient, clearly state what's needed for better analysis
12. Be specific with numbers, dates, and concrete details from the data

### Retrieved Data:
{context}

### User Question:
{query}

### Analysis & Reasoning:
Provide a comprehensive analysis of the data, including:
- Key insights and patterns identified
- Business implications and recommendations
- Any calculations or metrics derived from the data
- Strategic suggestions based on your analysis

### Answer:
"""

    response = client.chat.completions.create(
        model='default',
        messages=[{"role": "user", "content": prompt}]
    )
    
    ai_response = response.choices[0].message.content
    
    # Store assistant message
    assistant_message = {
        "role": "assistant",
        "content": ai_response,
        "timestamp": datetime.now()
    }
    chat_sessions[chat_id]["messages"].append(assistant_message)
    chat_sessions[chat_id]["updated_at"] = datetime.now()
    
    return ChatResponse(
        response=ai_response,
        chat_id=chat_id,
        timestamp=datetime.now()
    )

@app.post("/api/chat/stream")
async def send_message_stream(chat_message: ChatMessage):
    """
    Send a message and get streaming AI response
    
    Args:
        chat_message: User message and optional chat_id
        
    Returns:
        StreamingResponse: Server-Sent Events stream of AI response
    """
    # Create new chat if chat_id not provided
    if not chat_message.chat_id or chat_message.chat_id not in chat_sessions:
        chat_id = str(uuid.uuid4())
        chat_sessions[chat_id] = {
            "id": chat_id,
            "title": chat_message.message[:50],
            "messages": [],
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    else:
        chat_id = chat_message.chat_id
    
    # Store user message
    user_message = {
        "role": "user",
        "content": chat_message.message,
        "timestamp": datetime.now()
    }
    chat_sessions[chat_id]["messages"].append(user_message)
    
    async def generate():
        try:
            # Initialize OpenAI client
            client = openai.OpenAI(
                base_url="https://api.llm7.io/v1",
                api_key="unused"
            )
            
            query = chat_message.message
        
            print(f"🔍 Searching for: {query}")
            top_rows = query_rag(query, top_k=5)
            
            if not top_rows:
                error_msg = "I couldn't find any relevant data to answer your question. Please try rephrasing or ask about different data."
                yield f"data: {json.dumps({'chat_id': chat_id, 'type': 'start'})}\n\n"
                yield f"data: {json.dumps({'content': error_msg, 'type': 'chunk'})}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'chat_id': chat_id})}\n\n"
                return
            
            context = "\n".join([str(r) for r in top_rows])
            print(f"✅ Retrieved {len(top_rows)} relevant records")
            
            prompt = f"""
You are an expert CRM data analyst with deep knowledge of customer relationship management, sales patterns, and business intelligence. Your role is to analyze customer data, identify trends, and provide actionable insights.

IMPORTANT INSTRUCTIONS:
1. Answer using the information provided in the "Retrieved Data" below as your primary source
2. ANALYZE and REASON about the data - don't just list records
3. Identify patterns, trends, correlations, and insights from the data
4. Provide business intelligence and actionable recommendations
5. Compare and contrast different records when relevant
6. Calculate metrics, percentages, or aggregations when appropriate
7. Explain WHY certain patterns exist and WHAT they mean for business decisions
8. Suggest next steps or strategies based on the data analysis
9. Use markdown tables for structured data presentation
10. For visualizations, use chart format: [CHART:type|labels:label1,label2|data:value1,value2] where type can be bar, line, pie, etc.
11. If the data is insufficient, clearly state what's needed for better analysis
12. Be specific with numbers, dates, and concrete details from the data

### Retrieved Data:
{context}

### User Question:
{query}

### Analysis & Reasoning:
Provide a comprehensive analysis of the data, including:
- Key insights and patterns identified
- Business implications and recommendations
- Any calculations or metrics derived from the data
- Strategic suggestions based on your analysis

### Answer:
"""
            
            # Send chat_id first
            yield f"data: {json.dumps({'chat_id': chat_id, 'type': 'start'})}\n\n"
            
            # Stream the response
            full_response = ""
            stream = client.chat.completions.create(
                model='default',
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield f"data: {json.dumps({'content': content, 'type': 'chunk'})}\n\n"
                    await asyncio.sleep(0.01)  # Small delay for smoother streaming
            
            # Store complete assistant message
            assistant_message = {
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.now()
            }
            chat_sessions[chat_id]["messages"].append(assistant_message)
            chat_sessions[chat_id]["updated_at"] = datetime.now()
            
            # Send completion signal
            yield f"data: {json.dumps({'type': 'done', 'chat_id': chat_id})}\n\n"
            
        except Exception as e:
            print(f"❌ Error in streaming: {str(e)}")
            import traceback
            traceback.print_exc()
            error_message = f"I encountered an error: {str(e)}. Please try again or rephrase your question."
            yield f"data: {json.dumps({'type': 'error', 'error': error_message})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/api/chat/history")
async def get_chat_history():
    """
    Get all chat sessions
    
    Returns:
        dict: List of all chat sessions
    """
    chats = [
        {
            "id": chat["id"],
            "title": chat["title"],
            "created_at": chat["created_at"],
            "updated_at": chat["updated_at"],
            "message_count": len(chat["messages"])
        }
        for chat in chat_sessions.values()
    ]
    # Sort by most recent
    chats.sort(key=lambda x: x["updated_at"], reverse=True)
    return {"chats": chats}

@app.get("/api/chat/{chat_id}")
async def get_chat(chat_id: str):
    """
    Get specific chat session with all messages
    
    Args:
        chat_id: Chat session ID
        
    Returns:
        dict: Chat session with messages
    """
    if chat_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return chat_sessions[chat_id]


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        dict: API status
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "active_chats": len(chat_sessions)
    }

# Lifespan events for graceful startup/shutdown
@app.on_event("startup")
async def startup_event():
    print("🚀 Server started successfully!")
    print("📊 Using Pinecone vector search for embeddings")
    print("✅ Ready to accept requests")

@app.on_event("shutdown")
async def shutdown_event():
    print("\n👋 Shutting down gracefully...")
    print("✅ Server stopped")

if __name__ == "__main__":
    import uvicorn
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")

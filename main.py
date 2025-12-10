from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
from dotenv import load_dotenv
from supabase import create_client, Client
import os
from sentence_transformers import SentenceTransformer
import ast
import numpy as np
import openai
import json
import asyncio

app = FastAPI(title="Bank Advisor API", version="1.0.0")
load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
table_name = "term_deposit_campaigns"

rows = supabase.table(table_name).select("*").execute().data
model = SentenceTransformer("all-MiniLM-L6-v2")
print('model loaded')
embeddings = []
row_data = []

for row in rows:
    emb_str = row.get("embedding_vector")  # your column name
    if emb_str:
        # Convert string to list
        emb_list = ast.literal_eval(emb_str)
        embeddings.append(np.array(emb_list, dtype=np.float32))
        row_data.append(row)

# Now stack into a matrix
embeddings = np.vstack(embeddings)
print(embeddings.shape)

def cosine_similarity(a, b):
    a_norm = a / np.linalg.norm(a, axis=1, keepdims=True)
    b_norm = b / np.linalg.norm(b)
    return np.dot(a_norm, b_norm)
def query_rag(query, top_k=10):
    query_emb = model.encode(query)
    sims = cosine_similarity(embeddings, query_emb)  # shape: (num_rows,)
    top_idx = np.argsort(sims)[-top_k:][::-1]  # indices of top-k similar rows
    results = [row_data[i] for i in top_idx]
    return results

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
    """
    Create a new chat session
    
    Returns:
        dict: New chat session ID
    """
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
    """
    Send a message and get AI response
    
    Args:
        chat_message: User message and optional chat_id
        
    Returns:
        ChatResponse: AI response with chat_id and timestamp
        
    TODO: Replace this mock response with your actual AI model integration
    Examples:
    - Integrate with OpenAI API
    - Use local LLM (Ollama, LM Studio)
    - Connect to your RAG pipeline
    - Use Langchain for more complex workflows
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
    
    # Initialize OpenAI client
    client = openai.OpenAI(
        base_url="https://api.llm7.io/v1",
        api_key="unused"  # Or get it for free at https://token.llm7.io/ for higher rate limits.
    )
    
    query = chat_message.message
    top_rows = query_rag(query, top_k=10)

    context = "\n".join([str(r) for r in top_rows])

    prompt = f"""
You are a helpful AI banking assistant with expertise in analyzing customer data and financial patterns.

IMPORTANT INSTRUCTIONS:
1. Answer ONLY using the information provided in the "Retrieved Data" below
2. If the data doesn't contain enough information to answer fully, clearly state what's missing
3. Do NOT make assumptions or use outside knowledge
4. Provide specific details from the data (numbers, names, amounts, etc.)
5. If comparing or analyzing multiple records, structure your answer clearly
6. Be concise but thorough in your explanations
7. When relevant, explain patterns or insights you notice in the data

### Retrieved Data:
{context}

### User Question:
{query}

### Answer:
Let me analyze the data and provide a clear answer:
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
            top_rows = query_rag(query, top_k=10)
            context = "\n".join([str(r) for r in top_rows])
            
            prompt = f"""
You are a helpful AI banking assistant with expertise in analyzing customer data and financial patterns.

IMPORTANT INSTRUCTIONS:
1. Answer ONLY using the information provided in the "Retrieved Data" below
2. If the data doesn't contain enough information to answer fully, clearly state what's missing
3. Do NOT make assumptions or use outside knowledge
4. Provide specific details from the data (numbers, names, amounts, etc.)
5. If comparing or analyzing multiple records, structure your answer clearly
6. Be concise but thorough in your explanations
7. When relevant, explain patterns or insights you notice in the data

### Retrieved Data:
{context}

### User Question:
{query}

### Answer:
Let me analyze the data and provide a clear answer:
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
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
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

@app.delete("/api/chat/{chat_id}")
async def delete_chat(chat_id: str):
    """
    Delete a chat session
    
    Args:
        chat_id: Chat session ID
        
    Returns:
        dict: Confirmation message
    """
    if chat_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    del chat_sessions[chat_id]
    return {"message": "Chat deleted successfully"}

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
    print(f"📊 Loaded {len(embeddings)} embeddings")
    print("✅ Ready to accept requests")

@app.on_event("shutdown")
async def shutdown_event():
    print("\n👋 Shutting down gracefully...")
    print("✅ Server stopped")

if __name__ == "__main__":
    import uvicorn
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")

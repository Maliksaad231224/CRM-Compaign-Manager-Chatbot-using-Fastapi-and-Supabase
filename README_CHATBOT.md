# AI Chatbot - Supabase Style UI

A modern, responsive chatbot interface with FastAPI backend, styled like Supabase with light and dark themes.

## Features

✨ **Modern UI**
- Supabase-inspired design
- Light and dark theme support
- Smooth animations and transitions
- Fully responsive (mobile, tablet, desktop)

🚀 **Functionality**
- Real-time chat interface
- Message history
- Multiple chat sessions
- Auto-resizing input
- Loading indicators
- Suggestion cards

🔧 **Backend (FastAPI)**
- RESTful API endpoints
- Chat session management
- Message storage (in-memory, ready for database)
- CORS enabled
- Well-documented endpoints

## Project Structure

```
.
├── static/
│   ├── index.html      # Main HTML file
│   ├── styles.css      # Supabase-style CSS
│   └── script.js       # Frontend logic
├── app.py              # FastAPI backend
├── requirements.txt    # Python dependencies
└── README_CHATBOT.md   # This file
```

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the server:**
```bash
python app.py
```

3. **Open in browser:**
```
http://localhost:8000
```

## API Endpoints

### Chat Operations

- `POST /api/chat/new` - Create new chat session
- `POST /api/chat` - Send message and get response
- `GET /api/chat/history` - Get all chat sessions
- `GET /api/chat/{chat_id}` - Get specific chat
- `DELETE /api/chat/{chat_id}` - Delete chat session
- `GET /api/health` - Health check

### Example API Usage

**Send a message:**
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "chat_id": null}'
```

**Get chat history:**
```bash
curl "http://localhost:8000/api/chat/history"
```

## Integrating Your Backend

The current implementation uses mock responses. Replace the AI logic in `app.py`:

### Option 1: OpenAI Integration
```python
from openai import OpenAI

client = OpenAI(api_key="your-key")
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": m["role"], "content": m["content"]} 
              for m in chat_sessions[chat_id]["messages"]]
)
ai_response = response.choices[0].message.content
```

### Option 2: Ollama (Local)
```python
from ollama import chat

response = chat(
    model="llama2", 
    messages=chat_sessions[chat_id]["messages"]
)
ai_response = response.message.content
```

### Option 3: Your RAG Pipeline
```python
# Use your existing RAG functions
from your_rag_module import query_rag, format_context

context = query_rag(chat_message.message)
ai_response = your_llm_function(context, chat_message.message)
```

## Customization

### Change Theme Colors

Edit CSS variables in `static/styles.css`:

```css
:root {
    --accent-primary: #3ecf8e;  /* Change primary color */
    --bg-primary: #ffffff;      /* Change background */
    /* ... more variables */
}
```

### Add New Features

- **Voice input:** Add Web Speech API
- **File uploads:** Extend FastAPI endpoints
- **Streaming responses:** Use SSE or WebSockets
- **User authentication:** Add JWT tokens
- **Database:** Replace in-memory storage with PostgreSQL/MongoDB

## Database Integration (Optional)

Replace in-memory storage with a database:

### PostgreSQL Example
```python
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(String, primary_key=True)
    title = Column(String)
    # ... add more fields
```

### Supabase Example
```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Store message
supabase.table("messages").insert({
    "chat_id": chat_id,
    "role": "user",
    "content": message
}).execute()
```

## Environment Variables

Create a `.env` file for configuration:

```env
# API Keys (if using external services)
OPENAI_API_KEY=your-key-here
SUPABASE_URL=your-url
SUPABASE_KEY=your-key

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

## Deployment

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "app.py"]
```

### Using Vercel/Railway/Render

1. Push code to GitHub
2. Connect repository to platform
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python app.py`

## Troubleshooting

**CORS errors:**
- Check CORS middleware in `app.py`
- Ensure frontend URL is allowed

**Styles not loading:**
- Verify static files are in `static/` folder
- Check browser console for 404 errors

**API not responding:**
- Check server is running on correct port
- Verify API_BASE_URL in `script.js`

## License

MIT License - Feel free to use and modify!

## Credits

- Design inspired by [Supabase](https://supabase.com)
- Built with FastAPI and vanilla JavaScript

from fastapi import FastAPI, Request, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import socketio
import uvicorn
from celery_worker import chat_task
import os
from dotenv import load_dotenv
from database import engine, Base, AsyncSessionLocal
from models import Document, DocumentChunk
from orchestrator import embed_text
import uuid

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB tables on startup
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        # Create extension if not exists requires raw sql execution, but we'll assume pgvector is enabled via docker
        await conn.run_sync(Base.metadata.create_all)

mgr = socketio.AsyncRedisManager(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*', client_manager=mgr)
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "NexusAI Cognitive Gateway"}

async def process_document(doc_id: str, file_path: str, user_id: str):
    """Background task to extract text and embed chunks."""
    try:
        # Simplistic text extraction for TXT files (For PDF use PyPDF2 or Unstructured in prod)
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        # Simple chunking logic
        chunk_size = 1000
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        async with AsyncSessionLocal() as session:
            for chunk_text in chunks:
                if not chunk_text.strip(): continue
                embedding = await embed_text(chunk_text)
                chunk = DocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=doc_id,
                    content=chunk_text,
                    embedding=embedding
                )
                session.add(chunk)
            await session.commit()
            print(f"Processed document {doc_id} into {len(chunks)} chunks.")
    except Exception as e:
        print(f"Error processing document: {e}")

@app.post("/api/documents/upload")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    user_id = "default_user" # Mock user
    doc_id = str(uuid.uuid4())
    
    # Save file temporarily
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{doc_id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
        
    async with AsyncSessionLocal() as session:
        doc = Document(id=doc_id, user_id=user_id, filename=file.filename, file_type=file.content_type)
        session.add(doc)
        await session.commit()
        
    background_tasks.add_task(process_document, doc_id, file_path, user_id)
    return {"message": "Document uploaded and processing started.", "document_id": doc_id}

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event
async def chat_message(sid, data):
    prompt = data.get("prompt")
    conversation_id = data.get("conversation_id")
    user_id = "default_user" # Mock auth
    
    if prompt:
        task = chat_task.delay(prompt, sid, user_id, conversation_id)
        await sio.emit("chat:queued", {"jobId": task.id}, to=sid)
    else:
        await sio.emit("chat:error", {"message": "Prompt is required"}, to=sid)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3001))
    uvicorn.run("main:socket_app", host="0.0.0.0", port=port, reload=True)

import os
import asyncio
from celery import Celery
import socketio
from gemini import generate_streaming_response
from orchestrator import orchestrate_chat, save_ai_response
from database import AsyncSessionLocal
from dotenv import load_dotenv

load_dotenv()

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("tasks", broker=redis_url, backend=redis_url)

mgr = socketio.RedisManager(redis_url, write_only=True)
sio = socketio.Server(client_manager=mgr)

async def async_chat_execution(prompt: str, sid: str, user_id: str, conversation_id: str = None):
    try:
        async with AsyncSessionLocal() as session:
            # 1. Orchestrate: Build Context & Save State
            final_prompt, conv_id, msg_id = await orchestrate_chat(session, user_id, prompt, conversation_id)
            
            # Emit conversation ID back to frontend if it's new
            sio.emit("chat:metadata", {"conversation_id": conv_id}, to=sid)
            
            # 2. Stream Inference
            full_response = ""
            for chunk in generate_streaming_response(final_prompt):
                full_response += chunk
                sio.emit("chat:token", chunk, to=sid)
                
            # 3. Save AI Response
            await save_ai_response(session, conv_id, full_response)
            
            sio.emit("chat:complete", {"jobId": chat_task.request.id, "conversation_id": conv_id}, to=sid)
    except Exception as e:
        print(f"Async task failed: {e}")
        sio.emit("chat:error", {"message": "Internal Server Error"}, to=sid)

@celery_app.task(name="chat_task")
def chat_task(prompt: str, sid: str, user_id: str = "default_user", conversation_id: str = None):
    print(f"Executing chat task for {sid}")
    # Run the async execution within the sync celery worker
    asyncio.run(async_chat_execution(prompt, sid, user_id, conversation_id))

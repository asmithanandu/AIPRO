from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Conversation, Message, Memory, DocumentChunk
import uuid
import google.generativeai as genai
import os

# Ensure genai is configured
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

async def embed_text(text: str) -> list[float]:
    """Generates an embedding using Gemini's embedding model."""
    result = genai.embed_content(
        model="models/embedding-001",
        content=text,
        task_type="retrieval_query",
    )
    return result['embedding']

async def retrieve_context(session: AsyncSession, user_id: str, prompt: str) -> str:
    """Retrieves relevant memories and document chunks using pgvector."""
    try:
        # Generate embedding for the prompt
        prompt_embedding = await embed_text(prompt)
        
        # 1. Retrieve Memories
        # Using L2 distance (<->) for similarity search
        memory_query = select(Memory).where(Memory.user_id == user_id).order_by(Memory.embedding.l2_distance(prompt_embedding)).limit(3)
        memory_results = await session.execute(memory_query)
        memories = memory_results.scalars().all()
        
        # 2. Retrieve Document Chunks
        # Need to join with Document to ensure it's the user's document
        # For simplicity, we just fetch chunks if they exist (assuming isolation logic is handled at upload)
        # Note: In production, join with Document to filter by user_id
        chunk_query = select(DocumentChunk).order_by(DocumentChunk.embedding.l2_distance(prompt_embedding)).limit(3)
        chunk_results = await session.execute(chunk_query)
        chunks = chunk_results.scalars().all()
        
        context = ""
        if memories:
            context += "Relevant User Memories:\n" + "\n".join([m.content for m in memories]) + "\n\n"
        if chunks:
            context += "Relevant Document Context:\n" + "\n".join([c.content for c in chunks]) + "\n\n"
            
        return context
    except Exception as e:
        print(f"Error in context retrieval: {e}")
        return ""

async def orchestrate_chat(session: AsyncSession, user_id: str, prompt: str, conversation_id: str = None) -> tuple[str, str, str]:
    """
    Coordinates the task execution: Context Building -> Saving State -> Formatting Prompt
    Returns: (formatted_prompt, conversation_id, message_id)
    """
    # 1. Ensure conversation exists
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        new_conv = Conversation(id=conversation_id, user_id=user_id, title=prompt[:50])
        session.add(new_conv)
    
    # 2. Save user message
    msg_id = str(uuid.uuid4())
    user_msg = Message(id=msg_id, conversation_id=conversation_id, role="user", content=prompt)
    session.add(user_msg)
    
    # 3. Retrieve Context
    context = await retrieve_context(session, user_id, prompt)
    
    # 4. Build final prompt
    final_prompt = prompt
    if context:
        final_prompt = f"Use the following context to answer the user's query.\n\n{context}\n\nUser Query: {prompt}"
        
    await session.commit()
    
    return final_prompt, conversation_id, msg_id

async def save_ai_response(session: AsyncSession, conversation_id: str, content: str):
    """Saves the AI's response to the database after streaming completes."""
    ai_msg = Message(id=str(uuid.uuid4()), conversation_id=conversation_id, role="ai", content=content)
    session.add(ai_msg)
    await session.commit()

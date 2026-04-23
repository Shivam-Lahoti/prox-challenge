import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.startup import get_agent, get_vector_store

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    message: str
    artifacts: list[dict] | None = None
    images: list[str] | None = None
    conversation_id: str


@router.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "agent": "Vulcan OmniPro 220",
        "version": "1.0.0"
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint"""
    try:
        agent = get_agent()
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        
        logger.info(f"Query: {request.message}")
        
        # Get agent response
        response = await agent.process_query(
            query=request.message,
            conversation_id=request.conversation_id
        )
        
        logger.info(f"Response generated")
        
        return ChatResponse(
            message=response["message"],
            artifacts=response.get("artifacts"),
            images=response.get("images"),
            conversation_id=response["conversation_id"]
        )
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    """Detailed health check"""
    agent = get_agent()
    vector_store = get_vector_store()
    
    return {
        "status": "healthy",
        "agent_ready": agent is not None,
        "vector_store_ready": vector_store is not None,
        "documents_indexed": len(vector_store.documents) if vector_store else 0
    }
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from agent.welding_agent import WeldingAgent
from knowledge.pdf_processor import PDFProcessor
from knowledge.vector_store import VectorStore
from knowledge.structured_extractor import StructuredExtractor

logger = logging.getLogger(__name__)

# Global instances
agent = None
vector_store = None


def get_agent():
    """Get the global agent instance"""
    return agent


def get_vector_store():
    """Get the global vector store instance"""
    return vector_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources with hybrid approach"""
    global agent, vector_store
    
    logger.info("Initializing Vulcan OmniPro 220 Agent (Hybrid System)...")
    
    # Step 1: Process PDFs for text chunks and images (RAG)
    logger.info("Processing manual PDFs...")
    pdf_processor = PDFProcessor(manuals_dir="../files")
    documents, images = pdf_processor.process_all()
    
    logger.info(f" Extracted {len(documents)} text chunks and {len(images)} images")
    
    # Step 2: Extract structured data using Vision API
    logger.info("Extracting structured data using Claude Vision...")
    extractor = StructuredExtractor(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    try:
        structured_data = extractor.extract_all_structured_data("../files/owner-manual.pdf")
        logger.info(f"Structured data extracted:")
        logger.info(f"   - Duty cycles: {len(structured_data.get('duty_cycles', {}))} processes")
        logger.info(f"   - Polarity configs: {len(structured_data.get('polarity', {}))} processes")
        logger.info(f"   - Troubleshooting: {sum(len(v) for v in structured_data.get('troubleshooting', {}).values())} issues")
        logger.info(f"   - Weld diagnosis: {len(structured_data.get('weld_diagnosis', {}).get('defects', []))} defect types")
    except Exception as e:
        logger.error(f"Failed to extract structured data: {e}")
        logger.info("Falling back to RAG-only mode")
        structured_data = {
            "duty_cycles": {},
            "polarity": {},
            "troubleshooting": {},
            "weld_diagnosis": {}
        }
    
    # Step 3: Build vector store (for flexible RAG queries)
    logger.info("Building vector search index...")
    vector_store = VectorStore()
    vector_store.add_documents(documents)
    
    logger.info(f"Indexed {len(documents)} document chunks")
    
    # Step 4: Initialize hybrid agent
    logger.info("Initializing hybrid agent...")
    agent = WeldingAgent(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        vector_store=vector_store,
        images=images,
        structured_data=structured_data
    )
    
    logger.info("Hybrid agent ready!")
    logger.info("Structured data: High-precision answers")
    logger.info("RAG system: Flexible context retrieval")
    
    yield
    
    logger.info("Shutting down...")
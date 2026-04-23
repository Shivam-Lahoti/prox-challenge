import os
import logging
import uuid
from typing import Dict, List, Optional
from anthropic import Anthropic
import json
from knowledge.vector_store import VectorStore
from agent.tools import AgentTools

logger = logging.getLogger(__name__)


class WeldingAgent:
    """Hybrid agent: Uses structured data for precision + RAG for flexibility"""
    
    def __init__(
        self, 
        api_key: str, 
        vector_store: VectorStore, 
        images: Dict[str, str],
        structured_data: Dict
    ):
        """
        Initialize the welding agent
        
        Args:
            api_key: Anthropic API key
            vector_store: Vector store for RAG
            images: Dict mapping image_id -> filepath
            structured_data: Pre-extracted tables/configs from Vision API
        """
        self.client = Anthropic(api_key=api_key)
        self.vector_store = vector_store
        self.images = images
        self.structured_data = structured_data
        self.model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
        
        # Initialize tools with structured data
        self.tools = AgentTools(
            vector_store=vector_store,
            images=images,
            structured_data=structured_data
        )
        
        # Conversation memory
        self.conversations = {}
        
        logger.info(f"Hybrid agent initialized with model: {self.model}")
        logger.info(f"Structured data loaded: {list(structured_data.keys())}")
    
    async def process_query(
        self, 
        query: str, 
        conversation_id: Optional[str] = None
    ) -> Dict:
        """
        Process user query using hybrid approach
        
        Strategy:
        1. Check if query matches structured data (duty cycle, polarity, etc.)
        2. Use RAG for everything else (setup, safety, maintenance)
        3. Combine both when needed
        """
        # Create or get conversation
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
        
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        # Add user message
        self.conversations[conversation_id].append({
            "role": "user",
            "content": query
        })
        
        # Step 1: Detect query type and get structured data if applicable
        structured_answer = self._check_structured_data(query)
        
        # Step 2: Get RAG context (always, for additional context)
        logger.info("Searching manual content via RAG...")
        relevant_docs = self.vector_store.search(query, top_k=5)
        rag_context = self._build_rag_context(relevant_docs)
        
        # Step 3: Build system prompt with BOTH sources
        system_prompt = self._build_hybrid_system_prompt(
            rag_context=rag_context,
            structured_answer=structured_answer
        )
        
        # Step 4: Detect if we need artifacts or images
        needs_calculator = self._needs_duty_cycle_calculator(query)
        needs_polarity_diagram = self._needs_polarity_diagram(query)
        needs_images = self._needs_images(query)
        
        # Step 5: Call Claude
        logger.info("Generating response with agent...")
        
        messages = self.conversations[conversation_id].copy()
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=messages
        )
        
        # Extract response
        assistant_message = response.content[0].text
        
        # Add to conversation history
        self.conversations[conversation_id].append({
            "role": "assistant",
            "content": assistant_message
        })
        
        # Step 6: Generate artifacts
        artifacts = []
        
        if needs_calculator:
            calc_artifact = self.tools.generate_duty_cycle_calculator(query)
            if calc_artifact:
                artifacts.append(calc_artifact)
        
        if needs_polarity_diagram:
            diagram_artifact = self.tools.generate_polarity_diagram(query)
            if diagram_artifact:
                artifacts.append(diagram_artifact)
        
        # Step 7: Find relevant images
        image_urls = []
        if needs_images:
            image_urls = self.tools.find_relevant_images(query, relevant_docs)
        
        logger.info(f"Response generated (artifacts: {len(artifacts)}, images: {len(image_urls)})")
        
        return {
            "message": assistant_message,
            "artifacts": artifacts if artifacts else None,
            "images": image_urls if image_urls else None,
            "conversation_id": conversation_id
        }
    
    def _check_structured_data(self, query: str) -> Optional[Dict]:
        """Check if query can be answered with structured data"""
        query_lower = query.lower()
        
        # Duty cycle queries
        if any(keyword in query_lower for keyword in ['duty cycle', 'how long can i weld', 'rest time']):
            return {"type": "duty_cycle", "data": self.structured_data.get("duty_cycles")}
        
        # Polarity queries
        if any(keyword in query_lower for keyword in ['polarity', 'which socket', 'dcep', 'dcen', 'positive', 'negative']):
            return {"type": "polarity", "data": self.structured_data.get("polarity")}
        
        # Troubleshooting queries
        if any(keyword in query_lower for keyword in ['porosity', 'spatter', 'burn through', 'problem', 'issue', 'not working']):
            return {"type": "troubleshooting", "data": self.structured_data.get("troubleshooting")}
        
        # Weld defect queries
        if any(keyword in query_lower for keyword in ['weld looks', 'weld appearance', 'diagnosis', 'what caused']):
            return {"type": "weld_diagnosis", "data": self.structured_data.get("weld_diagnosis")}
        
        return None
    
    def _build_rag_context(self, relevant_docs: List[Dict]) -> str:
        """Build context from RAG retrieval"""
        if not relevant_docs:
            return "No additional manual content found."
        
        context_parts = []
        for i, doc in enumerate(relevant_docs, 1):
            source = doc['metadata']['source']
            page = doc['metadata']['page']
            content = doc['content'][:800]  # More content for context
            
            context_parts.append(
                f"[Source {i}: {source}, Page {page}]\n{content}\n"
            )
        
        return "\n".join(context_parts)
    
    def _build_hybrid_system_prompt(
        self, 
        rag_context: str, 
        structured_answer: Optional[Dict]
    ) -> str:
        """Build system prompt combining structured data + RAG"""
        
        base_prompt = """You are an expert technical support agent for the Vulcan OmniPro 220 multiprocess welding system.

                        You provide accurate, helpful answers about:
                        - Duty cycles and operational limits
                        - Polarity setup for different processes
                        - Troubleshooting welding issues
                        - Setup procedures and calibration
                        - Safety guidelines

                        **IMPORTANT INSTRUCTIONS:**
                        1. Always prioritize accuracy - if you're not certain, say so
                        2. For calculations (duty cycles), use exact numbers from the data
                        3. For setup procedures, be specific and step-by-step
                        4. For troubleshooting, list causes AND solutions
                        5. Keep tone professional but friendly - like an experienced welder helping someone
                        """
        
        # Add structured data if available
        if structured_answer:
            data_type = structured_answer['type']
            data = structured_answer['data']
            
            base_prompt += f"\n\n**STRUCTURED DATA ({data_type.upper()}):**\n"
            base_prompt += f"{json.dumps(data, indent=2)}\n"
            base_prompt += "\nThis structured data is 100% accurate. Use it for precise answers.\n"
        
        # Add RAG context
        base_prompt += f"\n\n**ADDITIONAL MANUAL CONTENT (for context):**\n{rag_context}\n"
        
        return base_prompt
    
    def _needs_duty_cycle_calculator(self, query: str) -> bool:
        """Check if query would benefit from calculator artifact"""
        keywords = ['duty cycle', 'how long', 'minutes', 'rest time']
        return any(k in query.lower() for k in keywords)
    
    def _needs_polarity_diagram(self, query: str) -> bool:
        """Check if query needs polarity diagram"""
        keywords = ['polarity', 'setup', 'socket', 'cable', 'connection', 'which goes where']
        return any(k in query.lower() for k in keywords)
    
    def _needs_images(self, query: str) -> bool:
        """Check if query needs manual images"""
        query_lower = query.lower()
        
        # Explicit image requests
        explicit_keywords = ['show me', 'picture', 'diagram', 'photo', 'looks like', 'visual', 'image']
        
        # Topics that benefit from images even without asking
        visual_topics = [
            'polarity', 'socket', 'setup', 'cable', 'connection',
            'panel', 'control', 'display', 'button',
            'wire feed', 'spool', 'mechanism', 'roller',
            'weld', 'bead', 'porosity', 'spatter', 'diagnosis',
            'wiring', 'schematic'
        ]
        
        # Return true if explicit request OR visual topic
        has_explicit = any(k in query_lower for k in explicit_keywords)
        has_visual_topic = any(k in query_lower for k in visual_topics)
        
        return has_explicit or has_visual_topic
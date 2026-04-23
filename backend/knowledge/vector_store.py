import os
import logging
from typing import List, Dict
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class VectorStore:
    """FAISS-based vector store for semantic search"""
    
    def __init__(self, model_name: str = None):
        """
        Initialize vector store with embedding model
        
        Args:
            model_name: SentenceTransformer model name (defaults to env variable)
        """

        if model_name is None:
            model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        # FAISS index (L2 distance)
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Store original documents
        self.documents = []
        
        # Get batch size from env
        self.batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
        
        logger.info(f"Vector store initialized (dimension: {self.dimension})")
    
    def add_documents(self, documents: List[Dict]):
        """
        Add documents to vector store
        
        Args:
            documents: List of dicts with 'content' and 'metadata' keys
        """
        if not documents:
            logger.warning("No documents to add")
            return
        
        logger.info(f"Generating embeddings for {len(documents)} documents...")
        
        # Extract text content
        texts = [doc['content'] for doc in documents]
        
        # Generate embeddings (batched for speed)
        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            batch_size=32,
            convert_to_numpy=True
        )
        
        # Add to FAISS index
        self.index.add(embeddings.astype('float32'))
        
        # Store documents
        self.documents.extend(documents)
        
        logger.info(f"Added {len(documents)} documents to vector store")
        logger.info(f"Total documents: {len(self.documents)}")
    
    def search(self, query: str, top_k: int = None) -> List[Dict]:
        """
        Search for most relevant documents
        
        Args:
            query: Search query
            top_k: Number of results to return (defaults to env variable)
        
        Returns:
            List of documents with relevance scores
        """
        if len(self.documents) == 0:
            logger.warning("Vector store is empty")
            return []
        
        # Use env variable or default
        if top_k is None:
            top_k = int(os.getenv("VECTOR_SEARCH_TOP_K", "5"))
        
        # Generate query embedding
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True
        ).astype('float32')
        
        # Search FAISS index
        distances, indices = self.index.search(query_embedding, min(top_k, len(self.documents)))
        
        # Build results
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.documents):
                doc = self.documents[idx].copy()
                doc['relevance_score'] = float(distance)
                results.append(doc)
        
        logger.info(f"Found {len(results)} relevant documents for query")
        
        return results
        
    
    def search_by_metadata(self, query: str, metadata_filter: Dict, top_k: int = None) -> List[Dict]:
        """
        Search with metadata filtering
        
        Args:
            query: Search query
            metadata_filter: Dict of metadata key-value pairs to filter by
            top_k: Number of results to return
        
        Returns:
            Filtered and ranked documents
        """
        if top_k is None:
            top_k = int(os.getenv("VECTOR_SEARCH_TOP_K", "5"))
        
        # Get more results initially for filtering
        initial_results = self.search(query, top_k * 3)
        
        # Filter by metadata
        filtered = []
        for doc in initial_results:
            match = True
            for key, value in metadata_filter.items():
                if doc.get('metadata', {}).get(key) != value:
                    match = False
                    break
            if match:
                filtered.append(doc)
            
            if len(filtered) >= top_k:
                break
        
        return filtered[:top_k]
    
    def get_stats(self) -> Dict:
        """Get vector store statistics"""
        return {
            "total_documents": len(self.documents),
            "embedding_dimension": self.dimension,
            "index_size": self.index.ntotal,
            "model": self.model.get_sentence_embedding_dimension()
        }
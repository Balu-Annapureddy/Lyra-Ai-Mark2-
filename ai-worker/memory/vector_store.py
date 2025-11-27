"""
Vector Store - Memory System
Using sentence-transformers + FAISS for semantic memory
"""

import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Vector-based memory store using sentence-transformers and FAISS
    """
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        self.index_path = self.data_dir / "memory_index.faiss"
        self.metadata_path = self.data_dir / "memory_metadata.json"
        
        self.encoder = None
        self.index = None
        self.metadata = []
        self.dimension = 384  # MiniLM dimension
        
        self._initialize()
    
    def _initialize(self):
        """Initialize encoder and index"""
        try:
            # Initialize sentence transformer
            from sentence_transformers import SentenceTransformer
            
            logger.info("Loading sentence transformer model...")
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Sentence transformer loaded")
            
            # Initialize or load FAISS index
            import faiss
            
            if self.index_path.exists():
                self.index = faiss.read_index(str(self.index_path))
                logger.info("Loaded existing FAISS index")
            else:
                self.index = faiss.IndexFlatL2(self.dimension)
                logger.info("Created new FAISS index")
            
            # Load metadata
            if self.metadata_path.exists():
                with open(self.metadata_path, 'r') as f:
                    self.metadata = json.load(f)
                logger.info(f"Loaded {len(self.metadata)} memory entries")
            
        except ImportError as e:
            logger.error(f"Failed to initialize vector store: {e}")
            logger.info("Install with: pip install sentence-transformers faiss-cpu")
            self.encoder = None
            self.index = None
    
    def is_ready(self) -> bool:
        """Check if vector store is ready"""
        return self.encoder is not None and self.index is not None
    
    def embed(self, text: str) -> Optional[np.ndarray]:
        """
        Generate embedding for text
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector or None
        """
        if not self.is_ready():
            logger.error("Vector store not initialized")
            return None
        
        try:
            embedding = self.encoder.encode([text])[0]
            return embedding
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return None
    
    def store(
        self,
        text: str,
        metadata: Optional[Dict] = None,
        category: str = "general"
    ) -> bool:
        """
        Store text in vector memory
        
        Args:
            text: Text to store
            metadata: Optional metadata dict
            category: Category tag
        
        Returns:
            True if successful
        """
        if not self.is_ready():
            logger.error("Vector store not initialized")
            return False
        
        try:
            # Generate embedding
            embedding = self.embed(text)
            if embedding is None:
                return False
            
            # Add to FAISS index
            import faiss
            self.index.add(np.array([embedding]))
            
            # Store metadata
            entry = {
                "id": len(self.metadata),
                "text": text,
                "category": category,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            self.metadata.append(entry)
            
            # Save to disk
            self._save()
            
            logger.info(f"Stored memory: {text[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return False
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for similar memories
        
        Args:
            query: Search query
            top_k: Number of results to return
            category: Optional category filter
        
        Returns:
            List of matching memory entries
        """
        if not self.is_ready():
            logger.error("Vector store not initialized")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embed(query)
            if query_embedding is None:
                return []
            
            # Search FAISS index
            import faiss
            distances, indices = self.index.search(
                np.array([query_embedding]),
                min(top_k, len(self.metadata))
            )
            
            # Retrieve results
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.metadata):
                    entry = self.metadata[idx].copy()
                    entry["similarity"] = float(1 / (1 + distances[0][i]))  # Convert distance to similarity
                    
                    # Apply category filter
                    if category is None or entry["category"] == category:
                        results.append(entry)
            
            logger.info(f"Found {len(results)} matching memories")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_recent(self, count: int = 10, category: Optional[str] = None) -> List[Dict]:
        """
        Get recent memories
        
        Args:
            count: Number of memories to retrieve
            category: Optional category filter
        
        Returns:
            List of recent memory entries
        """
        filtered = self.metadata
        
        if category:
            filtered = [m for m in filtered if m["category"] == category]
        
        # Sort by timestamp (most recent first)
        sorted_memories = sorted(
            filtered,
            key=lambda x: x["timestamp"],
            reverse=True
        )
        
        return sorted_memories[:count]
    
    def clear(self, category: Optional[str] = None) -> bool:
        """
        Clear memories
        
        Args:
            category: Optional category to clear (None = clear all)
        
        Returns:
            True if successful
        """
        try:
            if category:
                # Remove specific category
                self.metadata = [m for m in self.metadata if m["category"] != category]
                logger.info(f"Cleared memories in category: {category}")
            else:
                # Clear all
                self.metadata = []
                import faiss
                self.index = faiss.IndexFlatL2(self.dimension)
                logger.info("Cleared all memories")
            
            self._save()
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear memories: {e}")
            return False
    
    def _save(self):
        """Save index and metadata to disk"""
        try:
            import faiss
            
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_path))
            
            # Save metadata
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")

"""
RAG Manager - Manages retrieval-augmented generation
"""
import asyncio
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class RAGSource:
    """Represents a RAG knowledge source"""
    
    def __init__(
        self,
        source_id: str,
        name: str,
        collection_name: str,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        self.source_id = source_id
        self.name = name
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        self.embedder = SentenceTransformer(embedding_model)


class RAGManager:
    """Manages RAG sources and retrieval"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.sources: Dict[str, RAGSource] = {}
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        logger.info("RAGManager initialized")
    
    def add_source(
        self,
        source_id: str,
        name: str,
        collection_name: str,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """Add a new RAG source"""
        source = RAGSource(source_id, name, collection_name, embedding_model)
        self.sources[source_id] = source
        
        # Create or get collection
        try:
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"source_id": source_id, "name": name}
            )
            logger.info(f"Added RAG source: {name} ({source_id})")
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise
    
    async def add_documents(
        self,
        source_id: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ):
        """Add documents to a RAG source"""
        source = self.sources.get(source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")
        
        try:
            # Get collection
            collection = self.chroma_client.get_collection(source.collection_name)
            
            # Generate IDs if not provided
            if not ids:
                ids = [f"doc_{i}_{datetime.utcnow().timestamp()}" for i in range(len(documents))]
            
            # Generate embeddings
            embeddings = source.embedder.encode(documents).tolist()
            
            # Add to collection
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas or [{} for _ in documents],
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to {source_id}")
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
    
    async def retrieve_context(
        self,
        query: str,
        agent_id: str,
        sources: Optional[List[str]] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """Retrieve relevant context from RAG sources"""
        try:
            all_results = []
            
            # Determine which sources to query
            query_sources = sources or list(self.sources.keys())
            
            for source_id in query_sources:
                source = self.sources.get(source_id)
                if not source:
                    logger.warning(f"Source {source_id} not found, skipping")
                    continue
                
                # Get collection
                try:
                    collection = self.chroma_client.get_collection(source.collection_name)
                except Exception as e:
                    logger.warning(f"Collection {source.collection_name} not found: {e}")
                    continue
                
                # Generate query embedding
                query_embedding = source.embedder.encode([query])[0].tolist()
                
                # Query collection
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k
                )
                
                # Process results
                if results and results.get('documents'):
                    for i, doc in enumerate(results['documents'][0]):
                        distance = results['distances'][0][i] if 'distances' in results else 0
                        similarity = 1 - distance  # Convert distance to similarity
                        
                        if similarity >= similarity_threshold:
                            all_results.append({
                                'source_id': source_id,
                                'document': doc,
                                'similarity': similarity,
                                'metadata': results['metadatas'][0][i] if 'metadatas' in results else {}
                            })
            
            # Sort by similarity
            all_results.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Take top_k overall
            top_results = all_results[:top_k]
            
            # Format context
            context_str = "\n\n".join([
                f"[Source: {r['source_id']}, Relevance: {r['similarity']:.2f}]\n{r['document']}"
                for r in top_results
            ])
            
            return {
                'context': context_str,
                'results': top_results,
                'count': len(top_results)
            }
            
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return {
                'context': '',
                'results': [],
                'count': 0,
                'error': str(e)
            }
    
    async def hybrid_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search (semantic + keyword)"""
        # Simplified - in production, implement BM25 + vector search
        return await self.retrieve_context(query, agent_id="system", top_k=top_k)
    
    def get_source(self, source_id: str) -> Optional[RAGSource]:
        """Get a RAG source"""
        return self.sources.get(source_id)
    
    def list_sources(self) -> List[Dict[str, str]]:
        """List all RAG sources"""
        return [
            {
                'source_id': source.source_id,
                'name': source.name,
                'collection': source.collection_name
            }
            for source in self.sources.values()
        ]
    
    async def update_embeddings(
        self,
        source_id: str,
        document_ids: List[str],
        new_documents: List[str]
    ):
        """Update embeddings for specific documents"""
        source = self.sources.get(source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")
        
        try:
            collection = self.chroma_client.get_collection(source.collection_name)
            
            # Generate new embeddings
            embeddings = source.embedder.encode(new_documents).tolist()
            
            # Update collection
            collection.update(
                ids=document_ids,
                documents=new_documents,
                embeddings=embeddings
            )
            
            logger.info(f"Updated {len(document_ids)} documents in {source_id}")
            
        except Exception as e:
            logger.error(f"Failed to update embeddings: {e}")
            raise
    
    async def delete_documents(
        self,
        source_id: str,
        document_ids: List[str]
    ):
        """Delete documents from a source"""
        source = self.sources.get(source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")
        
        try:
            collection = self.chroma_client.get_collection(source.collection_name)
            collection.delete(ids=document_ids)
            logger.info(f"Deleted {len(document_ids)} documents from {source_id}")
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            raise

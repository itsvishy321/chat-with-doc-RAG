from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import uuid

class VectorStore:
    def __init__(self):
        # Initialize Qdrant client running on docker container
        self.client = QdrantClient(host="localhost", port=6333)
        
        # Initialize embedding model
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.vector_size = 384  # Dimension of all-MiniLM-L6-v2
        
    def create_collection(self, collection_name):
        """Create a new collection in Qdrant"""
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )
            print(f"Created collection: {collection_name}")
        except Exception as e:
            print(f"Error creating collection: {e}")
            
    def add_documents(self, collection_name, chunks, source_url):
        """Add document chunks to the vector database"""
        points = []
        
        for i, chunk in enumerate(chunks):
            # Generate embedding
            embedding = self.encoder.encode([chunk]).tolist()[0]
            
            # Create point
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "content": chunk,
                    "source_url": source_url,
                    "chunk_index": i
                }
            )
            points.append(point)
        
        # Upsert points to collection
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )
        print(f"Added {len(points)} chunks to collection {collection_name}")
        
    def search(self, collection_name, query, limit=5):
        """Search for similar chunks"""
        try:
            # Generate query embedding
            query_embedding = self.encoder.encode([query]).tolist()[0]
            
            # Search in Qdrant
            search_results = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "content": result.payload["content"],
                    "score": result.score,
                    "chunk_index": result.payload["chunk_index"]
                })
            
            return results
            
        except Exception as e:
            print(f"Error searching: {e}")
            return []
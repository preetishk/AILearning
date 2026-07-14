from datasets import load_dataset
import chromadb
from sentence_transformers import SentenceTransformer

# Load only the training split of the dataset
train_dataset = load_dataset("databricks/databricks-dolly-15k", split='train')

# Filter the dataset to only include entries with the 'closed_qa' category
closed_qa_dataset = train_dataset.filter(lambda example: example['category'] == 'closed_qa')

print(closed_qa_dataset[0])

# Initialize the ChromaDB client and create a collection
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="knowledge-base")



# class VectorStore:

#     def __init__(self, collection_name):
#        # Initialize the embedding model
#         self.embedding_model = SentenceTransformer('sentence-transformers/multi-qa-MiniLM-L6-cos-v1')
#         self.chroma_client = chromadb.Client()
#         self.collection = self.chroma_client.create_collection(name=collection_name)

#     # Method to populate the vector store with embeddings from a dataset
#     def populate_vectors(self, dataset):
#         for i, item in enumerate(dataset):
#             combined_text = f"{item['instruction']}. {item['context']}"
#             embeddings = self.embedding_model.encode(combined_text).tolist()
#             self.collection.add(embeddings=[embeddings], documents=[item['context']], ids=[f"id_{i}"])

#     # Method to search the ChromaDB collection for relevant context based on a query
#     def search_context(self, query, n_results=1):
#         query_embeddings = self.embedding_model.encode(query).tolist()
#         return self.collection.query(query_embeddings=query_embeddings, n_results=n_results)


# # Example usage
# if __name__ == "__main__":
#    # Initialize the handler with collection name
#     vector_store = VectorStore("knowledge-base")
    
#     # Assuming closed_qa_dataset is defined and available
#     vector_store.populate_vectors(closed_qa_dataset)


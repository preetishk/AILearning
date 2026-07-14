import chromadb

collection = chromadb.Client().get_collection("knowledge-base")

result = collection.query(
    query_texts=["Tomoaki Komorida born"], # Chroma will embed this for you
    n_results=1
)

print(result)
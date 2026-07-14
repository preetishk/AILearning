import requests
import json
import chromadb

def chat_with_llama(user_input,context):
    # Ollama API endpoint
    url = "http://localhost:11434/api/generate"
    updated_prompt = f"""You are a helpful assistant that uses the provided context to answer 
                            questions. If the context contains information relevant to the question, 
                            use that information to answer. If the context is not relevant or 
                            insufficient, rely on your own knowledge to provide an accurate and 
                            informative answer.
                        {context}
                        Question: {user_input}
                        Answer:"""
    # Prepare the request payload
    payload = {
        "model": "llama3.1",
        "prompt": updated_prompt,
        "stream": False
    }
    
    try:
        # Make the API request
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the response
        result = response.json()
        return result.get("response", "No response received")
    
    except requests.exceptions.RequestException as e:
        return f"Error connecting to Ollama: {str(e)}"

def get_from_chromadb(qry_text):
    client = chromadb.PersistentClient(path="C:\\Users\\KuPr272\\Documents\\AI\\MCP\RAG\\rag_chromadb\\data\\")
    collection = client.get_collection(name="my_collection")
    chroma_value = collection.query(query_texts=[qry_text],
                                    n_results =1)
    return chroma_value

def main():
    print("Welcome to Llama 3.1 Chat!")
    print("Type 'quit' to exit")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
        context = get_from_chromadb(user_input)
        response = chat_with_llama(user_input,context)
        print("\nLlama:", response)

if __name__ == "__main__":
    main() 
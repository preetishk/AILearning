import chromadb
from chromadb.config import Settings
import chromadb.server

settings = Settings(
    chroma_api_impl="chromadb.api.fastapi.FastAPI",
    chroma_server_host="0.0.0.0"
)

# Configure and start the server
server = chromadb.server(host="localhost", port=8000)
server.run()
# if __name__ == "__main__":
#     chromadb.server.start(settings)


# chroma run --host localhost --port 8000
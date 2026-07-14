import chromadb
from datetime import datetime
client = chromadb.PersistentClient(path="C:\\Users\\KuPr272\\Documents\\AI\\MCP\RAG\\rag_chromadb\\data\\")
collection = client.get_or_create_collection(name="my_collection",
                                      metadata={
                                            "description": "my first Chroma collection",
                                            "created": str(datetime.now())
                                            }
                                            )
doc_preetish = """
Preetish is a champion architect working in IT. He is a hard working person and like Me time.
He like to watch anime and his favorite Anime is Death Note. 
He has a bike which is good for long travel. 
"""

doc_sreeni = """
Sreeni is a champion Expert working in IT. He is a hard working and good.
He like to buy plots in his free time and is ultra rich. 
He has 3 plots in bangalore and unlimited plots in Andhra
"""

doc_sujith = """
Sujith Prasad is a champion Master working in IT with more than 25 years of experience.
He is a hard working and dedicated and a good mentor.
He likes VUCA environment and brings order to chaos.
"""

collection.add(
    documents=[doc_sujith],
    ids=["id3"]
)

import os

import chromadb
from llama_index.core import Document
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore

from . import json

embedding_strategy = os.getenv("LLM_EMBEDDING_MODEL", "openai")

# TODO: More embeddings: https://docs.llamaindex.ai/en/stable/examples/embeddings/OpenAI/
# There's probably a more programmatic way to do this.
if embedding_strategy == "llama2":
    from llama_index.embeddings.ollama import OllamaEmbedding
    embed_model = OllamaEmbedding(
        model_name="llama2",
        base_url=os.getenv("LLM_EMBEDDING_MODEL_BASE_URL", "http://localhost:8000"),
        ollama_additional_kwargs={"mirostat": 0},
    )
elif embedding_strategy == "local":
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    embed_model = HuggingFaceEmbedding(
        model_name="BAAI/bge-small-en-v1.5"
    )
else:
    from llama_index.embeddings.openai import OpenAIEmbedding
    embed_model = OpenAIEmbedding(
        base_url=os.getenv("LLM_EMBEDDING_MODEL_BASE_URL"),
    )


class LongTermMemory:
    def __init__(self):
        db = chromadb.Client()
        self.collection = db.get_or_create_collection(name="memories")
        vector_store = ChromaVectorStore(chroma_collection=self.collection)
        self.index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)
        self.thought_idx = 0

    def add_event(self, event):
        doc = Document(
            text=json.dumps(event),
            doc_id=str(self.thought_idx),
            extra_info={
                "type": event["action"],
                "idx": self.thought_idx,
            },
        )
        self.thought_idx += 1
        self.index.insert(doc)

    def search(self, query, k=10):
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=k,
        )
        results = retriever.retrieve(query)
        return [r.get_text() for r in results]



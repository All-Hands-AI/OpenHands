import chromadb
from llama_index.core import Document
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore

from opendevin import config
from . import json

embedding_strategy = config.get("LLM_EMBEDDING_MODEL")

# TODO: More embeddings: https://docs.llamaindex.ai/en/stable/examples/embeddings/OpenAI/
# There's probably a more programmatic way to do this.
if embedding_strategy == "llama2":
    from llama_index.embeddings.ollama import OllamaEmbedding
    embed_model = OllamaEmbedding(
        model_name="llama2",
        base_url=config.get_or_error("LLM_BASE_URL"),
        ollama_additional_kwargs={"mirostat": 0},
    )
elif embedding_strategy == "openai":
    from llama_index.embeddings.openai import OpenAIEmbedding
    embed_model = OpenAIEmbedding(
        model="text-embedding-ada-002"
    )
elif embedding_strategy == "azureopenai":
    from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding  # Need to instruct to set these env variables in documentation
    embed_model = AzureOpenAIEmbedding(
        model="text-embedding-ada-002",
        deployment_name=config.get_or_error("LLM_DEPLOYMENT_NAME"),
        api_key=config.get_or_error("LLM_API_KEY"),
        azure_endpoint=config.get_or_error("LLM_BASE_URL"),
        api_version=config.get_or_error("LLM_API_VERSION"),
    )
else:
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    embed_model = HuggingFaceEmbedding(
        model_name="BAAI/bge-small-en-v1.5"
    )


class LongTermMemory:
    def __init__(self):
        db = chromadb.Client()
        self.collection = db.get_or_create_collection(name="memories")
        vector_store = ChromaVectorStore(chroma_collection=self.collection)
        self.index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)
        self.thought_idx = 0

    def add_event(self, event):
        id = ""
        t = ""
        if "action" in event:
            t = "action"
            id = event["action"]
        elif "observation" in event:
            t = "observation"
            id = event["observation"]
        doc = Document(
            text=json.dumps(event),
            doc_id=str(self.thought_idx),
            extra_info={
                "type": t,
                "id": id,
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



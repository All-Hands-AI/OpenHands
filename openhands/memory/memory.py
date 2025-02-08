import json

from openhands.core.config import AgentConfig, LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.event import Event
from openhands.events.serialization.event import event_to_memory
from openhands.events.stream import EventStream
from openhands.utils.embeddings import (
    LLAMA_INDEX_AVAILABLE,
    EmbeddingsLoader,
    check_llama_index,
)

# Conditional imports based on llama_index availability
if LLAMA_INDEX_AVAILABLE:
    import chromadb
    from llama_index.core import Document
    from llama_index.core.indices.vector_store.base import VectorStoreIndex
    from llama_index.core.indices.vector_store.retrievers.retriever import (
        VectorIndexRetriever,
    )
    from llama_index.core.schema import TextNode
    from llama_index.vector_stores.chroma import ChromaVectorStore


class LongTermMemory:
    """Handles storing information for the agent to access later, using chromadb."""

    event_stream: EventStream

    def __init__(
        self,
        llm_config: LLMConfig,
        agent_config: AgentConfig,
        event_stream: EventStream,
    ):
        """Initialize the chromadb and set up ChromaVectorStore for later use."""

        check_llama_index()

        # initialize the chromadb client
        db = chromadb.PersistentClient(
            path=f'./cache/sessions/{event_stream.sid}/memory',
            # FIXME anonymized_telemetry=False,
        )
        self.collection = db.get_or_create_collection(name='memories')
        vector_store = ChromaVectorStore(chroma_collection=self.collection)

        # embedding model
        embedding_strategy = llm_config.embedding_model
        self.embed_model = EmbeddingsLoader.get_embedding_model(
            embedding_strategy, llm_config
        )
        logger.debug(f'Using embedding model: {self.embed_model}')

        # instantiate the index
        self.index = VectorStoreIndex.from_vector_store(vector_store, self.embed_model)
        self.thought_idx = 0

        # initialize the event stream
        self.event_stream = event_stream

        # max of threads to run the pipeline
        self.memory_max_threads = agent_config.memory_max_threads

    def add_event(self, event: Event):
        """Adds a new event to the long term memory with a unique id.

        Parameters:
        - event: The new event to be added to memory
        """
        try:
            # convert the event to a memory-friendly format, and don't truncate
            event_data = event_to_memory(event, -1)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f'Failed to process event: {e}')
            return

        # determine the event type and ID
        event_type = ''
        event_id = ''
        if 'action' in event_data:
            event_type = 'action'
            event_id = event_data['action']
        elif 'observation' in event_data:
            event_type = 'observation'
            event_id = event_data['observation']

        # create a Document instance for the event
        doc = Document(
            text=json.dumps(event_data),
            doc_id=str(self.thought_idx),
            extra_info={
                'type': event_type,
                'id': event_id,
                'idx': self.thought_idx,
            },
        )
        self.thought_idx += 1
        logger.debug('Adding %s event to memory: %d', event_type, self.thought_idx)
        self._add_document(document=doc)

    def _add_document(self, document: 'Document'):
        """Inserts a single document into the index."""
        self.index.insert_nodes([self._create_node(document)])

    def _create_node(self, document: 'Document') -> 'TextNode':
        """Create a TextNode from a Document instance."""
        return TextNode(
            text=document.text,
            doc_id=document.doc_id,
            extra_info=document.extra_info,
        )

    def search(self, query: str, k: int = 10) -> list[str]:
        """Searches through the current memory using VectorIndexRetriever.

        Parameters:
        - query (str): A query to match search results to
        - k (int): Number of top results to return

        Returns:
        - list[str]: List of top k results found in current memory
        """
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=k,
        )
        results = retriever.retrieve(query)

        for result in results:
            logger.debug(
                f'Doc ID: {result.doc_id}:\n Text: {result.get_text()}\n Score: {result.score}'
            )

        return [r.get_text() for r in results]

    def _events_to_docs(self) -> list['Document']:
        """Convert all events from the EventStream to documents for batch insert into the index."""
        try:
            events = self.event_stream.get_events()
        except Exception as e:
            logger.debug(f'No events found for session {self.event_stream.sid}: {e}')
            return []

        documents: list[Document] = []

        for event in events:
            try:
                # convert the event to a memory-friendly format, and don't truncate
                event_data = event_to_memory(event, -1)

                # determine the event type and ID
                event_type = ''
                event_id = ''
                if 'action' in event_data:
                    event_type = 'action'
                    event_id = event_data['action']
                elif 'observation' in event_data:
                    event_type = 'observation'
                    event_id = event_data['observation']

                # create a Document instance for the event
                doc = Document(
                    text=json.dumps(event_data),
                    doc_id=str(self.thought_idx),
                    extra_info={
                        'type': event_type,
                        'id': event_id,
                        'idx': self.thought_idx,
                    },
                )
                documents.append(doc)
                self.thought_idx += 1
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f'Failed to process event: {e}')
                continue

        if documents:
            logger.debug(f'Batch inserting {len(documents)} documents into the index.')
        else:
            logger.debug('No valid documents found to insert into the index.')

        return documents

    def create_nodes(self, documents: list['Document']) -> list['TextNode']:
        """Create nodes from a list of documents."""
        return [self._create_node(doc) for doc in documents]

import streamlit as st
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex
from llama_index.core.chat_engine.types import ChatMode
from llama_index.core.postprocessor import SentenceEmbeddingOptimizer

from opendevin.indexing.rag.postprocessing import DeduplicateNodePostprocessor
from opendevin.indexing.rag.rag import VectorIndex

load_dotenv()


@st.cache_resource(show_spinner=False)
def get_index() -> VectorStoreIndex:
    return VectorIndex().index


index = get_index()

if 'chat_engine' not in st.session_state.keys():
    postprocessor = SentenceEmbeddingOptimizer(
        embed_model=index.service_context.embed_model,
        percentile_cutoff=0.5,
        threshold_cutoff=0.7,
    )

    st.session_state.chat_engine = index.as_chat_engine(
        chat_mode=ChatMode.CONTEXT,
        verbose=True,
        node_postprocessors=[
            # postprocessor,
            DeduplicateNodePostprocessor()
        ],
    )

st.set_page_config(
    page_title='LlamaIndex Chat',
    page_icon='🦙',
    layout='wide',
    initial_sidebar_state='auto',
    menu_items=None,
)

st.title('LlamaIndex Chat 🦙')

if 'messages' not in st.session_state.keys():
    st.session_state.messages = [
        {'role': 'assistant', 'content': 'Hello! Ask me a question about LLamaIndex.'}
    ]

if prompt := st.chat_input('Your question'):
    st.session_state.messages.append({'role': 'user', 'content': prompt})

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.write(message['content'])

if st.session_state.messages[-1]['role'] != 'assistant':
    with st.chat_message('assistant'):
        with st.spinner('Thinking...'):
            response = st.session_state.chat_engine.chat(message=prompt)
            nodes = [
                node for node in response.source_nodes
            ]  # add breakpoint to inspect nodes
            st.write(response.response)

            for col, node, id in zip(st.columns(len(nodes)), nodes, range(len(nodes))):
                with col:
                    st.header(f'Source node {id+1}: score={node.score}')
                    # render markdown for code blocks
                    st.markdown(f'```python\n{node.text}\n```')

            st.session_state.messages.append(
                {
                    'role': 'assistant',
                    'content': response.response,
                }
            )

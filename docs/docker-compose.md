# Run Devin with `docker compose`

Simple start of Devin instance with support for Ollama models and MemGPT backends.

This will run the Devin server with UI and all backends it depends on, automatically 💻:
```bash
git clone https://github.com/OpenDevin/OpenDevin.git
docker compose up devin
```

## Services

 - [LiteLLM Proxy Service](https://litellm.vercel.app/docs/): Call 100+ LLMs using the same Input/Output Format
 - [MemGPT](https://memgpt.readme.io/docs/index): Allows you to build LLM agents with self-editing memory
 Note: Generating MemGPT-compatible outputs is a harder task for an LLM than regular text output. For this reason we **strongly advise** users to **NOT use models below Q5 quantization** - as the model gets worse, the number of errors you will encounter while using MemGPT will dramatically increase (MemGPT will not send messages properly, edit memory properly, etc. [[Read here](https://memgpt.readme.io/docs/local_llm)]).


 - [mitmproxy](https://docs.mitmproxy.org/stable/): A free and open source interactive HTTPS proxy. May be useful for developers


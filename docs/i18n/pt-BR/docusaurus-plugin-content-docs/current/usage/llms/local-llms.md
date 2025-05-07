# LLM Local com SGLang ou vLLM

:::warning
Ao usar um LLM Local, o OpenHands pode ter funcionalidades limitadas.
É altamente recomendável que você use GPUs para servir modelos locais para uma experiência ideal.
:::

## Notícias

- 2025/03/31: Lançamos um modelo aberto OpenHands LM v0.1 32B que alcança 37,1% no SWE-Bench Verified
([blog](https://www.all-hands.dev/blog/introducing-openhands-lm-32b----a-strong-open-coding-agent-model), [modelo](https://huggingface.co/all-hands/openhands-lm-32b-v0.1)).

## Baixar o Modelo do Huggingface

Por exemplo, para baixar o [OpenHands LM 32B v0.1](https://huggingface.co/all-hands/openhands-lm-32b-v0.1):

```bash
huggingface-cli download all-hands/openhands-lm-32b-v0.1 --local-dir all-hands/openhands-lm-32b-v0.1
```

## Criar um Endpoint Compatível com OpenAI Usando um Framework de Serviço de Modelo

### Servindo com SGLang

- Instale o SGLang seguindo [a documentação oficial](https://docs.sglang.ai/start/install.html).
- Exemplo de comando de lançamento para OpenHands LM 32B (com pelo menos 2 GPUs):

```bash
SGLANG_ALLOW_OVERWRITE_LONGER_CONTEXT_LEN=1 python3 -m sglang.launch_server \
    --model all-hands/openhands-lm-32b-v0.1 \
    --served-model-name openhands-lm-32b-v0.1 \
    --port 8000 \
    --tp 2 --dp 1 \
    --host 0.0.0.0 \
    --api-key mykey --context-length 131072
```

### Servindo com vLLM

- Instale o vLLM seguindo [a documentação oficial](https://docs.vllm.ai/en/latest/getting_started/installation.html).
- Exemplo de comando de lançamento para OpenHands LM 32B (com pelo menos 2 GPUs):

```bash
vllm serve all-hands/openhands-lm-32b-v0.1 \
    --host 0.0.0.0 --port 8000 \
    --api-key mykey \
    --tensor-parallel-size 2 \
    --served-model-name openhands-lm-32b-v0.1
    --enable-prefix-caching
```

## Executar e Configurar o OpenHands

### Executar o OpenHands

#### Usando Docker

Execute o OpenHands usando [o comando oficial do docker run](../installation#start-the-app).

#### Usando o Modo de Desenvolvimento

Use as instruções em [Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md) para construir o OpenHands.
Certifique-se de que o `config.toml` existe executando `make setup-config`, que criará um para você. No `config.toml`, insira o seguinte:

```
[core]
workspace_base="/caminho/para/seu/workspace"

[llm]
model="openhands-lm-32b-v0.1"
ollama_base_url="http://localhost:8000"
```

Inicie o OpenHands usando `make run`.

### Configurar o OpenHands

Depois que o OpenHands estiver em execução, você precisará definir o seguinte na interface do OpenHands através das Configurações:
1. Habilite as opções `Avançadas`.
2. Configure o seguinte:
- `Modelo Personalizado` para `openai/<nome-do-modelo-servido>` (ex: `openai/openhands-lm-32b-v0.1`)
- `URL Base` para `http://host.docker.internal:8000`
- `Chave de API` para a mesma string que você definiu ao servir o modelo (ex: `mykey`)

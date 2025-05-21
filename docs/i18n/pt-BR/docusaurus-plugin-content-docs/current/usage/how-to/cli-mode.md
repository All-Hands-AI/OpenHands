# Modo CLI

O OpenHands pode ser executado em um modo CLI interativo, que permite aos usuários iniciar uma sessão interativa via linha de comando.

Este modo é diferente do [modo headless](headless-mode), que é não interativo e melhor para scripts.

## Com Python

Para iniciar uma sessão interativa do OpenHands via linha de comando:

1. Certifique-se de ter seguido as [instruções de configuração de desenvolvimento](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).
2. Execute o seguinte comando:

```bash
poetry run python -m openhands.core.cli
```

Este comando iniciará uma sessão interativa onde você pode inserir tarefas e receber respostas do OpenHands.

Você precisará definir seu modelo, chave de API e outras configurações através de variáveis de ambiente
[ou do arquivo `config.toml`](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml).

## Com Docker

Para executar o OpenHands no modo CLI com Docker:

1. Defina as seguintes variáveis de ambiente em seu terminal:

- `SANDBOX_VOLUMES` para especificar o diretório que você quer que o OpenHands acesse (Ex: `export SANDBOX_VOLUMES=$(pwd)/workspace:/workspace:rw`).
  - O agente trabalha em `/workspace` por padrão, então monte seu diretório de projeto lá se quiser que o agente modifique arquivos.
  - Para dados somente leitura, use um caminho de montagem diferente (Ex: `export SANDBOX_VOLUMES=$(pwd)/workspace:/workspace:rw,/path/to/large/dataset:/data:ro`).
- `LLM_MODEL` para o modelo a ser usado (Ex: `export LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"`).
- `LLM_API_KEY` para a chave de API (Ex: `export LLM_API_KEY="sk_test_12345"`).

2. Execute o seguinte comando Docker:

```bash
docker run -it \
    --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.39-nikolaik \
    -e SANDBOX_USER_ID=$(id -u) \
    -e SANDBOX_VOLUMES=$SANDBOX_VOLUMES \
    -e LLM_API_KEY=$LLM_API_KEY \
    -e LLM_MODEL=$LLM_MODEL \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.openhands-state:/.openhands-state \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app-$(date +%Y%m%d%H%M%S) \
    docker.all-hands.dev/all-hands-ai/openhands:0.39 \
    python -m openhands.core.cli
```

Este comando iniciará uma sessão interativa no Docker onde você pode inserir tarefas e receber respostas do OpenHands.

O `-e SANDBOX_USER_ID=$(id -u)` é passado para o comando Docker para garantir que o usuário da sandbox corresponda às
permissões do usuário do host. Isso impede que o agente crie arquivos pertencentes ao root no workspace montado.

# Modo CLI

O OpenHands pode ser executado em um modo CLI interativo, que permite aos usuários iniciar uma sessão interativa via linha de comando.

Esse modo é diferente do [modo headless](headless-mode), que é não interativo e melhor para scripting.

## Com Python

Para iniciar uma sessão interativa do OpenHands via linha de comando:

1. Certifique-se de ter seguido as [instruções de configuração de desenvolvimento](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).
2. Execute o seguinte comando:

```bash
poetry run python -m openhands.core.cli
```

Esse comando iniciará uma sessão interativa onde você pode inserir tarefas e receber respostas do OpenHands.

Você precisará definir seu modelo, chave de API e outras configurações via variáveis de ambiente
[ou o arquivo `config.toml`](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml).

## Com Docker

Para executar o OpenHands no modo CLI com Docker:

1. Defina as seguintes variáveis de ambiente no seu terminal:

- `WORKSPACE_BASE` para o diretório que você deseja que o OpenHands edite (Ex: `export WORKSPACE_BASE=$(pwd)/workspace`).
- `LLM_MODEL` para o modelo a ser usado (Ex: `export LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"`).
- `LLM_API_KEY` para a chave de API (Ex: `export LLM_API_KEY="sk_test_12345"`).

2. Execute o seguinte comando Docker:

```bash
docker run -it \
    --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.35-nikolaik \
    -e SANDBOX_USER_ID=$(id -u) \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -e LLM_API_KEY=$LLM_API_KEY \
    -e LLM_MODEL=$LLM_MODEL \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.openhands-state:/.openhands-state \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app-$(date +%Y%m%d%H%M%S) \
    docker.all-hands.dev/all-hands-ai/openhands:0.35 \
    python -m openhands.core.cli
```

Esse comando iniciará uma sessão interativa no Docker onde você pode inserir tarefas e receber respostas do OpenHands.

## Exemplos de Comandos CLI e Saídas Esperadas

Aqui estão alguns exemplos de comandos CLI e suas saídas esperadas:

### Exemplo 1: Tarefa Simples

```bash
>> Escreva um script Python que imprima "Hello, World!"
```

Saída Esperada:

```bash
🤖 Claro! Aqui está um script Python que imprime "Hello, World!":

❯ print("Hello, World!")
```

### Exemplo 2: Comando Bash

```bash
>> Crie um diretório chamado "test_dir"
```

Saída Esperada:

```bash
🤖 Criando um diretório chamado "test_dir":

❯ mkdir test_dir
```

### Exemplo 3: Tratamento de Erro

```bash
>> Exclua um arquivo inexistente
```

Saída Esperada:

```bash
🤖 Ocorreu um erro. Por favor, tente novamente.
```

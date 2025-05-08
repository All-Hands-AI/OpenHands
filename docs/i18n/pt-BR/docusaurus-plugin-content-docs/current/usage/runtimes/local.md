# Runtime Local

O Runtime Local permite que o agente OpenHands execute ações diretamente em sua máquina local sem usar Docker.
Este runtime é destinado principalmente para ambientes controlados como pipelines de CI ou cenários de teste onde o Docker não está disponível.

:::caution
**Aviso de Segurança**: O Runtime Local é executado sem qualquer isolamento de sandbox. O agente pode acessar e modificar
arquivos diretamente em sua máquina. Use este runtime apenas em ambientes controlados ou quando você compreender completamente as implicações de segurança.
:::

## Pré-requisitos

Antes de usar o Runtime Local, certifique-se de que:

1. Você pode executar o OpenHands usando o [fluxo de Desenvolvimento](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).
2. O tmux está disponível em seu sistema.

## Configuração

Para usar o Runtime Local, além das configurações necessárias como o provedor LLM, modelo e chave API, você precisará definir
as seguintes opções através de variáveis de ambiente ou do [arquivo config.toml](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml) ao iniciar o OpenHands:

Via variáveis de ambiente:

```bash
# Obrigatório
export RUNTIME=local

# Opcional, mas recomendado
# O agente trabalha em /workspace por padrão, então monte seu diretório de projeto lá
export SANDBOX_VOLUMES=/caminho/para/seu/workspace:/workspace:rw
# Para dados somente leitura, use um caminho de montagem diferente
# export SANDBOX_VOLUMES=/caminho/para/seu/workspace:/workspace:rw,/caminho/para/grande/dataset:/data:ro
```

Via `config.toml`:

```toml
[core]
runtime = "local"

[sandbox]
# O agente trabalha em /workspace por padrão, então monte seu diretório de projeto lá
volumes = "/caminho/para/seu/workspace:/workspace:rw"
# Para dados somente leitura, use um caminho de montagem diferente
# volumes = "/caminho/para/seu/workspace:/workspace:rw,/caminho/para/grande/dataset:/data:ro"
```

Se `SANDBOX_VOLUMES` não for definido, o runtime criará um diretório temporário para o agente trabalhar.

## Exemplo de Uso

Aqui está um exemplo de como iniciar o OpenHands com o Runtime Local no Modo Headless:

```bash
# Defina o tipo de runtime como local
export RUNTIME=local

# Defina um diretório de workspace (o agente trabalha em /workspace por padrão)
export SANDBOX_VOLUMES=/caminho/para/seu/projeto:/workspace:rw
# Para dados somente leitura que você não quer que o agente modifique, use um caminho diferente
# export SANDBOX_VOLUMES=/caminho/para/seu/projeto:/workspace:rw,/caminho/para/dados/referencia:/data:ro

# Inicie o OpenHands
poetry run python -m openhands.core.main -t "escreva um script bash que imprima oi"
```

## Casos de Uso

O Runtime Local é particularmente útil para:

- Pipelines de CI/CD onde o Docker não está disponível.
- Testes e desenvolvimento do próprio OpenHands.
- Ambientes onde o uso de contêineres é restrito.

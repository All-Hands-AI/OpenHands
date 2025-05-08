# Protocolo de Contexto de Modelo (MCP)

:::note
Esta página descreve como configurar e usar o Protocolo de Contexto de Modelo (MCP) no OpenHands, permitindo que você estenda as capacidades do agente com ferramentas personalizadas.
:::

## Visão Geral

O Protocolo de Contexto de Modelo (MCP) é um mecanismo que permite ao OpenHands se comunicar com servidores de ferramentas externos. Esses servidores podem fornecer funcionalidades adicionais ao agente, como processamento especializado de dados, acesso a APIs externas ou ferramentas personalizadas. O MCP é baseado no padrão aberto definido em [modelcontextprotocol.io](https://modelcontextprotocol.io).

## Configuração

A configuração do MCP é definida na seção `[mcp]` do seu arquivo `config.toml`.

### Exemplo de Configuração

```toml
[mcp]
# Servidores SSE - Servidores externos que se comunicam via Server-Sent Events
sse_servers = [
    # Servidor SSE básico apenas com URL
    "http://example.com:8080/mcp",

    # Servidor SSE com autenticação por chave API
    {url="https://secure-example.com/mcp", api_key="your-api-key"}
]

# Servidores Stdio - Processos locais que se comunicam via entrada/saída padrão
stdio_servers = [
    # Servidor stdio básico
    {name="fetch", command="uvx", args=["mcp-server-fetch"]},

    # Servidor stdio com variáveis de ambiente
    {
        name="data-processor",
        command="python",
        args=["-m", "my_mcp_server"],
        env={
            "DEBUG": "true",
            "PORT": "8080"
        }
    }
]
```

## Opções de Configuração

### Servidores SSE

Os servidores SSE são configurados usando uma URL em string ou um objeto com as seguintes propriedades:

- `url` (obrigatório)
  - Tipo: `str`
  - Descrição: A URL do servidor SSE

- `api_key` (opcional)
  - Tipo: `str`
  - Padrão: `None`
  - Descrição: Chave API para autenticação com o servidor SSE

### Servidores Stdio

Os servidores Stdio são configurados usando um objeto com as seguintes propriedades:

- `name` (obrigatório)
  - Tipo: `str`
  - Descrição: Um nome único para o servidor

- `command` (obrigatório)
  - Tipo: `str`
  - Descrição: O comando para executar o servidor

- `args` (opcional)
  - Tipo: `lista de str`
  - Padrão: `[]`
  - Descrição: Argumentos de linha de comando para passar ao servidor

- `env` (opcional)
  - Tipo: `dicionário de str para str`
  - Padrão: `{}`
  - Descrição: Variáveis de ambiente para definir para o processo do servidor

## Como o MCP Funciona

Quando o OpenHands inicia, ele:

1. Lê a configuração MCP do `config.toml`
2. Conecta-se a quaisquer servidores SSE configurados
3. Inicia quaisquer servidores stdio configurados
4. Registra as ferramentas fornecidas por esses servidores com o agente

O agente pode então usar essas ferramentas como qualquer ferramenta integrada. Quando o agente chama uma ferramenta MCP:

1. OpenHands encaminha a chamada para o servidor MCP apropriado
2. O servidor processa a solicitação e retorna uma resposta
3. OpenHands converte a resposta em uma observação e a apresenta ao agente

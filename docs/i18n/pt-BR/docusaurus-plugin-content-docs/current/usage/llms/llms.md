# 🤖 Backends de LLM

O OpenHands pode se conectar a qualquer LLM suportado pelo LiteLLM. No entanto, ele requer um modelo poderoso para funcionar.

## Recomendações de Modelo

Com base em nossas avaliações de modelos de linguagem para tarefas de codificação (usando o conjunto de dados SWE-bench), podemos fornecer algumas recomendações para a seleção de modelos. Nossos resultados mais recentes de benchmarking podem ser encontrados nesta [planilha](https://docs.google.com/spreadsheets/d/1wOUdFCMyY6Nt0AIqF705KN4JKOWgeI4wUGUP60krXXs/edit?gid=0).

Com base nessas descobertas e no feedback da comunidade, os seguintes modelos foram verificados como funcionando razoavelmente bem com o OpenHands:

- anthropic/claude-3-5-sonnet-20241022 (recomendado)
- anthropic/claude-3-5-haiku-20241022
- deepseek/deepseek-chat
- gpt-4o

:::warning
O OpenHands enviará muitos prompts para o LLM que você configurar. A maioria desses LLMs custa dinheiro, então certifique-se de definir limites de gastos e monitorar o uso.
:::

Para obter uma lista completa dos provedores e modelos disponíveis, consulte a [documentação do litellm](https://docs.litellm.ai/docs/providers).

:::note
A maioria dos modelos locais e de código aberto atuais não são tão poderosos. Ao usar esses modelos, você pode ver longos tempos de espera entre as mensagens, respostas ruins ou erros sobre JSON malformado. O OpenHands só pode ser tão poderoso quanto os modelos que o impulsionam. No entanto, se você encontrar alguns que funcionem, adicione-os à lista verificada acima.
:::

## Configuração do LLM

O seguinte pode ser definido na interface do usuário do OpenHands por meio das Configurações:

- `Provedor LLM`
- `Modelo LLM`
- `Chave API`
- `URL Base` (através das configurações `Avançadas`)

Existem algumas configurações que podem ser necessárias para alguns LLMs/provedores que não podem ser definidas através da interface do usuário. Em vez disso, elas podem ser definidas por meio de variáveis de ambiente passadas para o comando docker run ao iniciar o aplicativo usando `-e`:

- `LLM_API_VERSION`
- `LLM_EMBEDDING_MODEL`
- `LLM_EMBEDDING_DEPLOYMENT_NAME`
- `LLM_DROP_PARAMS`
- `LLM_DISABLE_VISION`
- `LLM_CACHING_PROMPT`

Temos alguns guias para executar o OpenHands com provedores de modelo específicos:

- [Azure](llms/azure-llms)
- [Google](llms/google-llms)
- [Groq](llms/groq)
- [LiteLLM Proxy](llms/litellm-proxy)
- [OpenAI](llms/openai-llms)
- [OpenRouter](llms/openrouter)

### Novas tentativas de API e limites de taxa

Os provedores de LLM normalmente têm limites de taxa, às vezes muito baixos, e podem exigir novas tentativas. O OpenHands tentará automaticamente as solicitações novamente se receber um Erro de Limite de Taxa (código de erro 429).

Você pode personalizar essas opções conforme necessário para o provedor que está usando. Verifique a documentação deles e defina as seguintes variáveis de ambiente para controlar o número de novas tentativas e o tempo entre as novas tentativas:

- `LLM_NUM_RETRIES` (Padrão de 4 vezes)
- `LLM_RETRY_MIN_WAIT` (Padrão de 5 segundos)
- `LLM_RETRY_MAX_WAIT` (Padrão de 30 segundos)
- `LLM_RETRY_MULTIPLIER` (Padrão de 2)

Se você estiver executando o OpenHands no modo de desenvolvimento, também poderá definir essas opções no arquivo `config.toml`:

```toml
[llm]
num_retries = 4
retry_min_wait = 5
retry_max_wait = 30
retry_multiplier = 2
```

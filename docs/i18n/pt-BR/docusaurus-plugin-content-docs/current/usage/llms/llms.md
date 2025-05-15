# 🤖 Backends de LLM

:::note
Esta seção é para usuários que desejam conectar o OpenHands a diferentes LLMs.
:::

O OpenHands pode se conectar a qualquer LLM suportado pelo LiteLLM. No entanto, requer um modelo poderoso para funcionar.

## Recomendações de Modelos

Com base em nossas avaliações de modelos de linguagem para tarefas de codificação (usando o conjunto de dados SWE-bench), podemos fornecer algumas
recomendações para seleção de modelos. Nossos resultados de benchmarking mais recentes podem ser encontrados nesta [planilha](https://docs.google.com/spreadsheets/d/1wOUdFCMyY6Nt0AIqF705KN4JKOWgeI4wUGUP60krXXs/edit?gid=0).

Com base nessas descobertas e feedback da comunidade, os seguintes modelos foram verificados e funcionam razoavelmente bem com o OpenHands:

- [anthropic/claude-3-7-sonnet-20250219](https://www.anthropic.com/api) (recomendado)
- [gemini/gemini-2.5-pro](https://blog.google/technology/google-deepmind/gemini-model-thinking-updates-march-2025/)
- [deepseek/deepseek-chat](https://api-docs.deepseek.com/)
- [openai/o3-mini](https://openai.com/index/openai-o3-mini/)
- [openai/o3](https://openai.com/index/introducing-o3-and-o4-mini/)
- [openai/o4-mini](https://openai.com/index/introducing-o3-and-o4-mini/)
- [all-hands/openhands-lm-32b-v0.1](https://www.all-hands.dev/blog/introducing-openhands-lm-32b----a-strong-open-coding-agent-model) -- disponível através do [OpenRouter](https://openrouter.ai/all-hands/openhands-lm-32b-v0.1)


:::warning
O OpenHands enviará muitos prompts ao LLM que você configurar. A maioria desses LLMs custa dinheiro, então certifique-se de definir limites de gastos e monitorar o uso.
:::

Se você executou com sucesso o OpenHands com LLMs específicos que não estão na lista, adicione-os à lista verificada. Também incentivamos que você abra um PR para compartilhar seu processo de configuração e ajudar outros que usam o mesmo provedor e LLM!

Para uma lista completa dos provedores e modelos disponíveis, consulte a
[documentação do litellm](https://docs.litellm.ai/docs/providers).

:::note
A maioria dos modelos locais e de código aberto atuais não são tão poderosos. Ao usar esses modelos, você pode observar longos
tempos de espera entre mensagens, respostas ruins ou erros sobre JSON malformado. O OpenHands só pode ser tão poderoso quanto os
modelos que o impulsionam. No entanto, se você encontrar modelos que funcionem, adicione-os à lista verificada acima.
:::

## Configuração de LLM

O seguinte pode ser configurado na interface do OpenHands através das Configurações:

- `Provedor LLM`
- `Modelo LLM`
- `Chave API`
- `URL Base` (através das configurações `Avançadas`)

Existem algumas configurações que podem ser necessárias para alguns LLMs/provedores que não podem ser definidas através da interface. Em vez disso, estas
podem ser definidas através de variáveis de ambiente passadas para o comando docker run ao iniciar o aplicativo
usando `-e`:

- `LLM_API_VERSION`
- `LLM_EMBEDDING_MODEL`
- `LLM_EMBEDDING_DEPLOYMENT_NAME`
- `LLM_DROP_PARAMS`
- `LLM_DISABLE_VISION`
- `LLM_CACHING_PROMPT`

Temos alguns guias para executar o OpenHands com provedores de modelos específicos:

- [Azure](llms/azure-llms)
- [Google](llms/google-llms)
- [Groq](llms/groq)
- [LLMs Locais com SGLang ou vLLM](llms/../local-llms.md)
- [LiteLLM Proxy](llms/litellm-proxy)
- [OpenAI](llms/openai-llms)
- [OpenRouter](llms/openrouter)

### Novas tentativas de API e limites de taxa

Provedores de LLM geralmente têm limites de taxa, às vezes muito baixos, e podem exigir novas tentativas. O OpenHands automaticamente
tentará novamente as solicitações se receber um Erro de Limite de Taxa (código de erro 429).

Você pode personalizar essas opções conforme necessário para o provedor que está usando. Verifique a documentação deles e defina as
seguintes variáveis de ambiente para controlar o número de tentativas e o tempo entre elas:

- `LLM_NUM_RETRIES` (Padrão de 4 vezes)
- `LLM_RETRY_MIN_WAIT` (Padrão de 5 segundos)
- `LLM_RETRY_MAX_WAIT` (Padrão de 30 segundos)
- `LLM_RETRY_MULTIPLIER` (Padrão de 2)

Se você estiver executando o OpenHands no modo de desenvolvimento, também pode definir essas opções no arquivo `config.toml`:

```toml
[llm]
num_retries = 4
retry_min_wait = 5
retry_max_wait = 30
retry_multiplier = 2
```

Here is the translation to Brazilian Portuguese:

# Proxy LiteLLM

O OpenHands suporta o uso do [proxy LiteLLM](https://docs.litellm.ai/docs/proxy/quick_start) para acessar vários provedores de LLM.

## Configuração

Para usar o proxy LiteLLM com o OpenHands, você precisa:

1. Configurar um servidor proxy LiteLLM (veja a [documentação do LiteLLM](https://docs.litellm.ai/docs/proxy/quick_start))
2. Ao executar o OpenHands, você precisará definir o seguinte na interface do usuário do OpenHands através das Configurações:
  * Habilitar opções `Avançadas`
  * `Modelo Personalizado` para o prefixo `litellm_proxy/` + o modelo que você usará (por exemplo, `litellm_proxy/anthropic.claude-3-5-sonnet-20241022-v2:0`)
  * `URL Base` para a URL do seu proxy LiteLLM (por exemplo, `https://your-litellm-proxy.com`)
  * `Chave de API` para a chave de API do seu proxy LiteLLM

## Modelos Suportados

Os modelos suportados dependem da configuração do seu proxy LiteLLM. O OpenHands suporta qualquer modelo que o seu proxy LiteLLM esteja configurado para lidar.

Consulte a configuração do seu proxy LiteLLM para obter a lista de modelos disponíveis e seus nomes.

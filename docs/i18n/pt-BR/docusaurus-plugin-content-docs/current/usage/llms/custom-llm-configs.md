# Configurações Personalizadas de LLM

O OpenHands suporta a definição de múltiplas configurações nomeadas de LLM no seu arquivo `config.toml`. Este recurso permite que você use diferentes configurações de LLM para diferentes propósitos, como usar um modelo mais barato para tarefas que não exigem respostas de alta qualidade, ou usar diferentes modelos com diferentes parâmetros para agentes específicos.

## Como Funciona

As configurações nomeadas de LLM são definidas no arquivo `config.toml` usando seções que começam com `llm.`. Por exemplo:

```toml
# Configuração padrão de LLM
[llm]
model = "gpt-4"
api_key = "your-api-key"
temperature = 0.0

# Configuração personalizada de LLM para um modelo mais barato
[llm.gpt3]
model = "gpt-3.5-turbo"
api_key = "your-api-key"
temperature = 0.2

# Outra configuração personalizada com parâmetros diferentes
[llm.high-creativity]
model = "gpt-4"
api_key = "your-api-key"
temperature = 0.8
top_p = 0.9
```

Cada configuração nomeada herda todas as configurações da seção padrão `[llm]` e pode sobrescrever qualquer uma dessas configurações. Você pode definir quantas configurações personalizadas forem necessárias.

## Usando Configurações Personalizadas

### Com Agentes

Você pode especificar qual configuração de LLM um agente deve usar definindo o parâmetro `llm_config` na seção de configuração do agente:

```toml
[agent.RepoExplorerAgent]
# Usa a configuração mais barata do GPT-3 para este agente
llm_config = 'gpt3'

[agent.CodeWriterAgent]
# Usa a configuração de alta criatividade para este agente
llm_config = 'high-creativity'
```

### Opções de Configuração

Cada configuração nomeada de LLM suporta todas as mesmas opções que a configuração padrão de LLM. Isso inclui:

- Seleção de modelo (`model`)
- Configuração da API (`api_key`, `base_url`, etc.)
- Parâmetros do modelo (`temperature`, `top_p`, etc.)
- Configurações de repetição (`num_retries`, `retry_multiplier`, etc.)
- Limites de tokens (`max_input_tokens`, `max_output_tokens`)
- E todas as outras opções de configuração de LLM

Para uma lista completa das opções disponíveis, consulte a seção Configuração de LLM na documentação de [Opções de Configuração](../configuration-options).

## Casos de Uso

As configurações personalizadas de LLM são particularmente úteis em vários cenários:

- **Otimização de Custos**: Use modelos mais baratos para tarefas que não exigem respostas de alta qualidade, como exploração de repositório ou operações simples de arquivos.
- **Ajuste Específico de Tarefas**: Configure diferentes valores de temperature e top_p para tarefas que exigem diferentes níveis de criatividade ou determinismo.
- **Diferentes Provedores**: Use diferentes provedores de LLM ou endpoints de API para diferentes tarefas.
- **Testes e Desenvolvimento**: Alterne facilmente entre diferentes configurações de modelo durante o desenvolvimento e testes.

## Exemplo: Otimização de Custos

Um exemplo prático de uso de configurações personalizadas de LLM para otimizar custos:

```toml
# Configuração padrão usando GPT-4 para respostas de alta qualidade
[llm]
model = "gpt-4"
api_key = "your-api-key"
temperature = 0.0

# Configuração mais barata para exploração de repositório
[llm.repo-explorer]
model = "gpt-3.5-turbo"
temperature = 0.2

# Configuração para geração de código
[llm.code-gen]
model = "gpt-4"
temperature = 0.0
max_output_tokens = 2000

[agent.RepoExplorerAgent]
llm_config = 'repo-explorer'

[agent.CodeWriterAgent]
llm_config = 'code-gen'
```

Neste exemplo:
- A exploração de repositório usa um modelo mais barato, pois envolve principalmente entender e navegar pelo código
- A geração de código usa GPT-4 com um limite maior de tokens para gerar blocos de código maiores
- A configuração padrão permanece disponível para outras tarefas

# Configurações Personalizadas com Nomes Reservados

O OpenHands pode usar configurações personalizadas de LLM nomeadas com nomes reservados, para casos de uso específicos. Se você especificar o modelo e outras configurações sob os nomes reservados, então o OpenHands irá carregá-los e usá-los para um propósito específico. Até agora, uma dessas configurações está implementada: editor de rascunho.

## Configuração do Editor de Rascunho

A configuração `draft_editor` é um grupo de configurações que você pode fornecer, para especificar o modelo a ser usado para a elaboração preliminar de edições de código, para quaisquer tarefas que envolvam edição e refinamento de código. Você precisa fornecê-la na seção `[llm.draft_editor]`.

Por exemplo, você pode definir em `config.toml` um editor de rascunho assim:

```toml
[llm.draft_editor]
model = "gpt-4"
temperature = 0.2
top_p = 0.95
presence_penalty = 0.0
frequency_penalty = 0.0
```

Esta configuração:
- Usa GPT-4 para edições e sugestões de alta qualidade
- Define uma temperatura baixa (0,2) para manter a consistência, permitindo alguma flexibilidade
- Usa um valor alto de top_p (0,95) para considerar uma ampla gama de opções de tokens
- Desativa as penalidades de presença e frequência para manter o foco nas edições específicas necessárias

Use esta configuração quando quiser que um LLM faça um rascunho das edições antes de realizá-las. Em geral, pode ser útil para:
- Revisar e sugerir melhorias de código
- Refinar o conteúdo existente, mantendo seu significado principal
- Fazer alterações precisas e focadas no código ou texto

:::note
As configurações personalizadas de LLM estão disponíveis apenas quando se usa o OpenHands no modo de desenvolvimento, via `main.py` ou `cli.py`. Ao executar via `docker run`, por favor, use as opções de configuração padrão.
:::

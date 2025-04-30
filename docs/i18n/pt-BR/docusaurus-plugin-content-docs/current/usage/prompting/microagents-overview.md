# Visão Geral dos Microagentes

Os microagentes são prompts especializados que aprimoram o OpenHands com conhecimento específico de domínio, contexto específico de repositório e fluxos de trabalho específicos de tarefas. Eles ajudam fornecendo orientação especializada, automatizando tarefas comuns e garantindo práticas consistentes em todos os projetos.

## Tipos de Microagentes

Atualmente, o OpenHands suporta os seguintes tipos de microagentes:

* [Microagentes de Repositório](./microagents-repo): Contexto e diretrizes específicas do repositório para o OpenHands.
* [Microagentes Públicos](./microagents-public): Diretrizes gerais acionadas por palavras-chave para todos os usuários do OpenHands.

Quando o OpenHands trabalha com um repositório, ele:

1. Carrega instruções específicas do repositório de `.openhands/microagents/`, se presentes no repositório.
2. Carrega diretrizes gerais acionadas por palavras-chave nas conversas.
Veja os [Microagentes Públicos](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents/knowledge) atuais.

## Formato do Microagente

Todos os microagentes usam arquivos markdown com frontmatter YAML que possuem instruções especiais para ajudar o OpenHands a realizar tarefas:
```
---
name: <Nome do microagente>
type: <Tipo do Microagent>
version: <Versão do Microagent>
agent: <O tipo de agente (normalmente CodeActAgent)>
triggers:
- <Palavras-chave opcionais que acionam o microagente. Se os gatilhos forem removidos, ele sempre será incluído>
---

<Markdown com quaisquer diretrizes especiais, instruções e prompts que o OpenHands deve seguir.
Confira a documentação específica para cada microagente sobre as melhores práticas para obter mais informações.>
```

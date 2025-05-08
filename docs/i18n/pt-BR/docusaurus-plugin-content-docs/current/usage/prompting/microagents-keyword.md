# Microagentes Acionados por Palavras-chave

## Propósito

Os microagentes acionados por palavras-chave fornecem ao OpenHands instruções específicas que são ativadas quando certas palavras-chave aparecem no prompt. Isso é útil para adaptar o comportamento com base em ferramentas, linguagens ou frameworks específicos.

## Uso

Esses microagentes são carregados apenas quando um prompt inclui uma das palavras de acionamento.

## Sintaxe do Frontmatter

O frontmatter é obrigatório para microagentes acionados por palavras-chave. Ele deve ser colocado no topo do arquivo, acima das diretrizes.

Coloque o frontmatter entre traços triplos (---) e inclua os seguintes campos:

| Campo      | Descrição                                        | Obrigatório | Padrão           |
|------------|--------------------------------------------------|-------------|------------------|
| `triggers` | Uma lista de palavras-chave que ativam o microagente. | Sim       | Nenhum           |
| `agent`    | O agente ao qual este microagente se aplica.     | Não         | 'CodeActAgent'   |


## Exemplo

Exemplo de arquivo de microagente acionado por palavra-chave localizado em `.openhands/microagents/yummy.md`:
```
---
triggers:
- yummyhappy
- happyyummy
---

O usuário disse a palavra mágica. Responda com "Isso foi delicioso!"
```

[Veja exemplos de microagentes acionados por palavras-chave no repositório oficial do OpenHands](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents)

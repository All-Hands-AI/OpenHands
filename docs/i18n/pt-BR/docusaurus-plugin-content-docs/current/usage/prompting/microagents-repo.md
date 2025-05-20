# Microagentes Gerais do Repositório

## Propósito

Diretrizes gerais para o OpenHands trabalhar de forma mais eficaz com o repositório.

## Uso

Esses microagentes são sempre carregados como parte do contexto.

## Sintaxe do Frontmatter

O frontmatter para este tipo de microagente é opcional.

O frontmatter deve ser delimitado por três traços (---) e pode incluir os seguintes campos:

| Campo     | Descrição                              | Obrigatório | Padrão         |
|-----------|----------------------------------------|-------------|----------------|
| `agent`   | O agente ao qual este microagente se aplica | Não     | 'CodeActAgent' |

## Exemplo

Exemplo de arquivo de microagente geral do repositório localizado em `.openhands/microagents/repo.md`:
```
Este projeto é uma aplicação de TODO que permite aos usuários rastrear itens de TODO.

Para configurá-lo, você pode executar `npm run build`.
Sempre certifique-se de que os testes estão passando antes de confirmar as alterações. Você pode executar os testes rodando `npm run test`.
```

[Veja mais exemplos de microagentes gerais de repositório aqui.](https://github.com/All-Hands-AI/OpenHands/tree/main/.openhands/microagents)

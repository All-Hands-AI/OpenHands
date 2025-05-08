# Visão Geral dos Microagentes

Microagentes são prompts especializados que aprimoram o OpenHands com conhecimento específico de domínio.
Eles fornecem orientação especializada, automatizam tarefas comuns e garantem práticas consistentes em todos os projetos.

## Tipos de Microagentes

Atualmente, o OpenHands suporta os seguintes tipos de microagentes:

- [Microagentes Gerais de Repositório](./microagents-repo): Diretrizes gerais para o OpenHands sobre o repositório.
- [Microagentes Ativados por Palavras-chave](./microagents-keyword): Diretrizes ativadas por palavras-chave específicas nos prompts.

Para personalizar o comportamento do OpenHands, crie um diretório .openhands/microagents/ na raiz do seu repositório e
adicione arquivos `<nome_do_microagente>.md` dentro dele.

:::note
Os microagentes carregados ocupam espaço na janela de contexto.
Esses microagentes, juntamente com as mensagens do usuário, informam o OpenHands sobre a tarefa e o ambiente.
:::

Exemplo de estrutura de repositório:

```
some-repository/
└── .openhands/
    └── microagents/
        └── repo.md            # Diretrizes gerais do repositório
        └── trigger_this.md    # Microagente ativado por palavras-chave específicas
        └── trigger_that.md    # Microagente ativado por palavras-chave específicas
```

## Requisitos de Frontmatter para Microagentes

Cada arquivo de microagente pode incluir frontmatter que fornece informações adicionais. Em alguns casos, este frontmatter
é obrigatório:

| Tipo de Microagente                   | Obrigatório |
|---------------------------------------|-------------|
| `Microagentes Gerais de Repositório`  | Não         |
| `Microagentes Ativados por Palavras-chave` | Sim        |

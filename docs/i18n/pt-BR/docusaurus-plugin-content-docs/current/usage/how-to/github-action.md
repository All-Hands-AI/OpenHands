# Usando a Ação do GitHub OpenHands

Este guia explica como usar a Ação do GitHub OpenHands, tanto dentro do repositório OpenHands quanto em seus próprios projetos.

## Usando a Ação no Repositório OpenHands

Para usar a Ação do GitHub OpenHands em um repositório, você pode:

1. Criar uma issue no repositório.
2. Adicionar a etiqueta `fix-me` à issue ou deixar um comentário na issue começando com `@openhands-agent`.

A ação será acionada automaticamente e tentará resolver a issue.

## Instalando a Ação em um Novo Repositório

Para instalar a Ação do GitHub OpenHands em seu próprio repositório, siga o [README para o OpenHands Resolver](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/resolver/README.md).

## Dicas de Uso

### Resolução Iterativa

1. Crie uma issue no repositório.
2. Adicione a etiqueta `fix-me` à issue ou deixe um comentário começando com `@openhands-agent`.
3. Revise a tentativa de resolver a issue verificando o pull request.
4. Faça um acompanhamento com feedback por meio de comentários gerais, comentários de revisão ou comentários de thread inline.
5. Adicione a etiqueta `fix-me` ao pull request ou aborde um comentário específico começando com `@openhands-agent`.

### Etiqueta versus Macro

- Etiqueta (`fix-me`): Solicita ao OpenHands que aborde a issue ou pull request **inteiro**.
- Macro (`@openhands-agent`): Solicita ao OpenHands que considere apenas a descrição da issue/pull request e **o comentário específico**.

## Configurações Avançadas

### Adicionar configurações personalizadas do repositório

Você pode fornecer instruções personalizadas para o OpenHands seguindo o [README para o resolver](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/resolver/README.md#providing-custom-instructions).

### Configurações personalizadas

O GitHub resolver verificará automaticamente se há [segredos do repositório](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions?tool=webui#creating-secrets-for-a-repository) ou [variáveis do repositório](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/store-information-in-variables#creating-configuration-variables-for-a-repository) válidos para personalizar seu comportamento.
As opções de personalização que você pode definir são:

| **Nome do atributo**             | **Tipo** | **Finalidade**                                                                                       | **Exemplo**                                        |
| -------------------------------- | -------- | --------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `LLM_MODEL`                      | Variável | Definir o LLM a ser usado com o OpenHands                                                           | `LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"` |
| `OPENHANDS_MAX_ITER`             | Variável | Definir o limite máximo de iterações do agente                                                      | `OPENHANDS_MAX_ITER=10`                            |
| `OPENHANDS_MACRO`                | Variável | Personalizar a macro padrão para invocar o resolver                                                 | `OPENHANDS_MACRO=@resolveit`                       |
| `OPENHANDS_BASE_CONTAINER_IMAGE` | Variável | Sandbox personalizado ([saiba mais](https://docs.all-hands.dev/modules/usage/how-to/custom-sandbox-guide)) | `OPENHANDS_BASE_CONTAINER_IMAGE="custom_image"`    |
| `TARGET_BRANCH`                  | Variável | Mesclar em um branch diferente de `main`                                                            | `TARGET_BRANCH="dev"`                              |

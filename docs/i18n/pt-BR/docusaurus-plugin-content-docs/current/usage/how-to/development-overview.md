---
sidebar_position: 9
---

# Visão Geral do Desenvolvimento

Este guia fornece uma visão geral dos principais recursos de documentação disponíveis no repositório OpenHands. Se você está procurando contribuir, entender a arquitetura ou trabalhar em componentes específicos, esses recursos irão ajudá-lo a navegar pelo codebase de forma eficaz.

## Documentação Principal

### Fundamentos do Projeto
- **Visão Geral do Projeto Principal** (`/README.md`)
  O ponto de entrada principal para entender o OpenHands, incluindo recursos e instruções básicas de configuração.

- **Guia de Desenvolvimento** (`/Development.md`)
  Guia abrangente para desenvolvedores que trabalham no OpenHands, incluindo configuração, requisitos e fluxos de trabalho de desenvolvimento.

- **Diretrizes de Contribuição** (`/CONTRIBUTING.md`)
  Informações essenciais para contribuidores, abrangendo estilo de código, processo de PR e fluxos de trabalho de contribuição.

### Documentação de Componentes

#### Frontend
- **Aplicação Frontend** (`/frontend/README.md`)
  Guia completo para configurar e desenvolver a aplicação frontend baseada em React.

#### Backend
- **Implementação do Backend** (`/openhands/README.md`)
  Documentação detalhada da implementação e arquitetura do backend em Python.

- **Documentação do Servidor** (`/openhands/server/README.md`)
  Detalhes de implementação do servidor, documentação da API e arquitetura de serviços.

- **Ambiente de Execução** (`/openhands/runtime/README.md`)
  Documentação abrangendo o ambiente de execução, modelo de execução e configurações de tempo de execução.

#### Infraestrutura
- **Documentação de Contêineres** (`/containers/README.md`)
  Informações abrangentes sobre contêineres Docker, estratégias de implantação e gerenciamento de contêineres.

### Testes e Avaliação
- **Guia de Testes Unitários** (`/tests/unit/README.md`)
  Instruções para escrever, executar e manter testes unitários.

- **Framework de Avaliação** (`/evaluation/README.md`)
  Documentação para o framework de avaliação, benchmarks e testes de desempenho.

### Recursos Avançados
- **Arquitetura de Microagentes** (`/microagents/README.md`)
  Informações detalhadas sobre a arquitetura, implementação e uso de microagentes.

### Padrões de Documentação
- **Guia de Estilo de Documentação** (`/docs/DOC_STYLE_GUIDE.md`)
  Padrões e diretrizes para escrever e manter a documentação do projeto.

## Começando com o Desenvolvimento

Se você é novo no desenvolvimento com OpenHands, recomendamos seguir esta sequência:

1. Comece com o `README.md` principal para entender o propósito e os recursos do projeto
2. Revise as diretrizes em `CONTRIBUTING.md` se você planeja contribuir
3. Siga as instruções de configuração em `Development.md`
4. Mergulhe na documentação de componentes específicos com base na sua área de interesse:
   - Desenvolvedores frontend devem se concentrar em `/frontend/README.md`
   - Desenvolvedores backend devem começar com `/openhands/README.md`
   - O trabalho de infraestrutura deve começar com `/containers/README.md`

## Atualizações da Documentação

Ao fazer alterações no codebase, certifique-se de que:
1. A documentação relevante seja atualizada para refletir suas alterações
2. Novos recursos sejam documentados nos arquivos README apropriados
3. Quaisquer alterações na API sejam refletidas na documentação do servidor
4. A documentação siga o guia de estilo em `/docs/DOC_STYLE_GUIDE.md`

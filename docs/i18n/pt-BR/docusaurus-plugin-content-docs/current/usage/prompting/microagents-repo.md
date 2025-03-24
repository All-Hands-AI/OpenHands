# Microagentes de Repositório

## Visão Geral

O OpenHands pode ser personalizado para trabalhar de forma mais eficaz com repositórios específicos, fornecendo contexto
e diretrizes específicas do repositório. Esta seção explica como otimizar o OpenHands para o seu projeto.

## Criando um Micro-Agente de Repositório

Você pode personalizar o comportamento do OpenHands para o seu repositório criando um diretório `.openhands/microagents/` na raiz do seu repositório.
No mínimo, ele deve conter o arquivo
`.openhands/microagents/repo.md`, que inclui instruções que serão
fornecidas ao agente toda vez que ele trabalhar com este repositório.

### Melhores Práticas para Microagentes de Repositório

- **Mantenha as Instruções Atualizadas**: Atualize regularmente o seu diretório `.openhands/microagents/` à medida que o seu projeto evolui.
- **Seja Específico**: Inclua caminhos, padrões e requisitos específicos exclusivos do seu projeto.
- **Documente as Dependências**: Liste todas as ferramentas e dependências necessárias para o desenvolvimento.
- **Inclua Exemplos**: Forneça exemplos de bons padrões de código do seu projeto.
- **Especifique Convenções**: Documente convenções de nomenclatura, organização de arquivos e preferências de estilo de código.

### Etapas para Criar um Microagente de Repositório

#### 1. Planeje o Microagente de Repositório
Ao criar um micro-agente específico para um repositório, sugerimos incluir as seguintes informações:
- **Visão Geral do Repositório**: Uma breve descrição do propósito e arquitetura do seu projeto.
- **Estrutura de Diretórios**: Diretórios-chave e seus propósitos.
- **Diretrizes de Desenvolvimento**: Padrões e práticas de codificação específicas do projeto.
- **Requisitos de Teste**: Como executar testes e quais tipos de testes são necessários.
- **Instruções de Configuração**: Etapas necessárias para construir e executar o projeto.

#### 2. Crie o Arquivo

Crie um arquivo em seu repositório em `.openhands/microagents/` (Exemplo: `.openhands/microagents/repo.md`)

Atualize o arquivo com o frontmatter necessário [de acordo com o formato exigido](./microagents-overview#microagent-format)
e as diretrizes especializadas necessárias para o seu repositório.

### Exemplo de Microagente de Repositório

```
---
name: repo
type: repo
agent: CodeActAgent
---

Repository: MeuProjeto
Description: Uma aplicação web para gerenciamento de tarefas

Directory Structure:
- src/: Código principal da aplicação
- tests/: Arquivos de teste
- docs/: Documentação

Setup:
- Execute `npm install` para instalar as dependências
- Use `npm run dev` para desenvolvimento
- Execute `npm test` para testes

Guidelines:
- Siga a configuração do ESLint
- Escreva testes para todos os novos recursos
- Use TypeScript para novo código

Se adicionar um novo componente em src/components, sempre adicione testes unitários apropriados em tests/components/.
```

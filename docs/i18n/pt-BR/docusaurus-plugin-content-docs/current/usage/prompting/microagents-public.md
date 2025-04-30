# Microagentes Públicos

## Visão Geral

Microagentes públicos são diretrizes especializadas acionadas por palavras-chave para todos os usuários do OpenHands.
Eles são definidos em arquivos markdown no diretório
[`microagents/`](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents).

Microagentes públicos:
- Monitoram comandos recebidos em busca de suas palavras-chave de acionamento.
- São ativados quando os gatilhos relevantes são detectados.
- Aplicam seus conhecimentos e capacidades especializados.
- Seguem suas diretrizes e restrições específicas.

## Microagentes Públicos Atuais

Para mais informações sobre microagentes específicos, consulte seus arquivos de documentação individuais no
diretório [`microagents/`](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents/).

### Agente GitHub
**Arquivo**: `github.md`
**Gatilhos**: `github`, `git`

O agente GitHub é especializado em interações com a API do GitHub e gerenciamento de repositórios. Ele:
- Tem acesso a um `GITHUB_TOKEN` para autenticação na API.
- Segue diretrizes rígidas para interações com repositórios.
- Lida com gerenciamento de branches e pull requests.
- Usa a API do GitHub em vez de interações com navegador web.

Principais recursos:
- Proteção de branch (impede push direto para main/master)
- Criação automatizada de PR
- Gerenciamento de configuração do Git
- Abordagem API-first para operações do GitHub

Exemplo de Uso:

```bash
git checkout -b feature-branch
git commit -m "Add new feature"
git push origin feature-branch
```

### Agente NPM
**Arquivo**: `npm.md`
**Gatilhos**: `npm`

Especializado em lidar com gerenciamento de pacotes npm com foco específico em:
- Operações shell não interativas.
- Tratamento automatizado de confirmação usando o comando Unix 'yes'.
- Automação de instalação de pacotes.

Exemplo de Uso:

```bash
yes | npm install package-name
```

## Contribuindo com um Microagente Público

Você pode criar seus próprios microagentes públicos adicionando novos arquivos markdown ao
diretório [`microagents/`](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents/).

### Melhores Práticas para Microagentes Públicos

- **Escopo Claro**: Mantenha o microagente focado em um domínio ou tarefa específica.
- **Instruções Explícitas**: Forneça diretrizes claras e inequívocas.
- **Exemplos Úteis**: Inclua exemplos práticos de casos de uso comuns.
- **Segurança em Primeiro Lugar**: Inclua avisos e restrições necessárias.
- **Consciência de Integração**: Considere como o microagente interage com outros componentes.

### Etapas para Contribuir com um Microagente Público

#### 1. Planeje o Microagente Público

Antes de criar um microagente público, considere:
- Qual problema ou caso de uso específico ele abordará?
- Quais capacidades ou conhecimentos únicos ele deve ter?
- Quais palavras-chave fazem sentido para ativá-lo?
- Quais restrições ou diretrizes ele deve seguir?

#### 2. Crie o Arquivo

Crie um novo arquivo markdown em [`microagents/`](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents/)
com um nome descritivo (por exemplo, `docker.md` para um agente focado em Docker).

Atualize o arquivo com o frontmatter necessário [de acordo com o formato exigido](./microagents-overview#microagent-format)
e as diretrizes especializadas necessárias, seguindo as [melhores práticas acima](#melhores-práticas-para-microagentes-públicos).

#### 3. Testando o Microagente Público

- Teste o agente com vários prompts.
- Verifique se as palavras-chave acionam o agente corretamente.
- Certifique-se de que as instruções estão claras e abrangentes.
- Verifique possíveis conflitos com agentes existentes.

#### 4. Processo de Envio

Envie um pull request com:
- O novo arquivo do microagente.
- Documentação atualizada, se necessário.
- Descrição do propósito e das capacidades do agente.

### Exemplo de Implementação de Microagente Público

Aqui está um modelo para um novo microagente:

```markdown
---
name: docker
agent: CodeActAgent
triggers:
- docker
- container
---

Você é responsável pelo gerenciamento de contêineres Docker e criação de Dockerfile.

Principais responsabilidades:
1. Criar e modificar Dockerfiles
2. Gerenciar o ciclo de vida do contêiner
3. Lidar com configurações do Docker Compose

Diretrizes:
- Sempre use imagens base oficiais quando possível
- Inclua considerações de segurança necessárias
- Siga as melhores práticas do Docker para otimização de camadas

Exemplos:
1. Criando um Dockerfile:
   FROM node:18-alpine
   WORKDIR /app
   COPY package*.json ./
   RUN npm install
   COPY . .
   CMD ["npm", "start"]

2. Uso do Docker Compose:
   version: '3'
   services:
     web:
       build: .
       ports:
         - "3000:3000"

Lembre-se de:
- Validar a sintaxe do Dockerfile
- Verificar vulnerabilidades de segurança
- Otimizar para tempo de build e tamanho da imagem
```

Veja os [microagentes públicos atuais](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents) para
mais exemplos.

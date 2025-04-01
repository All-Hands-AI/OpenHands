# Modo GUI

O OpenHands fornece um modo de Interface Gráfica do Usuário (GUI) para interagir com o assistente de IA.

## Instalação e Configuração

1. Siga as instruções de instalação para instalar o OpenHands.
2. Após executar o comando, acesse o OpenHands em [http://localhost:3000](http://localhost:3000).

## Interagindo com a GUI

### Configuração Inicial

1. No primeiro lançamento, você verá uma página de configurações.
2. Selecione um `Provedor de LLM` e um `Modelo de LLM` nos menus suspensos. Se o modelo necessário não existir na lista,
   ative as opções `Avançadas` e insira-o com o prefixo correto na caixa de texto `Modelo Personalizado`.
3. Insira a `Chave de API` correspondente para o provedor escolhido.
4. Clique em `Salvar Alterações` para aplicar as configurações.

### Tokens de Controle de Versão

O OpenHands suporta múltiplos provedores de controle de versão. Você pode configurar tokens para vários provedores simultaneamente.

#### Configuração do Token do GitHub

O OpenHands exporta automaticamente um `GITHUB_TOKEN` para o ambiente shell se ele estiver disponível. Isso pode acontecer de duas maneiras:

**Instalação Local**: O usuário insere diretamente seu token do GitHub.
<details>
  <summary>Configurando um Token do GitHub</summary>

  1. **Gere um Personal Access Token (PAT)**:
   - No GitHub, vá para Settings > Developer Settings > Personal Access Tokens > Tokens (classic).
   - **New token (classic)**
     - Escopos necessários:
     - `repo` (Controle total de repositórios privados)
   - **Fine-Grained Tokens**
     - All Repositories (Você pode selecionar repositórios específicos, mas isso afetará o que retorna na pesquisa de repositórios)
     - Minimal Permissions (Selecione **Meta Data = Read-only** para pesquisa, **Pull Requests = Read and Write**, **Content = Read and Write** para criação de branches)
  2. **Insira o Token no OpenHands**:
   - Clique no botão Settings (ícone de engrenagem).
   - Navegue até a seção `Git Provider Settings`.
   - Cole seu token no campo `GitHub Token`.
   - Clique em `Save Changes` para aplicar as alterações.
</details>

<details>
  <summary>Políticas de Token Organizacional</summary>

  Se você estiver trabalhando com repositórios organizacionais, configurações adicionais podem ser necessárias:

  1. **Verifique os Requisitos da Organização**:
   - Os administradores da organização podem impor políticas específicas de token.
   - Algumas organizações exigem que os tokens sejam criados com SSO habilitado.
   - Revise as [configurações de política de token](https://docs.github.com/en/organizations/managing-programmatic-access-to-your-organization/setting-a-personal-access-token-policy-for-your-organization) da sua organização.
  2. **Verifique o Acesso à Organização**:
   - Vá para as configurações do seu token no GitHub.
   - Procure a organização em `Organization access`.
   - Se necessário, clique em `Enable SSO` ao lado da sua organização.
   - Conclua o processo de autorização SSO.
</details>

<details>
  <summary>Solução de Problemas</summary>

  Problemas comuns e soluções:

  - **Token Não Reconhecido**:
     - Certifique-se de que o token esteja salvo corretamente nas configurações.
     - Verifique se o token não expirou.
     - Verifique se o token possui os escopos necessários.
     - Tente regenerar o token.

  - **Acesso à Organização Negado**:
     - Verifique se o SSO é necessário, mas não está habilitado.
     - Verifique a associação à organização.
     - Entre em contato com o administrador da organização se as políticas de token estiverem bloqueando o acesso.

  - **Verificando se o Token Funciona**:
     - O aplicativo mostrará uma marca de seleção verde se o token for válido.
     - Tente acessar um repositório para confirmar as permissões.
     - Verifique o console do navegador em busca de mensagens de erro.
</details>

**OpenHands Cloud**: O token é obtido por meio da autenticação OAuth do GitHub.

<details>
  <summary>Autenticação OAuth</summary>

  Ao usar o OpenHands Cloud, o fluxo OAuth do GitHub solicita as seguintes permissões:
   - Acesso ao repositório (leitura/escrita)
   - Gerenciamento de fluxo de trabalho
   - Acesso de leitura à organização

  Para autenticar o OpenHands:
   - Clique em `Sign in with GitHub` quando solicitado.
   - Revise as permissões solicitadas.
   - Autorize o OpenHands a acessar sua conta do GitHub.
   - Se estiver usando uma organização, autorize o acesso à organização se solicitado.
</details>

#### Configuração do Token do GitLab

O OpenHands exporta automaticamente um `GITLAB_TOKEN` para o ambiente shell, apenas para instalações locais, se ele estiver disponível.

<details>
  <summary>Configurando um Token do GitLab</summary>

  1. **Gere um Personal Access Token (PAT)**:
   - No GitLab, vá para User Settings > Access Tokens.
   - Crie um novo token com os seguintes escopos:
     - `api` (Acesso à API)
     - `read_user` (Leitura de informações do usuário)
     - `read_repository` (Leitura do repositório)
     - `write_repository` (Escrita no repositório)
   - Defina uma data de expiração ou deixe em branco para um token sem expiração.
  2. **Insira o Token no OpenHands**:
   - Clique no botão Settings (ícone de engrenagem).
   - Navegue até a seção `Git Provider Settings`.
   - Cole seu token no campo `GitLab Token`.
   - Se estiver usando GitLab auto-hospedado, insira a URL da sua instância GitLab.
   - Clique em `Save Changes` para aplicar as alterações.
</details>

<details>
  <summary>Solução de Problemas</summary>

  Problemas comuns e soluções:

  - **Token Não Reconhecido**:
     - Certifique-se de que o token esteja salvo corretamente nas configurações.
     - Verifique se o token não expirou.
     - Verifique se o token possui os escopos necessários.
     - Para instâncias auto-hospedadas, verifique a URL correta da instância.

  - **Acesso Negado**:
     - Verifique as permissões de acesso ao projeto.
     - Verifique se o token possui os escopos necessários.
     - Para repositórios de grupo/organização, certifique-se de ter o acesso adequado.
</details>

### Configurações Avançadas

1. Dentro da página Settings, ative as opções `Advanced` para acessar configurações adicionais.
2. Use a caixa de texto `Custom Model` para inserir manualmente um modelo se ele não estiver na lista.
3. Especifique uma `Base URL` se necessário para o seu provedor de LLM.

### Interagindo com a IA

1. Digite seu prompt na caixa de entrada.
2. Clique no botão de envio ou pressione Enter para enviar sua mensagem.
3. A IA processará sua entrada e fornecerá uma resposta na janela de chat.
4. Você pode continuar a conversa fazendo perguntas de acompanhamento ou fornecendo informações adicionais.

## Dicas para Uso Eficaz

- Seja específico em suas solicitações para obter as respostas mais precisas e úteis, conforme descrito nas [melhores práticas de prompting](../prompting/prompting-best-practices).
- Use o painel de workspace para explorar a estrutura do seu projeto.
- Use um dos modelos recomendados, conforme descrito na seção [LLMs](usage/llms/llms.md).

Lembre-se, o modo GUI do OpenHands é projetado para tornar sua interação com o assistente de IA o mais suave e intuitiva
possível. Não hesite em explorar seus recursos para maximizar sua produtividade.

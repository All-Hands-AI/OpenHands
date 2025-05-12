# Modo GUI

O OpenHands oferece um modo de Interface Gráfica do Usuário (GUI) para interagir com o assistente de IA.

## Instalação e Configuração

1. Siga as instruções de instalação para instalar o OpenHands.
2. Após executar o comando, acesse o OpenHands em [http://localhost:3000](http://localhost:3000).

## Interagindo com a GUI

### Configuração Inicial

1. No primeiro lançamento, você verá um popup de configurações.
2. Selecione um `Provedor LLM` e `Modelo LLM` nos menus suspensos. Se o modelo necessário não existir na lista,
   selecione `ver configurações avançadas`. Em seguida, ative as opções `Avançadas` e insira-o com o prefixo correto na
   caixa de texto `Modelo Personalizado`.
3. Insira a `Chave API` correspondente para o provedor escolhido.
4. Clique em `Salvar Alterações` para aplicar as configurações.

### Tokens de Controle de Versão

O OpenHands suporta vários provedores de controle de versão. Você pode configurar tokens para vários provedores simultaneamente.

#### Configuração do Token do GitHub

O OpenHands exporta automaticamente um `GITHUB_TOKEN` para o ambiente shell se fornecido:

<details>
  <summary>Configurando um Token do GitHub</summary>

  1. **Gerar um Token de Acesso Pessoal (PAT)**:
   - No GitHub, vá para Configurações > Configurações de Desenvolvedor > Tokens de Acesso Pessoal > Tokens (clássico).
   - **Novo token (clássico)**
     - Escopos necessários:
     - `repo` (Controle total de repositórios privados)
   - **Tokens de Granularidade Fina**
     - Todos os Repositórios (Você pode selecionar repositórios específicos, mas isso afetará o que retorna na pesquisa de repositórios)
     - Permissões Mínimas (Selecione `Meta Dados = Somente leitura` para pesquisa, `Pull Requests = Leitura e Escrita` e `Conteúdo = Leitura e Escrita` para criação de branches)
  2. **Inserir Token no OpenHands**:
   - Clique no botão Configurações (ícone de engrenagem).
   - Cole seu token no campo `Token do GitHub`.
   - Clique em `Salvar` para aplicar as alterações.
</details>

<details>
  <summary>Políticas de Token Organizacional</summary>

  Se você estiver trabalhando com repositórios organizacionais, configurações adicionais podem ser necessárias:

  1. **Verificar Requisitos da Organização**:
   - Administradores da organização podem impor políticas específicas de token.
   - Algumas organizações exigem que tokens sejam criados com SSO habilitado.
   - Revise as [configurações de política de token](https://docs.github.com/en/organizations/managing-programmatic-access-to-your-organization/setting-a-personal-access-token-policy-for-your-organization) da sua organização.
  2. **Verificar Acesso à Organização**:
   - Vá para as configurações do seu token no GitHub.
   - Procure pela organização em `Acesso à Organização`.
   - Se necessário, clique em `Habilitar SSO` ao lado da sua organização.
   - Complete o processo de autorização SSO.
</details>

<details>
  <summary>Solução de Problemas</summary>

  Problemas comuns e soluções:

  - **Token Não Reconhecido**:
     - Certifique-se de que o token está devidamente salvo nas configurações.
     - Verifique se o token não expirou.
     - Confirme se o token tem os escopos necessários.
     - Tente regenerar o token.

  - **Acesso à Organização Negado**:
     - Verifique se o SSO é necessário, mas não está habilitado.
     - Confirme a associação à organização.
     - Contate o administrador da organização se as políticas de token estiverem bloqueando o acesso.

  - **Verificando se o Token Funciona**:
     - O aplicativo mostrará uma marca de verificação verde se o token for válido.
     - Tente acessar um repositório para confirmar as permissões.
     - Verifique o console do navegador para mensagens de erro.
</details>

#### Configuração do Token do GitLab

O OpenHands exporta automaticamente um `GITLAB_TOKEN` para o ambiente shell se fornecido:

<details>
  <summary>Configurando um Token do GitLab</summary>

  1. **Gerar um Token de Acesso Pessoal (PAT)**:
   - No GitLab, vá para Configurações do Usuário > Tokens de Acesso.
   - Crie um novo token com os seguintes escopos:
     - `api` (Acesso à API)
     - `read_user` (Ler informações do usuário)
     - `read_repository` (Ler repositório)
     - `write_repository` (Escrever no repositório)
   - Defina uma data de expiração ou deixe em branco para um token sem expiração.
  2. **Inserir Token no OpenHands**:
   - Clique no botão Configurações (ícone de engrenagem).
   - Cole seu token no campo `Token do GitLab`.
   - Insira a URL da sua instância GitLab se estiver usando GitLab auto-hospedado.
   - Clique em `Salvar` para aplicar as alterações.
</details>

<details>
  <summary>Solução de Problemas</summary>

  Problemas comuns e soluções:

  - **Token Não Reconhecido**:
     - Certifique-se de que o token está devidamente salvo nas configurações.
     - Verifique se o token não expirou.
     - Confirme se o token tem os escopos necessários.
     - Para instâncias auto-hospedadas, verifique se a URL da instância está correta.

  - **Acesso Negado**:
     - Verifique as permissões de acesso ao projeto.
     - Confirme se o token tem os escopos necessários.
     - Para repositórios de grupo/organização, certifique-se de ter o acesso adequado.
</details>

### Configurações Avançadas

1. Na página de Configurações, ative as opções `Avançadas` para acessar configurações adicionais.
2. Use a caixa de texto `Modelo Personalizado` para inserir manualmente um modelo se ele não estiver na lista.
3. Especifique uma `URL Base` se necessário pelo seu provedor LLM.

### Interagindo com a IA

1. Digite seu prompt na caixa de entrada.
2. Clique no botão de enviar ou pressione Enter para enviar sua mensagem.
3. A IA processará sua entrada e fornecerá uma resposta na janela de chat.
4. Você pode continuar a conversa fazendo perguntas de acompanhamento ou fornecendo informações adicionais.

## Dicas para Uso Eficaz

- Seja específico em suas solicitações para obter respostas mais precisas e úteis, conforme descrito nas [melhores práticas de prompt](../prompting/prompting-best-practices).
- Use um dos modelos recomendados, conforme descrito na [seção LLMs](usage/llms/llms.md).

Lembre-se, o modo GUI do OpenHands foi projetado para tornar sua interação com o assistente de IA o mais suave e intuitiva
possível. Não hesite em explorar seus recursos para maximizar sua produtividade.

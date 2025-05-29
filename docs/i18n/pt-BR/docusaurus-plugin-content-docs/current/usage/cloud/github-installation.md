# Instalação do GitHub

Este guia orienta você pelo processo de instalação e configuração do OpenHands Cloud para seus repositórios GitHub.

## Pré-requisitos

- Uma conta GitHub
- Acesso ao OpenHands Cloud

## Passos de Instalação

1. Faça login no [OpenHands Cloud](https://app.all-hands.dev)
2. Se você ainda não conectou sua conta GitHub:
   - Clique em `Conectar ao GitHub`
   - Revise e aceite os termos de serviço
   - Autorize a aplicação OpenHands AI

## Adicionando Acesso ao Repositório

Você pode conceder ao OpenHands acesso a repositórios específicos:

1. Clique no menu suspenso `Selecionar um projeto GitHub`, depois selecione `Adicionar mais repositórios...`
2. Selecione sua organização e escolha os repositórios específicos para conceder acesso ao OpenHands.
   - OpenHands solicita tokens de curta duração (expiração de 8 horas) com estas permissões:
     - Ações: Leitura e escrita
     - Administração: Somente leitura
     - Status de commit: Leitura e escrita
     - Conteúdos: Leitura e escrita
     - Issues: Leitura e escrita
     - Metadados: Somente leitura
     - Pull requests: Leitura e escrita
     - Webhooks: Leitura e escrita
     - Workflows: Leitura e escrita
   - O acesso ao repositório para um usuário é concedido com base em:
     - Permissão concedida para o repositório
     - Permissões do GitHub do usuário (proprietário/colaborador)
3. Clique em `Instalar e Autorizar`

![Adicionando acesso ao repositório ao OpenHands](/img/cloud/add-repo.png)

## Modificando o Acesso ao Repositório

Você pode modificar o acesso ao repositório a qualquer momento:
* Usando o mesmo fluxo de trabalho `Selecionar um projeto GitHub > Adicionar mais repositórios`, ou
* Visitando a página de Configurações e selecionando `Configurar Repositórios GitHub` na seção `Configurações do GitHub`.

## Usando OpenHands com GitHub

Depois de conceder acesso ao repositório, você pode usar o OpenHands com seus repositórios GitHub.

Para detalhes sobre como usar o OpenHands com issues e pull requests do GitHub, consulte a documentação do [Resolvedor de Problemas na Nuvem](./cloud-issue-resolver.md).

## Próximos Passos

- [Acesse a Interface da Nuvem](./cloud-ui.md) para interagir com a interface web
- [Use o Resolvedor de Problemas na Nuvem](./cloud-issue-resolver.md) para automatizar correções de código e obter assistência
- [Use a API da Nuvem](./cloud-api.md) para interagir programaticamente com o OpenHands

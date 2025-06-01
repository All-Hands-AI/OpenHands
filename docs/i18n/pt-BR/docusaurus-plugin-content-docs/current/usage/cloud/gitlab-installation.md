# Instalação do GitLab

Este guia orienta você pelo processo de instalação e configuração do OpenHands Cloud para seus repositórios GitLab.

## Pré-requisitos

- Uma conta GitLab
- Acesso ao OpenHands Cloud

## Passos de Instalação

1. Faça login no [OpenHands Cloud](https://app.all-hands.dev)
2. Se você ainda não conectou sua conta GitLab:
   - Clique em `Conectar ao GitLab`
   - Revise e aceite os termos de serviço
   - Autorize a aplicação OpenHands AI

## Adicionando Acesso ao Repositório

Você pode conceder ao OpenHands acesso a repositórios específicos:

1. Clique no menu suspenso `Selecionar um projeto GitLab`, depois selecione `Adicionar mais repositórios...`
2. Selecione sua organização e escolha os repositórios específicos para conceder acesso ao OpenHands.
   - OpenHands solicita permissões com estes escopos:
     - api: Acesso completo à API
     - read_user: Ler informações do usuário
     - read_repository: Ler informações do repositório
     - write_repository: Escrever no repositório
   - O acesso ao repositório para um usuário é concedido com base em:
     - Permissão concedida para o repositório
     - Permissões do GitLab do usuário (proprietário/mantenedor/desenvolvedor)
3. Clique em `Instalar e Autorizar`

## Modificando o Acesso ao Repositório

Você pode modificar o acesso ao repositório a qualquer momento:
* Usando o mesmo fluxo de trabalho `Selecionar um projeto GitLab > Adicionar mais repositórios`, ou
* Visitando a página de Configurações e selecionando `Configurar Repositórios GitLab` na seção `Configurações do GitLab`.

## Usando OpenHands com GitLab

Depois de conceder acesso ao repositório, você pode usar o OpenHands com seus repositórios GitLab.

Para detalhes sobre como usar o OpenHands com issues e merge requests do GitLab, consulte a documentação do [Resolvedor de Problemas na Nuvem](./cloud-issue-resolver.md).

## Próximos Passos

- [Acesse a Interface da Nuvem](./cloud-ui.md) para interagir com a interface web
- [Use o Resolvedor de Problemas na Nuvem](./cloud-issue-resolver.md) para automatizar correções de código e obter assistência
- [Use a API da Nuvem](./cloud-api.md) para interagir programaticamente com o OpenHands

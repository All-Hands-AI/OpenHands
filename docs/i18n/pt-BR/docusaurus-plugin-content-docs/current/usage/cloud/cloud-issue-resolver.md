# Resolvedor de Problemas na Nuvem

O Resolvedor de Problemas na Nuvem automatiza correções de código e fornece assistência inteligente para seus repositórios no GitHub e GitLab.

## Configuração

O Resolvedor de Problemas na Nuvem está disponível automaticamente quando você concede acesso ao repositório OpenHands Cloud:
- [Acesso ao repositório GitHub](./github-installation#adding-repository-access)
- [Acesso ao repositório GitLab](./gitlab-installation#adding-repository-access)

## Uso

Após conceder acesso ao repositório OpenHands Cloud, você pode usar o Resolvedor de Problemas na Nuvem em issues e pull/merge requests em seus repositórios.

### Trabalhando com Issues

No seu repositório, rotule uma issue com `openhands`. O OpenHands irá:
1. Comentar na issue para informar que está trabalhando nela
   - Você pode clicar no link para acompanhar o progresso no OpenHands Cloud
2. Abrir um pull request (GitHub) ou merge request (GitLab) se determinar que o problema foi resolvido com sucesso
3. Comentar na issue com um resumo das tarefas realizadas e um link para o PR/MR

### Trabalhando com Pull/Merge Requests

Para fazer o OpenHands trabalhar em pull requests (GitHub) ou merge requests (GitLab), mencione `@openhands` nos comentários para:
- Fazer perguntas
- Solicitar atualizações
- Obter explicações de código

O OpenHands irá:
1. Comentar para informar que está trabalhando nisso
2. Realizar a tarefa solicitada

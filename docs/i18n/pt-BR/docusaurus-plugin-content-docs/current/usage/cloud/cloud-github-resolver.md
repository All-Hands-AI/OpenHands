# Resolvedor GitHub na Nuvem

O Resolvedor GitHub automatiza correções de código e fornece assistência inteligente para seus repositórios.

## Configuração

O Resolvedor GitHub na Nuvem está disponível automaticamente quando você
[concede acesso de repositório ao OpenHands Cloud](./openhands-cloud#adding-repository-access).

## Uso

Após conceder acesso de repositório ao OpenHands Cloud, você pode usar o Resolvedor GitHub na Nuvem nos problemas e pull requests
do repositório.

### Problemas (Issues)

No seu repositório, rotule um problema com `openhands`. O OpenHands irá:
1. Comentar no problema para informar que está trabalhando nele.
    - Você pode clicar no link para acompanhar o progresso no OpenHands Cloud.
2. Abrir um pull request se determinar que o problema foi resolvido com sucesso.
3. Comentar no problema com um resumo das tarefas realizadas e um link para o pull request.


### Pull Requests

Para fazer o OpenHands trabalhar em pull requests, use `@openhands` em comentários de nível superior ou em linha para:
     - Fazer perguntas
     - Solicitar atualizações
     - Obter explicações de código

O OpenHands irá:
1. Comentar no PR para informar que está trabalhando nele.
2. Realizar a tarefa.

# Configuração de Runtime

:::note
Esta seção é para usuários que gostariam de usar um runtime diferente do Docker para o OpenHands.
:::

Um Runtime é um ambiente onde o agente OpenHands pode editar arquivos e executar
comandos.

Por padrão, o OpenHands usa um [runtime baseado em Docker](./runtimes/docker), executando em seu computador local.
Isso significa que você só precisa pagar pelo LLM que está usando, e seu código é enviado apenas para o LLM.

Também oferecemos suporte a outros runtimes, que geralmente são gerenciados por terceiros.

Além disso, fornecemos um [Runtime Local](./runtimes/local) que é executado diretamente em sua máquina sem Docker,
o que pode ser útil em ambientes controlados como pipelines de CI.

## Runtimes Disponíveis

O OpenHands suporta vários ambientes de runtime diferentes:

- [Runtime Docker](./runtimes/docker.md) - O runtime padrão que usa contêineres Docker para isolamento (recomendado para a maioria dos usuários).
- [Runtime Remoto OpenHands](./runtimes/remote.md) - Runtime baseado em nuvem para execução paralela (beta).
- [Runtime Modal](./runtimes/modal.md) - Runtime fornecido por nossos parceiros da Modal.
- [Runtime Daytona](./runtimes/daytona.md) - Runtime fornecido pela Daytona.
- [Runtime Local](./runtimes/local.md) - Execução direta em sua máquina local sem Docker.

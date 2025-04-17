# Configuração de Runtime

Um Runtime é um ambiente onde o agente OpenHands pode editar arquivos e executar comandos.

Por padrão, o OpenHands usa um runtime baseado em Docker, executando no seu computador local. Isso significa que você só precisa pagar pelo LLM que está usando, e seu código é enviado apenas para o LLM.

Também suportamos runtimes "remotos", que são tipicamente gerenciados por terceiros. Eles podem tornar a configuração um pouco mais simples e escalável, especialmente se você estiver executando muitas conversas do OpenHands em paralelo (por exemplo, para fazer avaliação).

Além disso, fornecemos um runtime "local" que é executado diretamente na sua máquina sem o Docker, o que pode ser útil em ambientes controlados como pipelines de CI.

## Runtime Docker
Este é o Runtime padrão que é usado quando você inicia o OpenHands. Você pode notar algumas flags sendo passadas para o `docker run` que tornam isso possível:

```
docker run # ...
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.33-nikolaik \
    -v /var/run/docker.sock:/var/run/docker.sock \
    # ...
```

O `SANDBOX_RUNTIME_CONTAINER_IMAGE` do nikolaik é uma imagem de runtime pré-construída que contém nosso servidor Runtime, bem como algumas utilidades básicas para Python e NodeJS. Você também pode [construir sua própria imagem de runtime](how-to/custom-sandbox-guide).

### Conectando ao seu sistema de arquivos
Um recurso útil aqui é a capacidade de se conectar ao seu sistema de arquivos local. Para montar seu sistema de arquivos no runtime:
1. Defina `WORKSPACE_BASE`:

    ```bash
    export WORKSPACE_BASE=/caminho/para/seu/codigo

    # Exemplo no Linux e Mac
    # export WORKSPACE_BASE=$HOME/OpenHands
    # Definirá $WORKSPACE_BASE como /home/<username>/OpenHands
    #
    # Exemplo no WSL no Windows
    # export WORKSPACE_BASE=/mnt/c/dev/OpenHands
    # Definirá $WORKSPACE_BASE como C:\dev\OpenHands
    ```
2. Adicione as seguintes opções ao comando `docker run`:

    ```bash
    docker run # ...
        -e SANDBOX_USER_ID=$(id -u) \
        -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
        -v $WORKSPACE_BASE:/opt/workspace_base \
        # ...
    ```

Tenha cuidado! Não há nada impedindo o agente OpenHands de excluir ou modificar quaisquer arquivos que estejam montados em seu workspace.

Essa configuração pode causar alguns problemas com permissões de arquivo (daí a variável `SANDBOX_USER_ID`), mas parece funcionar bem na maioria dos sistemas.

## OpenHands Remote Runtime

O OpenHands Remote Runtime está atualmente em beta (leia [aqui](https://runtime.all-hands.dev/) para mais detalhes), ele permite que você inicie runtimes em paralelo na nuvem. Preencha [este formulário](https://docs.google.com/forms/d/e/1FAIpQLSckVz_JFwg2_mOxNZjCtr7aoBFI2Mwdan3f75J_TrdMS1JV2g/viewform) para se inscrever se quiser experimentar isso!

NOTA: Este runtime é projetado especificamente apenas para fins de avaliação de agentes por meio do [harness de avaliação do OpenHands](https://github.com/All-Hands-AI/OpenHands/tree/main/evaluation). Ele não deve ser usado para iniciar aplicativos OpenHands em produção.

## Runtime Modal
Nossos parceiros na [Modal](https://modal.com/) também forneceram um runtime para o OpenHands.

Para usar o Runtime Modal, crie uma conta e, em seguida, [crie uma chave de API.](https://modal.com/settings)

Você precisará definir as seguintes variáveis de ambiente ao iniciar o OpenHands:
```bash
docker run # ...
    -e RUNTIME=modal \
    -e MODAL_API_TOKEN_ID="seu-id" \
    -e MODAL_API_TOKEN_SECRET="seu-segredo" \
```

## Runtime Daytona

Outra opção é usar o [Daytona](https://www.daytona.io/) como provedor de runtime:

### Passo 1: Recupere sua chave de API do Daytona
1. Visite o [Painel do Daytona](https://app.daytona.io/dashboard/keys).
2. Clique em **"Create Key"**.
3. Digite um nome para sua chave e confirme a criação.
4. Depois que a chave for gerada, copie-a.

### Passo 2: Defina sua chave de API como uma variável de ambiente
Execute o seguinte comando no seu terminal, substituindo `<sua-chave-de-api>` pela chave real que você copiou:
```bash
export DAYTONA_API_KEY="<sua-chave-de-api>"
```

Esta etapa garante que o OpenHands possa se autenticar na plataforma Daytona quando for executado.

### Passo 3: Execute o OpenHands localmente usando o Docker
Para iniciar a versão mais recente do OpenHands em sua máquina, execute o seguinte comando no seu terminal:
```bash
bash -i <(curl -sL https://get.daytona.io/openhands)
```

#### O que este comando faz:
- Baixa o script de lançamento mais recente do OpenHands.
- Executa o script em uma sessão interativa do Bash.
- Automaticamente baixa e executa o contêiner do OpenHands usando o Docker.

Uma vez executado, o OpenHands deve estar sendo executado localmente e pronto para uso.

Para mais detalhes e inicialização manual, veja o [README.md](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/runtime/impl/daytona/README.md) completo.

## Runtime Local

O Runtime Local permite que o agente OpenHands execute ações diretamente em sua máquina local sem usar o Docker. Este runtime é destinado principalmente para ambientes controlados, como pipelines de CI ou cenários de teste onde o Docker não está disponível.

:::caution
**Aviso de segurança**: O Runtime Local é executado sem nenhum isolamento de sandbox. O agente pode acessar e modificar diretamente os arquivos em sua máquina. Use este runtime apenas em ambientes controlados ou quando você entender completamente as implicações de segurança.
:::

### Pré-requisitos

Antes de usar o Runtime Local, certifique-se de ter as seguintes dependências instaladas:

1. Você seguiu as [instruções de configuração de desenvolvimento](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).
2. O tmux está disponível em seu sistema.

### Configuração

Para usar o Runtime Local, além das configurações necessárias como o modelo, chave de API, você precisará definir as seguintes opções por meio de variáveis de ambiente ou do [arquivo config.toml](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml) ao iniciar o OpenHands:

- Via variáveis de ambiente:

```bash
# Obrigatório
export RUNTIME=local

# Opcional, mas recomendado
export WORKSPACE_BASE=/caminho/para/seu/workspace
```

- Via `config.toml`:

```toml
[core]
runtime = "local"
workspace_base = "/caminho/para/seu/workspace"
```

Se `WORKSPACE_BASE` não for definido, o runtime criará um diretório temporário para o agente trabalhar.

### Exemplo de uso

Aqui está um exemplo de como iniciar o OpenHands com o Runtime Local no Modo Headless:

```bash
# Define o tipo de runtime como local
export RUNTIME=local

# Opcionalmente, define um diretório de workspace
export WORKSPACE_BASE=/caminho/para/seu/projeto

# Inicia o OpenHands
poetry run python -m openhands.core.main -t "escreva um script bash que imprima oi"
```

### Casos de uso

O Runtime Local é particularmente útil para:

- Pipelines de CI/CD onde o Docker não está disponível.
- Testes e desenvolvimento do próprio OpenHands.
- Ambientes onde o uso de contêineres é restrito.
- Cenários onde o acesso direto ao sistema de arquivos é necessário.

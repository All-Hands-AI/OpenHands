# Docker Runtime

Este é o Runtime padrão que é usado quando você inicia o OpenHands.

## Imagem
O `SANDBOX_RUNTIME_CONTAINER_IMAGE` da nikolaik é uma imagem de runtime pré-construída
que contém nosso servidor Runtime, bem como algumas utilidades básicas para Python e NodeJS.
Você também pode [construir sua própria imagem de runtime](../how-to/custom-sandbox-guide).

## Conectando ao seu sistema de arquivos
Um recurso útil é a capacidade de se conectar ao seu sistema de arquivos local. Para montar seu sistema de arquivos no runtime:

### Usando SANDBOX_VOLUMES

A maneira mais simples de montar seu sistema de arquivos local é usar a variável de ambiente `SANDBOX_VOLUMES`:

```bash
docker run # ...
    -e SANDBOX_USER_ID=$(id -u) \
    -e SANDBOX_VOLUMES=/path/to/your/code:/workspace:rw \
    # ...
```

O formato do `SANDBOX_VOLUMES` é: `caminho_host:caminho_container[:modo]`

- `caminho_host`: O caminho na sua máquina host que você deseja montar
- `caminho_container`: O caminho dentro do container onde o caminho do host será montado
  - Use `/workspace` para arquivos que você quer que o agente modifique. O agente trabalha em `/workspace` por padrão.
  - Use um caminho diferente (ex: `/data`) para materiais de referência somente leitura ou grandes conjuntos de dados
- `modo`: Modo de montagem opcional, pode ser `rw` (leitura-escrita, padrão) ou `ro` (somente leitura)

Você também pode especificar múltiplas montagens separando-as com vírgulas (`,`):

```bash
export SANDBOX_VOLUMES=/path1:/workspace/path1,/path2:/workspace/path2:ro
```

Exemplos:

```bash
# Exemplo para Linux e Mac - Workspace com permissão de escrita
export SANDBOX_VOLUMES=$HOME/OpenHands:/workspace:rw

# Exemplo para WSL no Windows - Workspace com permissão de escrita
export SANDBOX_VOLUMES=/mnt/c/dev/OpenHands:/workspace:rw

# Exemplo de código de referência somente leitura
export SANDBOX_VOLUMES=/path/to/reference/code:/data:ro

# Exemplo de múltiplas montagens - Workspace com permissão de escrita e dados de referência somente leitura
export SANDBOX_VOLUMES=$HOME/projects:/workspace:rw,/path/to/large/dataset:/data:ro
```

> **Nota:** Ao usar múltiplas montagens, a primeira montagem é considerada o workspace principal e será usada para compatibilidade com ferramentas que esperam um único workspace.

> **Importante:** O agente trabalhará em `/workspace` por padrão. Se você quiser que o agente modifique arquivos em seu diretório local, você deve montar esse diretório em `/workspace`. Se você tem dados somente leitura que deseja que o agente acesse mas não modifique, monte-os em um caminho diferente (como `/data`) e instrua explicitamente o agente a procurar lá.

### Usando variáveis WORKSPACE_* (Obsoleto)

> **Nota:** Este método está obsoleto e será removido em uma versão futura. Por favor, use `SANDBOX_VOLUMES` em vez disso.

1. Configure `WORKSPACE_BASE`:

    ```bash
    export WORKSPACE_BASE=/path/to/your/code
    ```

2. Adicione as seguintes opções ao comando `docker run`:

    ```bash
    docker run # ...
        -e SANDBOX_USER_ID=$(id -u) \
        -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
        -v $WORKSPACE_BASE:/opt/workspace_base \
        # ...
    ```

Tenha cuidado! Não há nada impedindo o agente OpenHands de excluir ou modificar
quaisquer arquivos que estejam montados em seu workspace.

O `-e SANDBOX_USER_ID=$(id -u)` é passado para o comando Docker para garantir que o usuário do sandbox corresponda às
permissões do usuário do host. Isso impede que o agente crie arquivos pertencentes ao root no workspace montado.

## Instalação Docker Reforçada

Ao implantar o OpenHands em ambientes onde a segurança é uma prioridade, você deve considerar implementar uma
configuração Docker reforçada. Esta seção fornece recomendações para proteger sua implantação Docker do OpenHands além da configuração padrão.

### Considerações de Segurança

A configuração Docker padrão no README é projetada para facilidade de uso em uma máquina de desenvolvimento local. Se você estiver
executando em uma rede pública (por exemplo, Wi-Fi de aeroporto), você deve implementar medidas de segurança adicionais.

### Segurança de Vinculação de Rede

Por padrão, o OpenHands se vincula a todas as interfaces de rede (`0.0.0.0`), o que pode expor sua instância a todas as redes às quais
o host está conectado. Para uma configuração mais segura:

1. **Restringir Vinculação de Rede**: Use a configuração `runtime_binding_address` para restringir quais interfaces de rede o OpenHands escuta:

   ```bash
   docker run # ...
       -e SANDBOX_RUNTIME_BINDING_ADDRESS=127.0.0.1 \
       # ...
   ```

   Esta configuração garante que o OpenHands só escute na interface de loopback (`127.0.0.1`), tornando-o acessível apenas a partir da máquina local.

2. **Vinculação Segura de Porta**: Modifique a flag `-p` para vincular apenas ao localhost em vez de todas as interfaces:

   ```bash
   docker run # ... \
       -p 127.0.0.1:3000:3000 \
   ```

   Isso garante que a interface web do OpenHands seja acessível apenas a partir da máquina local, não de outras máquinas na rede.

### Isolamento de Rede

Use os recursos de rede do Docker para isolar o OpenHands:

```bash
# Crie uma rede isolada
docker network create openhands-network

# Execute o OpenHands na rede isolada
docker run # ... \
    --network openhands-network \
```

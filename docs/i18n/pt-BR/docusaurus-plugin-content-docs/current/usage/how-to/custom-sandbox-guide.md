# Sandbox Personalizado

:::note
Este guia é para usuários que gostariam de usar sua própria imagem Docker personalizada para o runtime. Por exemplo,
com certas ferramentas ou linguagens de programação pré-instaladas.
:::

O sandbox é onde o agente realiza suas tarefas. Em vez de executar comandos diretamente no seu computador
(o que poderia ser arriscado), o agente os executa dentro de um contêiner Docker.

O sandbox padrão do OpenHands (`python-nodejs:python3.12-nodejs22`
do [nikolaik/python-nodejs](https://hub.docker.com/r/nikolaik/python-nodejs)) vem com alguns pacotes instalados como
python e Node.js, mas pode precisar de outros softwares instalados por padrão.

Você tem duas opções para personalização:

- Usar uma imagem existente com o software necessário.
- Criar sua própria imagem Docker personalizada.

Se você escolher a primeira opção, pode pular a seção `Criar Sua Imagem Docker`.

## Criar Sua Imagem Docker

Para criar uma imagem Docker personalizada, ela deve ser baseada em Debian.

Por exemplo, se você quiser que o OpenHands tenha `ruby` instalado, você poderia criar um `Dockerfile` com o seguinte conteúdo:

```dockerfile
FROM nikolaik/python-nodejs:python3.12-nodejs22

# Install required packages
RUN apt-get update && apt-get install -y ruby
```

Ou você poderia usar uma imagem base específica para Ruby:

```dockerfile
FROM ruby:latest
```

Salve este arquivo em uma pasta. Em seguida, construa sua imagem Docker (por exemplo, chamada custom-image) navegando até a pasta no
terminal e executando:
```bash
docker build -t custom-image .
```

Isso produzirá uma nova imagem chamada `custom-image`, que estará disponível no Docker.

## Usando o Comando Docker

Ao executar o OpenHands usando [o comando docker](/modules/usage/installation#start-the-app), substitua
`-e SANDBOX_RUNTIME_CONTAINER_IMAGE=...` por `-e SANDBOX_BASE_CONTAINER_IMAGE=<nome da imagem personalizada>`:

```commandline
docker run -it --rm --pull=always \
    -e SANDBOX_BASE_CONTAINER_IMAGE=custom-image \
    ...
```

## Usando o Fluxo de Trabalho de Desenvolvimento

### Configuração

Primeiro, certifique-se de que pode executar o OpenHands seguindo as instruções em [Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).

### Especificar a Imagem Base do Sandbox

No arquivo `config.toml` dentro do diretório OpenHands, defina o `base_container_image` para a imagem que você deseja usar.
Pode ser uma imagem que você já baixou ou uma que você construiu:

```bash
[core]
...
[sandbox]
base_container_image="custom-image"
```

### Opções de Configuração Adicionais

O arquivo `config.toml` suporta várias outras opções para personalizar seu sandbox:

```toml
[core]
# Install additional dependencies when the runtime is built
# Can contain any valid shell commands
# If you need the path to the Python interpreter in any of these commands, you can use the $OH_INTERPRETER_PATH variable
runtime_extra_deps = """
pip install numpy pandas
apt-get update && apt-get install -y ffmpeg
"""

# Set environment variables for the runtime
# Useful for configuration that needs to be available at runtime
runtime_startup_env_vars = { DATABASE_URL = "postgresql://user:pass@localhost/db" }

# Specify platform for multi-architecture builds (e.g., "linux/amd64" or "linux/arm64")
platform = "linux/amd64"
```

### Executar

Execute o OpenHands rodando ```make run``` no diretório de nível superior.

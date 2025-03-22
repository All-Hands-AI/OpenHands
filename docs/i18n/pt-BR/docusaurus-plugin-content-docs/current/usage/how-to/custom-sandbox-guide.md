# Sandbox Personalizado

O sandbox é onde o agente realiza suas tarefas. Em vez de executar comandos diretamente no seu computador
(o que poderia ser arriscado), o agente os executa dentro de um contêiner Docker.

O sandbox padrão do OpenHands (`python-nodejs:python3.12-nodejs22`
do [nikolaik/python-nodejs](https://hub.docker.com/r/nikolaik/python-nodejs)) vem com alguns pacotes instalados, como
python e Node.js, mas pode precisar de outros softwares instalados por padrão.

Você tem duas opções para personalização:

- Usar uma imagem existente com o software necessário.
- Criar sua própria imagem personalizada do Docker.

Se você escolher a primeira opção, pode pular a seção `Crie Sua Imagem Docker`.

## Crie Sua Imagem Docker

Para criar uma imagem personalizada do Docker, ela deve ser baseada no Debian.

Por exemplo, se você quiser que o OpenHands tenha o `ruby` instalado, você pode criar um `Dockerfile` com o seguinte conteúdo:

```dockerfile
FROM nikolaik/python-nodejs:python3.12-nodejs22

# Instalar pacotes necessários
RUN apt-get update && apt-get install -y ruby
```

Ou você pode usar uma imagem base específica do Ruby:

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

Primeiro, certifique-se de que você pode executar o OpenHands seguindo as instruções em [Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).

### Especifique a Imagem Base do Sandbox

No arquivo `config.toml` dentro do diretório OpenHands, defina `base_container_image` como a imagem que você deseja usar.
Isso pode ser uma imagem que você já baixou ou uma que você construiu:

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
# Instalar dependências adicionais quando o runtime for construído
# Pode conter quaisquer comandos shell válidos
# Se você precisar do caminho para o interpretador Python em qualquer um desses comandos, pode usar a variável $OH_INTERPRETER_PATH
runtime_extra_deps = """
pip install numpy pandas
apt-get update && apt-get install -y ffmpeg
"""

# Definir variáveis de ambiente para o runtime
# Útil para configuração que precisa estar disponível em tempo de execução
runtime_startup_env_vars = { DATABASE_URL = "postgresql://user:pass@localhost/db" }

# Especificar a plataforma para builds de várias arquiteturas (por exemplo, "linux/amd64" ou "linux/arm64")
platform = "linux/amd64"
```

### Executar

Execute o OpenHands executando ```make run``` no diretório de nível superior.

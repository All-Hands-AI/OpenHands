# Runtime Daytona

Você pode usar o [Daytona](https://www.daytona.io/) como um provedor de runtime:

## Passo 1: Obtenha Sua Chave de API do Daytona
1. Visite o [Painel do Daytona](https://app.daytona.io/dashboard/keys).
2. Clique em **"Create Key"**.
3. Digite um nome para sua chave e confirme a criação.
4. Depois que a chave for gerada, copie-a.

## Passo 2: Configure Sua Chave de API como uma Variável de Ambiente
Execute o seguinte comando no seu terminal, substituindo `<your-api-key>` pela chave real que você copiou:
```bash
export DAYTONA_API_KEY="<your-api-key>"
```

Este passo garante que o OpenHands possa se autenticar na plataforma Daytona quando for executado.

## Passo 3: Execute o OpenHands Localmente Usando Docker
Para iniciar a versão mais recente do OpenHands em sua máquina, execute o seguinte comando no seu terminal:
```bash
bash -i <(curl -sL https://get.daytona.io/openhands)
```

### O Que Este Comando Faz:
- Baixa o script da versão mais recente do OpenHands.
- Executa o script em uma sessão interativa do Bash.
- Automaticamente baixa e executa o contêiner do OpenHands usando Docker.

Uma vez executado, o OpenHands deve estar rodando localmente e pronto para uso.

Para mais detalhes e inicialização manual, veja o [README.md](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/runtime/impl/daytona/README.md) completo

# 🚧 Solução de Problemas

:::tip
OpenHands só suporta Windows via WSL. Certifique-se de executar todos os comandos dentro do seu terminal WSL.
:::

### Não é possível acessar a aba do VS Code via IP local

**Descrição**

Ao acessar o OpenHands através de uma URL não-localhost (como um endereço IP de LAN), a aba do VS Code mostra um erro "Forbidden", enquanto outras partes da interface funcionam normalmente.

**Resolução**

Isso acontece porque o VS Code é executado em uma porta alta aleatória que pode não estar exposta ou acessível de outras máquinas. Para corrigir isso:

1. Defina uma porta específica para o VS Code usando a variável de ambiente `SANDBOX_VSCODE_PORT`:
   ```bash
   docker run -it --rm \
       -e SANDBOX_VSCODE_PORT=41234 \
       -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:latest \
       -v /var/run/docker.sock:/var/run/docker.sock \
       -v ~/.openhands-state:/.openhands-state \
       -p 3000:3000 \
       -p 41234:41234 \
       --add-host host.docker.internal:host-gateway \
       --name openhands-app \
       docker.all-hands.dev/all-hands-ai/openhands:latest
   ```

2. Certifique-se de expor a mesma porta com `-p 41234:41234` no seu comando Docker.

3. Alternativamente, você pode definir isso no seu arquivo `config.toml`:
   ```toml
   [sandbox]
   vscode_port = 41234
   ```

### Falha ao iniciar o cliente docker

**Descrição**

Ao executar o OpenHands, o seguinte erro é exibido:
```
Launch docker client failed. Please make sure you have installed docker and started docker desktop/daemon.
```

**Resolução**

Tente estas soluções em ordem:
* Confirme se o `docker` está em execução no seu sistema. Você deve conseguir executar `docker ps` no terminal com sucesso.
* Se estiver usando o Docker Desktop, certifique-se de que `Settings > Advanced > Allow the default Docker socket to be used` esteja habilitado.
* Dependendo da sua configuração, você pode precisar habilitar `Settings > Resources > Network > Enable host networking` no Docker Desktop.
* Reinstale o Docker Desktop.

### Erro de Permissão

**Descrição**

No prompt inicial, um erro é exibido com `Permission Denied` ou `PermissionError`.

**Resolução**

* Verifique se o diretório `~/.openhands-state` pertence ao usuário `root`. Se sim, você pode:
  * Alterar a propriedade do diretório: `sudo chown <user>:<user> ~/.openhands-state`.
  * ou atualizar as permissões do diretório: `sudo chmod 777 ~/.openhands-state`
  * ou excluí-lo se você não precisar de dados anteriores. O OpenHands irá recriá-lo. Você precisará inserir novamente as configurações do LLM.
* Se estiver montando um diretório local, certifique-se de que seu `WORKSPACE_BASE` tenha as permissões necessárias para o usuário que está executando o OpenHands.

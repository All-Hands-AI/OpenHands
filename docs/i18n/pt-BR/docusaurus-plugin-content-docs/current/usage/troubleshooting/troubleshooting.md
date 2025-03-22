# 🚧 Solução de Problemas

:::tip
O OpenHands só suporta Windows via WSL. Certifique-se de executar todos os comandos dentro do seu terminal WSL.
:::

### Falha ao iniciar o cliente docker

**Descrição**

Ao executar o OpenHands, o seguinte erro é visto:

```
Launch docker client failed. Please make sure you have installed docker and started docker desktop/daemon.
```

**Resolução**

Tente estes passos em ordem:

- Confirme que o `docker` está em execução no seu sistema. Você deve ser capaz de executar `docker ps` no terminal com sucesso.
- Se estiver usando o Docker Desktop, certifique-se de que `Settings > Advanced > Allow the default Docker socket to be used` esteja habilitado.
- Dependendo da sua configuração, você pode precisar habilitar `Settings > Resources > Network > Enable host networking` no Docker Desktop.
- Reinstale o Docker Desktop.

---

# Problemas Específicos ao Ambiente de Desenvolvimento

### Erro ao construir a imagem docker do runtime

**Descrição**

Tentativas de iniciar uma nova sessão falham e erros com termos como os seguintes aparecem nos logs:

```
debian-security bookworm-security
InRelease At least one invalid signature was encountered.
```

Isso parece acontecer quando o hash de uma biblioteca externa existente muda e sua instância local do docker tem uma versão anterior em cache. Para contornar isso, tente o seguinte:

- Pare quaisquer contêineres onde o nome tenha o prefixo `openhands-runtime-`:
  `docker ps --filter name=openhands-runtime- --filter status=running -aq | xargs docker stop`
- Remova quaisquer contêineres onde o nome tenha o prefixo `openhands-runtime-`:
  `docker rmi $(docker images --filter name=openhands-runtime- -q --no-trunc)`
- Pare e remova quaisquer contêineres / imagens onde o nome tenha o prefixo `openhands-runtime-`
- Limpe contêineres / imagens: `docker container prune -f && docker image prune -f`

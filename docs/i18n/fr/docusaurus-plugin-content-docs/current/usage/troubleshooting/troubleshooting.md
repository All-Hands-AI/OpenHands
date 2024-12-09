

# 🚧 Dépannage

Il y a certains messages d'erreur qui sont fréquemment signalés par les utilisateurs.
Nous allons essayer de rendre le processus d'installation plus facile, mais pour l'instant vous pouvez rechercher votre message d'erreur ci-dessous et voir s'il y a des solutions de contournement.
Si vous trouvez plus d'informations ou une solution de contournement pour l'un de ces problèmes, veuillez ouvrir une *PR* pour ajouter des détails à ce fichier.

:::tip
OpenHands ne prend en charge Windows que via [WSL](https://learn.microsoft.com/en-us/windows/wsl/install).
Veuillez vous assurer d'exécuter toutes les commandes à l'intérieur de votre terminal WSL.
:::

## Problèmes courants

* [Impossible de se connecter à Docker](#impossible-de-se-connecter-à-docker)
* [404 Ressource introuvable](#404-ressource-introuvable)
* [`make build` bloqué sur les installations de paquets](#make-build-bloqué-sur-les-installations-de-paquets)
* [Les sessions ne sont pas restaurées](#les-sessions-ne-sont-pas-restaurées)

### Impossible de se connecter à Docker

[GitHub Issue](https://github.com/All-Hands-AI/OpenHands/issues/1226)

**Symptômes**

```bash
Error creating controller. Please check Docker is running and visit `https://docs.all-hands.dev/modules/usage/troubleshooting` for more debugging information.
```

```bash
docker.errors.DockerException: Error while fetching server API version: ('Connection aborted.', FileNotFoundError(2, 'No such file or directory'))
```

**Détails**

OpenHands utilise un conteneur Docker pour faire son travail en toute sécurité, sans risquer de casser votre machine.

**Solutions de contournement**

* Exécutez `docker ps` pour vous assurer que docker est en cours d'exécution
* Assurez-vous que vous n'avez pas besoin de `sudo` pour exécuter docker [voir ici](https://www.baeldung.com/linux/docker-run-without-sudo)
* Si vous êtes sur un Mac, vérifiez les [exigences d'autorisation](https://docs.docker.com/desktop/mac/permission-requirements/) et en particulier envisagez d'activer `Allow the default Docker socket to be used` sous `Settings > Advanced` dans Docker Desktop.
* De plus, mettez à niveau votre Docker vers la dernière version sous `Check for Updates`

---
### `404 Ressource introuvable`

**Symptômes**

```python
Traceback (most recent call last):
  File "/app/.venv/lib/python3.12/site-packages/litellm/llms/openai.py", line 414, in completion
    raise e
  File "/app/.venv/lib/python3.12/site-packages/litellm/llms/openai.py", line 373, in completion
    response = openai_client.chat.completions.create(**data, timeout=timeout)  # type: ignore
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/openai/_utils/_utils.py", line 277, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/openai/resources/chat/completions.py", line 579, in create
    return self._post(
           ^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/openai/_base_client.py", line 1232, in post
    return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/openai/_base_client.py", line 921, in request
    return self._request(
           ^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/openai/_base_client.py", line 1012, in _request
    raise self._make_status_error_from_response(err.response) from None
openai.NotFoundError: Error code: 404 - {'error': {'code': '404', 'message': 'Resource not found'}}
```

**Détails**

Cela se produit lorsque LiteLLM (notre bibliothèque pour se connecter à différents fournisseurs de LLM) ne peut pas trouver le point de terminaison d'API auquel vous essayez de vous connecter. Le plus souvent, cela se produit pour les utilisateurs d'Azure ou d'ollama.

**Solutions de contournement**

* Vérifiez que vous avez correctement défini `LLM_BASE_URL`
* Vérifiez que le modèle est correctement défini, en fonction de la [documentation de LiteLLM](https://docs.litellm.ai/docs/providers)
  * Si vous exécutez dans l'interface utilisateur, assurez-vous de définir le `model` dans la fenêtre modale des paramètres
  * Si vous exécutez en mode headless (via main.py), assurez-vous de définir `LLM_MODEL` dans votre env/config
* Assurez-vous d'avoir suivi toutes les instructions spéciales pour votre fournisseur de LLM
  * [Azure](/modules/usage/llms/azure-llms)
  * [Google](/modules/usage/llms/google-llms)
* Assurez-vous que votre clé API est correcte
* Voyez si vous pouvez vous connecter au LLM en utilisant `curl`
* Essayez de [vous connecter directement via LiteLLM](https://github.com/BerriAI/litellm) pour tester votre configuration

---
### `make build` bloqué sur les installations de paquets

**Symptômes**

L'installation des paquets est bloquée sur `Pending...` sans aucun message d'erreur :

```bash
Package operations: 286 installs, 0 updates, 0 removals

  - Installing certifi (2024.2.2): Pending...
  - Installing h11 (0.14.0): Pending...
  - Installing idna (3.7): Pending...
  - Installing sniffio (1.3.1): Pending...
  - Installing typing-extensions (4.11.0): Pending...
```

**Détails**

Dans de rares cas, `make build` peut sembler se bloquer sur les installations de paquets sans aucun message d'erreur.

**Solutions de contournement**

L'installateur de paquets Poetry peut manquer un paramètre de configuration pour savoir où rechercher les informations d'identification (keyring).

Vérifiez d'abord avec `env` si une valeur pour `PYTHON_KEYRING_BACKEND` existe.
Si ce n'est pas le cas, exécutez la commande ci-dessous pour la définir sur une valeur connue et réessayez la construction :

```bash
export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring
```

---
### Les sessions ne sont pas restaurées

**Symptômes**

OpenHands demande généralement s'il faut reprendre ou démarrer une nouvelle session lors de l'ouverture de l'interface utilisateur.
Mais cliquer sur "Reprendre" démarre quand même un nouveau chat.

**Détails**

Avec une installation standard à ce jour, les données de session sont stockées en mémoire.
Actuellement, si le service OpenHands est redémarré, les sessions précédentes deviennent invalides (un nouveau secret est généré) et donc non récupérables.

**Solutions de contournement**

* Modifiez la configuration pour rendre les sessions persistantes en éditant le fichier `config.toml` (dans le dossier racine d'OpenHands) en spécifiant un `file_store` et un `file_store_path` absolu :

```toml
file_store="local"
file_store_path="/absolute/path/to/openhands/cache/directory"
```

* Ajoutez un secret jwt fixe dans votre .bashrc, comme ci-dessous, afin que les ID de session précédents restent acceptés.

```bash
EXPORT JWT_SECRET=A_CONST_VALUE
```

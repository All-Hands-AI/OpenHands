---
sidebar_position: 5
---

# 🚧 Dépannage

Il existe certains messages d'erreur qui sont souvent signalés par les utilisateurs.

Nous essaierons de rendre le processus d'installation plus facile et ces messages d'erreur
mieux à l'avenir. Mais pour l'instant, vous pouvez rechercher votre message d'erreur ci-dessous et voir s'il existe des solutions de contournement.

Pour chacun de ces messages d'erreur, **il existe un problème existant**. Veuillez ne pas
ouvrir un nouveau problème - commentez simplement dessus.

Si vous trouvez plus d'informations ou une solution de contournement pour l'un de ces problèmes, veuillez ouvrir un *PR* pour ajouter des détails à ce fichier.

:::tip
Si vous utilisez Windows et que vous rencontrez des problèmes, consultez notre [guide pour les utilisateurs de Windows (WSL)](troubleshooting/windows).
:::

## Impossible de se connecter à Docker

[Problème GitHub](https://github.com/All-Hands-AI/OpenHands/issues/1226)

### Symptômes

```bash
Erreur lors de la création du contrôleur. Veuillez vérifier que Docker est en cours d'exécution et visitez `https://docs.all-hands.dev/modules/usage/troubleshooting` pour plus d'informations sur le débogage.
```

```bash
docker.errors.DockerException: Erreur lors de la récupération de la version de l'API du serveur : ('Connection aborted.', FileNotFoundError(2, 'Aucun fichier ou répertoire de ce type'))
```

### Détails

OpenHands utilise un conteneur Docker pour effectuer son travail en toute sécurité, sans risquer de briser votre machine.

### Solutions de contournement

* Exécutez `docker ps` pour vous assurer que docker est en cours d'exécution
* Assurez-vous que vous n'avez pas besoin de `sudo` pour exécuter docker [voir ici](https://www.baeldung.com/linux/docker-run-without-sudo)
* Si vous êtes sur un Mac, vérifiez les [exigences en matière d'autorisations](https://docs.docker.com/desktop/mac/permission-requirements/) et envisagez particulièrement d'activer l'option `Allow the default Docker socket to be used` sous `Settings > Advanced` dans Docker Desktop.
* De plus, mettez à jour Docker vers la dernière version sous `Check for Updates`

## Impossible de se connecter à la boîte SSH

[Problème GitHub](https://github.com/All-Hands-AI/OpenHands/issues/1156)

### Symptômes

```python
self.shell = DockerSSHBox(
...
pexpect.pxssh.ExceptionPxssh: Impossible d'établir une connexion avec l'hôte
```

### Détails

Par défaut, OpenHands se connecte à un conteneur en cours d'exécution via SSH. Sur certaines machines,
en particulier Windows, cela semble échouer.

### Solutions de contournement

* Redémarrez votre ordinateur (parfois cela fonctionne)
* Assurez-vous d'avoir les dernières versions de WSL et Docker
* Vérifiez que votre distribution dans WSL est également à jour
* Essayez [ce guide de réinstallation](https://github.com/All-Hands-AI/OpenHands/issues/1156#issuecomment-2064549427)

## Impossible de se connecter à LLM

[Problème GitHub](https://github.com/All-Hands-AI/OpenHands/issues/1208)

### Symptômes

```python
  File "/app/.venv/lib/python3.12/site-packages/openai/_exceptions.py", line 81, in __init__
    super().__init__(message, response.request, body=body)
                              ^^^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'request'
```

### Détails

[Problèmes GitHub](https://github.com/All-Hands-AI/OpenHands/issues?q=is%3Aissue+is%3Aopen+404)

Cela se produit généralement avec les configurations de LLM *locales*, lorsque OpenHands ne parvient pas à se connecter au serveur LLM.
Consultez notre guide pour [LLMs locaux](llms/local-llms) pour plus d'informations.

### Solutions de contournement

* Vérifiez votre `base_url` dans votre config.toml (si elle existe) sous la section "llm"
* Vérifiez que ollama (ou tout autre LLM que vous utilisez) fonctionne correctement
* Assurez-vous d'utiliser `--add-host host.docker.internal:host-gateway` lorsque vous utilisez Docker

## `404 Ressource non trouvée`

### Symptômes

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
openai.NotFoundError: Code d'erreur : 404 - {'error': {'code': '404', 'message': 'Ressource non trouvée'}}
```

### Détails

Cela se produit lorsque LiteLLM (notre bibliothèque pour se connecter à différents fournisseurs de LLM) ne parvient pas à trouver
le point de terminaison API avec lequel vous essayez de vous connecter. Cela arrive le plus souvent aux utilisateurs de Azure ou ollama.

### Solutions de contournement

* Vérifiez que vous avez correctement défini `LLM_BASE_URL`
* Vérifiez que le modèle est correctement défini, en fonction des [docs de LiteLLM](https://docs.litellm.ai/docs/providers)
  * Si vous êtes en cours d'exécution dans l'interface utilisateur, assurez-vous de définir le `model` dans le modal des paramètres
  * Si vous êtes en cours d'exécution sans interface (via main.py), assurez-vous de définir `LLM_MODEL` dans votre env/config
* Assurez-vous de suivre les instructions spéciales de votre fournisseur de LLM
  * [ollama](/fr/modules/usage/llms/local-llms)
  * [Azure](/fr/modules/usage/llms/azure-llms)
  * [Google](/fr/modules/usage/llms/google-llms)
* Assurez-vous que votre clé API est correcte
* Voyez si vous pouvez vous connecter au LLM en utilisant `curl`
* Essayez de [vous connecter via LiteLLM directement](https://github.com/BerriAI/litellm) pour tester votre configuration

## `make build` bloqué sur les installations de packages

### Symptômes

Installation de package bloquée sur `En attente...` sans aucun message d'erreur :

```bash
Opérations de package : 286 installations, 0 mises à jour, 0 suppressions

  - Installation de certifi (2024.2.2) : En attente...
  - Installation de h11 (0.14.0) : En attente...
  - Installation de idna (3.7) : En attente...
  - Installation de sniffio (1.3.1) : En attente...
  - Installation de typing-extensions (4.11.0) : En attente...
```

### Détails

Dans de rares cas, `make build` peut sembler bloqué sur les installations de packages
sans aucun message d'erreur.

### Solutions de contournement

* Le gestionnaire de packages Poetry peut manquer d'un paramètre de configuration concernant
l'emplacement où doivent être recherchées les informations d'identification (keyring).

### Solution de contournement

Tout d'abord, vérifiez avec `env` si une valeur pour `PYTHON_KEYRING_BACKEND` existe.
Sinon, exécutez la commande ci-dessous pour la définir à une valeur connue et réessayez la construction :

```bash
export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring
```

## Les sessions ne sont pas restaurées

### Symptômes

OpenHands demande généralement s'il faut reprendre ou commencer une nouvelle session lors de l'ouverture de l'interface utilisateur.
Mais cliquer sur "Reprendre" démarre toujours une toute nouvelle discussion.

### Détails

Avec une installation standard à ce jour, les données de session sont stockées en mémoire.
Actuellement, si le service OpenHands est redémarré, les sessions précédentes deviennent
invalides (un nouveau secret est généré) et donc non récupérables.

### Solutions de contournement

* Modifiez la configuration pour rendre les sessions persistantes en éditant le fichier `config.toml`
(dans le dossier racine d'OpenHands) en spécifiant un `file_store` et un
`file_store_path` absolu :

```toml
file_store="local"
file_store_path="/absolute/path/to/openhands/cache/directory"
```

* Ajoutez un secret jwt fixe dans votre .bashrc, comme ci-dessous, afin que les id de session précédents
restent acceptés.

```bash
EXPORT JWT_SECRET=A_CONST_VALUE
```

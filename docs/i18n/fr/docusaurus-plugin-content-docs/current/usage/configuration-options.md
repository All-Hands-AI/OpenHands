# Options de Configuration

:::note
Cette page présente toutes les options de configuration disponibles pour OpenHands, vous permettant de personnaliser son comportement et
de l'intégrer avec d'autres services. En Mode GUI, tous les paramètres appliqués via l'interface Paramètres auront la priorité.
:::

## Configuration Principale

Les options de configuration principales sont définies dans la section `[core]` du fichier `config.toml`.

### Clés API
- `e2b_api_key`
  - Type: `str`
  - Défaut: `""`
  - Description: Clé API pour E2B

- `modal_api_token_id`
  - Type: `str`
  - Défaut: `""`
  - Description: ID de token API pour Modal

- `modal_api_token_secret`
  - Type: `str`
  - Défaut: `""`
  - Description: Secret de token API pour Modal

### Espace de travail
- `workspace_base` **(Déprécié)**
  - Type: `str`
  - Défaut: `"./workspace"`
  - Description: Chemin de base pour l'espace de travail. **Déprécié: Utilisez `SANDBOX_VOLUMES` à la place.**

- `cache_dir`
  - Type: `str`
  - Défaut: `"/tmp/cache"`
  - Description: Chemin du répertoire de cache

### Débogage et Journalisation
- `debug`
  - Type: `bool`
  - Défaut: `false`
  - Description: Activer le débogage

- `disable_color`
  - Type: `bool`
  - Défaut: `false`
  - Description: Désactiver la couleur dans la sortie du terminal

### Trajectoires
- `save_trajectory_path`
  - Type: `str`
  - Défaut: `"./trajectories"`
  - Description: Chemin pour stocker les trajectoires (peut être un dossier ou un fichier). Si c'est un dossier, les trajectoires seront sauvegardées dans un fichier nommé avec l'ID de session et l'extension .json, dans ce dossier.

- `replay_trajectory_path`
  - Type: `str`
  - Défaut: `""`
  - Description: Chemin pour charger une trajectoire et la rejouer. Si fourni, doit être un chemin vers le fichier de trajectoire au format JSON. Les actions dans le fichier de trajectoire seront rejouées d'abord avant que toute instruction utilisateur ne soit exécutée.

### Stockage de Fichiers
- `file_store_path`
  - Type: `str`
  - Défaut: `"/tmp/file_store"`
  - Description: Chemin du stockage de fichiers

- `file_store`
  - Type: `str`
  - Défaut: `"memory"`
  - Description: Type de stockage de fichiers

- `file_uploads_allowed_extensions`
  - Type: `liste de str`
  - Défaut: `[".*"]`
  - Description: Liste des extensions de fichiers autorisées pour les téléchargements

- `file_uploads_max_file_size_mb`
  - Type: `int`
  - Défaut: `0`
  - Description: Taille maximale de fichier pour les téléchargements, en mégaoctets

- `file_uploads_restrict_file_types`
  - Type: `bool`
  - Défaut: `false`
  - Description: Restreindre les types de fichiers pour les téléchargements

- `file_uploads_allowed_extensions`
  - Type: `liste de str`
  - Défaut: `[".*"]`
  - Description: Liste des extensions de fichiers autorisées pour les téléchargements

### Gestion des Tâches
- `max_budget_per_task`
  - Type: `float`
  - Défaut: `0.0`
  - Description: Budget maximum par tâche (0.0 signifie pas de limite)

- `max_iterations`
  - Type: `int`
  - Défaut: `100`
  - Description: Nombre maximum d'itérations

### Configuration du Sandbox
- `volumes`
  - Type: `str`
  - Défaut: `None`
  - Description: Montages de volumes au format 'chemin_hôte:chemin_conteneur[:mode]', par ex. '/my/host/dir:/workspace:rw'. Plusieurs montages peuvent être spécifiés en utilisant des virgules, par ex. '/path1:/workspace/path1,/path2:/workspace/path2:ro'

- `workspace_mount_path_in_sandbox` **(Déprécié)**
  - Type: `str`
  - Défaut: `"/workspace"`
  - Description: Chemin pour monter l'espace de travail dans le sandbox. **Déprécié: Utilisez `SANDBOX_VOLUMES` à la place.**

- `workspace_mount_path` **(Déprécié)**
  - Type: `str`
  - Défaut: `""`
  - Description: Chemin pour monter l'espace de travail. **Déprécié: Utilisez `SANDBOX_VOLUMES` à la place.**

- `workspace_mount_rewrite` **(Déprécié)**
  - Type: `str`
  - Défaut: `""`
  - Description: Chemin pour réécrire le chemin de montage de l'espace de travail. Vous pouvez généralement ignorer cela, cela fait référence à des cas spéciaux d'exécution à l'intérieur d'un autre conteneur. **Déprécié: Utilisez `SANDBOX_VOLUMES` à la place.**

### Divers
- `run_as_openhands`
  - Type: `bool`
  - Défaut: `true`
  - Description: Exécuter en tant qu'OpenHands

- `runtime`
  - Type: `str`
  - Défaut: `"docker"`
  - Description: Environnement d'exécution

- `default_agent`
  - Type: `str`
  - Défaut: `"CodeActAgent"`
  - Description: Nom de l'agent par défaut

- `jwt_secret`
  - Type: `str`
  - Défaut: `uuid.uuid4().hex`
  - Description: Secret JWT pour l'authentification. Veuillez le définir avec votre propre valeur.

## Configuration LLM

Les options de configuration LLM (Large Language Model) sont définies dans la section `[llm]` du fichier `config.toml`.

Pour les utiliser avec la commande docker, passez `-e LLM_<option>`. Exemple: `-e LLM_NUM_RETRIES`.

:::note
Pour les configurations de développement, vous pouvez également définir des configurations LLM personnalisées nommées. Voir [Configurations LLM personnalisées](./llms/custom-llm-configs) pour plus de détails.
:::

**Identifiants AWS**
- `aws_access_key_id`
  - Type: `str`
  - Défaut: `""`
  - Description: ID de clé d'accès AWS

- `aws_region_name`
  - Type: `str`
  - Défaut: `""`
  - Description: Nom de région AWS

- `aws_secret_access_key`
  - Type: `str`
  - Défaut: `""`
  - Description: Clé d'accès secrète AWS

### Configuration API
- `api_key`
  - Type: `str`
  - Défaut: `None`
  - Description: Clé API à utiliser

- `base_url`
  - Type: `str`
  - Défaut: `""`
  - Description: URL de base de l'API

- `api_version`
  - Type: `str`
  - Défaut: `""`
  - Description: Version de l'API

- `input_cost_per_token`
  - Type: `float`
  - Défaut: `0.0`
  - Description: Coût par token d'entrée

- `output_cost_per_token`
  - Type: `float`
  - Défaut: `0.0`
  - Description: Coût par token de sortie

### Fournisseur LLM personnalisé
- `custom_llm_provider`
  - Type: `str`
  - Défaut: `""`
  - Description: Fournisseur LLM personnalisé

### Gestion des messages
- `max_message_chars`
  - Type: `int`
  - Défaut: `30000`
  - Description: Le nombre approximatif maximum de caractères dans le contenu d'un événement inclus dans le prompt au LLM. Les observations plus grandes sont tronquées.

- `max_input_tokens`
  - Type: `int`
  - Défaut: `0`
  - Description: Nombre maximum de tokens d'entrée

- `max_output_tokens`
  - Type: `int`
  - Défaut: `0`
  - Description: Nombre maximum de tokens de sortie

### Sélection du modèle
- `model`
  - Type: `str`
  - Défaut: `"claude-3-5-sonnet-20241022"`
  - Description: Modèle à utiliser

### Nouvelles tentatives
- `num_retries`
  - Type: `int`
  - Défaut: `8`
  - Description: Nombre de tentatives à effectuer

- `retry_max_wait`
  - Type: `int`
  - Défaut: `120`
  - Description: Temps d'attente maximum (en secondes) entre les tentatives

- `retry_min_wait`
  - Type: `int`
  - Défaut: `15`
  - Description: Temps d'attente minimum (en secondes) entre les tentatives

- `retry_multiplier`
  - Type: `float`
  - Défaut: `2.0`
  - Description: Multiplicateur pour le calcul de backoff exponentiel

### Options avancées
- `drop_params`
  - Type: `bool`
  - Défaut: `false`
  - Description: Ignorer les paramètres non mappés (non pris en charge) sans provoquer d'exception

- `caching_prompt`
  - Type: `bool`
  - Défaut: `true`
  - Description: Utiliser la fonctionnalité de mise en cache des prompts si fournie par le LLM et prise en charge

- `ollama_base_url`
  - Type: `str`
  - Défaut: `""`
  - Description: URL de base pour l'API OLLAMA

- `temperature`
  - Type: `float`
  - Défaut: `0.0`
  - Description: Température pour l'API

- `timeout`
  - Type: `int`
  - Défaut: `0`
  - Description: Délai d'attente pour l'API

- `top_p`
  - Type: `float`
  - Défaut: `1.0`
  - Description: Top p pour l'API

- `disable_vision`
  - Type: `bool`
  - Défaut: `None`
  - Description: Si le modèle est capable de vision, cette option permet de désactiver le traitement d'images (utile pour réduire les coûts)

## Configuration de l'Agent

Les options de configuration de l'agent sont définies dans les sections `[agent]` et `[agent.<agent_name>]` du fichier `config.toml`.

### Configuration LLM
- `llm_config`
  - Type: `str`
  - Défaut: `'your-llm-config-group'`
  - Description: Le nom de la configuration LLM à utiliser

### Configuration de l'espace d'action
- `function_calling`
  - Type: `bool`
  - Défaut: `true`
  - Description: Si l'appel de fonction est activé

- `enable_browsing`
  - Type: `bool`
  - Défaut: `false`
  - Description: Si le délégué de navigation est activé dans l'espace d'action (fonctionne uniquement avec l'appel de fonction)

- `enable_llm_editor`
  - Type: `bool`
  - Défaut: `false`
  - Description: Si l'éditeur LLM est activé dans l'espace d'action (fonctionne uniquement avec l'appel de fonction)

- `enable_jupyter`
  - Type: `bool`
  - Défaut: `false`
  - Description: Si Jupyter est activé dans l'espace d'action

- `enable_history_truncation`
  - Type: `bool`
  - Défaut: `true`
  - Description: Si l'historique doit être tronqué pour continuer la session lorsqu'on atteint la limite de longueur de contexte du LLM

### Utilisation des microagents
- `enable_prompt_extensions`
  - Type: `bool`
  - Défaut: `true`
  - Description: Si les microagents doivent être utilisés

- `disabled_microagents`
  - Type: `liste de str`
  - Défaut: `None`
  - Description: Une liste de microagents à désactiver

## Configuration du Sandbox

Les options de configuration du sandbox sont définies dans la section `[sandbox]` du fichier `config.toml`.

Pour les utiliser avec la commande docker, passez `-e SANDBOX_<option>`. Exemple: `-e SANDBOX_TIMEOUT`.

### Exécution
- `timeout`
  - Type: `int`
  - Défaut: `120`
  - Description: Délai d'attente du sandbox en secondes

- `user_id`
  - Type: `int`
  - Défaut: `1000`
  - Description: ID utilisateur du sandbox

### Image du conteneur
- `base_container_image`
  - Type: `str`
  - Défaut: `"nikolaik/python-nodejs:python3.12-nodejs22"`
  - Description: Image de conteneur à utiliser pour le sandbox

### Réseau
- `use_host_network`
  - Type: `bool`
  - Défaut: `false`
  - Description: Utiliser le réseau de l'hôte

- `runtime_binding_address`
  - Type: `str`
  - Défaut: `0.0.0.0`
  - Description: L'adresse de liaison pour les ports d'exécution. Elle spécifie quelle interface réseau sur la machine hôte Docker doit lier les ports d'exécution.

### Linting et Plugins
- `enable_auto_lint`
  - Type: `bool`
  - Défaut: `false`
  - Description: Activer le linting automatique après l'édition

- `initialize_plugins`
  - Type: `bool`
  - Défaut: `true`
  - Description: Si les plugins doivent être initialisés

### Dépendances et Environnement
- `runtime_extra_deps`
  - Type: `str`
  - Défaut: `""`
  - Description: Dépendances supplémentaires à installer dans l'image d'exécution

- `runtime_startup_env_vars`
  - Type: `dict`
  - Défaut: `{}`
  - Description: Variables d'environnement à définir au lancement de l'exécution

### Évaluation
- `browsergym_eval_env`
  - Type: `str`
  - Défaut: `""`
  - Description: Environnement BrowserGym à utiliser pour l'évaluation

## Configuration de Sécurité

Les options de configuration de sécurité sont définies dans la section `[security]` du fichier `config.toml`.

Pour les utiliser avec la commande docker, passez `-e SECURITY



# Options de configuration

Ce guide détaille toutes les options de configuration disponibles pour OpenHands, vous aidant à personnaliser son comportement et à l'intégrer avec d'autres services.

:::note
Si vous exécutez en [Mode GUI](https://docs.all-hands.dev/modules/usage/how-to/gui-mode), les paramètres disponibles dans l'interface utilisateur des paramètres auront toujours
la priorité.
:::

---

# Table des matières

1. [Configuration de base](#configuration-de-base)
   - [Clés API](#clés-api)
   - [Espace de travail](#espace-de-travail)
   - [Débogage et journalisation](#débogage-et-journalisation)
   - [Gestion des sessions](#gestion-des-sessions)
   - [Trajectoires](#trajectoires)
   - [Stockage de fichiers](#stockage-de-fichiers)
   - [Gestion des tâches](#gestion-des-tâches)
   - [Configuration du bac à sable](#configuration-du-bac-à-sable)
   - [Divers](#divers)
2. [Configuration LLM](#configuration-llm)
   - [Informations d'identification AWS](#informations-didentification-aws)
   - [Configuration de l'API](#configuration-de-lapi)
   - [Fournisseur LLM personnalisé](#fournisseur-llm-personnalisé)
   - [Embeddings](#embeddings)
   - [Gestion des messages](#gestion-des-messages)
   - [Sélection du modèle](#sélection-du-modèle)
   - [Nouvelles tentatives](#nouvelles-tentatives)
   - [Options avancées](#options-avancées)
3. [Configuration de l'agent](#configuration-de-lagent)
   - [Configuration du micro-agent](#configuration-du-micro-agent)
   - [Configuration de la mémoire](#configuration-de-la-mémoire)
   - [Configuration LLM](#configuration-llm-2)
   - [Configuration de l'espace d'action](#configuration-de-lespace-daction)
   - [Utilisation du micro-agent](#utilisation-du-micro-agent)
4. [Configuration du bac à sable](#configuration-du-bac-à-sable-2)
   - [Exécution](#exécution)
   - [Image de conteneur](#image-de-conteneur)
   - [Mise en réseau](#mise-en-réseau)
   - [Linting et plugins](#linting-et-plugins)
   - [Dépendances et environnement](#dépendances-et-environnement)
   - [Évaluation](#évaluation)
5. [Configuration de sécurité](#configuration-de-sécurité)
   - [Mode de confirmation](#mode-de-confirmation)
   - [Analyseur de sécurité](#analyseur-de-sécurité)

---

## Configuration de base

Les options de configuration de base sont définies dans la section `[core]` du fichier `config.toml`.

**Clés API**
- `e2b_api_key`
  - Type : `str`
  - Valeur par défaut : `""`
  - Description : Clé API pour E2B

- `modal_api_token_id`
  - Type : `str`
  - Valeur par défaut : `""`
  - Description : ID du jeton API pour Modal

- `modal_api_token_secret`
  - Type : `str`
  - Valeur par défaut : `""`
  - Description : Secret du jeton API pour Modal

**Espace de travail**
- `workspace_base`
  - Type : `str`
  - Valeur par défaut : `"./workspace"`
  - Description : Chemin de base pour l'espace de travail

- `cache_dir`
  - Type : `str`
  - Valeur par défaut : `"/tmp/cache"`
  - Description : Chemin du répertoire de cache

**Débogage et journalisation**
- `debug`
  - Type : `bool`
  - Valeur par défaut : `false`
  - Description : Activer le débogage

- `disable_color`
  - Type : `bool`
  - Valeur par défaut : `false`
  - Description : Désactiver la couleur dans la sortie du terminal

**Trajectoires**
- `trajectories_path`
  - Type : `str`
  - Valeur par défaut : `"./trajectories"`
  - Description : Chemin pour stocker les trajectoires (peut être un dossier ou un fichier). Si c'est un dossier, les trajectoires seront enregistrées dans un fichier nommé avec l'ID de session et l'extension .json, dans ce dossier.

**Stockage de fichiers**
- `file_store_path`
  - Type : `str`
  - Valeur par défaut : `"/tmp/file_store"`
  - Description : Chemin de stockage des fichiers

- `file_store`
  - Type : `str`
  - Valeur par défaut : `"memory"`
  - Description : Type de stockage de fichiers

- `file_uploads_allowed_extensions`
  - Type : `list of str`
  - Valeur par défaut : `[".*"]`
  - Description : Liste des extensions de fichiers autorisées pour les téléchargements

- `file_uploads_max_file_size_mb`
  - Type : `int`
  - Valeur par défaut : `0`
  - Description : Taille maximale des fichiers pour les téléchargements, en mégaoctets

- `file_uploads_restrict_file_types`
  - Type : `bool`
  - Valeur par défaut : `false`
  - Description : Restreindre les types de fichiers pour les téléchargements de fichiers

- `file_uploads_allowed_extensions`
  - Type : `list of str`
  - Valeur par défaut : `[".*"]`
  - Description : Liste des extensions de fichiers autorisées pour les téléchargements

**Gestion des tâches**
- `max_budget_per_task`
  - Type : `float`
  - Valeur par défaut : `0.0`
  - Description : Budget maximal par tâche (0.0 signifie aucune limite)

- `max_iterations`
  - Type : `int`
  - Valeur par défaut : `100`
  - Description : Nombre maximal d'itérations

**Configuration du bac à sable**
- `workspace_mount_path_in_sandbox`
  - Type : `str`
  - Valeur par défaut : `"/workspace"`
  - Description : Chemin de montage de l'espace de travail dans le bac à sable

- `workspace_mount_path`
  - Type : `str`
  - Valeur par défaut : `""`
  - Description : Chemin de montage de l'espace de travail

- `workspace_mount_rewrite`
  - Type : `str`
  - Valeur par défaut : `""`
  - Description : Chemin pour réécrire le chemin de montage de l'espace de travail. Vous pouvez généralement ignorer cela, cela fait référence à des cas spéciaux d'exécution à l'intérieur d'un autre conteneur.

**Divers**
- `run_as_openhands`
  - Type : `bool`
  - Valeur par défaut : `true`
  - Description : Exécuter en tant qu'OpenHands

- `runtime`
  - Type : `str`
  - Valeur par défaut : `"eventstream"`
  - Description : Environnement d'exécution

- `default_agent`
  - Type : `str`
  - Valeur par défaut : `"CodeActAgent"`
  - Description : Nom de l'agent par défaut

- `jwt_secret`
  - Type : `str`
  - Valeur par défaut : `uuid.uuid4().hex`
  - Description : Secret JWT pour l'authentification. Veuillez le définir sur votre propre valeur.

## Configuration LLM

Les options de configuration LLM (Large Language Model) sont définies dans la section `[llm]` du fichier `config.toml`.

Pour les utiliser avec la commande docker, passez `-e LLM_<option>`. Exemple : `-e LLM_NUM_RETRIES`.

**Informations d'identification AWS**
- `aws_access_key_id`
  - Type : `str`
  - Valeur par défaut : `""`
  - Description : ID de clé d'accès AWS

- `aws_region_name`
  - Type : `str`
  - Valeur par défaut : `""`
  - Description : Nom de la région AWS

- `aws_secret_access_key`
  - Type : `str`
  - Valeur par défaut : `""`
  - Description : Clé d'accès secrète AWS

**Configuration de l'API**
- `api_key`
  - Type : `str`
  - Valeur par défaut : `None`
  - Description : Clé API à utiliser

- `base_url`
  - Type : `str`
  - Valeur par défaut : `""`
  - Description : URL de base de l'API

- `api_version`
  - Type : `str`
  - Valeur par défaut : `""`
  - Description : Version de l'API

- `input_cost_per_token`
  - Type : `float`
  - Valeur par défaut : `0.0`
  - Description : Coût par jeton d'entrée

- `output_cost_per_token`
  - Type : `float`
  - Valeur par défaut : `0.0`
  - Description : Coût par jeton de sortie

**Fournisseur LLM personnalisé**
- `custom_llm_provider`
  - Type : `str`
  - Valeur par défaut : `""`
  - Description : Fournisseur LLM personnalisé

**Embeddings**
- `embedding_base_url`
  - Type : `str`
  - Valeur par défaut : `""`
  - Description : URL de base de l'API d'embedding

- `embedding_deployment_name`
  - Type : `str`
  - Valeur par défaut : `""`
  - Description : Nom du déploiement d'embedding

- `embedding_model`
  - Type : `str`
  - Valeur par défaut : `"local"`
  - Description : Modèle d'embedding à utiliser

**Gestion des messages**
- `max_message_chars`
  - Type : `int`
  - Valeur par défaut : `30000`
  - Description : Le nombre maximum approximatif de caractères dans le contenu d'un événement inclus dans l'invite au LLM. Les observations plus grandes sont tronquées.

- `max_input_tokens`
  - Type : `int`
  - Valeur par défaut : `0`
  - Description : Nombre maximal de jetons d'entrée

- `max_output_tokens`
  - Type : `int`
  - Valeur par défaut : `0`
  - Description : Nombre maximal de jetons de sortie

**Sélection du modèle**
- `model`
  - Type : `str`
  - Valeur par défaut : `"claude-3-5-sonnet-20241022"`
  - Description : Modèle à utiliser

**Nouvelles tentatives**
- `num_retries`
  - Type : `int`
  - Valeur par défaut : `8`
  - Description : Nombre de nouvelles tentatives à effectuer

- `retry_max_wait`
  - Type : `int`
  - Valeur par défaut : `120`
  - Description : Temps d'attente maximal (en secondes) entre les tentatives de nouvelle tentative

- `retry_min_wait`
  - Type : `int`
  - Valeur par défaut : `15`
  - Description : Temps d'attente minimal (en secondes) entre les tentatives de nouvelle tentative

- `retry_multiplier`
  - Type : `float`
  - Valeur par défaut : `2.0`
  - Description : Multiplicateur pour le calcul du backoff exponentiel

**Options avancées**
- `drop_params`
  - Type : `bool`
  - Valeur par défaut : `false`
  - Description : Supprimer tous les paramètres non mappés (non pris en charge) sans provoquer d'exception

- `caching_prompt`
  - Type : `bool`
  - Valeur par défaut : `true`
  - Description : Utiliser la fonctionnalité de mise en cache des invites si elle est fournie par le LLM et prise en charge

- `ollama_base_url`
  - Type : `str`
  - Valeur par défaut : `""`
  - Description : URL de base pour l'API OLLAMA

- `temperature`
  - Type : `float`
  - Valeur par défaut : `0.0`
  - Description : Température pour l'API

- `timeout`
  - Type : `int`
  - Valeur par défaut : `0`
  - Description : Délai d'expiration pour l'API

- `top_p`
  - Type : `float`
  - Valeur par défaut : `1.0`
  - Description : Top p pour l'API

- `disable_vision`
  - Type : `bool`
  - Valeur par défaut : `None`
  - Description : Si le modèle est capable de vision, cette option permet de désactiver le traitement des images (utile pour réduire les coûts)

## Configuration de l'agent

Les options de configuration de l'agent sont définies dans les sections `[agent]` et `[agent.<agent_name>]` du fichier `config.toml`.

**Configuration du micro-agent**
- `micro_agent_name`
  - Type : `str`
  - Valeur par défaut : `""`
  - Description : Nom du micro-agent à utiliser pour cet agent

**Configuration de la mémoire**
- `memory_enabled`
  - Type : `bool`
  - Valeur par défaut : `false`
  - Description : Si la mémoire à long terme (embeddings) est activée

- `memory_max_threads`
  - Type : `int`
  - Valeur par défaut : `3`
  - Description : Le nombre maximum de threads indexant en même temps pour les embeddings

**Configuration LLM**
- `llm_config`
  - Type : `str`
  - Valeur par défaut : `'your-llm-config-group'`
  - Description : Le nom de la configuration LLM à utiliser

**Configuration de l'espace d'action**
- `function_calling`
  - Type : `bool`
  - Valeur par défaut : `true`
  - Description : Si l'appel de fonction est activé

- `codeact_enable_browsing`
  - Type : `bool`
  - Valeur par défaut : `false`
  - Description : Si le délégué de navigation est activé dans l'espace d'action (fonctionne uniquement avec l'appel de fonction)

- `codeact_enable_llm_editor`
  - Type : `bool`
  - Valeur par défaut : `false`
  - Description : Si l'éditeur LLM est activé dans l'espace d'action (foncti

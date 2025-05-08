# LLM local avec SGLang ou vLLM

:::warning
Lorsque vous utilisez un LLM local, OpenHands peut avoir des fonctionnalités limitées.
Il est fortement recommandé d'utiliser des GPU pour servir les modèles locaux afin d'obtenir une expérience optimale.
:::

## Actualités

- 2025/03/31 : Nous avons publié un modèle ouvert OpenHands LM v0.1 32B qui atteint 37,1% sur SWE-Bench Verified
([blog](https://www.all-hands.dev/blog/introducing-openhands-lm-32b----a-strong-open-coding-agent-model), [modèle](https://huggingface.co/all-hands/openhands-lm-32b-v0.1)).

## Télécharger le modèle depuis Huggingface

Par exemple, pour télécharger [OpenHands LM 32B v0.1](https://huggingface.co/all-hands/openhands-lm-32b-v0.1) :

```bash
huggingface-cli download all-hands/openhands-lm-32b-v0.1 --local-dir all-hands/openhands-lm-32b-v0.1
```

## Créer un point de terminaison compatible OpenAI avec un framework de service de modèle

### Service avec SGLang

- Installez SGLang en suivant [la documentation officielle](https://docs.sglang.ai/start/install.html).
- Exemple de commande de lancement pour OpenHands LM 32B (avec au moins 2 GPU) :

```bash
SGLANG_ALLOW_OVERWRITE_LONGER_CONTEXT_LEN=1 python3 -m sglang.launch_server \
    --model all-hands/openhands-lm-32b-v0.1 \
    --served-model-name openhands-lm-32b-v0.1 \
    --port 8000 \
    --tp 2 --dp 1 \
    --host 0.0.0.0 \
    --api-key mykey --context-length 131072
```

### Service avec vLLM

- Installez vLLM en suivant [la documentation officielle](https://docs.vllm.ai/en/latest/getting_started/installation.html).
- Exemple de commande de lancement pour OpenHands LM 32B (avec au moins 2 GPU) :

```bash
vllm serve all-hands/openhands-lm-32b-v0.1 \
    --host 0.0.0.0 --port 8000 \
    --api-key mykey \
    --tensor-parallel-size 2 \
    --served-model-name openhands-lm-32b-v0.1
    --enable-prefix-caching
```

## Exécuter et configurer OpenHands

### Exécuter OpenHands

#### Utilisation de Docker

Exécutez OpenHands en utilisant [la commande docker run officielle](../installation#start-the-app).

#### Utilisation du mode développement

Utilisez les instructions dans [Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md) pour construire OpenHands.
Assurez-vous que `config.toml` existe en exécutant `make setup-config` qui en créera un pour vous. Dans le fichier `config.toml`, saisissez ce qui suit :

```
[core]
workspace_base="/path/to/your/workspace"

[llm]
model="openhands-lm-32b-v0.1"
ollama_base_url="http://localhost:8000"
```

Démarrez OpenHands en utilisant `make run`.

### Configurer OpenHands

Une fois qu'OpenHands est en cours d'exécution, vous devrez définir les éléments suivants dans l'interface utilisateur d'OpenHands via les Paramètres :
1. Activez les options `Avancées`.
2. Définissez les éléments suivants :
- `Modèle personnalisé` sur `openai/<served-model-name>` (par exemple `openai/openhands-lm-32b-v0.1`)
- `URL de base` sur `http://host.docker.internal:8000`
- `Clé API` sur la même chaîne que celle que vous avez définie lors du service du modèle (par exemple `mykey`)

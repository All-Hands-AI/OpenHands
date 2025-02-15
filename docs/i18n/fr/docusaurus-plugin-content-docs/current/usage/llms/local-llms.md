

# LLM local avec Ollama

:::warning
Lors de l'utilisation d'un LLM local, OpenHands peut avoir des fonctionnalités limitées.
:::

Assurez-vous que le serveur Ollama est opérationnel.
Pour des instructions détaillées sur le démarrage, référez-vous à [ici](https://github.com/ollama/ollama).

Ce guide suppose que vous avez démarré ollama avec `ollama serve`. Si vous exécutez ollama différemment (par exemple dans docker), les instructions peuvent nécessiter des modifications. Veuillez noter que si vous utilisez WSL, la configuration par défaut d'ollama bloque les requêtes provenant des conteneurs docker. Voir [ici](#configuring-ollama-service-wsl-fr).

## Récupérer les modèles

Les noms des modèles Ollama peuvent être trouvés [ici](https://ollama.com/library). Pour un petit exemple, vous pouvez utiliser le modèle `codellama:7b`. Les modèles plus gros auront généralement de meilleures performances.

```bash
ollama pull codellama:7b
```

Vous pouvez vérifier quels modèles vous avez téléchargés comme ceci :

```bash
~$ ollama list
NAME                            ID              SIZE    MODIFIED
codellama:7b                    8fdf8f752f6e    3.8 GB  6 weeks ago
mistral:7b-instruct-v0.2-q4_K_M eb14864c7427    4.4 GB  2 weeks ago
starcoder2:latest               f67ae0f64584    1.7 GB  19 hours ago
```

## Exécuter OpenHands avec Docker

### Démarrer OpenHands
Utilisez les instructions [ici](../getting-started) pour démarrer OpenHands en utilisant Docker.
Mais lorsque vous exécutez `docker run`, vous devrez ajouter quelques arguments supplémentaires :

```bash
docker run # ...
    --add-host host.docker.internal:host-gateway \
    -e LLM_OLLAMA_BASE_URL="http://host.docker.internal:11434" \
    # ...
```

LLM_OLLAMA_BASE_URL est optionnel. Si vous le définissez, il sera utilisé pour afficher
les modèles installés disponibles dans l'interface utilisateur.


### Configurer l'application Web

Lors de l'exécution d'`openhands`, vous devrez définir les éléments suivants dans l'interface utilisateur d'OpenHands via les paramètres :
- le modèle à "ollama/&lt;nom-du-modèle&gt;"
- l'URL de base à `http://host.docker.internal:11434`
- la clé API est optionnelle, vous pouvez utiliser n'importe quelle chaîne, comme `ollama`.


## Exécuter OpenHands en mode développement

### Compiler à partir du code source

Utilisez les instructions dans [Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md) pour compiler OpenHands.
Assurez-vous que `config.toml` est présent en exécutant `make setup-config` qui en créera un pour vous. Dans `config.toml`, entrez ce qui suit :

```
[core]
workspace_base="./workspace"

[llm]
embedding_model="local"
ollama_base_url="http://localhost:11434"

```

Terminé ! Vous pouvez maintenant démarrer OpenHands avec : `make run`. Vous devriez maintenant pouvoir vous connecter à `http://localhost:3000/`

### Configurer l'application Web

Dans l'interface utilisateur d'OpenHands, cliquez sur la roue des paramètres dans le coin inférieur gauche.
Ensuite, dans le champ `Model`, entrez `ollama/codellama:7b`, ou le nom du modèle que vous avez récupéré précédemment.
S'il n'apparaît pas dans la liste déroulante, activez `Advanced Settings` et tapez-le. Veuillez noter : vous avez besoin du nom du modèle tel qu'il est listé par `ollama list`, avec le préfixe `ollama/`.

Dans le champ API Key, entrez `ollama` ou n'importe quelle valeur, puisque vous n'avez pas besoin d'une clé particulière.

Dans le champ Base URL, entrez `http://localhost:11434`.

Et maintenant vous êtes prêt à démarrer !

## Configurer le service ollama (WSL) {#configuring-ollama-service-wsl-fr}

La configuration par défaut d'ollama dans WSL ne sert que localhost. Cela signifie que vous ne pouvez pas y accéder depuis un conteneur docker. Par ex. cela ne fonctionnera pas avec OpenHands. Testons d'abord qu'ollama fonctionne correctement.

```bash
ollama list # obtenir la liste des modèles installés
curl http://localhost:11434/api/generate -d '{"model":"[NOM]","prompt":"hi"}'
#ex. curl http://localhost:11434/api/generate -d '{"model":"codellama:7b","prompt":"hi"}'
#ex. curl http://localhost:11434/api/generate -d '{"model":"codellama","prompt":"hi"}' #le tag est optionnel s'il n'y en a qu'un
```

Une fois cela fait, testez qu'il autorise les requêtes "extérieures", comme celles provenant d'un conteneur docker.

```bash
docker ps # obtenir la liste des conteneurs docker en cours d'exécution, pour un test plus précis choisissez le conteneur sandbox OpenHands.
docker exec [ID CONTENEUR] curl http://host.docker.internal:11434/api/generate -d '{"model":"[NOM]","prompt":"hi"}'
#ex. docker exec cd9cc82f7a11 curl http://host.docker.internal:11434/api/generate -d '{"model":"codellama","prompt":"hi"}'
```

## Résoudre le problème

Maintenant, faisons en sorte que cela fonctionne. Modifiez /etc/systemd/system/ollama.service avec des privilèges sudo. (Le chemin peut varier selon la distribution Linux)

```bash
sudo vi /etc/systemd/system/ollama.service
```

ou

```bash
sudo nano /etc/systemd/system/ollama.service
```

Dans le bloc [Service], ajoutez ces lignes

```
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
```

Ensuite, sauvegardez, rechargez la configuration et redémarrez le service.

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

Enfin, testez qu'ollama est accessible depuis le conteneur

```bash
ollama list # obtenir la liste des modèles installés
docker ps # obtenir la liste des conteneurs docker en cours d'exécution, pour un test plus précis choisissez le conteneur sandbox OpenHands.
docker exec [ID CONTENEUR] curl http://host.docker.internal:11434/api/generate -d '{"model":"[NOM]","prompt":"hi"}'
```


# LLM local avec LM Studio

Étapes pour configurer LM Studio :
1. Ouvrez LM Studio
2. Allez dans l'onglet Serveur local.
3. Cliquez sur le bouton "Démarrer le serveur".
4. Sélectionnez le modèle que vous souhaitez utiliser dans la liste déroulante.


Définissez les configurations suivantes :
```bash
LLM_MODEL="openai/lmstudio"
LLM_BASE_URL="http://localhost:1234/v1"
CUSTOM_LLM_PROVIDER="openai"
```

### Docker

```bash
docker run # ...
    -e LLM_MODEL="openai/lmstudio" \
    -e LLM_BASE_URL="http://host.docker.internal:1234/v1" \
    -e CUSTOM_LLM_PROVIDER="openai" \
    # ...
```

Vous devriez maintenant pouvoir vous connecter à `http://localhost:3000/`

Dans l'environnement de développement, vous pouvez définir les configurations suivantes dans le fichier `config.toml` :

```
[core]
workspace_base="./workspace"

[llm]
model="openai/lmstudio"
base_url="http://localhost:1234/v1"
custom_llm_provider="openai"
```

Terminé ! Vous pouvez maintenant démarrer OpenHands avec : `make run` sans Docker. Vous devriez maintenant pouvoir vous connecter à `http://localhost:3000/`

# Note

Pour WSL, exécutez les commandes suivantes dans cmd pour configurer le mode réseau en miroir :

```
python -c  "print('[wsl2]\nnetworkingMode=mirrored',file=open(r'%UserProfile%\.wslconfig','w'))"
wsl --shutdown
```

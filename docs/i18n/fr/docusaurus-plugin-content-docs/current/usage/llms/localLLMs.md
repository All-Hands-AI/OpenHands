# LLM Local avec Ollama

Assurez-vous que le serveur Ollama est en cours d'exécution.
Pour des instructions détaillées de démarrage, consultez [ici](https://github.com/ollama/ollama)

Ce guide suppose que vous avez démarré ollama avec `ollama serve`. Si vous exécutez ollama différemment (par exemple, à l'intérieur de docker), les instructions pourraient devoir être modifiées. Veuillez noter que si vous utilisez WSL, la configuration par défaut de ollama bloque les requêtes des conteneurs docker. Voir [ici](#configuring-ollama-service-fr).

## Télécharger des modèles

Les noms des modèles Ollama peuvent être trouvés [ici](https://ollama.com/library). Pour un petit exemple, vous pouvez utiliser
le modèle `codellama:7b`. Des modèles plus grands offriront généralement de meilleures performances.

```bash
ollama pull codellama:7b
```

vous pouvez vérifier quels modèles vous avez téléchargés de cette manière :

```bash
~$ ollama list
NAME                            ID              SIZE    MODIFIED
codellama:7b                    8fdf8f752f6e    3.8 GB  6 weeks ago
mistral:7b-instruct-v0.2-q4_K_M eb14864c7427    4.4 GB  2 weeks ago
starcoder2:latest               f67ae0f64584    1.7 GB  19 hours ago
```

## Démarrer OpenDevin

### Docker

Utilisez les instructions [ici](../intro) pour démarrer OpenDevin en utilisant Docker.
Mais lors de l'exécution de `docker run`, vous devrez ajouter quelques arguments supplémentaires :

```bash
--add-host host.docker.internal:host-gateway \
-e LLM_API_KEY="ollama" \
-e LLM_BASE_URL="http://host.docker.internal:11434" \
```

Par exemple :

```bash
# Le répertoire que vous souhaitez qu'OpenDevin modifie. DOIT être un chemin absolu !
export WORKSPACE_BASE=$(pwd)/workspace

docker run \
    -it \
    --pull=always \
    --add-host host.docker.internal:host-gateway \
    -e SANDBOX_USER_ID=$(id -u) \
    -e LLM_API_KEY="ollama" \
    -e LLM_BASE_URL="http://host.docker.internal:11434" \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -p 3000:3000 \
    ghcr.io/opendevin/opendevin:main
```

Vous devriez maintenant pouvoir vous connecter à `http://localhost:3000/`

### Compiler à partir des sources

Utilisez les instructions dans [Development.md](https://github.com/OpenDevin/OpenDevin/blob/main/Development.md) pour compiler OpenDevin.
Assurez-vous que `config.toml` soit présent en exécutant `make setup-config` qui en créera un pour vous. Dans `config.toml`, saisissez les éléments suivants :

```
LLM_MODEL="ollama/codellama:7b"
LLM_API_KEY="ollama"
LLM_EMBEDDING_MODEL="local"
LLM_BASE_URL="http://localhost:11434"
WORKSPACE_BASE="./workspace"
WORKSPACE_DIR="$(pwd)/workspace"
```

Remplacez `LLM_MODEL` par celui de votre choix si nécessaire.

Fini ! Vous pouvez maintenant démarrer Devin avec : `make run` sans Docker. Vous devriez maintenant pouvoir vous connecter à `http://localhost:3000/`

## Sélection de votre modèle

Dans l'interface OpenDevin, cliquez sur l'icône des paramètres en bas à gauche.
Ensuite, dans l'entrée `Model`, saisissez `ollama/codellama:7b`, ou le nom du modèle que vous avez téléchargé précédemment.
S'il n'apparaît pas dans un menu déroulant, ce n'est pas grave, tapez-le simplement. Cliquez sur Enregistrer lorsque vous avez terminé.

Et maintenant, vous êtes prêt à démarrer !

## Configuration du service ollama (WSL){#configuring-ollama-service-fr}

La configuration par défaut pour ollama sous WSL ne sert que localhost. Cela signifie que vous ne pouvez pas l'atteindre depuis un conteneur docker, par exemple, il ne fonctionnera pas avec OpenDevin. Testons d'abord que ollama est en cours d'exécution correctement.

```bash
ollama list # obtenir la liste des modèles installés
curl http://localhost:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
#ex. curl http://localhost:11434/api/generate -d '{"model":"codellama:7b","prompt":"hi"}'
#ex. curl http://localhost:11434/api/generate -d '{"model":"codellama","prompt":"hi"}' #le tag est optionnel s'il n'y en a qu'un seul
```

Une fois cela fait, testez qu'il accepte les requêtes "externes", comme celles provenant d'un conteneur docker.

```bash
docker ps # obtenir la liste des conteneurs docker en cours d'exécution, pour un test le plus précis choisissez le conteneur de sandbox open devin.
docker exec [CONTAINER ID] curl http://host.docker.internal:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
#ex. docker exec cd9cc82f7a11 curl http://host.docker.internal:11434/api/generate -d '{"model":"codellama","prompt":"hi"}'
```

## Correction

Maintenant faisons en sorte que cela fonctionne. Modifiez /etc/systemd/system/ollama.service avec les privilèges sudo. (Le chemin peut varier selon la distribution Linux)

```bash
sudo vi /etc/systemd/system/ollama.service
```

ou

```bash
sudo nano /etc/systemd/system/ollama.service
```

Dans la section [Service], ajoutez ces lignes

```
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
```

Ensuite, sauvegardez, rechargez la configuration et redémarrez le service.

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

Enfin, testez que ollama est accessible depuis le conteneur

```bash
ollama list # obtenir la liste des modèles installés
docker ps # obtenir la liste des conteneurs docker en cours d'exécution, pour un test le plus précis choisissez le conteneur de sandbox open devin.
docker exec [CONTAINER ID] curl http://host.docker.internal:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
```

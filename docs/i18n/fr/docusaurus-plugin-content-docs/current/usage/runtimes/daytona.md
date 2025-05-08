# Runtime Daytona

Vous pouvez utiliser [Daytona](https://www.daytona.io/) comme fournisseur de runtime :

## Étape 1 : Récupérer votre clé API Daytona
1. Visitez le [Tableau de bord Daytona](https://app.daytona.io/dashboard/keys).
2. Cliquez sur **"Create Key"**.
3. Entrez un nom pour votre clé et confirmez la création.
4. Une fois la clé générée, copiez-la.

## Étape 2 : Définir votre clé API comme variable d'environnement
Exécutez la commande suivante dans votre terminal, en remplaçant `<your-api-key>` par la clé que vous avez copiée :
```bash
export DAYTONA_API_KEY="<your-api-key>"
```

Cette étape garantit qu'OpenHands peut s'authentifier auprès de la plateforme Daytona lors de son exécution.

## Étape 3 : Exécuter OpenHands localement avec Docker
Pour démarrer la dernière version d'OpenHands sur votre machine, exécutez la commande suivante dans votre terminal :
```bash
bash -i <(curl -sL https://get.daytona.io/openhands)
```

### Ce que fait cette commande :
- Télécharge le script de la dernière version d'OpenHands.
- Exécute le script dans une session Bash interactive.
- Extrait et exécute automatiquement le conteneur OpenHands à l'aide de Docker.

Une fois exécuté, OpenHands devrait fonctionner localement et être prêt à l'emploi.

Pour plus de détails et une initialisation manuelle, consultez le [README.md](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/runtime/impl/daytona/README.md) complet

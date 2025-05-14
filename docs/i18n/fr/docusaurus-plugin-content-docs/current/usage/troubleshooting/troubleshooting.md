# 🚧 Dépannage

:::tip
OpenHands ne prend en charge Windows que via WSL. Veuillez vous assurer d'exécuter toutes les commandes dans votre terminal WSL.
:::

### Impossible d'accéder à l'onglet VS Code via une IP locale

**Description**

Lors de l'accès à OpenHands via une URL non-localhost (comme une adresse IP LAN), l'onglet VS Code affiche une erreur "Forbidden", alors que les autres parties de l'interface fonctionnent correctement.

**Résolution**

Cela se produit car VS Code s'exécute sur un port élevé aléatoire qui peut ne pas être exposé ou accessible depuis d'autres machines. Pour résoudre ce problème :

1. Définissez un port spécifique pour VS Code en utilisant la variable d'environnement `SANDBOX_VSCODE_PORT` :
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

2. Assurez-vous d'exposer le même port avec `-p 41234:41234` dans votre commande Docker.

3. Alternativement, vous pouvez définir cela dans votre fichier `config.toml` :
   ```toml
   [sandbox]
   vscode_port = 41234
   ```

### Échec du lancement du client docker

**Description**

Lors de l'exécution d'OpenHands, l'erreur suivante apparaît :
```
Launch docker client failed. Please make sure you have installed docker and started docker desktop/daemon.
```

**Résolution**

Essayez ces solutions dans l'ordre :
* Confirmez que `docker` est en cours d'exécution sur votre système. Vous devriez pouvoir exécuter `docker ps` dans le terminal avec succès.
* Si vous utilisez Docker Desktop, assurez-vous que `Paramètres > Avancé > Autoriser l'utilisation du socket Docker par défaut` est activé.
* Selon votre configuration, vous pourriez avoir besoin d'activer `Paramètres > Ressources > Réseau > Activer le réseau hôte` dans Docker Desktop.
* Réinstallez Docker Desktop.

### Erreur de permission

**Description**

Lors de la première invite, une erreur avec `Permission Denied` ou `PermissionError` est affichée.

**Résolution**

* Vérifiez si le répertoire `~/.openhands-state` appartient à `root`. Si c'est le cas, vous pouvez :
  * Changer le propriétaire du répertoire : `sudo chown <utilisateur>:<utilisateur> ~/.openhands-state`.
  * ou mettre à jour les permissions du répertoire : `sudo chmod 777 ~/.openhands-state`
  * ou le supprimer si vous n'avez pas besoin des données précédentes. OpenHands le recréera. Vous devrez ressaisir les paramètres LLM.
* Si vous montez un répertoire local, assurez-vous que votre `WORKSPACE_BASE` dispose des permissions nécessaires pour l'utilisateur exécutant OpenHands.

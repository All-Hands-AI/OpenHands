# Notes pour les utilisateurs de Windows et WSL

OpenDevin ne supporte Windows que via [WSL](https://learn.microsoft.com/en-us/windows/wsl/install).
Veuillez vous assurer de lancer toutes les commandes à l'intérieur de votre terminal WSL.

## Dépannage

### Erreur : 'docker' n'a pas pu être trouvé dans cette distribution WSL 2.

Si vous utilisez Docker Desktop, assurez-vous de le démarrer avant d'exécuter toute commande docker depuis l'intérieur de WSL.
Docker doit également avoir l'option d'intégration WSL activée.

### Recommandation : Ne pas exécuter en tant qu'utilisateur root

Pour des raisons de sécurité, il est fortement recommandé de ne pas exécuter OpenDevin en tant qu'utilisateur root, mais en tant qu'utilisateur avec un UID non nul.
De plus, les sandboxes persistants ne seront pas pris en charge lors de l'exécution en tant que root et un message approprié pourrait apparaître lors du démarrage d'OpenDevin.

Références :

* [Pourquoi il est mauvais de se connecter en tant que root](https://askubuntu.com/questions/16178/why-is-it-bad-to-log-in-as-root)
* [Définir l'utilisateur par défaut dans WSL](https://www.tenforums.com/tutorials/128152-set-default-user-windows-subsystem-linux-distro-windows-10-a.html#option2)
Astuce pour la 2e référence : pour les utilisateurs d'Ubuntu, la commande pourrait en fait être "ubuntupreview" au lieu de "ubuntu".

### Échec de la création de l'utilisateur opendevin

Si vous rencontrez l'erreur suivante lors de l'installation :

```sh
Exception: Failed to create opendevin user in sandbox: 'useradd: UID 0 is not unique'
```

Vous pouvez la résoudre en exécutant :

```sh
export SANDBOX_USER_ID=1000
```

### Installation de Poetry

* Si vous rencontrez des problèmes pour exécuter Poetry même après l'avoir installé pendant le processus de construction, il peut être nécessaire d'ajouter son chemin binaire à votre environnement :

```sh
export PATH="$HOME/.local/bin:$PATH"
```

* Si `make build` s'arrête avec une erreur telle que :

```sh
ModuleNotFoundError: no module named <module-name>
```

Cela pourrait être un problème avec le cache de Poetry.
Essayez d'exécuter ces 2 commandes l'une après l'autre :

```sh
rm -r ~/.cache/pypoetry
make build
```

### L'objet NoneType n'a pas d'attribut 'request'

Si vous rencontrez des problèmes liés au réseau, tels que `NoneType object has no attribute 'request'` lors de l'exécution de `make run`, il peut être nécessaire de configurer vos paramètres réseau WSL2. Suivez ces étapes :

* Ouvrez ou créez le fichier `.wslconfig` situé à `C:\Users\%username%\.wslconfig` sur votre machine hôte Windows.
* Ajoutez la configuration suivante au fichier `.wslconfig` :

```sh
[wsl2]
networkingMode=mirrored
localhostForwarding=true
```

* Enregistrez le fichier `.wslconfig`.
* Redémarrez WSL2 complètement en quittant toute instance WSL2 en cours d'exécution et en exécutant la commande `wsl --shutdown` dans votre invite de commande ou terminal.
* Après avoir redémarré WSL, essayez d'exécuter `make run` à nouveau.
Le problème réseau devrait être résolu.

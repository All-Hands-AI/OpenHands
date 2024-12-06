

# Notes pour les utilisateurs de WSL sur Windows

OpenHands ne prend en charge Windows que via [WSL](https://learn.microsoft.com/en-us/windows/wsl/install).
Veuillez vous assurer d'exécuter toutes les commandes dans votre terminal WSL.

## Dépannage

### Recommandation : Ne pas exécuter en tant qu'utilisateur root

Pour des raisons de sécurité, il est fortement recommandé de ne pas exécuter OpenHands en tant qu'utilisateur root, mais en tant qu'utilisateur avec un UID non nul.

Références :

* [Pourquoi il est mauvais de se connecter en tant que root](https://askubuntu.com/questions/16178/why-is-it-bad-to-log-in-as-root)
* [Définir l'utilisateur par défaut dans WSL](https://www.tenforums.com/tutorials/128152-set-default-user-windows-subsystem-linux-distro-windows-10-a.html#option2)
Astuce concernant la 2ème référence : pour les utilisateurs d'Ubuntu, la commande pourrait en fait être "ubuntupreview" au lieu de "ubuntu".

---
### Erreur : 'docker' n'a pas pu être trouvé dans cette distribution WSL 2.

Si vous utilisez Docker Desktop, assurez-vous de le démarrer avant d'appeler toute commande docker depuis WSL.
Docker doit également avoir l'option d'intégration WSL activée.

---
### Installation de Poetry

* Si vous rencontrez des problèmes pour exécuter Poetry même après l'avoir installé pendant le processus de build, vous devrez peut-être ajouter son chemin binaire à votre environnement :

```sh
export PATH="$HOME/.local/bin:$PATH"
```

* Si make build s'arrête sur une erreur comme celle-ci :

```sh
ModuleNotFoundError: no module named <module-name>
```

Cela pourrait être un problème avec le cache de Poetry.
Essayez d'exécuter ces 2 commandes l'une après l'autre :

```sh
rm -r ~/.cache/pypoetry
make build
```

---
### L'objet NoneType n'a pas d'attribut 'request'

Si vous rencontrez des problèmes liés au réseau, tels que `NoneType object has no attribute 'request'` lors de l'exécution de `make run`, vous devrez peut-être configurer les paramètres réseau de WSL2. Suivez ces étapes :

* Ouvrez ou créez le fichier `.wslconfig` situé à `C:\Users\%username%\.wslconfig` sur votre machine hôte Windows.
* Ajoutez la configuration suivante au fichier `.wslconfig` :

```sh
[wsl2]
networkingMode=mirrored
localhostForwarding=true
```

* Enregistrez le fichier `.wslconfig`.
* Redémarrez complètement WSL2 en quittant toutes les instances WSL2 en cours d'exécution et en exécutant la commande `wsl --shutdown` dans votre invite de commande ou terminal.
* Après avoir redémarré WSL, essayez d'exécuter à nouveau `make run`.
Le problème de réseau devrait être résolu.

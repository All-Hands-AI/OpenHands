

# Persistance des données de session

Avec l'installation standard, les données de session sont stockées en mémoire. Actuellement, si le service OpenHands est redémarré,
les sessions précédentes deviennent invalides (un nouveau secret est généré) et ne sont donc pas récupérables.

## Comment persister les données de session

### Workflow de développement
Dans le fichier `config.toml`, spécifiez ce qui suit :
```
[core]
...
file_store="local"
file_store_path="/absolute/path/to/openhands/cache/directory"
jwt_secret="secretpass"
```

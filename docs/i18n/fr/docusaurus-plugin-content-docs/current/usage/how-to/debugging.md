# Débogage

Ce qui suit est destiné à servir d'introduction au débogage d'OpenHands à des fins de développement.

## Serveur / VSCode

Le fichier `launch.json` suivant permettra de déboguer les éléments de l'agent, du contrôleur et du serveur, mais pas le bac à sable (qui s'exécute dans Docker). Il ignorera tous les changements dans le répertoire `workspace/` :

```
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "OpenHands CLI",
            "type": "debugpy",
            "request": "launch",
            "module": "openhands.core.cli",
            "justMyCode": false
        },
        {
            "name": "OpenHands WebApp",
            "type": "debugpy",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "openhands.server.listen:app",
                "--reload",
                "--reload-exclude",
                "${workspaceFolder}/workspace",
                "--port",
                "3000"
            ],
            "justMyCode": false
        }
    ]
}
```

Des configurations de débogage plus spécifiques qui incluent davantage de paramètres peuvent être spécifiées :

```
    ...
    {
      "name": "Debug CodeAct",
      "type": "debugpy",
      "request": "launch",
      "module": "openhands.core.main",
      "args": [
        "-t",
        "Ask me what your task is.",
        "-d",
        "${workspaceFolder}/workspace",
        "-c",
        "CodeActAgent",
        "-l",
        "llm.o1",
        "-n",
        "prompts"
      ],
      "justMyCode": false
    }
    ...
```

Les valeurs dans l'extrait ci-dessus peuvent être mises à jour de sorte que :

    * *t* : la tâche
    * *d* : le répertoire de travail openhands
    * *c* : l'agent
    * *l* : la configuration LLM (prédéfinie dans config.toml)
    * *n* : nom de session (par exemple, nom d'eventstream)

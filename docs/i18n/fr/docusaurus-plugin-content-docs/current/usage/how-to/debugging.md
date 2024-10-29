

# Débogage

Ce qui suit est destiné à servir d'introduction au débogage d'OpenHands à des fins de développement.

## Serveur / VSCode

Le `launch.json` suivant permettra de déboguer les éléments agent, contrôleur et serveur, mais pas le bac à sable (qui s'exécute dans docker). Il ignorera toutes les modifications à l'intérieur du répertoire `workspace/` :

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

Des configurations de débogage plus spécifiques qui incluent plus de paramètres peuvent être spécifiées :

```
    ...
    {
      "name": "Debug CodeAct",
      "type": "debugpy",
      "request": "launch",
      "module": "openhands.core.main",
      "args": [
        "-t",
        "Demandez-moi quelle est votre tâche.",
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

Les valeurs dans l'extrait ci-dessus peuvent être mises à jour de telle sorte que :

    * *t* : la tâche
    * *d* : le répertoire de l'espace de travail openhands
    * *c* : l'agent
    * *l* : la configuration LLM (prédéfinie dans config.toml)
    * *n* : le nom de la session (par exemple, le nom du flux d'événements)

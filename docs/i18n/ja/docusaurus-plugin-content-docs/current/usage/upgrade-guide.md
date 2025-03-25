

# ⬆️ Guide de mise à niveau

## 0.8.0 (2024-07-13)

### Changements de configuration importants

Dans cette version, nous avons introduit quelques changements importants dans les configurations backend.
Si vous avez uniquement utilisé OpenHands via l'interface frontend (interface web), aucune action n'est nécessaire.

Voici une liste des changements importants dans les configurations. Ils ne s'appliquent qu'aux utilisateurs qui
utilisent OpenHands CLI via `main.py`. Pour plus de détails, voir [#2756](https://github.com/All-Hands-AI/OpenHands/pull/2756).

#### Suppression de l'option --model-name de main.py

Veuillez noter que l'option `--model-name`, ou `-m`, n'existe plus. Vous devez configurer les
configurations LLM dans `config.toml` ou via des variables d'environnement.

#### Les groupes de configuration LLM doivent être des sous-groupes de 'llm'

Avant la version 0.8, vous pouviez utiliser un nom arbitraire pour la configuration LLM dans `config.toml`, par exemple :

```toml
[gpt-4o]
model="gpt-4o"
api_key="<your_api_key>"
```

puis utiliser l'argument CLI `--llm-config` pour spécifier le groupe de configuration LLM souhaité
par nom. Cela ne fonctionne plus. Au lieu de cela, le groupe de configuration doit être sous le groupe `llm`,
par exemple :

```toml
[llm.gpt-4o]
model="gpt-4o"
api_key="<your_api_key>"
```

Si vous avez un groupe de configuration nommé `llm`, il n'est pas nécessaire de le modifier, il sera utilisé
comme groupe de configuration LLM par défaut.

#### Le groupe 'agent' ne contient plus le champ 'name'

Avant la version 0.8, vous pouviez avoir ou non un groupe de configuration nommé `agent` qui
ressemblait à ceci :

```toml
[agent]
name="CodeActAgent"
memory_max_threads=2
```

Notez que le champ `name` est maintenant supprimé. Au lieu de cela, vous devez mettre le champ `default_agent`
sous le groupe `core`, par exemple :

```toml
[core]
# autres configurations
default_agent='CodeActAgent'

[agent]
llm_config='llm'
memory_max_threads=2

[agent.CodeActAgent]
llm_config='gpt-4o'
```

Notez que, comme pour les sous-groupes `llm`, vous pouvez également définir des sous-groupes `agent`.
De plus, un agent peut être associé à un groupe de configuration LLM spécifique. Pour plus
de détails, voir les exemples dans `config.template.toml`.

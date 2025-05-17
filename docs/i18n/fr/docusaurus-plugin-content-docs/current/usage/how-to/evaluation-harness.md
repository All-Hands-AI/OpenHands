# Évaluation

Ce guide fournit un aperçu de la façon d'intégrer votre propre benchmark d'évaluation dans le framework OpenHands.

## Configuration de l'environnement et configuration du LLM

Veuillez suivre les instructions [ici](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md) pour configurer votre environnement de développement local.
OpenHands en mode développement utilise `config.toml` pour suivre la plupart des configurations.

Voici un exemple de fichier de configuration que vous pouvez utiliser pour définir et utiliser plusieurs LLM :

```toml
[llm]
# IMPORTANT: ajoutez votre clé API ici et définissez le modèle que vous souhaitez évaluer
model = "claude-3-5-sonnet-20241022"
api_key = "sk-XXX"

[llm.eval_gpt4_1106_preview_llm]
model = "gpt-4-1106-preview"
api_key = "XXX"
temperature = 0.0

[llm.eval_some_openai_compatible_model_llm]
model = "openai/MODEL_NAME"
base_url = "https://OPENAI_COMPATIBLE_URL/v1"
api_key = "XXX"
temperature = 0.0
```


## Comment utiliser OpenHands en ligne de commande

OpenHands peut être exécuté depuis la ligne de commande en utilisant le format suivant :

```bash
poetry run python ./openhands/core/main.py \
        -i <max_iterations> \
        -t "<task_description>" \
        -c <agent_class> \
        -l <llm_config>
```

Par exemple :

```bash
poetry run python ./openhands/core/main.py \
        -i 10 \
        -t "Write me a bash script that prints hello world." \
        -c CodeActAgent \
        -l llm
```

Cette commande exécute OpenHands avec :
- Un maximum de 10 itérations
- La description de tâche spécifiée
- Utilisant le CodeActAgent
- Avec la configuration LLM définie dans la section `llm` de votre fichier `config.toml`

## Comment fonctionne OpenHands

Le point d'entrée principal d'OpenHands se trouve dans `openhands/core/main.py`. Voici un flux simplifié de son fonctionnement :

1. Analyser les arguments de ligne de commande et charger la configuration
2. Créer un environnement d'exécution en utilisant `create_runtime()`
3. Initialiser l'agent spécifié
4. Exécuter le contrôleur en utilisant `run_controller()`, qui :
   - Attache le runtime à l'agent
   - Exécute la tâche de l'agent
   - Renvoie un état final une fois terminé

La fonction `run_controller()` est le cœur de l'exécution d'OpenHands. Elle gère l'interaction entre l'agent, le runtime et la tâche, en gérant des éléments comme la simulation d'entrée utilisateur et le traitement des événements.


## Façon la plus simple de commencer : Explorer les benchmarks existants

Nous vous encourageons à examiner les différents benchmarks d'évaluation disponibles dans le [répertoire `evaluation/benchmarks/`](https://github.com/All-Hands-AI/OpenHands/blob/main/evaluation/benchmarks) de notre dépôt.

Pour intégrer votre propre benchmark, nous vous suggérons de commencer par celui qui ressemble le plus à vos besoins. Cette approche peut considérablement simplifier votre processus d'intégration, vous permettant de vous appuyer sur des structures existantes et de les adapter à vos exigences spécifiques.

## Comment créer un workflow d'évaluation


Pour créer un workflow d'évaluation pour votre benchmark, suivez ces étapes :

1. Importez les utilitaires OpenHands pertinents :
   ```python
    import openhands.agenthub
    from evaluation.utils.shared import (
        EvalMetadata,
        EvalOutput,
        make_metadata,
        prepare_dataset,
        reset_logger_for_multiprocessing,
        run_evaluation,
    )
    from openhands.controller.state.state import State
    from openhands.core.config import (
        AppConfig,
        SandboxConfig,
        get_llm_config_arg,
        parse_arguments,
    )
    from openhands.core.logger import openhands_logger as logger
    from openhands.core.main import create_runtime, run_controller
    from openhands.events.action import CmdRunAction
    from openhands.events.observation import CmdOutputObservation, ErrorObservation
    from openhands.runtime.runtime import Runtime
   ```

2. Créez une configuration :
   ```python
   def get_config(instance: pd.Series, metadata: EvalMetadata) -> AppConfig:
       config = AppConfig(
           default_agent=metadata.agent_class,
           runtime='docker',
           max_iterations=metadata.max_iterations,
           sandbox=SandboxConfig(
               base_container_image='your_container_image',
               enable_auto_lint=True,
               timeout=300,
           ),
       )
       config.set_llm_config(metadata.llm_config)
       return config
   ```

3. Initialisez le runtime et configurez l'environnement d'évaluation :
   ```python
   def initialize_runtime(runtime: Runtime, instance: pd.Series):
       # Configurez votre environnement d'évaluation ici
       # Par exemple, définir des variables d'environnement, préparer des fichiers, etc.
       pass
   ```

4. Créez une fonction pour traiter chaque instance :
   ```python
   from openhands.utils.async_utils import call_async_from_sync
   def process_instance(instance: pd.Series, metadata: EvalMetadata) -> EvalOutput:
       config = get_config(instance, metadata)
       runtime = create_runtime(config)
       call_async_from_sync(runtime.connect)
       initialize_runtime(runtime, instance)

       instruction = get_instruction(instance, metadata)

       state = run_controller(
           config=config,
           task_str=instruction,
           runtime=runtime,
           fake_user_response_fn=your_user_response_function,
       )

       # Évaluez les actions de l'agent
       evaluation_result = await evaluate_agent_actions(runtime, instance)

       return EvalOutput(
           instance_id=instance.instance_id,
           instruction=instruction,
           test_result=evaluation_result,
           metadata=metadata,
           history=compatibility_for_eval_history_pairs(state.history),
           metrics=state.metrics.get() if state.metrics else None,
           error=state.last_error if state and state.last_error else None,
       )
   ```

5. Exécutez l'évaluation :
   ```python
   metadata = make_metadata(llm_config, dataset_name, agent_class, max_iterations, eval_note, eval_output_dir)
   output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')
   instances = prepare_dataset(your_dataset, output_file, eval_n_limit)

   await run_evaluation(
       instances,
       metadata,
       output_file,
       num_workers,
       process_instance
   )
   ```

Ce workflow configure la configuration, initialise l'environnement d'exécution, traite chaque instance en exécutant l'agent et en évaluant ses actions, puis collecte les résultats dans un objet `EvalOutput`. La fonction `run_evaluation` gère la parallélisation et le suivi de la progression.

N'oubliez pas de personnaliser les fonctions `get_instruction`, `your_user_response_function` et `evaluate_agent_actions` selon les exigences spécifiques de votre benchmark.

En suivant cette structure, vous pouvez créer un workflow d'évaluation robuste pour votre benchmark dans le framework OpenHands.


## Comprendre la fonction `user_response_fn`

La fonction `user_response_fn` est un composant crucial dans le workflow d'évaluation d'OpenHands. Elle simule l'interaction utilisateur avec l'agent, permettant des réponses automatisées pendant le processus d'évaluation. Cette fonction est particulièrement utile lorsque vous souhaitez fournir des réponses cohérentes et prédéfinies aux requêtes ou actions de l'agent.


### Workflow et interaction

Le workflow correct pour gérer les actions et la fonction `user_response_fn` est le suivant :

1. L'agent reçoit une tâche et commence à la traiter
2. L'agent émet une Action
3. Si l'Action est exécutable (par exemple, CmdRunAction, IPythonRunCellAction) :
   - Le Runtime traite l'Action
   - Le Runtime renvoie une Observation
4. Si l'Action n'est pas exécutable (généralement une MessageAction) :
   - La fonction `user_response_fn` est appelée
   - Elle renvoie une réponse utilisateur simulée
5. L'agent reçoit soit l'Observation, soit la réponse simulée
6. Les étapes 2 à 5 se répètent jusqu'à ce que la tâche soit terminée ou que le nombre maximum d'itérations soit atteint

Voici une représentation visuelle plus précise :

```
                 [Agent]
                    |
                    v
               [Émet Action]
                    |
                    v
            [L'Action est-elle exécutable ?]
           /                       \
         Oui                        Non
          |                          |
          v                          v
     [Runtime]               [user_response_fn]
          |                          |
          v                          v
  [Renvoie Observation]    [Réponse simulée]
           \                        /
            \                      /
             v                    v
           [L'agent reçoit le feedback]
                    |
                    v
         [Continue ou termine la tâche]
```

Dans ce workflow :

- Les actions exécutables (comme l'exécution de commandes ou de code) sont gérées directement par le Runtime
- Les actions non exécutables (généralement lorsque l'agent veut communiquer ou demander des clarifications) sont gérées par la fonction `user_response_fn`
- L'agent traite ensuite le feedback, qu'il s'agisse d'une Observation du Runtime ou d'une réponse simulée de la fonction `user_response_fn`

Cette approche permet une gestion automatisée des actions concrètes et des interactions utilisateur simulées, ce qui la rend adaptée aux scénarios d'évaluation où vous souhaitez tester la capacité de l'agent à accomplir des tâches avec une intervention humaine minimale.

### Exemple d'implémentation

Voici un exemple de fonction `user_response_fn` utilisée dans l'évaluation SWE-Bench :

```python
def codeact_user_response(state: State | None) -> str:
    msg = (
        'Please continue working on the task on whatever approach you think is suitable.\n'
        'If you think you have solved the task, please first send your answer to user through message and then <execute_bash> exit </execute_bash>.\n'
        'IMPORTANT: YOU SHOULD NEVER ASK FOR HUMAN HELP.\n'
    )

    if state and state.history:
        # check if the agent has tried to talk to the user 3 times, if so, let the agent know it can give up
        user_msgs = [
            event
            for event in state.history
            if isinstance(event, MessageAction) and event.source == 'user'
        ]
        if len(user_msgs) >= 2:
            # let the agent know that it can give up when it has tried 3 times
            return (
                msg
                + 'If you want to give up, run: <execute_bash> exit </execute_bash>.\n'
            )
    return msg
```

Cette fonction fait ce qui suit :

1. Fournit un message standard encourageant l'agent à continuer à travailler
2. Vérifie combien de fois l'agent a tenté de communiquer avec l'utilisateur
3. Si l'agent a fait plusieurs tentatives, elle lui fournit une option pour abandonner

En utilisant cette fonction, vous pouvez assurer un comportement cohérent à travers plusieurs séries d'évaluations et empêcher l'agent de rester bloqué en attendant une entrée humaine.

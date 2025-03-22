# Avaliação

Este guia fornece uma visão geral de como integrar seu próprio benchmark de avaliação ao framework OpenHands.

## Configurar Ambiente e Configuração do LLM

Por favor, siga as instruções [aqui](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md) para configurar seu ambiente de desenvolvimento local.
O OpenHands no modo de desenvolvimento usa `config.toml` para manter o controle da maioria das configurações.

Aqui está um exemplo de arquivo de configuração que você pode usar para definir e usar múltiplos LLMs:

```toml
[llm]
# IMPORTANTE: adicione sua chave de API aqui e defina o modelo para o que você deseja avaliar
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


## Como usar o OpenHands na linha de comando

O OpenHands pode ser executado a partir da linha de comando usando o seguinte formato:

```bash
poetry run python ./openhands/core/main.py \
        -i <max_iterations> \
        -t "<task_description>" \
        -c <agent_class> \
        -l <llm_config>
```

Por exemplo:

```bash
poetry run python ./openhands/core/main.py \
        -i 10 \
        -t "Write me a bash script that prints hello world." \
        -c CodeActAgent \
        -l llm
```

Este comando executa o OpenHands com:
- Um máximo de 10 iterações
- A descrição da tarefa especificada
- Usando o CodeActAgent
- Com a configuração do LLM definida na seção `llm` do seu arquivo `config.toml`

## Como o OpenHands funciona

O ponto de entrada principal para o OpenHands está em `openhands/core/main.py`. Aqui está um fluxo simplificado de como ele funciona:

1. Analisa os argumentos da linha de comando e carrega a configuração
2. Cria um ambiente de execução usando `create_runtime()`
3. Inicializa o agente especificado
4. Executa o controlador usando `run_controller()`, que:
   - Anexa o ambiente de execução ao agente
   - Executa a tarefa do agente
   - Retorna um estado final quando concluído

A função `run_controller()` é o núcleo da execução do OpenHands. Ela gerencia a interação entre o agente, o ambiente de execução e a tarefa, lidando com coisas como simulação de entrada do usuário e processamento de eventos.


## Maneira mais fácil de começar: Explorando Benchmarks Existentes

Encorajamos você a revisar os vários benchmarks de avaliação disponíveis no [diretório `evaluation/benchmarks/`](https://github.com/All-Hands-AI/OpenHands/blob/main/evaluation/benchmarks) do nosso repositório.

Para integrar seu próprio benchmark, sugerimos começar com aquele que mais se assemelha às suas necessidades. Essa abordagem pode simplificar significativamente seu processo de integração, permitindo que você construa sobre estruturas existentes e as adapte aos seus requisitos específicos.

## Como criar um fluxo de trabalho de avaliação


Para criar um fluxo de trabalho de avaliação para o seu benchmark, siga estas etapas:

1. Importe as utilidades relevantes do OpenHands:
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

2. Crie uma configuração:
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

3. Inicialize o ambiente de execução e configure o ambiente de avaliação:
   ```python
   def initialize_runtime(runtime: Runtime, instance: pd.Series):
       # Configure seu ambiente de avaliação aqui
       # Por exemplo, definindo variáveis de ambiente, preparando arquivos, etc.
       pass
   ```

4. Crie uma função para processar cada instância:
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

       # Avalie as ações do agente
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

5. Execute a avaliação:
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

Este fluxo de trabalho configura a configuração, inicializa o ambiente de execução, processa cada instância executando o agente e avaliando suas ações e, em seguida, coleta os resultados em um objeto `EvalOutput`. A função `run_evaluation` lida com a paralelização e o rastreamento do progresso.

Lembre-se de personalizar as funções `get_instruction`, `your_user_response_function` e `evaluate_agent_actions` de acordo com os requisitos específicos do seu benchmark.

Ao seguir essa estrutura, você pode criar um fluxo de trabalho de avaliação robusto para o seu benchmark dentro do framework OpenHands.


## Entendendo a `user_response_fn`

A `user_response_fn` é um componente crucial no fluxo de trabalho de avaliação do OpenHands. Ela simula a interação do usuário com o agente, permitindo respostas automatizadas durante o processo de avaliação. Essa função é particularmente útil quando você deseja fornecer respostas consistentes e predefinidas às consultas ou ações do agente.


### Fluxo de Trabalho e Interação

O fluxo de trabalho correto para lidar com ações e a `user_response_fn` é o seguinte:

1. O agente recebe uma tarefa e começa a processar
2. O agente emite uma Ação
3. Se a Ação for executável (por exemplo, CmdRunAction, IPythonRunCellAction):
   - O Runtime processa a Ação
   - O Runtime retorna uma Observação
4. Se a Ação não for executável (normalmente uma MessageAction):
   - A `user_response_fn` é chamada
   - Ela retorna uma resposta simulada do usuário
5. O agente recebe a Observação ou a resposta simulada
6. As etapas 2-5 se repetem até que a tarefa seja concluída ou o número máximo de iterações seja atingido

Aqui está uma representação visual mais precisa:

```
                 [Agente]
                    |
                    v
               [Emitir Ação]
                    |
                    v
            [A Ação é Executável?]
           /                       \
         Sim                        Não
          |                          |
          v                          v
     [Runtime]               [user_response_fn]
          |                          |
          v                          v
  [Retornar Observação]    [Resposta Simulada]
           \                        /
            \                      /
             v                    v
           [Agente recebe feedback]
                    |
                    v
         [Continuar ou Concluir Tarefa]
```

Neste fluxo de trabalho:

- Ações executáveis (como executar comandos ou código) são tratadas diretamente pelo Runtime
- Ações não executáveis (normalmente quando o agente deseja se comunicar ou pedir esclarecimentos) são tratadas pela `user_response_fn`
- O agente então processa o feedback, seja uma Observação do Runtime ou uma resposta simulada da `user_response_fn`

Essa abordagem permite o tratamento automatizado de ações concretas e interações simuladas do usuário, tornando-a adequada para cenários de avaliação em que você deseja testar a capacidade do agente de concluir tarefas com intervenção humana mínima.

### Exemplo de Implementação

Aqui está um exemplo de uma `user_response_fn` usada na avaliação SWE-Bench:

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

Esta função faz o seguinte:

1. Fornece uma mensagem padrão encorajando o agente a continuar trabalhando
2. Verifica quantas vezes o agente tentou se comunicar com o usuário
3. Se o agente fez várias tentativas, fornece uma opção para desistir

Ao usar essa função, você pode garantir um comportamento consistente em várias execuções de avaliação e evitar que o agente fique preso esperando a entrada do usuário.

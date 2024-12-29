# 评估

本指南概述了如何将您自己的评估基准集成到 OpenHands 框架中。

## 设置环境和 LLM 配置

请按照[此处](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)的说明设置您的本地开发环境。
开发模式下的 OpenHands 使用 `config.toml` 来跟踪大多数配置。

以下是一个示例配置文件，您可以使用它来定义和使用多个 LLM：

```toml
[llm]
# 重要：在此处添加您的 API 密钥，并将模型设置为您要评估的模型
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


## 如何在命令行中使用 OpenHands

可以使用以下格式从命令行运行 OpenHands：

```bash
poetry run python ./openhands/core/main.py \
        -i <max_iterations> \
        -t "<task_description>" \
        -c <agent_class> \
        -l <llm_config>
```

例如：

```bash
poetry run python ./openhands/core/main.py \
        -i 10 \
        -t "Write me a bash script that prints hello world." \
        -c CodeActAgent \
        -l llm
```

此命令使用以下参数运行 OpenHands：
- 最大迭代次数为 10
- 指定的任务描述
- 使用 CodeActAgent
- 使用 `config.toml` 文件的 `llm` 部分中定义的 LLM 配置

## OpenHands 如何工作

OpenHands 的主要入口点在 `openhands/core/main.py` 中。以下是它的简化工作流程：

1. 解析命令行参数并加载配置
2. 使用 `create_runtime()` 创建运行时环境
3. 初始化指定的代理
4. 使用 `run_controller()` 运行控制器，它：
   - 将运行时附加到代理
   - 执行代理的任务
   - 完成后返回最终状态

`run_controller()` 函数是 OpenHands 执行的核心。它管理代理、运行时和任务之间的交互，处理用户输入模拟和事件处理等事项。


## 入门最简单的方法：探索现有基准

我们鼓励您查看我们仓库的 [`evaluation/benchmarks/` 目录](https://github.com/All-Hands-AI/OpenHands/blob/main/evaluation/benchmarks)中提供的各种评估基准。

要集成您自己的基准，我们建议从最接近您需求的基准开始。这种方法可以显著简化您的集成过程，允许您在现有结构的基础上进行构建并使其适应您的特定要求。

## 如何创建评估工作流


要为您的基准创建评估工作流，请按照以下步骤操作：

1. 导入相关的 OpenHands 实用程序：
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

2. 创建配置：
   ```python
   def get_config(instance: pd.Series, metadata: EvalMetadata) -> AppConfig:
       config = AppConfig(
           default_agent=metadata.agent_class,
           runtime='eventstream',
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

3. 初始化运行时并设置评估环境：
   ```python
   def initialize_runtime(runtime: Runtime, instance: pd.Series):
       # 在此处设置您的评估环境
       # 例如，设置环境变量、准备文件等
       pass
   ```

4. 创建一个函数来处理每个实例：
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

       # 评估代理的操作
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

5. 运行评估：
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

此工作流设置配置，初始化运行时环境，通过运行代理并评估其操作来处理每个实例，然后将结果收集到 `EvalOutput` 对象中。`run_evaluation` 函数处理并行化和进度跟踪。

请记住根据您特定的基准要求自定义 `get_instruction`、`your_user_response_function` 和 `evaluate_agent_actions` 函数。

通过遵循此结构，您可以在 OpenHands 框架内为您的基准创建强大的评估工作流。


## 理解 `user_response_fn`

`user_response_fn` 是 OpenHands 评估工作流中的关键组件。它模拟用户与代理的交互，允许在评估过程中自动响应。当您想要为代理的查询或操作提供一致的、预定义的响应时，此函数特别有用。


### 工作流和交互

处理操作和 `user_response_fn` 的正确工作流如下：

1. 代理接收任务并开始处理
2. 代理发出操作
3. 如果操作可执行（例如 CmdRunAction、IPythonRunCellAction）：
   - 运行时处理操作
   - 运行时返回观察结果
4. 如果操作不可执行（通常是 MessageAction）：
   - 调用 `user_response_fn`
   - 它返回模拟的用户响应
5. 代理接收观察结果或模拟响应
6. 重复步骤 2-5，直到任务完成或达到最大迭代次数

以下是更准确的可视化表示：

```
                 [代理]
                    |
                    v
               [发出操作]
                    |
                    v
            [操作是否可执行？]
           /                       \
         是                         否
          |                          |
          v                          v
     [运行时]                 [user_response_fn]
          |                          |
          v                          v
  [返回观察结果]           [模拟响应]
           \                        /
            \                      /
             v                    v
           [代理接收反馈]
                    |
                    v
         [继续或完成任务]
```

在此工作流中：

- 可执行的操作（如运行命令或执行代码）由运行时直接处理
- 不可执行的操作（通常是当代理想要通信或寻求澄清时）由 `user_response_fn` 处理
- 然后，代理处理反馈，无论是来自运行时的观察结果还是来自 `user_response_fn` 的模拟响应

这种方法允许自动处理具体操作和模拟用户交互，使其适用于您想要测试代理在最少人工干预的情况下完成任务的能力的评估场景。

### 示例实现

以下是 SWE-Bench 评估中使用的 `user_response_fn` 示例：

```python
def codeact_user_response(state: State | None) -> str:
    msg = (
        'Please continue working on the task on whatever approach you think is suitable.\n'
        'If you think you have solved the task, please first send your answer to user through message and then <execute_bash> exit </execute_bash>.\n'
        'IMPORTANT: YOU SHOULD NEVER ASK FOR HUMAN HELP.\n'
    )

    if state and state.history:
        # 检查代理是否已尝试与用户对话 3 次，如果是，让代理知道它可以放弃
        user_msgs = [
            event
            for event in state.history
            if isinstance(event, MessageAction) and event.source == 'user'
        ]
        if len(user_msgs) >= 2:
            # 当代理已尝试 3 次时，让它知道可以放弃
            return (
                msg
                + 'If you want to give up, run: <execute_bash> exit </execute_bash>.\n'
            )
    return msg
```

此函数执行以下操作：

1. 提供一条标准消息，鼓励代理继续工作
2. 检查代理尝试与用户通信的次数
3. 如果代理已多次尝试，它会提供放弃的选项

通过使用此函数，您可以确保在多次评估运行中保持一致的行为，并防止代理在等待人工输入时陷入困境。

# 评估

本指南概述了如何将您自己的评估基准集成到OpenHands框架中。

## 设置环境和LLM配置

请按照[此处](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)的说明设置您的本地开发环境。
OpenHands在开发模式下使用`config.toml`来跟踪大多数配置。

以下是一个示例配置文件，您可以用它来定义和使用多个LLM：

```toml
[llm]
# 重要：在此处添加您的API密钥，并将模型设置为您要评估的模型
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


## 如何在命令行中使用OpenHands

OpenHands可以使用以下格式从命令行运行：

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

此命令运行OpenHands，具有：
- 最多10次迭代
- 指定的任务描述
- 使用CodeActAgent
- 使用`config.toml`文件中`llm`部分定义的LLM配置

## OpenHands如何工作

OpenHands的主要入口点在`openhands/core/main.py`中。以下是其工作流程的简化说明：

1. 解析命令行参数并加载配置
2. 使用`create_runtime()`创建运行时环境
3. 初始化指定的代理
4. 使用`run_controller()`运行控制器，它会：
   - 将运行时附加到代理
   - 执行代理的任务
   - 完成时返回最终状态

`run_controller()`函数是OpenHands执行的核心。它管理代理、运行时和任务之间的交互，处理用户输入模拟和事件处理等内容。


## 最简单的入门方式：探索现有基准

我们鼓励您查看我们仓库中[`evaluation/benchmarks/`目录](https://github.com/All-Hands-AI/OpenHands/blob/main/evaluation/benchmarks)中可用的各种评估基准。

要集成您自己的基准，我们建议从最接近您需求的基准开始。这种方法可以显著简化您的集成过程，让您能够在现有结构的基础上构建并根据您的特定需求进行调整。

## 如何创建评估工作流程


要为您的基准创建评估工作流程，请按照以下步骤操作：

1. 导入相关的OpenHands工具：
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

3. 初始化运行时并设置评估环境：
   ```python
   def initialize_runtime(runtime: Runtime, instance: pd.Series):
       # 在此处设置您的评估环境
       # 例如，设置环境变量、准备文件等
       pass
   ```

4. 创建一个处理每个实例的函数：
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

       # 评估代理的行动
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

这个工作流程设置配置，初始化运行时环境，通过运行代理并评估其行动来处理每个实例，然后将结果收集到`EvalOutput`对象中。`run_evaluation`函数处理并行化和进度跟踪。

记得根据您的特定基准要求自定义`get_instruction`、`your_user_response_function`和`evaluate_agent_actions`函数。

通过遵循这种结构，您可以在OpenHands框架内为您的基准创建一个健壮的评估工作流程。


## 理解`user_response_fn`

`user_response_fn`是OpenHands评估工作流程中的一个关键组件。它模拟用户与代理的交互，允许在评估过程中进行自动响应。当您想要向代理的查询或行动提供一致的、预定义的响应时，这个函数特别有用。


### 工作流程和交互

处理行动和`user_response_fn`的正确工作流程如下：

1. 代理接收任务并开始处理
2. 代理发出一个Action
3. 如果Action是可执行的（例如，CmdRunAction，IPythonRunCellAction）：
   - 运行时处理该Action
   - 运行时返回一个Observation
4. 如果Action不可执行（通常是MessageAction）：
   - 调用`user_response_fn`
   - 它返回一个模拟的用户响应
5. 代理接收Observation或模拟响应
6. 步骤2-5重复，直到任务完成或达到最大迭代次数

以下是更准确的可视化表示：

```
                 [代理]
                    |
                    v
               [发出Action]
                    |
                    v
            [Action是否可执行？]
           /                       \
         是                         否
          |                          |
          v                          v
     [运行时]                 [user_response_fn]
          |                          |
          v                          v
  [返回Observation]        [模拟响应]
           \                        /
            \                      /
             v                    v
           [代理接收反馈]
                    |
                    v
         [继续或完成任务]
```

在这个工作流程中：

- 可执行的行动（如运行命令或执行代码）由运行时直接处理
- 不可执行的行动（通常是当代理想要沟通或请求澄清时）由`user_response_fn`处理
- 然后代理处理反馈，无论是来自运行时的Observation还是来自`user_response_fn`的模拟响应

这种方法允许自动处理具体行动和模拟用户交互，使其适用于评估场景，在这些场景中，您希望测试代理在最少人工干预的情况下完成任务的能力。

### 示例实现

以下是SWE-Bench评估中使用的`user_response_fn`示例：

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

这个函数执行以下操作：

1. 提供一个标准消息，鼓励代理继续工作
2. 检查代理尝试与用户通信的次数
3. 如果代理已经多次尝试，它提供一个放弃的选项

通过使用这个函数，您可以确保在多次评估运行中的一致行为，并防止代理因等待人工输入而卡住。

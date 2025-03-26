# 評価

このガイドでは、独自の評価ベンチマークをOpenHandsフレームワークに統合する方法の概要を説明します。

## 環境のセットアップとLLMの設定

ローカル開発環境のセットアップ方法については、[こちら](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)の手順に従ってください。
開発モードのOpenHandsは、ほとんどの設定を追跡するために`config.toml`を使用します。

複数のLLMを定義して使用するために使用できる設定ファイルの例を以下に示します。

```toml
[llm]
# 重要: ここにAPIキーを追加し、モデルを評価したいものに設定してください
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


## コマンドラインでOpenHandsを使用する方法

OpenHandsは、以下の形式でコマンドラインから実行できます。

```bash
poetry run python ./openhands/core/main.py \
        -i <max_iterations> \
        -t "<task_description>" \
        -c <agent_class> \
        -l <llm_config>
```

例:

```bash
poetry run python ./openhands/core/main.py \
        -i 10 \
        -t "Write me a bash script that prints hello world." \
        -c CodeActAgent \
        -l llm
```

このコマンドは、以下の設定でOpenHandsを実行します:
- 最大10回の反復
- 指定されたタスクの説明
- CodeActAgentを使用
- `config.toml`ファイルの`llm`セクションで定義されたLLM設定

## OpenHandsの動作原理

OpenHandsのメインエントリーポイントは`openhands/core/main.py`にあります。簡略化された動作の流れは次のとおりです。

1. コマンドライン引数を解析し、設定を読み込む
2. `create_runtime()`を使用して実行時環境を作成する
3. 指定されたエージェントを初期化する
4. `run_controller()`を使用してコントローラーを実行する
   - 実行時環境をエージェントにアタッチする
   - エージェントのタスクを実行する
   - 完了時に最終状態を返す

`run_controller()`関数は、OpenHandsの実行の中核です。エージェント、実行時環境、およびタスク間の相互作用を管理し、ユーザー入力シミュレーションやイベント処理などを処理します。


## 最も簡単な開始方法: 既存のベンチマークの探索

リポジトリの[`evaluation/benchmarks/`ディレクトリ](https://github.com/All-Hands-AI/OpenHands/blob/main/evaluation/benchmarks)にある様々な評価ベンチマークを確認することをお勧めします。

独自のベンチマークを統合するには、ニーズに最も近いものから始めることをお勧めします。このアプローチは、既存の構造を基にして特定の要件に適応させることで、統合プロセスを大幅に合理化できます。

## 評価ワークフローの作成方法

ベンチマークの評価ワークフローを作成するには、次の手順に従います。

1. 関連するOpenHandsユーティリティをインポートします:
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

2. 設定を作成します:
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

3. 実行時環境を初期化し、評価環境をセットアップします:
   ```python
   def initialize_runtime(runtime: Runtime, instance: pd.Series):
       # ここで評価環境をセットアップします
       # 例えば、環境変数の設定、ファイルの準備など
       pass
   ```

4. 各インスタンスを処理する関数を作成します:
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

       # エージェントのアクションを評価する
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

5. 評価を実行します:
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

このワークフローでは、設定をセットアップし、実行時環境を初期化し、エージェントを実行して各インスタンスのアクションを評価し、結果を`EvalOutput`オブジェクトに収集します。`run_evaluation`関数は、並列化と進捗状況の追跡を処理します。

`get_instruction`、`your_user_response_function`、および`evaluate_agent_actions`関数は、特定のベンチマークの要件に応じてカスタマイズすることを忘れないでください。

この構造に従うことで、OpenHandsフレームワーク内で独自のベンチマークの堅牢な評価ワークフローを作成できます。


## `user_response_fn`の理解

`user_response_fn`は、OpenHandsの評価ワークフローにおいて重要な役割を果たします。これは、評価プロセス中にエージェントとのユーザー対話をシミュレートし、自動化された応答を可能にします。この関数は、エージェントのクエリやアクションに対して一貫性のある事前定義された応答を提供したい場合に特に役立ちます。


### ワークフローと相互作用

アクションと`user_response_fn`を処理するための正しいワークフローは次のとおりです。

1. エージェントがタスクを受け取り、処理を開始する
2. エージェントがアクションを発行する
3. アクションが実行可能な場合(CmdRunAction、IPythonRunCellActionなど):
   - 実行時環境がアクションを処理する
   - 実行時環境が観測結果を返す
4. アクションが実行不可能な場合(通常はMessageAction):
   - `user_response_fn`が呼び出される
   - シミュレートされたユーザー応答を返す
5. エージェントは、観測結果またはシミュレートされた応答のいずれかを受け取る
6. ステップ2〜5が、タスクが完了するか最大反復回数に達するまで繰り返される

より正確な視覚的表現は次のとおりです。

```
                 [Agent]
                    |
                    v
               [Emit Action]
                    |
                    v
            [Is Action Executable?]
           /                       \
         Yes                        No
          |                          |
          v                          v
     [Runtime]               [user_response_fn]
          |                          |
          v                          v
  [Return Observation]    [Simulated Response]
           \                        /
            \                      /
             v                    v
           [Agent receives feedback]
                    |
                    v
         [Continue or Complete Task]
```

このワークフローでは:

- 実行可能なアクション(コマンドの実行やコードの実行など)は、実行時環境によって直接処理される
- 実行不可能なアクション(通常、エージェントがコミュニケーションを取ったり、明確化を求めたりする場合)は、`user_response_fn`によって処理される
- エージェントは、実行時環境からの観測結果または`user_response_fn`からのシミュレートされた応答のいずれかのフィードバックを処理する

このアプローチにより、具体的なアクションとシミュレートされたユーザー対話の両方を自動的に処理できるため、人的介入を最小限に抑えてエージェントのタスク完了能力をテストしたい評価シナリオに適しています。

### 実装例

SWE-Benchの評価で使用される`user_response_fn`の例を以下に示します。

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

この関数は次のことを行います。

1. エージェントに作業を続けるよう促す標準メッセージを提供する
2. エージェントがユーザーとのコミュニケーションを試みた回数をチェックする
3. エージェントが複数回試行した場合、諦めるオプションを提供する

この関数を使用することで、複数の評価実行全体で一貫した動作を確保し、エージェントが人間の入力を待って停止するのを防ぐことができます。

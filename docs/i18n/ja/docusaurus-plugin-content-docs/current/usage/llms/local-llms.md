# ローカルLLM（SGLangまたはvLLM）の使用

:::warning
ローカルLLMを使用する場合、OpenHandsの機能が制限される可能性があります。
最適な体験を得るためには、GPUを使用してローカルモデルを提供することを強く推奨します。
:::

## ニュース

- 2025/03/31: SWE-Bench Verifiedで37.1%を達成するオープンモデルOpenHands LM v0.1 32Bをリリースしました
（[ブログ](https://www.all-hands.dev/blog/introducing-openhands-lm-32b----a-strong-open-coding-agent-model)、[モデル](https://huggingface.co/all-hands/openhands-lm-32b-v0.1)）。

## Huggingfaceからモデルをダウンロード

例えば、[OpenHands LM 32B v0.1](https://huggingface.co/all-hands/openhands-lm-32b-v0.1)をダウンロードするには：

```bash
huggingface-cli download all-hands/openhands-lm-32b-v0.1 --local-dir all-hands/openhands-lm-32b-v0.1
```

## モデル提供フレームワークでOpenAI互換エンドポイントを作成

### SGLangでの提供

- [公式ドキュメント](https://docs.sglang.ai/start/install.html)に従ってSGLangをインストールします。
- OpenHands LM 32B用の起動コマンド例（少なくとも2つのGPUが必要）：

```bash
SGLANG_ALLOW_OVERWRITE_LONGER_CONTEXT_LEN=1 python3 -m sglang.launch_server \
    --model all-hands/openhands-lm-32b-v0.1 \
    --served-model-name openhands-lm-32b-v0.1 \
    --port 8000 \
    --tp 2 --dp 1 \
    --host 0.0.0.0 \
    --api-key mykey --context-length 131072
```

### vLLMでの提供

- [公式ドキュメント](https://docs.vllm.ai/en/latest/getting_started/installation.html)に従ってvLLMをインストールします。
- OpenHands LM 32B用の起動コマンド例（少なくとも2つのGPUが必要）：

```bash
vllm serve all-hands/openhands-lm-32b-v0.1 \
    --host 0.0.0.0 --port 8000 \
    --api-key mykey \
    --tensor-parallel-size 2 \
    --served-model-name openhands-lm-32b-v0.1
    --enable-prefix-caching
```

## OpenHandsの実行と設定

### OpenHandsの実行

#### Dockerを使用

[公式のdocker実行コマンド](../installation#start-the-app)を使用してOpenHandsを実行します。

#### 開発モードを使用

[Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)の指示に従ってOpenHandsをビルドします。
`make setup-config`を実行して`config.toml`が存在することを確認します。これにより設定ファイルが作成されます。`config.toml`に以下を入力します：

```
[core]
workspace_base="/path/to/your/workspace"

[llm]
model="openhands-lm-32b-v0.1"
ollama_base_url="http://localhost:8000"
```

`make run`を使用してOpenHandsを起動します。

### OpenHandsの設定

OpenHandsが実行されたら、設定を通じてOpenHands UIで以下を設定する必要があります：
1. `Advanced`オプションを有効にします。
2. 以下を設定します：
- `Custom Model`を`openai/<served-model-name>`（例：`openai/openhands-lm-32b-v0.1`）に設定
- `Base URL`を`http://host.docker.internal:8000`に設定
- `API key`をモデル提供時に設定したのと同じ文字列（例：`mykey`）に設定

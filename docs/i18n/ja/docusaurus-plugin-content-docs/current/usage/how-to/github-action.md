# OpenHands GitHub Actionの使用方法

このガイドでは、OpenHands自体のリポジトリ内および独自のプロジェクトの両方で、OpenHands GitHub Actionを使用する方法について説明します。

## OpenHands リポジトリ内でのActionの使用

リポジトリ内でOpenHands GitHub Actionを使用するには、以下の手順を実行します。

1. リポジトリ内にissueを作成します。
2. issueに`fix-me`ラベルを追加するか、`@openhands-agent`で始まるコメントをissueに残します。

アクションは自動的にトリガーされ、issueの解決を試みます。

## 新しいリポジトリへのActionのインストール

独自のリポジトリにOpenHands GitHub Actionをインストールするには、[OpenHands Resolverの README](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/resolver/README.md)に従ってください。

## 使用のヒント

### 反復的な解決

1. リポジトリ内にissueを作成します。
2. issueに`fix-me`ラベルを追加するか、`@openhands-agent`で始まるコメントを残します。
3. プルリクエストを確認して、issueを解決する試みをレビューします。
4. 一般的なコメント、レビューコメント、またはインラインスレッドコメントを通じてフィードバックをフォローアップします。
5. プルリクエストに`fix-me`ラベルを追加するか、`@openhands-agent`で始まる特定のコメントに対処します。

### ラベルとマクロ

- ラベル（`fix-me`）：OpenHandsに**全体の** issueまたはプルリクエストへの対処を要求します。
- マクロ（`@openhands-agent`）：OpenHandsにissue/プルリクエストの説明と**特定のコメント**のみを考慮するように要求します。

## 高度な設定

### カスタムリポジトリ設定の追加

[resolverのREADME](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/resolver/README.md#providing-custom-instructions)に従って、OpenHandsにカスタムの指示を提供できます。

### カスタム構成

GitHub resolverは、自動的に有効な[リポジトリシークレット](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions?tool=webui#creating-secrets-for-a-repository)または[リポジトリ変数](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/store-information-in-variables#creating-configuration-variables-for-a-repository)をチェックして、その動作をカスタマイズします。
設定可能なカスタマイズオプションは次のとおりです。

| **属性名**                        | **タイプ** | **目的**                                                                                                 | **例**                                              |
| -------------------------------- | -------- | -------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `LLM_MODEL`                      | Variable | OpenHandsで使用するLLMを設定                                                                                 | `LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"` |
| `OPENHANDS_MAX_ITER`             | Variable | エージェントの反復の最大制限を設定                                                                                   | `OPENHANDS_MAX_ITER=10`                            |
| `OPENHANDS_MACRO`                | Variable | リゾルバを呼び出すためのデフォルトマクロをカスタマイズ                                                                         | `OPENHANDS_MACRO=@resolveit`                       |
| `OPENHANDS_BASE_CONTAINER_IMAGE` | Variable | カスタムSandbox（[詳細](https://docs.all-hands.dev/modules/usage/how-to/custom-sandbox-guide)）                 | `OPENHANDS_BASE_CONTAINER_IMAGE="custom_image"`    |
| `TARGET_BRANCH`                  | Variable | `main`以外のブランチにマージ                                                                                     | `TARGET_BRANCH="dev"`                              |

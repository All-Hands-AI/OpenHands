# OpenHands GitHub Actionの使用方法

このガイドでは、自分のプロジェクトでOpenHands GitHub Actionを使用する方法について説明します。

## OpenHandsリポジトリでのActionの使用

OpenHands GitHub Actionをリポジトリで使用するには、以下の手順に従います：

1. リポジトリでイシューを作成します。
2. イシューに`fix-me`ラベルを追加するか、`@openhands-agent`で始まるコメントをイシューに残します。

アクションは自動的にトリガーされ、イシューの解決を試みます。

## 新しいリポジトリにActionをインストールする

自分のリポジトリにOpenHands GitHub Actionをインストールするには、
[OpenHands Resolverのリードミー](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/resolver/README.md)に従ってください。

## 使用上のヒント

### 反復的な解決

1. リポジトリでイシューを作成します。
2. イシューに`fix-me`ラベルを追加するか、`@openhands-agent`で始まるコメントを残します。
3. プルリクエストを確認して、イシュー解決の試みをレビューします。
4. 一般的なコメント、レビューコメント、またはインラインスレッドコメントを通じてフィードバックを行います。
5. プルリクエストに`fix-me`ラベルを追加するか、`@openhands-agent`で始めて特定のコメントに対応します。

### ラベルとマクロの違い

- ラベル（`fix-me`）：OpenHandsにイシューまたはプルリクエスト**全体**に対応するよう要求します。
- マクロ（`@openhands-agent`）：OpenHandsにイシュー/プルリクエストの説明と**特定のコメント**のみを考慮するよう要求します。

## 高度な設定

### カスタムリポジトリ設定の追加

[リゾルバーのリードミー](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/resolver/README.md#providing-custom-instructions)に従って、OpenHandsにカスタム指示を提供できます。

### カスタム構成

GitHub resolverは、動作をカスタマイズするために有効な[リポジトリシークレット](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions?tool=webui#creating-secrets-for-a-repository)または[リポジトリ変数](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/store-information-in-variables#creating-configuration-variables-for-a-repository)を自動的にチェックします。
設定できるカスタマイズオプションは以下の通りです：

| **属性名**                       | **タイプ** | **目的**                                                                                          | **例**                                             |
| -------------------------------- | ---------- | ------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `LLM_MODEL`                      | 変数       | OpenHandsで使用するLLMを設定                                                                      | `LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"` |
| `OPENHANDS_MAX_ITER`             | 変数       | エージェントの反復回数の最大制限を設定                                                            | `OPENHANDS_MAX_ITER=10`                            |
| `OPENHANDS_MACRO`                | 変数       | リゾルバーを呼び出すためのデフォルトマクロをカスタマイズ                                          | `OPENHANDS_MACRO=@resolveit`                       |
| `OPENHANDS_BASE_CONTAINER_IMAGE` | 変数       | カスタムサンドボックス（[詳細](https://docs.all-hands.dev/modules/usage/how-to/custom-sandbox-guide)） | `OPENHANDS_BASE_CONTAINER_IMAGE="custom_image"`    |
| `TARGET_BRANCH`                  | 変数       | `main`以外のブランチにマージ                                                                      | `TARGET_BRANCH="dev"`                              |

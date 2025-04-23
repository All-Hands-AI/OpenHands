# Microagentsの概要

Microagentsは、ドメイン固有の知識、リポジトリ固有のコンテキスト、タスク固有のワークフローでOpenHandsを強化する特殊なプロンプトです。専門家のガイダンスを提供し、一般的なタスクを自動化し、プロジェクト全体で一貫したプラクティスを確保するのに役立ちます。

## Microagentの種類

現在、OpenHandsは以下の種類のmicroagentsをサポートしています:

* [リポジトリMicroagents](./microagents-repo): OpenHands用のリポジトリ固有のコンテキストとガイドライン。
* [パブリックMicroagents](./microagents-public): すべてのOpenHandsユーザーのためにキーワードによってトリガーされる一般的なガイドライン。

OpenHandsがリポジトリで動作する際:

1. リポジトリに`.openhands/microagents/`が存在する場合、そこからリポジトリ固有の指示を読み込みます。
2. 会話のキーワードによってトリガーされる一般的なガイドラインを読み込みます。
現在の[パブリックMicroagents](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents/knowledge)を参照してください。

## Microagentのフォーマット

すべてのmicroagentsは、YAMLのfrontmatterを持つmarkdownファイルを使用します。これには、OpenHandsがタスクを達成するための特別な指示が含まれています:
```
---
name: <Microagentの名前>
type: <Microagentのタイプ>
version: <Microagentのバージョン>
agent: <エージェントのタイプ (通常はCodeActAgent)>
triggers:
- <オプション: microagentをトリガーするキーワード。トリガーを削除すると、常に含まれるようになります>
---

<OpenHandsが従うべき特別なガイドライン、指示、プロンプトを含むMarkdown。
ベストプラクティスに関する各microagentの具体的なドキュメントを確認してください。>
```

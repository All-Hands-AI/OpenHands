# 🧠 メインエージェントと機能

## CodeActAgent

### 説明

このエージェントはCodeActのアイデア（[論文](https://arxiv.org/abs/2402.01030)、[ツイート](https://twitter.com/xingyaow_/status/1754556835703751087)）を実装しており、LLMエージェントの**アクション**を統一された**コード**アクション空間に統合することで、_シンプルさ_と_パフォーマンス_の両方を実現します。

概念的なアイデアは以下のように示されています。各ターンで、エージェントは以下のことができます：

1. **会話**: 人間と自然言語でコミュニケーションを取り、明確化や確認などを求める
2. **CodeAct**: コードを実行してタスクを実行することを選択する

- 有効なLinux `bash` コマンドを実行する
- [インタラクティブなPythonインタプリタ](https://ipython.org/)で有効な`Python`コードを実行する。これは`bash`コマンドを通じてシミュレートされます。詳細については以下のプラグインシステムを参照してください。

![image](https://github.com/All-Hands-AI/OpenHands/assets/38853559/92b622e3-72ad-4a61-8f41-8c040b6d5fb3)

### デモ

https://github.com/All-Hands-AI/OpenHands/assets/38853559/f592a192-e86c-4f48-ad31-d69282d5f6ac

_`gpt-4-turbo-2024-04-09`を使用したCodeActAgentがデータサイエンスタスク（線形回帰）を実行する例_。

# 🧠 メインエージェントと機能

## CodeActAgent

### 説明

このエージェントは、CodeActのアイデア ([論文](https://arxiv.org/abs/2402.01030), [ツイート](https://twitter.com/xingyaow_/status/1754556835703751087)) を実装しており、LLMエージェントの**行動**を、_シンプルさ_と_パフォーマンス_の両方のために、統一された**コード**行動空間に統合します。

概念的なアイデアは以下の図に示されています。各ターンで、エージェントは以下のことができます。

1. **会話**: 明確化、確認などのために、自然言語で人間とコミュニケーションをとる。
2. **CodeAct**: コードを実行してタスクを実行することを選択する

- 任意の有効なLinux `bash`コマンドを実行する
- [対話型Pythonインタープリター](https://ipython.org/)で任意の有効な`Python`コードを実行する。これは`bash`コマンドを通してシミュレートされます。詳細はプラグインシステムを参照してください。

![image](https://github.com/All-Hands-AI/OpenHands/assets/38853559/92b622e3-72ad-4a61-8f41-8c040b6d5fb3)

### デモ

https://github.com/All-Hands-AI/OpenHands/assets/38853559/f592a192-e86c-4f48-ad31-d69282d5f6ac

_データサイエンスタスク（線形回帰）を実行する`gpt-4-turbo-2024-04-09`を使用したCodeActAgentの例_。

# リポジトリのカスタマイズ

リポジトリのルートレベルに `.openhands` ディレクトリを作成することで、OpenHandsがあなたのリポジトリとどのように連携するかをカスタマイズできます。

## マイクロエージェント

マイクロエージェントを使用すると、OpenHandsのプロンプトをプロジェクト固有の情報で拡張し、OpenHandsがどのように機能するかを定義できます。詳細については[マイクロエージェントの概要](../prompting/microagents-overview)をご覧ください。


## セットアップスクリプト
`.openhands/setup.sh` ファイルを追加すると、OpenHandsがあなたのリポジトリで作業を開始するたびに実行されます。
これは依存関係のインストール、環境変数の設定、その他のセットアップタスクを実行するための理想的な場所です。

例えば：
```bash
#!/bin/bash
export MY_ENV_VAR="my value"
sudo apt-get update
sudo apt-get install -y lsof
cd frontend && npm install ; cd ..
```

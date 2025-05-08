# Cloud GitHub Resolver

GitHub Resolverはコードの修正を自動化し、リポジトリに対してインテリジェントな支援を提供します。

## セットアップ

Cloud GitHub Resolverは、[OpenHands Cloudにリポジトリアクセス権を付与する](./openhands-cloud#adding-repository-access)と自動的に利用可能になります。

## 使用方法

OpenHands Cloudにリポジトリアクセス権を付与した後、リポジトリの課題（Issue）とプルリクエストでCloud GitHub Resolverを使用できます。

### 課題（Issues）

リポジトリで課題に`openhands`ラベルを付けると、OpenHandsは以下の操作を行います：
1. 課題にコメントして、作業中であることを通知します。
    - OpenHands Cloudで進捗状況を追跡するためのリンクをクリックできます。
2. 課題が正常に解決されたと判断した場合、プルリクエストを開きます。
3. 実行されたタスクの概要とプルリクエストへのリンクを含むコメントを課題に投稿します。


### プルリクエスト

プルリクエストでOpenHandsを利用するには、トップレベルまたはインラインコメントで`@openhands`を使用して：
     - 質問する
     - 更新をリクエストする
     - コードの説明を取得する

OpenHandsは以下の操作を行います：
1. PRにコメントして、作業中であることを通知します。
2. タスクを実行します。

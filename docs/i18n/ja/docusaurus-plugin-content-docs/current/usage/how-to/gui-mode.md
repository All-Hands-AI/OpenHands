# GUIモード

OpenHandsは、AI アシスタントとやり取りするためのグラフィカルユーザーインターフェース（GUI）モードを提供しています。

## インストールとセットアップ

1. インストール手順に従って、OpenHandsをインストールします。
2. コマンドを実行した後、[http://localhost:3000](http://localhost:3000)でOpenHandsにアクセスします。

## GUIでのやり取り

### 初期設定

1. 初回起動時に、設定ページが表示されます。
2. ドロップダウンメニューから`LLM Provider`と`LLM Model`を選択します。必要なモデルがリストにない場合は、`Advanced`オプションを切り替えて、正しいプレフィックスを付けて`Custom Model`テキストボックスに入力します。
3. 選択したプロバイダーに対応する`API Key`を入力します。
4. `Save Changes`をクリックして設定を適用します。

### バージョン管理トークン

OpenHandsは複数のバージョン管理プロバイダーをサポートしています。複数のプロバイダーのトークンを同時に設定できます。

#### GitHubトークンの設定

OpenHandsは、利用可能な場合、自動的に`GITHUB_TOKEN`をシェル環境にエクスポートします。これは2つの方法で行われます。

**ローカルインストール**: ユーザーが直接GitHubトークンを入力します。
<details>
  <summary>GitHubトークンの設定</summary>

  1. **Personal Access Token（PAT）の生成**:
   - GitHubで、Settings > Developer Settings > Personal Access Tokens > Tokens (classic)に移動します。
   - **New token (classic)**
     - 必要なスコープ:
     - `repo`（プライベートリポジトリの完全な制御）
   - **Fine-Grained Tokens**
     - All Repositories（特定のリポジトリを選択できますが、これはリポジトリ検索の結果に影響します）
     - Minimal Permissions（検索用に**Meta Data = Read-only**を選択し、ブランチ作成用に**Pull Requests = Read and Write**、**Content = Read and Write**を選択します）
  2. **OpenHandsにトークンを入力**:
   - 設定ボタン（歯車アイコン）をクリックします。
   - `Git Provider Settings`セクションに移動します。
   - `GitHub Token`フィールドにトークンを貼り付けます。
   - `Save Changes`をクリックして変更を適用します。
</details>

<details>
  <summary>組織のトークンポリシー</summary>

  組織のリポジトリを使用する場合は、追加の設定が必要になる場合があります。

  1. **組織の要件を確認**:
   - 組織の管理者は、特定のトークンポリシーを適用することがあります。
   - 一部の組織では、SSOを有効にしてトークンを作成する必要があります。
   - 組織の[トークンポリシー設定](https://docs.github.com/en/organizations/managing-programmatic-access-to-your-organization/setting-a-personal-access-token-policy-for-your-organization)を確認してください。
  2. **組織へのアクセスを確認**:
   - GitHubのトークン設定に移動します。
   - `Organization access`の下で組織を探します。
   - 必要に応じて、組織の横にある`Enable SSO`をクリックします。
   - SSOの認証プロセスを完了します。
</details>

<details>
  <summary>トラブルシューティング</summary>

  一般的な問題と解決策:

  - **トークンが認識されない**:
     - トークンが設定に正しく保存されていることを確認します。
     - トークンの有効期限が切れていないことを確認します。
     - トークンに必要なスコープがあることを確認します。
     - トークンを再生成してみてください。

  - **組織へのアクセスが拒否された**:
     - SSOが必要だが有効になっていないかどうかを確認します。
     - 組織のメンバーシップを確認します。
     - トークンポリシーがアクセスをブロックしている場合は、組織の管理者に連絡してください。

  - **トークンが機能することを確認**:
     - トークンが有効な場合、アプリにグリーンのチェックマークが表示されます。
     - リポジトリにアクセスして、権限を確認してみてください。
     - ブラウザのコンソールでエラーメッセージを確認してください。
</details>

**OpenHands Cloud**: トークンはGitHub OAuth認証を通じて取得されます。

<details>
  <summary>OAuth認証</summary>

  OpenHands Cloudを使用する場合、GitHub OAuthフローは以下の権限を要求します:
   - リポジトリアクセス（読み取り/書き込み）
   - ワークフロー管理
   - 組織の読み取りアクセス

  OpenHandsを認証するには:
   - プロンプトが表示されたら、`Sign in with GitHub`をクリックします。
   - 要求された権限を確認します。
   - OpenHandsがGitHubアカウントにアクセスすることを承認します。
   - 組織を使用している場合は、プロンプトが表示されたら組織へのアクセスを承認します。
</details>

#### GitLabトークンの設定

OpenHandsは、利用可能な場合、ローカルインストールのみ、自動的に`GITLAB_TOKEN`をシェル環境にエクスポートします。

<details>
  <summary>GitLabトークンの設定</summary>

  1. **Personal Access Token（PAT）の生成**:
   - GitLabで、User Settings > Access Tokensに移動します。
   - 以下のスコープを持つ新しいトークンを作成します:
     - `api`（APIアクセス）
     - `read_user`（ユーザー情報の読み取り）
     - `read_repository`（リポジトリ読み取り）
     - `write_repository`（リポジトリ書き込み）
   - 有効期限を設定するか、無期限トークンの場合は空白のままにします。
  2. **OpenHandsにトークンを入力**:
   - 設定ボタン（歯車アイコン）をクリックします。
   - `Git Provider Settings`セクションに移動します。
   - `GitLab Token`フィールドにトークンを貼り付けます。
   - セルフホスト型GitLabを使用している場合は、GitLabインスタンスのURLを入力します。
   - `Save Changes`をクリックして変更を適用します。
</details>

<details>
  <summary>トラブルシューティング</summary>

  一般的な問題と解決策:

  - **トークンが認識されない**:
     - トークンが設定に正しく保存されていることを確認します。
     - トークンの有効期限が切れていないことを確認します。
     - トークンに必要なスコープがあることを確認します。
     - セルフホスト型インスタンスの場合は、正しいインスタンスURLを確認します。

  - **アクセスが拒否された**:
     - プロジェクトのアクセス権限を確認します。
     - トークンに必要なスコープがあるかどうかを確認します。
     - グループ/組織のリポジトリの場合は、適切なアクセス権があることを確認します。
</details>

### 高度な設定

1. 設定ページ内で、`Advanced`オプションを切り替えて追加の設定にアクセスします。
2. `Custom Model`テキストボックスを使用して、リストにないモデルを手動で入力します。
3. LLMプロバイダーで必要な場合は、`Base URL`を指定します。

### AIとのやり取り

1. 入力ボックスにプロンプトを入力します。
2. 送信ボタンをクリックするか、Enterキーを押してメッセージを送信します。
3. AIは入力を処理し、チャットウィンドウに応答を提供します。
4. フォローアップの質問をしたり、追加情報を提供したりして、会話を続けることができます。

## 効果的な使用のためのヒント

- [プロンプトのベストプラクティス](../prompting/prompting-best-practices)で説明されているように、要求を具体的にすることで、最も正確で役立つ応答を得ることができます。
- ワークスペースパネルを使用して、プロジェクト構造を探索します。
- [LLMsセクション](usage/llms/llms.md)で説明されているように、推奨モデルの1つを使用します。

OpenHandsのGUIモードは、AIアシスタントとのやり取りをできるだけスムーズで直感的にすることを目的としています。生産性を最大限に高めるために、ぜひその機能を探ってみてください。

# GUI 模式

OpenHands 提供了一个图形用户界面(GUI)模式，用于与 AI 助手交互。

## 安装和设置

1. 按照安装说明安装 OpenHands。
2. 运行命令后，通过 [http://localhost:3000](http://localhost:3000) 访问 OpenHands。

## 与 GUI 交互

### 初始设置

1. 首次启动时，您将看到一个设置弹窗。
2. 从下拉菜单中选择 `LLM Provider` 和 `LLM Model`。如果所需模型不在列表中，
   选择 `see advanced settings`。然后切换 `Advanced` 选项，并在
   `Custom Model` 文本框中输入正确前缀的模型名称。
3. 输入您所选提供商对应的 `API Key`。
4. 点击 `Save Changes` 应用设置。

### 版本控制令牌

OpenHands 支持多个版本控制提供商。您可以同时配置多个提供商的令牌。

#### GitHub 令牌设置

如果提供了 GitHub 令牌，OpenHands 会自动将 `GITHUB_TOKEN` 导出到 shell 环境：

<details>
  <summary>设置 GitHub 令牌</summary>

  1. **生成个人访问令牌 (PAT)**：
   - 在 GitHub 上，前往 Settings > Developer Settings > Personal Access Tokens > Tokens (classic)。
   - **New token (classic)**
     - 所需权限范围：
     - `repo` (对私有仓库的完全控制)
   - **Fine-Grained Tokens**
     - 所有仓库（您可以选择特定仓库，但这会影响仓库搜索返回的结果）
     - 最小权限（选择 `Meta Data = Read-only` 用于搜索，`Pull Requests = Read and Write` 和 `Content = Read and Write` 用于分支创建）
  2. **在 OpenHands 中输入令牌**：
   - 点击设置按钮（齿轮图标）。
   - 在 `GitHub Token` 字段中粘贴您的令牌。
   - 点击 `Save` 应用更改。
</details>

<details>
  <summary>组织令牌策略</summary>

  如果您使用组织仓库，可能需要额外设置：

  1. **检查组织要求**：
   - 组织管理员可能强制执行特定的令牌策略。
   - 某些组织要求创建启用了 SSO 的令牌。
   - 查看您组织的[令牌策略设置](https://docs.github.com/en/organizations/managing-programmatic-access-to-your-organization/setting-a-personal-access-token-policy-for-your-organization)。
  2. **验证组织访问权限**：
   - 前往 GitHub 上的令牌设置。
   - 在 `Organization access` 下查找您的组织。
   - 如果需要，点击组织旁边的 `Enable SSO`。
   - 完成 SSO 授权流程。
</details>

<details>
  <summary>故障排除</summary>

  常见问题和解决方案：

  - **令牌未被识别**：
     - 确保令牌已正确保存在设置中。
     - 检查令牌是否已过期。
     - 验证令牌是否具有所需的权限范围。
     - 尝试重新生成令牌。

  - **组织访问被拒绝**：
     - 检查是否需要 SSO 但未启用。
     - 验证组织成员资格。
     - 如果令牌策略阻止访问，请联系组织管理员。

  - **验证令牌是否有效**：
     - 如果令牌有效，应用程序将显示绿色对勾。
     - 尝试访问仓库以确认权限。
     - 检查浏览器控制台是否有错误消息。
</details>

#### GitLab 令牌设置

如果提供了 GitLab 令牌，OpenHands 会自动将 `GITLAB_TOKEN` 导出到 shell 环境：

<details>
  <summary>设置 GitLab 令牌</summary>

  1. **生成个人访问令牌 (PAT)**：
   - 在 GitLab 上，前往 User Settings > Access Tokens。
   - 创建一个具有以下权限范围的新令牌：
     - `api` (API 访问)
     - `read_user` (读取用户信息)
     - `read_repository` (读取仓库)
     - `write_repository` (写入仓库)
   - 设置过期日期，或留空以创建永不过期的令牌。
  2. **在 OpenHands 中输入令牌**：
   - 点击设置按钮（齿轮图标）。
   - 在 `GitLab Token` 字段中粘贴您的令牌。
   - 如果使用自托管 GitLab，请输入您的 GitLab 实例 URL。
   - 点击 `Save` 应用更改。
</details>

<details>
  <summary>故障排除</summary>

  常见问题和解决方案：

  - **令牌未被识别**：
     - 确保令牌已正确保存在设置中。
     - 检查令牌是否已过期。
     - 验证令牌是否具有所需的权限范围。
     - 对于自托管实例，验证实例 URL 是否正确。

  - **访问被拒绝**：
     - 验证项目访问权限。
     - 检查令牌是否具有必要的权限范围。
     - 对于群组/组织仓库，确保您拥有适当的访问权限。
</details>

### 高级设置

1. 在设置页面内，切换 `Advanced` 选项以访问其他设置。
2. 如果模型不在列表中，使用 `Custom Model` 文本框手动输入模型。
3. 如果您的 LLM 提供商需要，请指定 `Base URL`。

### 与 AI 交互

1. 在输入框中输入您的提示。
2. 点击发送按钮或按 Enter 键提交您的消息。
3. AI 将处理您的输入并在聊天窗口中提供响应。
4. 您可以通过提出后续问题或提供额外信息来继续对话。

## 有效使用的技巧

- 在请求中具体明确，以获得最准确和最有帮助的回应，如[提示最佳实践](../prompting/prompting-best-practices)中所述。
- 使用[LLMs 部分](usage/llms/llms.md)中描述的推荐模型之一。

请记住，OpenHands 的 GUI 模式旨在使您与 AI 助手的交互尽可能顺畅和直观。请随时探索其功能，以最大限度地提高您的生产力。

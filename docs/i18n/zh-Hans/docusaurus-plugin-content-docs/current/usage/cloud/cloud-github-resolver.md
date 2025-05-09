# Cloud GitHub Resolver

GitHub Resolver 自动修复代码并为您的仓库提供智能辅助。

## 设置

当您[授予 OpenHands Cloud 仓库访问权限](./openhands-cloud#adding-repository-access)后，Cloud GitHub Resolver 会自动可用。

## 使用方法

授予 OpenHands Cloud 仓库访问权限后，您可以在仓库的 issues 和 pull requests 中使用 Cloud GitHub Resolver。

### Issues

在您的仓库中，给 issue 添加 `openhands` 标签。OpenHands 将会：
1. 在 issue 上发表评论，让您知道它正在处理该问题。
    - 您可以点击链接在 OpenHands Cloud 上跟踪进度。
2. 如果确定问题已成功解决，则会打开一个 pull request。
3. 在 issue 上发表评论，总结已执行的任务并提供 pull request 的链接。


### Pull Requests

要让 OpenHands 处理 pull requests，请在顶级或内联评论中使用 `@openhands` 来：
     - 提问
     - 请求更新
     - 获取代码解释

OpenHands 将会：
1. 在 PR 上发表评论，让您知道它正在处理该请求。
2. 执行任务。

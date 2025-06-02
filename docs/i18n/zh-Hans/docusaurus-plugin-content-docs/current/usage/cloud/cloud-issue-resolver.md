# 云问题解决器

云问题解决器可以自动修复代码并为您的GitHub和GitLab仓库提供智能辅助。

## 设置

当您授予OpenHands Cloud仓库访问权限时，云问题解决器会自动可用：
- [GitHub仓库访问](./github-installation#adding-repository-access)
- [GitLab仓库访问](./gitlab-installation#adding-repository-access)

![向OpenHands添加仓库访问权限](/img/cloud/add-repo.png)

## 使用方法

授予OpenHands Cloud仓库访问权限后，您可以在仓库的问题和拉取/合并请求中使用云问题解决器。

### 处理问题

在您的仓库中，给问题添加`openhands`标签或添加以`@openhands`开头的消息。OpenHands将会：
1. 在问题上发表评论，让您知道它正在处理
   - 您可以点击链接在OpenHands Cloud上跟踪进度
2. 如果确定问题已成功解决，则打开拉取请求（GitHub）或合并请求（GitLab）
3. 在问题上发表评论，总结已执行的任务并提供PR/MR的链接

![OpenHands问题解决器运行中](/img/cloud/issue-resolver.png)

#### 问题命令示例

以下是您可以在问题解决器中使用的命令示例：

```
@openhands 阅读问题描述并修复它
```

### 处理拉取/合并请求

要让OpenHands处理拉取请求（GitHub）或合并请求（GitLab），在评论中提及`@openhands`以：
- 提问
- 请求更新
- 获取代码解释

OpenHands将会：
1. 发表评论让您知道它正在处理
2. 执行请求的任务

#### 拉取/合并请求命令示例

以下是您可以在拉取/合并请求中使用的命令示例：

```
@openhands 反映审查评论
```

```
@openhands 修复合并冲突并确保CI通过
```

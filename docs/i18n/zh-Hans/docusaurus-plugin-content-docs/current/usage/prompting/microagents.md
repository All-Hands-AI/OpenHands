# 微代理

OpenHands 使用专门的微代理来高效处理特定任务和上下文。这些微代理是小型、专注的组件，为特定场景提供专门的行为和知识。

## 概述

微代理在 `openhands/agenthub/codeact_agent/micro/` 目录下的 Markdown 文件中定义。每个微代理都配置有：

- 唯一的名称
- 代理类型（通常是 CodeActAgent）
- 触发代理的关键词
- 具体的指令和功能

## 可用的微代理

### GitHub 代理
**文件**：`github.md`
**触发词**：`github`、`git`

GitHub 代理专门用于 GitHub API 交互和仓库管理。它：
- 可以访问用于 API 身份验证的 `GITHUB_TOKEN`
- 遵循严格的仓库交互准则
- 处理分支管理和拉取请求
- 使用 GitHub API 而不是网页浏览器交互

主要特点：
- 分支保护（防止直接推送到 main/master）
- 自动创建 PR
- Git 配置管理
- 以 API 为先的 GitHub 操作方式

### NPM 代理
**文件**：`npm.md`
**触发词**：`npm`

专门处理 npm 包管理，特别关注：
- 非交互式 shell 操作
- 使用 Unix 'yes' 命令自动处理确认
- 包安装自动化

### 自定义微代理

你可以通过在微代理目录中添加新的 Markdown 文件来创建自己的微代理。每个文件应遵循以下结构：

```markdown
---
name: agent_name
agent: CodeActAgent
triggers:
- trigger_word1
- trigger_word2
---

微代理的指令和功能...
```

## 最佳实践

使用微代理时：

1. **使用适当的触发词**：确保你的命令包含相关的触发词以激活正确的微代理
2. **遵循代理准则**：每个代理都有特定的指令和限制 - 遵守这些准则以获得最佳结果
3. **API 优先方法**：如果可用，使用 API 端点而不是网页界面
4. **自动化友好**：设计适合非交互式环境的命令

## 集成

微代理自动集成到 OpenHands 的工作流程中。它们：
- 监视传入的命令是否包含触发词
- 在检测到相关触发词时激活
- 应用其专门的知识和能力
- 遵循其特定的准则和限制

## 使用示例

```bash
# GitHub 代理示例
git checkout -b feature-branch
git commit -m "Add new feature"
git push origin feature-branch

# NPM 代理示例
yes | npm install package-name
```

有关特定代理的更多信息，请参阅微代理目录中的各个文档文件。

## 贡献微代理

要为 OpenHands 贡献新的微代理，请遵循以下准则：

### 1. 规划你的微代理

在创建微代理之前，请考虑：
- 它将解决什么具体问题或用例？
- 它应该具有什么独特的能力或知识？
- 什么触发词适合激活它？
- 它应该遵循什么约束或准则？

### 2. 文件结构

在 `openhands/agenthub/codeact_agent/micro/` 中创建一个新的 Markdown 文件，文件名要有描述性（例如，`docker.md` 用于专注于 Docker 的代理）。

### 3. 必需组件

你的微代理文件必须包括：

1. **Front Matter**：文件开头的 YAML 元数据：
```markdown
---
name: your_agent_name
agent: CodeActAgent
triggers:
- trigger_word1
- trigger_word2
---
```

2. **指令**：明确、具体的代理行为准则：
```markdown
你负责 [特定任务/领域]。

主要职责：
1. [职责 1]
2. [职责 2]

准则：
- [准则 1]
- [准则 2]

使用示例：
[示例 1]
[示例 2]
```

### 4. 微代理开发的最佳实践

1. **明确范围**：让代理专注于特定领域或任务
2. **明确指令**：提供清晰、明确的指引
3. **有用的示例**：包括常见用例的实际示例
4. **安全第一**：包括必要的警告和约束
5. **集成意识**：考虑代理如何与其他组件交互

### 5. 测试你的微代理

在提交之前：
1. 用各种提示测试代理
2. 验证触发词是否正确激活代理
3. 确保指令清晰全面
4. 检查与现有代理的潜在冲突

### 6. 示例实现

这是一个新微代理的模板：

```markdown
---
name: docker
agent: CodeActAgent
triggers:
- docker
- container
---

你负责 Docker 容器管理和 Dockerfile 创建。

主要职责：
1. 创建和修改 Dockerfile
2. 管理容器生命周期
3. 处理 Docker Compose 配置

准则：
- 尽可能使用官方基础镜像
- 包括必要的安全考虑
- 遵循 Docker 最佳实践进行层优化

示例：
1. 创建 Dockerfile：
   ```dockerfile
   FROM node:18-alpine
   WORKDIR /app
   COPY package*.json ./
   RUN npm install
   COPY . .
   CMD ["npm", "start"]
   ```

2. Docker Compose 用法：
   ```yaml
   version: '3'
   services:
     web:
       build: .
       ports:
         - "3000:3000"
   ```

记住要：
- 验证 Dockerfile 语法
- 检查安全漏洞
- 优化构建时间和镜像大小
```

### 7. 提交流程

1. 在正确的目录中创建你的微代理文件
2. 全面测试
3. 提交包含以下内容的拉取请求：
   - 新的微代理文件
   - 更新文档（如果需要）
   - 代理的目的和功能说明

请记住，微代理是在特定领域扩展 OpenHands 功能的强大方式。设计良好的代理可以显著提高系统处理专门任务的能力。

# 自定义代理行为

OpenHands 可以通过提供特定仓库的上下文和指南来进行自定义,以更有效地处理特定仓库。本节将解释如何为你的项目优化 OpenHands。

## 仓库配置

你可以通过在仓库根目录下创建 `.openhands` 目录来自定义 OpenHands 在你的仓库中的行为。至少,它应该包含文件 `.openhands/microagents/repo.md`,其中包括每次代理处理此仓库时都会提供给代理的指令。

我们建议包括以下信息:
1. **仓库概述**:简要描述你的项目的目的和架构
2. **目录结构**:关键目录及其用途
3. **开发指南**:项目特定的编码标准和实践
4. **测试要求**:如何运行测试以及需要哪些类型的测试
5. **设置说明**:构建和运行项目所需的步骤

### 仓库配置示例
`.openhands/microagents/repo.md` 文件示例:
```
Repository: MyProject
Description: A web application for task management

Directory Structure:
- src/: Main application code
- tests/: Test files
- docs/: Documentation

Setup:
- Run `npm install` to install dependencies
- Use `npm run dev` for development
- Run `npm test` for testing

Guidelines:
- Follow ESLint configuration
- Write tests for all new features
- Use TypeScript for new code
```

### 自定义提示

在处理自定义仓库时:

1. **参考项目标准**:提及你的项目中使用的特定编码标准或模式
2. **包括上下文**:参考相关文档或现有实现
3. **指定测试要求**:在提示中包括项目特定的测试要求

自定义提示示例:
```
Add a new task completion feature to src/components/TaskList.tsx following our existing component patterns.
Include unit tests in tests/components/ and update the documentation in docs/features/.
The component should use our shared styling from src/styles/components.
```

### 仓库自定义的最佳实践

1. **保持说明更新**:随着项目的发展,定期更新你的 `.openhands` 目录
2. **要具体**:包括特定于你的项目的具体路径、模式和要求
3. **记录依赖项**:列出开发所需的所有工具和依赖项
4. **包括示例**:提供项目中良好代码模式的示例
5. **指定约定**:记录命名约定、文件组织和代码风格偏好

通过为你的仓库自定义 OpenHands,你将获得更准确、更一致的结果,这些结果符合你的项目标准和要求。

## 其他微代理
你可以在 `.openhands/microagents/` 目录中创建其他指令,如果找到特定关键字,如 `test`、`frontend` 或 `migration`,这些指令将发送给代理。有关更多信息,请参阅 [Microagents](microagents.md)。

# 在 OpenHands 仓库中使用 GitHub Action

本指南解释了如何在 OpenHands 仓库内以及你自己的项目中使用 OpenHands GitHub Action。

## 在 OpenHands 仓库中使用 Action

要在仓库中使用 OpenHands GitHub Action，你可以：

1. 在仓库中创建一个 issue。
2. 为 issue 添加 `fix-me` 标签，或在 issue 中留下以 `@openhands-agent` 开头的评论。

该 action 将自动触发并尝试解决该 issue。

## 在新仓库中安装 Action

要在你自己的仓库中安装 OpenHands GitHub Action，请按照 [OpenHands Resolver 的 README](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/resolver/README.md) 进行操作。

## 使用技巧

### 迭代解决

1. 在仓库中创建一个 issue。
2. 为 issue 添加 `fix-me` 标签，或留下以 `@openhands-agent` 开头的评论。
3. 通过检查 pull request 来审查解决 issue 的尝试。
4. 通过一般评论、审查评论或内联线程评论提供反馈。
5. 为 pull request 添加 `fix-me` 标签，或通过以 `@openhands-agent` 开头来解决特定的评论。

### 标签与宏

- 标签（`fix-me`）：请求 OpenHands 解决**整个** issue 或 pull request。
- 宏（`@openhands-agent`）：请求 OpenHands 仅考虑 issue/pull request 描述和**特定评论**。

## 高级设置

### 添加自定义仓库设置

你可以按照 [resolver 的 README](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/resolver/README.md#providing-custom-instructions) 为 OpenHands 提供自定义指令。

### 自定义配置

Github resolver 将自动检查有效的 [仓库机密](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions?tool=webui#creating-secrets-for-a-repository) 或 [仓库变量](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/store-information-in-variables#creating-configuration-variables-for-a-repository) 以自定义其行为。
你可以设置的自定义选项有：

| **属性名称**                      | **类型** | **用途**                                                                                    | **示例**                                             |
|----------------------------------| -------- |-------------------------------------------------------------------------------------------|------------------------------------------------------|
| `LLM_MODEL`                      | Variable | 设置与 OpenHands 一起使用的 LLM                                                                | `LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"`   |
| `OPENHANDS_MAX_ITER`             | Variable | 设置代理迭代的最大限制                                                                             | `OPENHANDS_MAX_ITER=10`                              |
| `OPENHANDS_MACRO`                | Variable | 自定义用于调用 resolver 的默认宏                                                                   | `OPENHANDS_MACRO=@resolveit`                         |
| `OPENHANDS_BASE_CONTAINER_IMAGE` | Variable | 自定义沙箱 ([了解更多](https://docs.all-hands.dev/modules/usage/how-to/custom-sandbox-guide))   | `OPENHANDS_BASE_CONTAINER_IMAGE="custom_image"`      |

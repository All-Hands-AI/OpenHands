---
sidebar_position: 9
---

# 开发概述

本指南提供了 OpenHands 仓库中可用的关键文档资源概述。无论您是想要贡献代码、了解架构还是处理特定组件，这些资源都将帮助您有效地浏览代码库。

## 核心文档

### 项目基础
- **主项目概述** (`/README.md`)
  了解 OpenHands 的主要入口点，包括功能和基本设置说明。

- **开发指南** (`/Development.md`)
  为 OpenHands 开发人员提供的综合指南，包括设置、要求和开发工作流程。

- **贡献指南** (`/CONTRIBUTING.md`)
  为贡献者提供的基本信息，涵盖代码风格、PR 流程和贡献工作流程。

### 组件文档

#### 前端
- **前端应用程序** (`/frontend/README.md`)
  设置和开发基于 React 的前端应用程序的完整指南。

#### 后端
- **后端实现** (`/openhands/README.md`)
  Python 后端实现和架构的详细文档。

- **服务器文档** (`/openhands/server/README.md`)
  服务器实现细节、API 文档和服务架构。

- **运行时环境** (`/openhands/runtime/README.md`)
  涵盖运行时环境、执行模型和运行时配置的文档。

#### 基础设施
- **容器文档** (`/containers/README.md`)
  关于 Docker 容器、部署策略和容器管理的综合信息。

### 测试和评估
- **单元测试指南** (`/tests/unit/README.md`)
  编写、运行和维护单元测试的说明。

- **评估框架** (`/evaluation/README.md`)
  评估框架、基准测试和性能测试的文档。

### 高级功能
- **微代理架构** (`/microagents/README.md`)
  关于微代理架构、实现和使用的详细信息。

### 文档标准
- **文档风格指南** (`/docs/DOC_STYLE_GUIDE.md`)
  编写和维护项目文档的标准和指南。

## 开发入门

如果您是 OpenHands 开发的新手，我们建议按照以下顺序进行：

1. 从主 `README.md` 开始，了解项目的目的和功能
2. 如果您计划贡献，请查看 `CONTRIBUTING.md` 指南
3. 按照 `Development.md` 中的设置说明进行操作
4. 根据您的兴趣领域深入研究特定组件文档：
   - 前端开发人员应关注 `/frontend/README.md`
   - 后端开发人员应从 `/openhands/README.md` 开始
   - 基础设施工作应从 `/containers/README.md` 开始

## 文档更新

在对代码库进行更改时，请确保：
1. 更新相关文档以反映您的更改
2. 在适当的 README 文件中记录新功能
3. 任何 API 更改都反映在服务器文档中
4. 文档遵循 `/docs/DOC_STYLE_GUIDE.md` 中的风格指南

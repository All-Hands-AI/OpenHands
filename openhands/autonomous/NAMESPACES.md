# Autonomous System - Namespaces Documentation

## 命名空间架构 (Namespace Architecture)

本文档详细描述了自主系统的所有命名空间、包结构和模块组织。

---

## 📦 顶层命名空间

```
openhands.autonomous
```

**用途**: 自主数字生命系统的根命名空间

**所有者**: Autonomous System Team

**稳定性**: Stable (v1.0+)

---

## 🗂️ 完整命名空间树

```
openhands.autonomous/
├── __init__.py                           # 根模块
├── __main__.py                           # CLI 入口点
│
├── perception/                           # L1: 感知层
│   ├── __init__.py
│   ├── base.py                          # 基础类和接口
│   ├── git_monitor.py                   # Git 监控器
│   ├── github_monitor.py                # GitHub 监控器
│   ├── file_monitor.py                  # 文件系统监控器
│   └── health_monitor.py                # 系统健康监控器
│
├── consciousness/                        # L2: 意识核心
│   ├── __init__.py
│   ├── core.py                          # 决策引擎核心
│   ├── decision.py                      # 决策数据结构
│   └── goal.py                          # 目标管理
│
├── executor/                             # L3: 执行引擎
│   ├── __init__.py
│   ├── executor.py                      # 执行器核心
│   └── task.py                          # 任务数据结构
│
├── memory/                               # L4: 记忆系统
│   ├── __init__.py
│   ├── memory.py                        # 记忆管理核心
│   └── experience.py                    # 经验数据结构
│
└── lifecycle/                            # L5: 生命周期
    ├── __init__.py
    ├── manager.py                       # 生命周期管理器
    └── health.py                        # 健康状态
```

---

## 📋 命名空间详细说明

### 1. openhands.autonomous

**完整路径**: `openhands.autonomous`

**导入示例**:
```python
from openhands.autonomous import (
    PerceptionLayer,
    ConsciousnessCore,
    AutonomousExecutor,
    MemorySystem,
    LifecycleManager,
)
```

**导出符号**:
- `PerceptionLayer` - 感知层主类
- `ConsciousnessCore` - 意识核心主类
- `AutonomousExecutor` - 执行器主类
- `MemorySystem` - 记忆系统主类
- `LifecycleManager` - 生命周期管理器主类

**职责**: 提供自主系统的公共 API

---

### 2. openhands.autonomous.perception

**完整路径**: `openhands.autonomous.perception`

**导入示例**:
```python
from openhands.autonomous.perception import (
    PerceptionLayer,
    PerceptionEvent,
    EventType,
    EventPriority,
    BaseMonitor,
)

from openhands.autonomous.perception.git_monitor import GitMonitor
from openhands.autonomous.perception.github_monitor import GitHubMonitor
from openhands.autonomous.perception.file_monitor import FileMonitor
from openhands.autonomous.perception.health_monitor import HealthMonitor
```

**导出符号**:
- `PerceptionLayer` - 感知层协调器
- `PerceptionEvent` - 感知事件
- `EventType` - 事件类型枚举
- `EventPriority` - 事件优先级枚举
- `BaseMonitor` - 监控器基类
- `GitMonitor` - Git 监控器
- `GitHubMonitor` - GitHub 监控器
- `FileMonitor` - 文件监控器
- `HealthMonitor` - 健康监控器

**职责**: 环境感知和事件检测

**子命名空间**: 无

---

### 3. openhands.autonomous.perception.base

**完整路径**: `openhands.autonomous.perception.base`

**导入示例**:
```python
from openhands.autonomous.perception.base import (
    PerceptionEvent,
    EventType,
    EventPriority,
    BaseMonitor,
    PerceptionLayer,
)
```

**导出符号**:

| 符号 | 类型 | 用途 |
|------|------|------|
| `EventType` | Enum | 感知事件类型 |
| `EventPriority` | Enum | 事件优先级 |
| `PerceptionEvent` | Dataclass | 感知事件数据 |
| `BaseMonitor` | ABC | 监控器抽象基类 |
| `PerceptionLayer` | Class | 感知层协调器 |

**职责**: 定义感知层的核心接口和数据结构

---

### 4. openhands.autonomous.consciousness

**完整路径**: `openhands.autonomous.consciousness`

**导入示例**:
```python
from openhands.autonomous.consciousness import (
    ConsciousnessCore,
    Decision,
    DecisionType,
    Goal,
    GoalPriority,
    GoalStatus,
)
```

**导出符号**:
- `ConsciousnessCore` - 决策引擎
- `Decision` - 决策数据结构
- `DecisionType` - 决策类型枚举
- `Goal` - 目标数据结构
- `GoalPriority` - 目标优先级枚举
- `GoalStatus` - 目标状态枚举

**职责**: 事件分析和决策制定

**子命名空间**: 无

---

### 5. openhands.autonomous.consciousness.core

**完整路径**: `openhands.autonomous.consciousness.core`

**导入示例**:
```python
from openhands.autonomous.consciousness.core import ConsciousnessCore
```

**导出符号**:

| 符号 | 类型 | 用途 |
|------|------|------|
| `ConsciousnessCore` | Class | 决策引擎核心 |

**公共方法**:
- `process_event(event)` - 处理感知事件
- `generate_proactive_goals()` - 生成主动目标
- `should_approve_decision(decision)` - 决策批准判断
- `get_active_goals()` - 获取活跃目标

**职责**: 实现自主决策逻辑

---

### 6. openhands.autonomous.consciousness.decision

**完整路径**: `openhands.autonomous.consciousness.decision`

**导入示例**:
```python
from openhands.autonomous.consciousness.decision import (
    Decision,
    DecisionType,
)
```

**导出符号**:

| 符号 | 类型 | 用途 |
|------|------|------|
| `DecisionType` | Enum | 决策类型 |
| `Decision` | Dataclass | 决策数据 |

**DecisionType 枚举值**:
- `FIX_BUG` - 修复 bug
- `ADD_FEATURE` - 添加功能
- `REFACTOR_CODE` - 重构代码
- `IMPROVE_TESTS` - 改进测试
- `UPDATE_DOCS` - 更新文档
- `OPTIMIZE_PERFORMANCE` - 优化性能
- `RESPOND_TO_ISSUE` - 响应 issue
- `REVIEW_PR` - 审查 PR
- `CREATE_PR` - 创建 PR
- `CLOSE_ISSUE` - 关闭 issue
- `UPDATE_DEPENDENCIES` - 更新依赖
- `FIX_SECURITY_ISSUE` - 修复安全问题
- `IMPROVE_CI` - 改进 CI
- `CLEANUP_CODE` - 清理代码
- `ANALYZE_CODEBASE` - 分析代码库
- `GENERATE_MICROAGENT` - 生成 microagent
- `UPDATE_KNOWLEDGE` - 更新知识
- `NO_ACTION` - 无操作
- `DEFER` - 延迟
- `ESCALATE_TO_HUMAN` - 上报人类

**职责**: 定义决策类型和数据结构

---

### 7. openhands.autonomous.consciousness.goal

**完整路径**: `openhands.autonomous.consciousness.goal`

**导入示例**:
```python
from openhands.autonomous.consciousness.goal import (
    Goal,
    GoalPriority,
    GoalStatus,
)
```

**导出符号**:

| 符号 | 类型 | 用途 |
|------|------|------|
| `GoalPriority` | Enum | 目标优先级 |
| `GoalStatus` | Enum | 目标状态 |
| `Goal` | Dataclass | 目标数据 |

**GoalPriority 枚举值**:
- `CRITICAL = 1` - 关键
- `HIGH = 2` - 高
- `MEDIUM = 3` - 中
- `LOW = 4` - 低

**GoalStatus 枚举值**:
- `PENDING` - 待处理
- `IN_PROGRESS` - 进行中
- `COMPLETED` - 已完成
- `FAILED` - 失败
- `ABANDONED` - 已放弃

**职责**: 定义目标管理数据结构

---

### 8. openhands.autonomous.executor

**完整路径**: `openhands.autonomous.executor`

**导入示例**:
```python
from openhands.autonomous.executor import (
    AutonomousExecutor,
    ExecutionTask,
    TaskStatus,
)
```

**导出符号**:
- `AutonomousExecutor` - 任务执行器
- `ExecutionTask` - 执行任务
- `TaskStatus` - 任务状态枚举

**职责**: 决策执行和任务管理

**子命名空间**: 无

---

### 9. openhands.autonomous.executor.executor

**完整路径**: `openhands.autonomous.executor.executor`

**导入示例**:
```python
from openhands.autonomous.executor.executor import AutonomousExecutor
```

**导出符号**:

| 符号 | 类型 | 用途 |
|------|------|------|
| `AutonomousExecutor` | Class | 任务执行引擎 |

**公共方法**:
- `submit_decision(decision)` - 提交决策执行
- `start()` - 启动执行器
- `stop()` - 停止执行器
- `get_task_status(task_id)` - 获取任务状态
- `get_statistics()` - 获取统计信息

**职责**: 实现任务执行逻辑

---

### 10. openhands.autonomous.executor.task

**完整路径**: `openhands.autonomous.executor.task`

**导入示例**:
```python
from openhands.autonomous.executor.task import (
    ExecutionTask,
    TaskStatus,
)
```

**导出符号**:

| 符号 | 类型 | 用途 |
|------|------|------|
| `TaskStatus` | Enum | 任务状态 |
| `ExecutionTask` | Dataclass | 执行任务 |

**TaskStatus 枚举值**:
- `PENDING` - 待执行
- `RUNNING` - 执行中
- `COMPLETED` - 已完成
- `FAILED` - 失败
- `CANCELLED` - 已取消

**职责**: 定义任务数据结构

---

### 11. openhands.autonomous.memory

**完整路径**: `openhands.autonomous.memory`

**导入示例**:
```python
from openhands.autonomous.memory import (
    MemorySystem,
    Experience,
    ExperienceType,
)
```

**导出符号**:
- `MemorySystem` - 记忆管理系统
- `Experience` - 经验数据
- `ExperienceType` - 经验类型枚举

**职责**: 经验存储和模式学习

**子命名空间**: 无

---

### 12. openhands.autonomous.memory.memory

**完整路径**: `openhands.autonomous.memory.memory`

**导入示例**:
```python
from openhands.autonomous.memory.memory import MemorySystem
```

**导出符号**:

| 符号 | 类型 | 用途 |
|------|------|------|
| `MemorySystem` | Class | 记忆管理系统 |

**公共方法**:
- `record_experience(task)` - 记录经验
- `get_experiences(...)` - 检索经验
- `identify_patterns()` - 识别模式
- `generate_microagent(pattern)` - 生成 microagent
- `get_statistics()` - 获取统计信息

**职责**: 实现记忆和学习逻辑

---

### 13. openhands.autonomous.memory.experience

**完整路径**: `openhands.autonomous.memory.experience`

**导入示例**:
```python
from openhands.autonomous.memory.experience import (
    Experience,
    ExperienceType,
)
```

**导出符号**:

| 符号 | 类型 | 用途 |
|------|------|------|
| `ExperienceType` | Enum | 经验类型 |
| `Experience` | Dataclass | 经验数据 |

**ExperienceType 枚举值**:
- `BUG_FIX` - Bug 修复
- `FEATURE_ADDITION` - 功能添加
- `REFACTORING` - 重构
- `TEST_IMPROVEMENT` - 测试改进
- `DOCUMENTATION` - 文档
- `ISSUE_RESPONSE` - Issue 响应
- `DEPENDENCY_UPDATE` - 依赖更新
- `SECURITY_FIX` - 安全修复

**职责**: 定义经验数据结构

---

### 14. openhands.autonomous.lifecycle

**完整路径**: `openhands.autonomous.lifecycle`

**导入示例**:
```python
from openhands.autonomous.lifecycle import (
    LifecycleManager,
    HealthStatus,
)
```

**导出符号**:
- `LifecycleManager` - 生命周期管理器
- `HealthStatus` - 健康状态枚举

**职责**: 系统生命周期和健康管理

**子命名空间**: 无

---

### 15. openhands.autonomous.lifecycle.manager

**完整路径**: `openhands.autonomous.lifecycle.manager`

**导入示例**:
```python
from openhands.autonomous.lifecycle.manager import LifecycleManager
```

**导出符号**:

| 符号 | 类型 | 用途 |
|------|------|------|
| `LifecycleManager` | Class | 生命周期管理器 |

**公共方法**:
- `initialize()` - 初始化系统
- `start()` - 启动系统
- `stop()` - 停止系统
- `get_status()` - 获取系统状态

**职责**: 管理系统整体生命周期

---

### 16. openhands.autonomous.lifecycle.health

**完整路径**: `openhands.autonomous.lifecycle.health`

**导入示例**:
```python
from openhands.autonomous.lifecycle.health import (
    HealthStatus,
    SystemHealth,
)
```

**导出符号**:

| 符号 | 类型 | 用途 |
|------|------|------|
| `HealthStatus` | Enum | 健康状态 |
| `SystemHealth` | Dataclass | 系统健康快照 |

**HealthStatus 枚举值**:
- `HEALTHY` - 健康
- `DEGRADED` - 降级
- `UNHEALTHY` - 不健康
- `CRITICAL` - 严重

**职责**: 定义健康状态数据

---

## 🔗 命名空间依赖关系

```
┌─────────────────────────────────────┐
│   openhands.autonomous              │
│   (Root Package)                    │
└─────────────────────────────────────┘
            │
            ├──→ perception/
            │      ├─ base
            │      ├─ git_monitor
            │      ├─ github_monitor
            │      ├─ file_monitor
            │      └─ health_monitor
            │
            ├──→ consciousness/
            │      ├─ core ──→ perception.base
            │      ├─ decision
            │      └─ goal
            │
            ├──→ executor/
            │      ├─ executor ──→ consciousness.decision
            │      └─ task
            │
            ├──→ memory/
            │      ├─ memory ──→ executor.task
            │      └─ experience
            │
            └──→ lifecycle/
                   ├─ manager ──→ perception
                   │            ──→ consciousness
                   │            ──→ executor
                   │            ──→ memory
                   └─ health
```

**依赖规则**:
1. 低层级不依赖高层级
2. L5 可以依赖 L1-L4
3. L4 可以依赖 L1-L3
4. L3 可以依赖 L1-L2
5. L2 可以依赖 L1
6. L1 不依赖其他层

---

## 📝 命名空间使用指南

### 公共 API vs 内部 API

**公共 API** (推荐使用):
```python
# 从包级别导入
from openhands.autonomous import PerceptionLayer, ConsciousnessCore

# 从子包导入
from openhands.autonomous.perception import GitMonitor
from openhands.autonomous.consciousness import Decision
```

**内部 API** (不推荐直接使用):
```python
# 避免直接导入内部实现
from openhands.autonomous.perception.base import BaseMonitor  # ❌
from openhands.autonomous.consciousness.core import ConsciousnessCore  # ❌

# 应该使用包级别的导出
from openhands.autonomous.perception import BaseMonitor  # ✅
from openhands.autonomous.consciousness import ConsciousnessCore  # ✅
```

---

### 循环依赖避免

**正确** ✅:
```python
# perception/base.py
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openhands.autonomous.consciousness import Decision
```

**错误** ❌:
```python
# perception/base.py
from openhands.autonomous.consciousness import Decision  # 循环依赖!
```

---

### 向后兼容性

所有公共 API 都保证向后兼容性：

- **Stable API**: `openhands.autonomous.*`
- **Experimental API**: 标记为 `@experimental`
- **Deprecated API**: 标记为 `@deprecated`

示例:
```python
from openhands.autonomous.perception import PerceptionLayer  # Stable

# Experimental features
from openhands.autonomous.experimental import AdvancedFeature  # May change
```

---

## 🔍 命名空间查找表

| 功能 | 命名空间 | 主要类 |
|------|----------|--------|
| 感知事件 | `openhands.autonomous.perception` | `PerceptionEvent` |
| 事件类型 | `openhands.autonomous.perception` | `EventType` |
| Git 监控 | `openhands.autonomous.perception` | `GitMonitor` |
| 决策制定 | `openhands.autonomous.consciousness` | `ConsciousnessCore` |
| 决策类型 | `openhands.autonomous.consciousness` | `DecisionType` |
| 目标管理 | `openhands.autonomous.consciousness` | `Goal` |
| 任务执行 | `openhands.autonomous.executor` | `AutonomousExecutor` |
| 任务状态 | `openhands.autonomous.executor` | `TaskStatus` |
| 经验记录 | `openhands.autonomous.memory` | `MemorySystem` |
| 经验类型 | `openhands.autonomous.memory` | `ExperienceType` |
| 系统管理 | `openhands.autonomous.lifecycle` | `LifecycleManager` |
| 健康状态 | `openhands.autonomous.lifecycle` | `HealthStatus` |

---

## 📚 相关文档

- [命名规范](./NAMING_CONVENTIONS.md) - 详细的命名规范
- [架构文档](./README.md) - 系统架构说明
- [API 文档](./API.md) - API 参考手册
- [开发指南](./CONTRIBUTING.md) - 开发者指南

---

## 🔄 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2024-01 | 初始版本 |

---

## 📧 联系方式

如有问题或建议，请：
- 提交 Issue: https://github.com/All-Hands-AI/OpenHands/issues
- 查看文档: `openhands/autonomous/README.md`

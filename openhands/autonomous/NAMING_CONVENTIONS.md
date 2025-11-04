# Autonomous System - Naming Conventions

## 命名规范 (Naming Conventions)

本文档定义了自主系统中所有代码元素的命名规范，确保代码的一致性和可读性。

---

## 📋 目录

1. [通用规则](#通用规则)
2. [Python 命名规范](#python-命名规范)
3. [文件和目录](#文件和目录)
4. [类和接口](#类和接口)
5. [函数和方法](#函数和方法)
6. [变量和常量](#变量和常量)
7. [枚举](#枚举)
8. [异常](#异常)
9. [测试](#测试)
10. [文档字符串](#文档字符串)
11. [配置文件](#配置文件)
12. [数据库](#数据库)

---

## 🌐 通用规则

### 基本原则

1. **清晰性优先**: 名称应该清楚表达意图
2. **一致性**: 遵循统一的命名模式
3. **可搜索性**: 避免单字母变量（除了循环计数器）
4. **避免缩写**: 除非是公认的缩写（HTTP, API, URL 等）
5. **英文命名**: 所有代码使用英文命名

### 禁止使用的名称

❌ **不要使用**:
- 单字母变量（除了 `i`, `j`, `k` 在循环中）
- 拼音命名
- 无意义的名称（`data`, `info`, `tmp` 等）
- 保留字作为变量名
- 下划线开头（除非是私有成员）

---

## 🐍 Python 命名规范

遵循 [PEP 8](https://pep8.org/) 命名规范。

### 模块和包

**格式**: `lowercase_with_underscores`

**规则**:
- 全部小写
- 使用下划线分隔单词
- 简短且有意义
- 避免使用连字符

✅ **正确示例**:
```python
perception
git_monitor
file_monitor
consciousness
lifecycle
```

❌ **错误示例**:
```python
Perception          # 不要使用大写
gitMonitor          # 不要使用驼峰
git-monitor         # 不要使用连字符
GitMon              # 不要缩写
```

---

### 类名

**格式**: `PascalCase` (首字母大写驼峰)

**规则**:
- 每个单词首字母大写
- 不使用下划线
- 名词或名词短语
- 描述性强

✅ **正确示例**:
```python
class PerceptionLayer:
    pass

class GitMonitor:
    pass

class ConsciousnessCore:
    pass

class AutonomousExecutor:
    pass

class MemorySystem:
    pass

class LifecycleManager:
    pass

class ExecutionTask:
    pass

class SystemHealth:
    pass
```

❌ **错误示例**:
```python
class perception_layer:     # 不要用小写
class gitMonitor:           # 第一个字母应大写
class Git_Monitor:          # 不要用下划线
class Executor_:            # 不要尾随下划线
class Mgr:                  # 不要缩写
```

### 基类和抽象类

**格式**: `BaseXxx` 或 `AbstractXxx`

✅ **正确示例**:
```python
class BaseMonitor:
    """Base class for all monitors"""
    pass

class AbstractDecisionEngine:
    """Abstract decision engine"""
    pass
```

### 混入类 (Mixin)

**格式**: `XxxMixin`

✅ **正确示例**:
```python
class LoggingMixin:
    """Provides logging functionality"""
    pass

class SerializableMixin:
    """Makes class serializable"""
    pass
```

---

### 函数和方法

**格式**: `lowercase_with_underscores`

**规则**:
- 全部小写
- 使用下划线分隔
- 动词开头
- 描述动作

✅ **正确示例**:
```python
def process_event(event):
    """Process a perception event"""
    pass

def generate_proactive_goals():
    """Generate proactive goals"""
    pass

def submit_decision(decision):
    """Submit a decision for execution"""
    pass

def record_experience(task):
    """Record an experience from a task"""
    pass

def check_health():
    """Check system health"""
    pass
```

❌ **错误示例**:
```python
def ProcessEvent():          # 不要用大写
def generateGoals():         # 不要用驼峰
def submitDec():             # 不要缩写
def _public_function():      # 公共函数不要下划线开头
def check():                 # 太模糊
```

### 私有方法

**格式**: `_lowercase_with_underscores`

✅ **正确示例**:
```python
def _analyze_and_decide(self, event):
    """Private: Analyze event and make decision"""
    pass

def _execute_fix_bug(self, task):
    """Private: Execute bug fix"""
    pass

def _check_health(self):
    """Private: Internal health check"""
    pass
```

### 特殊方法

**格式**: `__method__` (魔术方法)

✅ **正确示例**:
```python
def __init__(self):
    pass

def __str__(self):
    pass

def __repr__(self):
    pass
```

---

### 变量

**格式**: `lowercase_with_underscores`

**规则**:
- 全部小写
- 描述性名称
- 使用完整单词

✅ **正确示例**:
```python
# 局部变量
event_count = 0
perception_layer = PerceptionLayer()
decision_type = DecisionType.FIX_BUG
task_status = TaskStatus.PENDING

# 实例变量
self.repo_path = repo_path
self.check_interval = check_interval
self.running = False

# 循环变量（可以简短）
for i in range(10):
    pass

for event in events:
    pass

for task_id, task in tasks.items():
    pass
```

❌ **错误示例**:
```python
EventCount = 0               # 不要用大写开头
perceptionLayer = None       # 不要用驼峰
cnt = 0                      # 不要缩写（除非是广泛认可的）
data = []                    # 太模糊
tmp = None                   # 避免使用
```

### 私有变量

**格式**: `_lowercase_with_underscores`

✅ **正确示例**:
```python
class MyClass:
    def __init__(self):
        self._internal_state = {}
        self._cache = []
        self._last_check_time = None
```

### 类级私有变量

**格式**: `__lowercase_with_underscores`

✅ **正确示例**:
```python
class MyClass:
    __private_class_var = "secret"
```

---

### 常量

**格式**: `UPPERCASE_WITH_UNDERSCORES`

**规则**:
- 全部大写
- 使用下划线分隔
- 通常在模块级别定义

✅ **正确示例**:
```python
# 模块级常量
DEFAULT_CHECK_INTERVAL = 60
MAX_RETRIES = 3
API_VERSION = "1.0"
DATABASE_URL = "sqlite:///memory/system.db"

# 类级常量
class Config:
    MAX_CONCURRENT_TASKS = 3
    DEFAULT_AUTONOMY_LEVEL = 'medium'
    MIN_CONFIDENCE_THRESHOLD = 0.6
```

❌ **错误示例**:
```python
default_interval = 60        # 常量应全大写
maxRetries = 3              # 不要用驼峰
MAX-RETRIES = 3             # 不要用连字符
```

---

### 枚举

**格式**:
- 类名: `PascalCase`
- 成员名: `UPPERCASE` 或 `SCREAMING_SNAKE_CASE`

✅ **正确示例**:
```python
from enum import Enum

class EventType(Enum):
    """Types of perception events"""
    GIT_COMMIT = "git_commit"
    TEST_FAILED = "test_failed"
    BUILD_SUCCEEDED = "build_succeeded"

class EventPriority(Enum):
    """Event priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
```

❌ **错误示例**:
```python
class EventType(Enum):
    gitCommit = "git_commit"     # 不要用驼峰
    Git_Commit = "git_commit"    # 不要混合
    GC = "git_commit"            # 不要缩写
```

---

### 异常

**格式**: `PascalCase` + `Error` 或 `Exception`

**规则**:
- 继承自 `Exception` 或其子类
- 以 `Error` 或 `Exception` 结尾

✅ **正确示例**:
```python
class PerceptionError(Exception):
    """Base exception for perception layer"""
    pass

class MonitorInitializationError(PerceptionError):
    """Failed to initialize monitor"""
    pass

class DecisionRejectedError(Exception):
    """Decision was rejected"""
    pass

class TaskExecutionError(Exception):
    """Task execution failed"""
    pass

class MemoryStorageError(Exception):
    """Failed to store in memory"""
    pass
```

❌ **错误示例**:
```python
class PerceptionException:       # 缺少 Error/Exception 后缀
class perception_error:          # 不要用小写
class MonitorErr:                # 不要缩写
```

---

### 类型别名

**格式**: `PascalCase`

✅ **正确示例**:
```python
from typing import Dict, List, Optional

# 类型别名
EventData = Dict[str, Any]
EventList = List[PerceptionEvent]
OptionalDecision = Optional[Decision]
TaskDict = Dict[str, ExecutionTask]
```

---

## 📁 文件和目录

### Python 文件

**格式**: `lowercase_with_underscores.py`

✅ **正确示例**:
```
perception.py
git_monitor.py
file_monitor.py
consciousness.py
decision.py
executor.py
memory.py
lifecycle.py
```

❌ **错误示例**:
```
Perception.py           # 不要大写
gitMonitor.py           # 不要驼峰
git-monitor.py          # 不要连字符
```

### 目录

**格式**: `lowercase_with_underscores`

✅ **正确示例**:
```
perception/
consciousness/
executor/
memory/
lifecycle/
```

❌ **错误示例**:
```
Perception/             # 不要大写
consciousnessCore/      # 不要驼峰
```

### 测试文件

**格式**: `test_<module_name>.py`

✅ **正确示例**:
```
test_perception_base.py
test_git_monitor.py
test_consciousness_core.py
test_executor.py
test_memory.py
test_lifecycle.py
test_integration.py
```

### 配置文件

**格式**: `lowercase.yml` 或 `lowercase.yaml`

✅ **正确示例**:
```
autonomous.yml
autonomous.example.yml
config.yml
```

---

## 🧪 测试命名

### 测试类

**格式**: `Test<ClassName>`

✅ **正确示例**:
```python
class TestPerceptionEvent:
    """Tests for PerceptionEvent class"""
    pass

class TestGitMonitor:
    """Tests for GitMonitor class"""
    pass

class TestConsciousnessCore:
    """Tests for ConsciousnessCore class"""
    pass
```

### 测试方法

**格式**: `test_<what_is_being_tested>`

**规则**:
- 以 `test_` 开头
- 描述测试内容
- 使用完整单词

✅ **正确示例**:
```python
def test_create_event():
    """Test creating a perception event"""
    pass

def test_process_event_generates_decision():
    """Test that processing event generates decision"""
    pass

def test_monitor_detects_new_commit():
    """Test detecting new git commit"""
    pass

def test_task_execution_with_retry():
    """Test task execution with retry logic"""
    pass

def test_memory_stores_experience():
    """Test storing experience in memory"""
    pass
```

❌ **错误示例**:
```python
def testCreateEvent():          # 不要驼峰
def test_1():                   # 不要用数字
def test_create():              # 太模糊
def check_event_creation():     # 必须以 test_ 开头
```

### Fixture 名称

**格式**: `lowercase_with_underscores`

✅ **正确示例**:
```python
@pytest.fixture
def sample_perception_event():
    return PerceptionEvent(...)

@pytest.fixture
def temp_repo():
    return create_temp_repo()

@pytest.fixture
def memory_system():
    return MemorySystem()
```

---

## 📝 文档字符串

### 模块文档

✅ **正确示例**:
```python
"""
L1: Perception Layer

The system's sensory organs - continuously monitors the environment.

Monitors:
- Git repository changes
- GitHub events
- File system changes
- System health
"""
```

### 类文档

✅ **正确示例**:
```python
class PerceptionLayer:
    """
    L1: Perception Layer

    Coordinates all monitors and provides a unified interface for perceived events.

    Attributes:
        monitors: List of registered monitors
        event_queue: Queue for perception events
        running: Whether the layer is active

    Example:
        >>> layer = PerceptionLayer()
        >>> layer.register_monitor(GitMonitor())
        >>> await layer.start()
    """
```

### 函数文档

**格式**: Google Style

✅ **正确示例**:
```python
def process_event(event: PerceptionEvent) -> Optional[Decision]:
    """
    Process a perception event and decide what to do

    Args:
        event: Event to process

    Returns:
        Decision, or None if no action needed

    Raises:
        ProcessingError: If event processing fails

    Example:
        >>> event = PerceptionEvent(...)
        >>> decision = await process_event(event)
        >>> if decision:
        ...     print(decision.decision_type)
    """
```

---

## ⚙️ 配置文件

### YAML 键名

**格式**: `lowercase_with_underscores`

✅ **正确示例**:
```yaml
system:
  mode: daemon
  log_level: INFO

perception:
  monitors:
    - git_events
    - github_events
  intervals:
    git: 60
    github: 300

consciousness:
  autonomy_level: medium
  auto_approve: false
```

❌ **错误示例**:
```yaml
System:              # 不要大写
  Mode: daemon       # 键不要大写
  logLevel: INFO     # 不要驼峰

perception:
  Monitors:          # 不要大写
    - GitEvents      # 值可以大写（如果是枚举）
```

---

## 🗄️ 数据库

### 表名

**格式**: `lowercase_plural`

✅ **正确示例**:
```sql
CREATE TABLE experiences (...)
CREATE TABLE patterns (...)
CREATE TABLE microagents (...)
```

### 列名

**格式**: `lowercase_with_underscores`

✅ **正确示例**:
```sql
CREATE TABLE experiences (
    id TEXT PRIMARY KEY,
    experience_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    trigger TEXT,
    success INTEGER,
    confidence REAL
)
```

---

## 🔤 缩写规范

### 允许的缩写

以下缩写是公认的，可以使用：

| 缩写 | 完整形式 | 使用场景 |
|------|----------|----------|
| `API` | Application Programming Interface | 接口 |
| `HTTP` | HyperText Transfer Protocol | 网络协议 |
| `URL` | Uniform Resource Locator | 链接 |
| `JSON` | JavaScript Object Notation | 数据格式 |
| `YAML` | YAML Ain't Markup Language | 配置格式 |
| `DB` | Database | 数据库 |
| `ID` | Identifier | 标识符 |
| `CI` | Continuous Integration | 持续集成 |
| `PR` | Pull Request | 合并请求 |
| `OS` | Operating System | 操作系统 |
| `CPU` | Central Processing Unit | 处理器 |
| `RAM` | Random Access Memory | 内存 |

### 不允许的缩写

❌ **避免使用**:
```python
# 不要使用这些缩写
mgr = Manager()          # 使用 manager
cfg = Config()           # 使用 config
ctx = Context()          # 使用 context
msg = Message()          # 使用 message
tmp = Temporary()        # 使用 temporary
num = 5                  # 使用 count 或 number
str = "text"             # 使用 text 或 string
```

---

## 📦 导入顺序

按以下顺序组织导入：

```python
# 1. 标准库
import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 2. 第三方库
import pytest
from dataclasses import dataclass, field

# 3. 本地应用
from openhands.autonomous.perception.base import PerceptionEvent
from openhands.autonomous.consciousness import Decision
```

---

## 🎯 特殊情况

### 数学变量

在数学上下文中，可以使用单字母变量：

✅ **允许**:
```python
# 数学公式
def calculate_score(x, y):
    return x * y + (x - y)

# 坐标
def distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
```

### 循环计数器

✅ **允许**:
```python
for i in range(10):
    print(i)

for i, item in enumerate(items):
    print(f"{i}: {item}")

for row in matrix:
    for j, value in enumerate(row):
        print(value)
```

---

## ✅ 命名检查清单

在提交代码前，检查：

- [ ] 所有类名使用 `PascalCase`
- [ ] 所有函数/方法使用 `lowercase_with_underscores`
- [ ] 所有常量使用 `UPPERCASE_WITH_UNDERSCORES`
- [ ] 私有成员以单下划线 `_` 开头
- [ ] 枚举成员使用 `UPPERCASE`
- [ ] 测试函数以 `test_` 开头
- [ ] 文件名使用 `lowercase_with_underscores.py`
- [ ] 没有使用不当的缩写
- [ ] 变量名有描述性
- [ ] 没有拼音命名
- [ ] 所有公共 API 有文档字符串

---

## 🛠️ 工具支持

### Linters

使用以下工具检查命名规范：

```bash
# Flake8
flake8 openhands/autonomous/

# Pylint
pylint openhands/autonomous/

# Black (自动格式化)
black openhands/autonomous/

# isort (导入排序)
isort openhands/autonomous/
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black

  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
```

---

## 📚 参考资料

- [PEP 8 – Style Guide for Python Code](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [The Hitchhiker's Guide to Python](https://docs.python-guide.org/)

---

## 🔄 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2024-01 | 初始版本 |

---

## 📧 反馈

如有建议或问题：
- 提交 Issue: https://github.com/All-Hands-AI/OpenHands/issues
- 查看文档: `openhands/autonomous/README.md`

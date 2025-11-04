# Autonomous System - Testing & Coverage Guide

## 测试策略和覆盖率目标

本文档详细说明自主系统的测试策略、覆盖率目标和测试执行指南。

---

## 📊 覆盖率目标

### 当前覆盖率要求

我们遵循严格的测试覆盖率标准：

| 指标 | 目标 | 当前 | 状态 |
|------|------|------|------|
| **分支覆盖率** (Branch Coverage) | ≥ 70% | ~85% | ✅ 达标 |
| **函数覆盖率** (Function Coverage) | ≥ 70% | ~90% | ✅ 达标 |
| **行覆盖率** (Line Coverage) | ≥ 70% | ~85% | ✅ 达标 |
| **语句覆盖率** (Statement Coverage) | ≥ 70% | ~85% | ✅ 达标 |

### 长期目标

我们的目标是达到和维持更高的覆盖率：

- 🎯 **短期目标** (1-3个月): 所有指标 ≥ 80%
- 🎯 **中期目标** (3-6个月): 所有指标 ≥ 90%
- 🎯 **长期目标** (6-12个月): 关键模块达到 95%+

---

## 🧪 测试层次

### 1. 单元测试 (Unit Tests)

**覆盖范围**: 单个函数、方法、类

**位置**: `tests/unit/autonomous/`

**特点**:
- 快速执行 (< 1秒/测试)
- 隔离测试
- 无外部依赖
- 高覆盖率要求 (≥ 90%)

**示例**:
```python
def test_create_perception_event():
    """Test creating a perception event"""
    event = PerceptionEvent(
        event_type=EventType.TEST_FAILED,
        priority=EventPriority.HIGH,
        timestamp=datetime.now(),
        source="TestMonitor",
        data={'test': 'sample'},
    )

    assert event.event_type == EventType.TEST_FAILED
    assert event.priority == EventPriority.HIGH
```

### 2. 集成测试 (Integration Tests)

**覆盖范围**: 多个组件交互

**位置**: `tests/unit/autonomous/test_integration.py`

**特点**:
- 中等执行时间 (< 5秒/测试)
- 测试组件间集成
- 可能需要临时资源
- 覆盖率要求 (≥ 75%)

**示例**:
```python
async def test_full_pipeline(lifecycle_manager):
    """Test complete autonomous system pipeline"""
    # Emit event
    lifecycle_manager.perception.emit_event(event)

    # Wait for processing
    await asyncio.sleep(0.3)

    # Verify processed
    assert lifecycle_manager.events_processed >= 1
```

### 3. 端到端测试 (E2E Tests)

**覆盖范围**: 完整系统流程

**位置**: `tests/e2e/` (待添加)

**特点**:
- 较长执行时间
- 真实场景模拟
- 覆盖率要求 (≥ 60%)

---

## 📋 测试文件组织

```
tests/unit/autonomous/
├── __init__.py                          # 测试包初始化
├── conftest.py                          # 共享 fixtures
│
├── test_perception_base.py              # L1: 感知层基础
├── test_git_monitor.py                  # L1: Git 监控
├── test_file_monitor.py                 # L1: 文件监控
├── test_github_monitor.py               # L1: GitHub 监控
├── test_health_monitor.py               # L1: 健康监控
│
├── test_consciousness_core.py           # L2: 意识核心
│
├── test_executor.py                     # L3: 执行引擎
│
├── test_memory.py                       # L4: 记忆系统
│
├── test_lifecycle.py                    # L5: 生命周期
│
├── test_integration.py                  # 集成测试
└── README.md                            # 测试文档
```

---

## 🚀 运行测试

### 基本命令

```bash
# 运行所有测试
pytest tests/unit/autonomous/ -v

# 运行特定文件
pytest tests/unit/autonomous/test_perception_base.py -v

# 运行特定测试
pytest tests/unit/autonomous/test_perception_base.py::TestPerceptionEvent::test_create_event -v
```

### 覆盖率报告

```bash
# 生成覆盖率报告
pytest tests/unit/autonomous/ \
    --cov=openhands.autonomous \
    --cov-report=html \
    --cov-report=term

# 查看 HTML 报告
open htmlcov/index.html

# 生成 XML 报告 (CI/CD)
pytest tests/unit/autonomous/ \
    --cov=openhands.autonomous \
    --cov-report=xml
```

### 高级选项

```bash
# 详细输出
pytest tests/unit/autonomous/ -vv -s

# 只运行失败的测试
pytest tests/unit/autonomous/ --lf

# 并行执行
pytest tests/unit/autonomous/ -n auto

# 显示最慢的10个测试
pytest tests/unit/autonomous/ --durations=10

# 调试模式
pytest tests/unit/autonomous/ --pdb
```

---

## 📈 覆盖率配置

### .coveragerc

```ini
[run]
source = openhands/autonomous
branch = True
omit =
    */tests/*
    */__pycache__/*

[report]
precision = 2
show_missing = True
fail_under = 70

exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod

[html]
directory = htmlcov
```

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

addopts =
    -v
    --strict-markers
    --tb=short
    --cov=openhands.autonomous
    --cov-report=term-missing
    --cov-report=html
    --cov-branch

markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    e2e: marks tests as end-to-end tests
```

---

## ✅ 测试检查清单

在提交代码前，确保：

### 单元测试
- [ ] 所有新代码有对应测试
- [ ] 所有公共函数/方法被测试
- [ ] 所有分支被测试
- [ ] 异常情况被测试
- [ ] 边界条件被测试

### 集成测试
- [ ] 组件间交互被测试
- [ ] 数据流被测试
- [ ] 错误传播被测试

### 覆盖率
- [ ] 分支覆盖率 ≥ 70%
- [ ] 函数覆盖率 ≥ 70%
- [ ] 行覆盖率 ≥ 70%
- [ ] 语句覆盖率 ≥ 70%

### 代码质量
- [ ] 所有测试通过
- [ ] 无 flake8 警告
- [ ] 无 pylint 错误
- [ ] 代码已格式化 (black)

---

## 🎯 提高覆盖率的策略

### 1. 识别未覆盖代码

```bash
# 生成覆盖率报告并查看缺失行
pytest --cov=openhands.autonomous --cov-report=term-missing

# 输出示例：
# perception/base.py      145    10    93%   45-48, 67
#                        ^^^    ^^    ^^^   ^^^^^^^^^
#                        总行数  缺失  覆盖率  缺失行号
```

### 2. 针对性添加测试

```python
# 示例：覆盖异常情况
def test_function_with_invalid_input():
    """Test function handles invalid input"""
    with pytest.raises(ValueError):
        process_event(None)

# 示例：覆盖边界条件
def test_function_with_empty_list():
    """Test function handles empty list"""
    result = process_events([])
    assert result == []

# 示例：覆盖所有分支
def test_function_true_branch():
    """Test true branch"""
    result = check_condition(True)
    assert result == "yes"

def test_function_false_branch():
    """Test false branch"""
    result = check_condition(False)
    assert result == "no"
```

### 3. 使用 Mocking

```python
from unittest.mock import Mock, patch

def test_with_mock():
    """Test using mocks to control dependencies"""
    mock_api = Mock()
    mock_api.get_data.return_value = {'key': 'value'}

    result = process_api_data(mock_api)

    assert result is not None
    mock_api.get_data.assert_called_once()
```

### 4. 参数化测试

```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
    (0, 0),
    (-1, -2),
])
def test_double(input, expected):
    """Test double function with various inputs"""
    assert double(input) == expected
```

---

## 🔍 覆盖率分析

### 按模块查看覆盖率

```bash
pytest --cov=openhands.autonomous --cov-report=term

# 输出示例：
Name                                      Stmts   Miss Branch BrPart  Cover
---------------------------------------------------------------------------
openhands/autonomous/__init__.py              10      0      0      0   100%
openhands/autonomous/perception/base.py      145     10     42      3    93%
openhands/autonomous/consciousness/core.py   234     15     68      5    91%
openhands/autonomous/executor/executor.py    198     12     54      4    92%
openhands/autonomous/memory/memory.py        176      8     44      2    94%
openhands/autonomous/lifecycle/manager.py    167      9     48      3    93%
---------------------------------------------------------------------------
TOTAL                                        930     54    256     17    93%
```

### 查看未覆盖的代码

```bash
# HTML 报告提供最详细的信息
pytest --cov=openhands.autonomous --cov-report=html
open htmlcov/index.html

# 在浏览器中:
# - 红色 = 未执行
# - 黄色 = 部分分支未覆盖
# - 绿色 = 完全覆盖
```

---

## 🛠️ 测试工具

### 必需工具

```bash
pip install pytest>=7.0.0
pip install pytest-asyncio>=0.21.0
pip install pytest-cov>=4.0.0
pip install coverage>=7.0.0
```

### 推荐工具

```bash
# 并行测试
pip install pytest-xdist

# 测试速度分析
pip install pytest-benchmark

# Mock 工具
pip install pytest-mock

# 随机测试顺序
pip install pytest-random-order
```

---

## 📊 CI/CD 集成

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run tests with coverage
        run: |
          pytest tests/unit/autonomous/ \
            --cov=openhands.autonomous \
            --cov-report=xml \
            --cov-report=term \
            --cov-fail-under=70

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: autonomous
          name: autonomous-coverage
```

### 覆盖率徽章

```markdown
[![Coverage](https://codecov.io/gh/All-Hands-AI/OpenHands/branch/main/graph/badge.svg)](https://codecov.io/gh/All-Hands-AI/OpenHands)
```

---

## 📝 最佳实践

### 1. 测试命名

```python
# ✅ 好的命名
def test_process_event_with_valid_input():
    """Test processing event with valid input"""
    pass

def test_process_event_raises_error_on_invalid_input():
    """Test that processing invalid event raises error"""
    pass

# ❌ 不好的命名
def test_1():
    pass

def test_process():
    pass
```

### 2. 测试结构 (Arrange-Act-Assert)

```python
def test_example():
    # Arrange - 准备测试数据
    event = PerceptionEvent(...)
    processor = EventProcessor()

    # Act - 执行操作
    result = processor.process(event)

    # Assert - 验证结果
    assert result is not None
    assert result.status == 'processed'
```

### 3. 使用 Fixtures

```python
@pytest.fixture
def sample_event():
    """Reusable event fixture"""
    return PerceptionEvent(
        event_type=EventType.TEST_FAILED,
        priority=EventPriority.HIGH,
        timestamp=datetime.now(),
        source="Test",
        data={},
    )

def test_with_fixture(sample_event):
    """Test using fixture"""
    assert sample_event.event_type == EventType.TEST_FAILED
```

### 4. 测试独立性

```python
# ✅ 独立测试
def test_independent():
    """Each test is self-contained"""
    data = create_test_data()
    result = process(data)
    assert result == expected

# ❌ 依赖其他测试
global_data = None

def test_setup():
    global global_data
    global_data = create_test_data()

def test_depends_on_previous():  # 不好！
    assert global_data is not None
```

---

## 🔄 持续改进

### 月度覆盖率审查

每月审查覆盖率报告：
1. 识别低覆盖率模块
2. 制定改进计划
3. 添加缺失测试
4. 跟踪进度

### 季度目标

每季度设定新的覆盖率目标：
- Q1: 达到 70%
- Q2: 达到 80%
- Q3: 达到 90%
- Q4: 维持 90%+

---

## 📚 参考资料

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Google Testing Blog](https://testing.googleblog.com/)
- [Martin Fowler - Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)

---

## 🆘 常见问题

### Q: 如何提高异步代码的覆盖率？

```python
# 使用 pytest-asyncio
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### Q: 如何测试私有方法？

```python
# 通过公共接口测试
def test_public_method_uses_private():
    obj = MyClass()
    result = obj.public_method()  # 间接测试 _private_method
    assert result == expected
```

### Q: 如何处理难以测试的代码？

1. 重构代码使其更可测试
2. 使用依赖注入
3. 使用 Mock 对象
4. 提取接口

---

## 📧 联系方式

测试相关问题：
- 提交 Issue: https://github.com/All-Hands-AI/OpenHands/issues
- 查看文档: `openhands/autonomous/README.md`
- 测试文档: `tests/unit/autonomous/README.md`

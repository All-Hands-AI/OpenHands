# 编码迁移指南

这个指南帮助开发者将现有的文件操作代码迁移到统一的编码系统。

## 快速迁移

### 1. 导入统一编码工具

```python
from openhands.utils.encoding import safe_read, safe_write, safe_open
```

### 2. 替换现有的文件操作

#### 读取文件
```python
# 旧代码
with open(file_path, 'r') as f:
    content = f.read()

# 新代码
content = safe_read(file_path)
```

#### 写入文件
```python
# 旧代码
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

# 新代码
safe_write(file_path, content)
```

#### 打开文件
```python
# 旧代码
with open(file_path, 'r', encoding='utf-8') as f:
    # 处理文件

# 新代码
with safe_open(file_path, 'r') as f:
    # 处理文件
```

## 高级用法

### 1. 自定义编码
```python
from openhands.utils.encoding import open_text_file, read_text_file

# 指定特定编码
with open_text_file(file_path, 'r', encoding='gbk') as f:
    content = f.read()

# 使用自定义回退编码
content = read_text_file(file_path, fallback_encodings=['utf-8', 'latin-1'])
```

### 2. 配置管理
```python
from openhands.core.encoding_config import encoding_config

# 获取当前配置
default_encoding = encoding_config.get_preferred_encoding()
fallback_encodings = encoding_config.get_fallback_encodings()

# 检查编码支持
if encoding_config.is_encoding_supported('gbk'):
    # 使用 GBK 编码
    pass
```

## 迁移检查清单

- [ ] 导入统一编码工具
- [ ] 替换所有 `open()` 调用
- [ ] 移除硬编码的编码参数
- [ ] 测试跨平台兼容性
- [ ] 更新文档和注释

## 常见问题

### Q: 为什么要统一编码配置？
A: 统一编码配置可以：
- 确保跨平台兼容性
- 简化代码维护
- 提供一致的错误处理
- 支持多种编码的自动检测

### Q: 如何处理特殊编码的文件？
A: 使用 `read_text_file()` 函数，它会自动尝试多种编码：
```python
from openhands.utils.encoding import read_text_file

# 自动尝试多种编码
content = read_text_file(file_path)
```

### Q: 如何添加新的编码支持？
A: 修改 `encoding_config.py` 中的 `FALLBACK_ENCODINGS` 列表：
```python
FALLBACK_ENCODINGS = [
    'utf-8-sig',
    'latin-1',
    'cp1252',
    'gbk',
    'your-new-encoding',  # 添加新编码
]
```

## 性能考虑

- `safe_read()` 和 `safe_write()` 函数已经优化，性能影响最小
- 编码检测只在第一次失败时进行
- 二进制文件操作不受影响

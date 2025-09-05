# OpenHands Windows Runtime

这个目录包含了OpenHands的Windows容器runtime实现，允许在Windows环境中运行OpenHands的Windows Docker Runtime模式。

## 文件说明

- `Dockerfile.windows` - Windows容器镜像定义文件
- `build-windows-runtime.ps1` - 构建脚本
- `README-Windows.md` - 本说明文件（中文版）
- `README-Windows-EN.md` - 英文版说明文件

## 前置要求

1. **Windows 10/11 企业版或专业版** - 支持Windows容器的版本（**不支持家庭版**，因为Docker Desktop在家庭版上不支持Windows容器）
2. **Docker Desktop** - 启用Windows容器支持
3. **PowerShell 7+** - 用于运行构建脚本和启动服务
4. **.NET Core Runtime** - 用于PowerShell集成
5. **Python 3.12 或 3.13** - 用于运行OpenHands后端
6. **Node.js 和 npm** - 用于构建前端
7. **Poetry** - Python包管理器
8. **Git** - 用于克隆仓库

## 运行OpenHands

### 1. 克隆和设置OpenHands

```powershell
# 克隆包含Windows支持的仓库
git clone https://github.com/All-Hands-AI/OpenHands.git
cd OpenHands

# 切换到Windows支持分支（如果使用分支）
git checkout windows_runtime_docker

# 安装Python依赖
poetry install
```

### 2. 构建前端

```powershell
# 构建前端资源
cd frontend
npm install
npm run build
cd ..
```

### 3. 获取Windows Runtime镜像

#### 方法1：使用预构建镜像（推荐）

```powershell
# 拉取预构建镜像
docker pull shx815666/openhands-windows-runtime:latest

# 重新标记为本地使用的名称
docker tag shx815666/openhands-windows-runtime:latest openhands-windows-runtime:latest
```

#### 方法2：构建Windows Runtime镜像

##### 使用构建脚本（推荐）

```powershell
# 在OpenHands/containers/runtime/目录下运行
.\build-windows-runtime.ps1
```

##### 手动构建

```powershell
# 在OpenHands项目根目录下运行
docker build -f containers/runtime/Dockerfile.windows -t openhands-windows-runtime:latest .
```

### 4. 设置环境变量

```powershell
# 设置Windows Docker runtime
$env:RUNTIME = "windows-docker"
$env:SANDBOX_RUNTIME_CONTAINER_IMAGE = "openhands-windows-runtime:latest"
```

### 5. 启动OpenHands

```powershell
# 启动OpenHands服务
poetry run uvicorn openhands.server.listen:app --host 0.0.0.0 --port 3000 --reload --reload-exclude "./workspace"
```

### 6. 访问应用

打开浏览器访问：`http://localhost:3000`

> **注意**: 如果遇到 `RuntimeError: Directory './frontend/build' does not exist` 错误，请确保你已经按照步骤2构建了前端。

## 技术细节

### 端口配置

Windows runtime使用以下端口范围（与OpenHands DockerRuntime兼容）：

- **执行服务器端口**: 30000-34999
- **VSCode端口**: 35000-39999  
- **应用端口范围1**: 40000-44999
- **应用端口范围2**: 45000-49151

### 环境变量

关键环境变量：

- `POETRY_VIRTUALENVS_PATH`: Poetry虚拟环境路径
- `PYTHON_ROOT`: Python安装路径
- `WORK_DIR`: 工作目录路径
- `OH_INTERPRETER_PATH`: Python解释器路径

### 目录结构

```
C:\openhands\
├── poetry\              # Poetry虚拟环境
├── code\                # 应用代码
├── workspace\           # 工作空间
└── logs\                # 日志文件
```

## Windows Runtime特性

### 与Linux Runtime的区别

1. **基础镜像**: 使用`mcr.microsoft.com/windows/servercore:ltsc2022`
2. **包管理器**: 使用Chocolatey而不是apt
3. **环境管理**: 使用Python + Poetry而不是micromamba
4. **路径分隔符**: 使用反斜杠`\`而不是正斜杠`/`
5. **权限管理**: 使用`icacls`而不是`chmod`
6. **Shell**: 使用PowerShell而不是bash
7. **Runtime类型**: 使用`windows-docker`而不是`docker`

### Windows Runtime类

OpenHands现在包含专门的`WindowsDockerRuntime`类，它：

- 自动处理Windows路径转换
- 使用Windows特定的端口范围
- 支持Windows容器平台
- 提供Windows特定的环境变量
- 优化了Windows容器的启动和配置


## 故障排除

### Windows 容器相关问题

#### Docker 容器启动失败

如果Windows容器无法启动：

**解决方案：**
1. 确保Docker Desktop启用了Windows容器支持
2. 检查Windows版本是否支持容器（**必须是企业版或专业版，家庭版不支持**）
3. 确保有足够的磁盘空间和内存
4. 在Docker Desktop设置中切换到Windows容器模式

#### 前端构建错误

如果遇到 `Directory './frontend/build' does not exist` 错误：

**解决方案：**
1. 确保在项目根目录下
2. 运行前端构建命令：
   ```powershell
   cd frontend
   npm install
   npm run build
   cd ..
   ```

### 通用 Windows 问题

对于其他常见的 Windows 相关问题（如 PowerShell 集成、.NET Core 错误等），请参考官方文档：

**[OpenHands Windows 故障排除指南](https://docs.all-hands.dev/usage/windows-without-wsl#troubleshooting)**

该文档详细介绍了以下问题的解决方案：
- "System.Management.Automation" 未找到错误
- CoreCLR 错误
- PowerShell 7 安装和配置
- .NET Core Runtime 安装
- 其他 Windows 兼容性问题


## 开发说明

### 修改Dockerfile

如果需要修改Windows runtime配置：

1. 编辑`Dockerfile.windows`
2. 重新构建镜像
3. 测试更改

### 添加依赖

在Dockerfile中添加新的依赖：

```dockerfile
# 在适当位置添加
RUN pwsh -Command "choco install <package-name> -y"
```

### 自定义环境变量

在Dockerfile中添加自定义环境变量：

```dockerfile
ENV CUSTOM_VAR=value
```

### 调试容器

进入运行中的容器进行调试：

```powershell
# 查看容器列表
docker ps

# 进入容器
docker exec -it <container-name> pwsh

# 查看容器日志
docker logs <container-name>
```

## 与官方文档的差异

本Windows Runtime实现与[官方Windows文档](https://docs.all-hands.dev/usage/windows-without-wsl)的主要差异：

1. **Runtime类型**: 使用 `windows-docker` 而不是 `local`
2. **容器化**: 在Windows容器中运行，而不是直接在主机上
3. **隔离性**: 提供更好的环境隔离和一致性
4. **部署**: 支持镜像分发和部署

## 贡献

欢迎提交Issue和Pull Request来改进Windows runtime支持。

## 许可证

与OpenHands项目使用相同的许可证。

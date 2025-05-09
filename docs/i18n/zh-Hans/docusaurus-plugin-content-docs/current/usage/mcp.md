# 模型上下文协议 (MCP)

:::note
本页概述了如何在OpenHands中配置和使用模型上下文协议(MCP)，使您能够通过自定义工具扩展代理的功能。
:::

## 概述

模型上下文协议(MCP)是一种允许OpenHands与外部工具服务器通信的机制。这些服务器可以为代理提供额外的功能，如专业数据处理、外部API访问或自定义工具。MCP基于[modelcontextprotocol.io](https://modelcontextprotocol.io)定义的开放标准。

## 配置

MCP配置在`config.toml`文件的`[mcp]`部分中定义。

### 配置示例

```toml
[mcp]
# SSE服务器 - 通过服务器发送事件通信的外部服务器
sse_servers = [
    # 仅有URL的基本SSE服务器
    "http://example.com:8080/mcp",

    # 带API密钥认证的SSE服务器
    {url="https://secure-example.com/mcp", api_key="your-api-key"}
]

# Stdio服务器 - 通过标准输入/输出通信的本地进程
stdio_servers = [
    # 基本stdio服务器
    {name="fetch", command="uvx", args=["mcp-server-fetch"]},

    # 带环境变量的stdio服务器
    {
        name="data-processor",
        command="python",
        args=["-m", "my_mcp_server"],
        env={
            "DEBUG": "true",
            "PORT": "8080"
        }
    }
]
```

## 配置选项

### SSE服务器

SSE服务器可以使用字符串URL或具有以下属性的对象进行配置：

- `url` (必需)
  - 类型: `str`
  - 描述: SSE服务器的URL

- `api_key` (可选)
  - 类型: `str`
  - 默认值: `None`
  - 描述: 用于SSE服务器认证的API密钥

### Stdio服务器

Stdio服务器使用具有以下属性的对象进行配置：

- `name` (必需)
  - 类型: `str`
  - 描述: 服务器的唯一名称

- `command` (必需)
  - 类型: `str`
  - 描述: 运行服务器的命令

- `args` (可选)
  - 类型: `list of str`
  - 默认值: `[]`
  - 描述: 传递给服务器的命令行参数

- `env` (可选)
  - 类型: `dict of str to str`
  - 默认值: `{}`
  - 描述: 为服务器进程设置的环境变量

## MCP工作原理

当OpenHands启动时，它会：

1. 从`config.toml`读取MCP配置
2. 连接到任何已配置的SSE服务器
3. 启动任何已配置的stdio服务器
4. 向代理注册这些服务器提供的工具

然后代理可以像使用任何内置工具一样使用这些工具。当代理调用MCP工具时：

1. OpenHands将调用路由到适当的MCP服务器
2. 服务器处理请求并返回响应
3. OpenHands将响应转换为观察结果并呈现给代理

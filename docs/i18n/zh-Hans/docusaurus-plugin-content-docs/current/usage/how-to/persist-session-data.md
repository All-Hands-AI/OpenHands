以下是翻译后的内容:

# 持久化会话数据

使用标准安装,会话数据存储在内存中。目前,如果 OpenHands 服务重新启动,之前的会话将失效(生成新的密钥),因此无法恢复。

## 如何持久化会话数据

### 开发工作流
在 `config.toml` 文件中,指定以下内容:
```
[core]
...
file_store="local"
file_store_path="/absolute/path/to/openhands/cache/directory"
jwt_secret="secretpass"
```

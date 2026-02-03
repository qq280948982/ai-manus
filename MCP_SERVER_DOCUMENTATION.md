# ai-manus MCP 服务器部署与使用文档

## 项目概述

ai-manus 是一个开源项目，提供了强大的代码执行和沙箱环境管理功能。本文档将详细说明如何将 ai-manus 改造为 MCP（Model Context Protocol）服务器，使其能够通过 MCP 协议为外部应用提供服务。

### MCP 服务器功能

ai-manus MCP 服务器提供以下工具：

- **create_sandbox**：创建一个新的 Docker sandbox 容器
- **exec_command**：在 sandbox 中执行命令
- **file_write**：在 sandbox 中写入文件
- **file_read**：从 sandbox 中读取文件
- **file_delete**：从 sandbox 中删除文件
- **file_list**：列出 sandbox 目录内容

## 部署步骤

### 1. 环境要求

- Docker
- Docker Compose
- Python 3.12+

### 2. 克隆项目

```bash
git clone https://github.com/your-username/ai-manus.git
cd ai-manus
```

### 3. 配置文件

确保 `docker-compose.yml` 文件中包含以下 MCP 服务器配置：

```yaml
mcp-server:
  build:
    context: ./backend
    dockerfile: Dockerfile
  image: simpleyyt/manus-backend:latest
  command: python -m app.infrastructure.external.mcp.run_server
  ports:
    - "8081:8081"
  networks:
    - manus-network
  depends_on:
    - mongodb
    - redis
  environment:
    - MONGODB_URL=mongodb://mongodb:27017/manus
    - REDIS_URL=redis://redis:6379/0
    - DOCKER_HOST=unix:///var/run/docker.sock
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
```

### 4. 构建和启动服务

```bash
docker compose down && docker compose build && docker compose up -d
```

### 5. 验证服务

检查 MCP 服务器是否正常运行：

```bash
docker compose ps
```

输出应显示 `ai-manus-mcp-server-1` 状态为 `Up`。

检查 MCP 服务器日志：

```bash
docker logs ai-manus-mcp-server-1
```

日志应显示服务器已成功启动并运行在 `http://0.0.0.0:8081`。

## MCP 服务器配置

### 1. 服务器端点

MCP 服务器的默认端点为：

```
http://localhost:8081/mcp
```

### 2. 传输协议

ai-manus MCP 服务器支持以下传输协议：

- **streamable-http**：推荐使用，支持流式响应
- **sse**：服务器发送事件

## 使用示例

### 1. 使用 MCP 客户端连接

以下是使用 Python MCP 客户端连接到 ai-manus MCP 服务器的示例：

```python
import asyncio
from mcp.client.streamable_http import streamablehttp_client

async def main():
    # 连接到 MCP 服务器
    async with streamablehttp_client(url="http://localhost:8081/mcp") as transport:
        # 初始化会话
        await transport.initialize()
        
        # 列出可用工具
        tools = await transport.list_tools()
        print("可用工具:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")
        
        # 测试创建 sandbox
        create_result = await transport.call_tool(
            name="create_sandbox",
            arguments={}
        )
        print(f"创建 sandbox 结果: {create_result}")
        
        if create_result.success:
            sandbox_id = create_result.content.get("sandbox_id")
            print(f"Sandbox ID: {sandbox_id}")
            
            # 测试执行命令
            exec_result = await transport.call_tool(
                name="exec_command",
                arguments={
                    "sandbox_id": sandbox_id,
                    "command": "echo 'Hello from MCP server!'",
                    "exec_dir": "/"
                }
            )
            print(f"执行命令结果: {exec_result}")
            
            # 测试写入文件
            write_result = await transport.call_tool(
                name="file_write",
                arguments={
                    "sandbox_id": sandbox_id,
                    "file": "/tmp/test.txt",
                    "content": "This is a test file created via MCP",
                    "append": False
                }
            )
            print(f"写入文件结果: {write_result}")
            
            # 测试读取文件
            read_result = await transport.call_tool(
                name="file_read",
                arguments={
                    "sandbox_id": sandbox_id,
                    "file": "/tmp/test.txt"
                }
            )
            print(f"读取文件结果: {read_result}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. 通过 HTTP 请求使用

以下是使用 curl 命令通过 HTTP 请求与 ai-manus MCP 服务器交互的示例：

```bash
# 初始化会话
curl -X POST http://localhost:8081/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "method": "initialize", "params": {}, "id": 1}'

# 列出可用工具
curl -X POST http://localhost:8081/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "method": "list_tools", "params": {}, "id": 2}'

# 创建 sandbox
curl -X POST http://localhost:8081/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "method": "call_tool", "params": {"name": "create_sandbox", "arguments": {}}, "id": 3}'
```

## 故障排除

### 1. MCP 服务器启动失败

**症状**：`docker compose ps` 显示 `mcp-server` 状态为 `Restarting` 或 `Exited`。

**解决方案**：

- 检查 MCP 服务器日志：`docker logs ai-manus-mcp-server-1`
- 确保 Docker 套接字权限正确：`/var/run/docker.sock`
- 确保所有依赖服务（mongodb、redis）正常运行

### 2. 连接 MCP 服务器失败

**症状**：客户端连接时报错 "Connection refused" 或 "Not Acceptable"。

**解决方案**：

- 确保 MCP 服务器端口 8081 已正确映射并可访问
- 确保客户端请求包含正确的 `Accept` 头：`application/json, text/event-stream`
- 检查网络连接是否正常

### 3. 执行命令失败

**症状**：调用 `exec_command` 工具时报错。

**解决方案**：

- 确保 sandbox 容器已成功创建
- 检查命令格式是否正确
- 检查 sandbox 容器是否正在运行：`docker ps`

### 4. 文件操作失败

**症状**：调用 `file_write`、`file_read` 等工具时报错。

**解决方案**：

- 确保 sandbox 容器已成功创建
- 检查文件路径是否正确
- 检查文件权限是否允许操作

## 常见问题

### 1. MCP 服务器默认端口是什么？

默认端口是 8081，可以在 `docker-compose.yml` 文件中修改。

### 2. 如何查看 MCP 服务器的日志？

使用以下命令：

```bash
docker logs ai-manus-mcp-server-1
```

### 3. 如何重启 MCP 服务器？

使用以下命令：

```bash
docker compose restart mcp-server
```

### 4. MCP 服务器支持哪些传输协议？

支持 `streamable-http` 和 `sse` 传输协议。

## 总结

ai-manus MCP 服务器为外部应用提供了强大的代码执行和沙箱环境管理功能。通过本文档的部署步骤，您可以快速将 ai-manus 改造为 MCP 服务器，并通过 MCP 协议为您的应用提供服务。

如果您在使用过程中遇到任何问题，请参考故障排除部分，或在 GitHub 仓库中提交 issue。
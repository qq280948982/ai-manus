# ai-manus MCP 服务器部署与使用文档

## 项目概述

ai-manus 是一个开源项目，提供了强大的代码执行和沙箱环境管理功能。本文档将详细说明如何将 ai-manus 改造为 MCP（Model Context Protocol）服务器，使其能够通过 MCP 协议为外部应用提供服务。

### MCP 服务器功能

ai-manus MCP 服务器提供以下工具：

#### 🏗️ 沙箱管理工具
- **create_sandbox**：创建一个新的 Docker sandbox 容器
- **exec_command**：在 sandbox 中执行 shell 命令（支持 sudo 权限）

#### 📁 文件操作工具
- **file_write**：在 sandbox 中写入文件内容（支持 sudo 权限）
- **file_read**：从 sandbox 中读取文件内容（支持 sudo 权限）
- **file_delete**：从 sandbox 中删除文件（支持 sudo 权限）
- **file_list**：列出 sandbox 目录内容（支持 sudo 权限）
- **file_search**：在文件中搜索内容（支持正则表达式）
- **file_replace**：替换文件中的字符串内容（支持 sudo 权限）
- **file_find**：根据通配符模式查找文件

#### 🖥️ Shell 会话管理工具
- **shell_view**：查看 shell 会话的输出内容
- **shell_wait**：等待 shell 会话中的进程执行完成
- **shell_write**：向 shell 会话的进程写入输入内容
- **shell_kill**：终止 shell 会话中的进程

#### 🔧 系统服务管理工具
- **supervisor_status**：获取 sandbox 中所有服务的状态信息
- **supervisor_restart**：重启 sandbox 中的所有服务

#### 🌐 浏览器操作工具
- **browser_navigate**：在浏览器中导航到指定网址
- **browser_view**：查看浏览器当前页面的内容和交互元素
- **browser_click**：点击页面元素或指定坐标
- **browser_input**：向页面元素输入文本
- **browser_screenshot**：对当前页面进行截图（返回 base64 编码）
- **browser_scroll**：滚动页面（支持上下滚动和跳转到顶部/底部）
- **browser_console_exec**：在浏览器中执行 JavaScript 代码
- **browser_console_view**：查看浏览器的控制台输出

## 部署步骤

### 1. 环境要求

- Docker 20.10+
- Docker Compose
- 支持的操作系统：Linux、Windows、macOS

### 2. 项目结构

```
ai-manus/
├── backend/                    # 后端服务
│   ├── app/
│   │   └── infrastructure/
│   │       └── external/
│   │           └── mcp/       # MCP 服务器实现
│   │               ├── server.py
│   │               └── run_server.py
│   └── Dockerfile
├── sandbox/                    # 沙箱服务
├── docker-compose.yml          # Docker Compose 配置
└── MCP_SERVER_DOCUMENTATION.md # 本文档
```

### 3. Docker Compose 配置

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
  restart: unless-stopped
  ports:
    - "8081:8081"
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
  networks:
    - manus-network
  env_file:
    - .env
  command: python -m app.infrastructure.external.mcp.run_server
```

### 4. 构建和启动服务

```bash
# 克隆项目（如果尚未克隆）
git clone https://github.com/your-username/ai-manus.git
cd ai-manus

# 构建并启动所有服务
docker compose down && docker compose build && docker compose up -d
```

### 5. 验证服务状态

检查 MCP 服务器是否正常运行：

```bash
# 查看服务状态
docker compose ps

# 检查 MCP 服务器日志
docker logs ai-manus-mcp-server-1

# 测试 MCP 服务器端点
curl -X POST http://localhost:8081/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "method": "initialize", "params": {}, "id": 1}'
```

## MCP 服务器配置

### 1. 服务器端点

MCP 服务器的默认配置：
- **端点**: `http://localhost:8081/mcp`
- **传输协议**: streamable-http（推荐）和 sse
- **主机绑定**: 0.0.0.0:8081
- **安全设置**: 允许所有主机和来源（可根据需要调整）

### 2. 传输协议

ai-manus MCP 服务器支持以下传输协议：
- **streamable-http**: 推荐使用，支持流式响应
- **sse**: 服务器发送事件

### 3. 环境变量

可以通过 `.env` 文件配置以下环境变量：
- `MONGODB_URL`: MongoDB 连接地址
- `REDIS_URL`: Redis 连接地址
- `DOCKER_HOST`: Docker 守护进程地址

## 使用示例

### 1. 基本工作流示例

以下是使用 Python MCP 客户端连接到 ai-manus MCP 服务器的完整示例：

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
        
        # 创建 sandbox
        create_result = await transport.call_tool(
            name="create_sandbox",
            arguments={}
        )
        print(f"创建 sandbox 结果: {create_result}")
        
        if create_result.success:
            sandbox_id = create_result.content.get("sandbox_id")
            print(f"Sandbox ID: {sandbox_id}")
            
            # 执行命令
            exec_result = await transport.call_tool(
                name="exec_command",
                arguments={
                    "sandbox_id": sandbox_id,
                    "command": "echo 'Hello from MCP server!' && pwd",
                    "exec_dir": "/home/ubuntu"
                }
            )
            print(f"执行命令结果: {exec_result}")
            
            # 写入文件
            write_result = await transport.call_tool(
                name="file_write",
                arguments={
                    "sandbox_id": sandbox_id,
                    "file": "/home/ubuntu/test.txt",
                    "content": "This is a test file created via MCP",
                    "append": False
                }
            )
            print(f"写入文件结果: {write_result}")
            
            # 读取文件
            read_result = await transport.call_tool(
                name="file_read",
                arguments={
                    "sandbox_id": sandbox_id,
                    "file": "/home/ubuntu/test.txt"
                }
            )
            print(f"读取文件结果: {read_result}")
            
            # 检查文件是否存在（避免读取不存在的文件）
            exists_result = await transport.call_tool(
                name="file_exists",
                arguments={
                    "sandbox_id": sandbox_id,
                    "file": "/home/ubuntu/test.txt"
                }
            )
            print(f"文件存在检查结果: {exists_result}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. 浏览器自动化示例

```python
# 浏览器导航和截图
navigate_result = await transport.call_tool(
    name="browser_navigate",
    arguments={
        "sandbox_id": sandbox_id,
        "url": "https://www.google.com",
        "timeout_seconds": 10  # 超时时间，单位为秒
    }
)

# 查看页面内容
view_result = await transport.call_tool(
    name="browser_view",
    arguments={"sandbox_id": sandbox_id}
)

# 输入搜索内容
input_result = await transport.call_tool(
    name="browser_input",
    arguments={
        "sandbox_id": sandbox_id,
        "text": "人工智能最新发展",
        "index": 1,  # 搜索框元素索引
        "press_enter": True
    }
)

# 截图保存结果
screenshot_result = await transport.call_tool(
    name="browser_screenshot",
    arguments={
        "sandbox_id": sandbox_id,
        "full_page": True
    }
)
```

### 3. 通过 HTTP 请求使用

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
  -d '{
    "jsonrpc": "2.0", 
    "method": "call_tool", 
    "params": {
      "name": "create_sandbox", 
      "arguments": {}
    }, 
    "id": 3
  }'

# 执行命令
curl -X POST http://localhost:8081/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0", 
    "method": "call_tool", 
    "params": {
      "name": "exec_command", 
      "arguments": {
        "sandbox_id": "sandbox-xxx",
        "command": "ls -la /home/ubuntu",
        "exec_dir": "/home/ubuntu"
      }
    }, 
    "id": 4
  }'
```

## 工具参数说明

### 通用参数约定
- **sandbox_id**: 所有工具都需要此参数，用于指定目标 sandbox
- **sudo**: 文件操作工具支持此参数，用于获取 root 权限
- **路径参数**: 建议使用 `/home/ubuntu/` 目录，避免权限问题

### 文件操作最佳实践
```json
// 推荐的用户目录操作
{
  "sandbox_id": "sandbox-xxx",
  "file": "/home/ubuntu/myfile.txt",
  "content": "文件内容",
  "sudo": false
}

// 系统文件操作（需要 sudo）
{
  "sandbox_id": "sandbox-xxx", 
  "file": "/etc/hosts",
  "content": "系统文件内容",
  "sudo": true
}

// 文件存在性检查（避免读取不存在的文件）
{
  "sandbox_id": "sandbox-xxx",
  "file": "/home/ubuntu/data.json"
}

// 读取文件前先检查是否存在
{
  "tool": "file_exists",
  "args": {
    "sandbox_id": "sandbox-xxx",
    "file": "/home/ubuntu/.cache/chromium/Default/History"
  }
}

// 如果存在再读取
{
  "tool": "file_read", 
  "args": {
    "sandbox_id": "sandbox-xxx",
    "file": "/home/ubuntu/.cache/chromium/Default/History"
  }
}
```

### 浏览器操作工作流
```json
// 1. 首先导航到网站
{
  "tool": "browser_navigate",
  "args": {
    "sandbox_id": "sandbox-xxx",
    "url": "https://example.com",
    "timeout_seconds": 15  // 超时时间，单位为秒
  }
}

// 2. 查看页面获取交互元素
{
  "tool": "browser_view",
  "args": {"sandbox_id": "sandbox-xxx"}
}

// 3. 根据返回的交互元素索引进行操作
{
  "tool": "browser_click",
  "args": {
    "sandbox_id": "sandbox-xxx",
    "index": 2  // 从 browser_view 结果中获取
  }
}
```

### 重要参数说明
⚠️ **timeout_seconds 参数单位是秒，不是毫秒！**
- `browser_navigate` 的 `timeout_seconds` 参数单位是秒，默认15秒
- `shell_wait` 的 `seconds` 参数单位是秒，默认10秒
- 其他工具没有timeout参数

**错误示例（会导致执行上下文被销毁）：**
```json
// ❌ 错误：传入10000会被当作10000秒，导致超时
{
  "tool": "browser_navigate",
  "args": {
    "sandbox_id": "sandbox-xxx",
    "url": "https://example.com",
    "timeout_seconds": 10000
  }
}

// ✅ 正确：传入10表示10秒
{
  "tool": "browser_navigate",
  "args": {
    "sandbox_id": "sandbox-xxx",
    "url": "https://example.com",
    "timeout_seconds": 10
  }
}
```

## 故障排除

### 1. MCP 服务器启动失败

**症状**：`docker compose ps` 显示 `mcp-server` 状态为 `Restarting` 或 `Exited`。

**解决方案**：
- 检查 MCP 服务器日志：`docker logs ai-manus-mcp-server-1`
- 确保 Docker 套接字权限正确：`/var/run/docker.sock`
- 确保所有依赖服务（mongodb、redis）正常运行
- 检查端口 8081 是否被占用

### 2. 连接 MCP 服务器失败

**症状**：客户端连接时报错 "Connection refused" 或 "Not Acceptable"。

**解决方案**：
- 确保 MCP 服务器端口 8081 已正确映射并可访问
- 确保客户端请求包含正确的 `Accept` 头：`application/json, text/event-stream`
- 检查网络连接是否正常
- 验证 MCP 服务器是否正在运行

### 3. Sandbox 创建失败

**症状**：调用 `create_sandbox` 工具时报错。

**解决方案**：
- 检查 Docker 是否正常运行
- 验证 Docker 套接字权限
- 检查系统资源是否充足
- 查看详细的错误日志

### 4. 命令执行失败

**症状**：调用 `exec_command` 工具时报错。

**解决方案**：
- 确保 sandbox 容器已成功创建
- 检查命令格式是否正确
- 验证执行目录是否存在
- 检查是否需要 sudo 权限

### 5. 文件操作失败

**症状**：调用文件操作工具时报错。

**解决方案**：
- 确保文件路径正确且存在（读取时）
- 检查文件权限是否允许操作
- 验证目录是否存在
- 考虑使用 sudo 权限（谨慎使用）

**特殊说明 - 浏览器缓存文件**：
AI有时会尝试读取浏览器缓存文件（如 `/home/ubuntu/.cache/chromium/Default/History`），但这些文件可能不存在或路径不正确。

**推荐做法**：
1. 先使用 `file_exists` 工具检查文件是否存在
2. 如果文件不存在，不要尝试读取
3. 考虑使用其他方式获取浏览器信息（如 `browser_view` 工具）

```python
# 错误做法（会导致文件不存在错误）
read_result = await transport.call_tool(
    name="file_read",
    arguments={
        "sandbox_id": sandbox_id,
        "file": "/home/ubuntu/.cache/chromium/Default/History"  # 可能不存在
    }
)

# 正确做法（先检查再读取）
exists_result = await transport.call_tool(
    name="file_exists", 
    arguments={
        "sandbox_id": sandbox_id,
        "file": "/home/ubuntu/.cache/chromium/Default/History"
    }
)

if exists_result.data.get("exists"):
    read_result = await transport.call_tool(
        name="file_read",
        arguments={
            "sandbox_id": sandbox_id,
            "file": "/home/ubuntu/.cache/chromium/Default/History"
        }
    )
else:
    print("浏览器历史文件不存在，使用 browser_view 获取页面信息")
```

### 6. 浏览器操作失败

**症状**：浏览器相关工具报错。

**解决方案**：
- 确保 sandbox 中的 Chrome 服务正常运行
- 检查目标网站是否可访问
- 验证元素索引是否正确
- 考虑增加操作等待时间

## 性能优化建议

### 1. Sandbox 生命周期管理
- 及时销毁不再使用的 sandbox 容器
- 合理复用现有的 sandbox
- 监控资源使用情况

### 2. 错误处理
- 实现重试机制
- 添加适当的超时设置
- 记录详细的错误日志

### 3. 安全配置
- 限制可访问的 URL 范围
- 控制文件系统访问权限
- 监控异常行为

## 常见问题

### 1. MCP 服务器默认端口是什么？

默认端口是 8081，可以在 `docker-compose.yml` 文件中修改端口映射。

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

支持 `streamable-http`（推荐）和 `sse`（服务器发送事件）传输协议。

### 5. 如何限制 sandbox 的资源使用？

可以通过 Docker 配置限制 CPU、内存等资源，在创建 sandbox 时设置相关参数。

### 6. 浏览器操作支持哪些功能？

支持导航、点击、输入、截图、滚动、JavaScript 执行等完整的浏览器自动化功能。

## 更新日志

### v2.0.0 (当前版本)
- ✅ 新增浏览器操作工具（8个工具）
- ✅ 新增文件搜索、替换、查找工具
- ✅ 新增 Shell 会话管理工具
- ✅ 新增系统服务管理工具
- ✅ 增强错误处理和参数验证
- ✅ 支持 sudo 权限操作
- ✅ 改进跨平台兼容性

### v1.0.0
- ✅ 基础 sandbox 管理
- ✅ 文件读写操作
- ✅ 命令执行功能

## 总结

ai-manus MCP 服务器现在提供了完整的功能集，包括：

- **沙箱环境管理**：创建、销毁、资源管理
- **文件系统操作**：读写、搜索、替换、权限管理
- **Shell 命令执行**：交互式会话、进程管理
- **浏览器自动化**：导航、交互、截图、JavaScript 执行
- **系统服务管理**：状态监控、服务重启

通过本文档的部署步骤和使用指南，您可以充分利用 ai-manus MCP 服务器的强大功能，为您的 AI 应用提供安全、可靠的代码执行环境。

如果您在使用过程中遇到任何问题，请参考故障排除部分，或在项目 GitHub 仓库中提交 issue。
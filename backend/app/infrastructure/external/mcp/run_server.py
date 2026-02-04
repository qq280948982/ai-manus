import uvicorn
from app.infrastructure.external.mcp.server import ManusMCPServer

# 创建 MCP 服务器实例
manus_mcp_server = ManusMCPServer()
mcp_server = manus_mcp_server.get_server()

# 获取 ASGI 应用
app = mcp_server.streamable_http_app

if __name__ == "__main__":
    # 使用 uvicorn 运行 ASGI 应用
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8081,
        reload=False,
        forwarded_allow_ips="*",
        log_level="debug"
    )

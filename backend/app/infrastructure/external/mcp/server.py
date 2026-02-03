import logging
from typing import Dict, Any, List
from mcp.server import FastMCP
from mcp.types import Tool, CallToolResult
from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class ManusMCPServer:
    """ai-manus MCP 服务器实现"""
    
    def __init__(self):
        self.server = FastMCP(name="ai-manus")
        self._register_tools()
    
    def _register_tools(self):
        """注册 MCP 工具"""
        # 注册 sandbox 相关工具
        self.server.add_tool(
            fn=self._handle_create_sandbox,
            name="create_sandbox",
            description="创建一个新的 Docker sandbox 容器"
        )
        
        self.server.add_tool(
            fn=self._handle_exec_command,
            name="exec_command",
            description="在 sandbox 中执行命令"
        )
        
        self.server.add_tool(
            fn=self._handle_file_write,
            name="file_write",
            description="在 sandbox 中写入文件"
        )
        
        self.server.add_tool(
            fn=self._handle_file_read,
            name="file_read",
            description="从 sandbox 中读取文件"
        )
        
        self.server.add_tool(
            fn=self._handle_file_delete,
            name="file_delete",
            description="从 sandbox 中删除文件"
        )
        
        self.server.add_tool(
            fn=self._handle_file_list,
            name="file_list",
            description="列出 sandbox 目录内容"
        )
    
    async def _handle_create_sandbox(self, arguments: Dict[str, Any]) -> CallToolResult:
        """处理创建 sandbox 请求"""
        try:
            sandbox = await DockerSandbox.create()
            await sandbox.ensure_sandbox()
            
            return CallToolResult(
                success=True,
                data={
                    "sandbox_id": sandbox.id,
                    "ip_address": sandbox.ip,
                    "status": "created"
                }
            )
        except Exception as e:
            logger.error(f"创建 sandbox 失败: {e}")
            return CallToolResult(
                success=False,
                message=f"创建 sandbox 失败: {str(e)}"
            )
    
    async def _handle_exec_command(self, arguments: Dict[str, Any]) -> CallToolResult:
        """处理执行命令请求"""
        try:
            sandbox_id = arguments.get("sandbox_id")
            command = arguments.get("command")
            exec_dir = arguments.get("exec_dir", "/")
            
            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.exec_command(sandbox_id, exec_dir, command)
            
            return CallToolResult(
                success=result.success,
                data=result.data,
                message=result.message
            )
        except Exception as e:
            logger.error(f"执行命令失败: {e}")
            return CallToolResult(
                success=False,
                message=f"执行命令失败: {str(e)}"
            )
    
    async def _handle_file_write(self, arguments: Dict[str, Any]) -> CallToolResult:
        """处理文件写入请求"""
        try:
            sandbox_id = arguments.get("sandbox_id")
            file = arguments.get("file")
            content = arguments.get("content")
            append = arguments.get("append", False)
            
            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.file_write(
                file=file,
                content=content,
                append=append
            )
            
            return CallToolResult(
                success=result.success,
                data=result.data,
                message=result.message
            )
        except Exception as e:
            logger.error(f"写入文件失败: {e}")
            return CallToolResult(
                success=False,
                message=f"写入文件失败: {str(e)}"
            )
    
    async def _handle_file_read(self, arguments: Dict[str, Any]) -> CallToolResult:
        """处理文件读取请求"""
        try:
            sandbox_id = arguments.get("sandbox_id")
            file = arguments.get("file")
            
            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.file_read(file=file)
            
            return CallToolResult(
                success=result.success,
                data=result.data,
                message=result.message
            )
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            return CallToolResult(
                success=False,
                message=f"读取文件失败: {str(e)}"
            )
    
    async def _handle_file_delete(self, arguments: Dict[str, Any]) -> CallToolResult:
        """处理文件删除请求"""
        try:
            sandbox_id = arguments.get("sandbox_id")
            file = arguments.get("file")
            
            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.file_delete(path=file)
            
            return CallToolResult(
                success=result.success,
                data=result.data,
                message=result.message
            )
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return CallToolResult(
                success=False,
                message=f"删除文件失败: {str(e)}"
            )
    
    async def _handle_file_list(self, arguments: Dict[str, Any]) -> CallToolResult:
        """处理目录列表请求"""
        try:
            sandbox_id = arguments.get("sandbox_id")
            path = arguments.get("path")
            
            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.file_list(path=path)
            
            return CallToolResult(
                success=result.success,
                data=result.data,
                message=result.message
            )
        except Exception as e:
            logger.error(f"列出目录失败: {e}")
            return CallToolResult(
                success=False,
                message=f"列出目录失败: {str(e)}"
            )
    
    def get_server(self):
        """获取 MCP 服务器实例"""
        return self.server

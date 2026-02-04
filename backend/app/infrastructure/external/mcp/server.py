import logging
import json
from typing import Dict, Any, List, Optional
from mcp.server import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import Tool, CallToolResult, TextContent
from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ManusMCPServer:
    """ai-manus MCP 服务器实现"""

    def __init__(self):
        # 配置传输安全设置，允许来自任何主机的请求
        transport_security = TransportSecuritySettings(
            enable_dns_rebinding_protection=False,
            allowed_hosts=["*"],
            allowed_origins=["*"]
        )

        self.server = FastMCP(
            name="ai-manus",
            transport_security=transport_security
        )
        self._register_tools()

    def _register_tools(self):
        """注册 MCP 工具"""
        # 注册 sandbox 相关工具
        self.server.add_tool(
            fn=self._handle_create_sandbox,
            name="create_sandbox",
            description="创建一个新的 Docker sandbox 容器，返回 sandbox_id 和 IP 地址"
        )

        self.server.add_tool(
            fn=self._handle_exec_command,
            name="exec_command",
            description="在指定的 sandbox 容器中执行 shell 命令。支持 sudo 权限执行系统命令"
        )

        self.server.add_tool(
            fn=self._handle_file_write,
            name="file_write",
            description="在指定的 sandbox 容器中写入文件内容。建议使用用户主目录 /home/ubuntu/ 或 /tmp/，避免使用根目录 /"
        )

        self.server.add_tool(
            fn=self._handle_file_read,
            name="file_read",
            description="从指定的 sandbox 容器中读取文件内容。支持 sudo 权限读取系统文件"
        )

        self.server.add_tool(
            fn=self._handle_file_delete,
            name="file_delete",
            description="从指定的 sandbox 容器中删除文件。支持 sudo 权限删除系统文件"
        )

        self.server.add_tool(
            fn=self._handle_file_list,
            name="file_list",
            description="列出指定 sandbox 容器中目录的内容。支持 sudo 权限列出系统目录"
        )

    def _create_success_result(self, data: Dict[str, Any]) -> CallToolResult:
        """创建成功的 CallToolResult"""
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(data, ensure_ascii=False)
                )
            ],
            isError=False
        )

    def _create_error_result(self, message: str) -> CallToolResult:
        """创建错误的 CallToolResult"""
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps({"error": message}, ensure_ascii=False)
                )
            ],
            isError=True
        )

    async def _handle_create_sandbox(self) -> CallToolResult:
        """
        创建一个新的 Docker sandbox 容器
        
        参数: 无
        
        返回:
            - sandbox_id: 创建的 sandbox 唯一标识符
            - ip_address: sandbox 容器的 IP 地址
            - status: 创建状态
        """
        try:
            sandbox = await DockerSandbox.create()
            await sandbox.ensure_sandbox()

            return self._create_success_result({
                "sandbox_id": sandbox.id,
                "ip_address": sandbox.ip,
                "status": "created",
                "user": "ubuntu",
                "home_dir": "/home/ubuntu",
                "note": "默认用户: ubuntu, 默认工作目录: /home/ubuntu, 所有工具支持 sudo 参数"
            })
        except Exception as e:
            logger.error(f"创建 sandbox 失败: {e}")
            return self._create_error_result(f"创建 sandbox 失败: {str(e)}")

    async def _handle_exec_command(
        self,
        sandbox_id: str,
        command: str,
        exec_dir: str = "/home/ubuntu",
        sudo: bool = False
    ) -> CallToolResult:
        """
        在指定的 sandbox 容器中执行 shell 命令
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
            - command (必填): 要执行的 shell 命令
            - exec_dir (选填): 执行命令的工作目录，默认为 "/home/ubuntu"
            - sudo (选填): 是否使用 sudo 权限执行命令，默认为 false
        
        返回:
            - success: 是否执行成功
            - data: 命令执行的输出结果
            - message: 执行结果的详细信息
        """
        try:
            if not sandbox_id or sandbox_id.strip() == "":
                return self._create_error_result("缺少 sandbox_id 参数，sandbox ID 不能为空")
            if not command or command.strip() == "":
                return self._create_error_result("缺少 command 参数，命令不能为空")

            sandbox = await DockerSandbox.get(sandbox_id)
            # 如果需要 sudo，用 shell 包裹整个命令，避免引号转义问题
            if sudo:
                actual_command = f"sudo sh -c {json.dumps(command)}"
            else:
                actual_command = command
            # 使用 sandbox.id 作为 session_id 调用 exec_command
            result = await sandbox.exec_command(sandbox.id, exec_dir, actual_command)

            if result.success:
                return self._create_success_result({
                    "success": True,
                    "data": result.data,
                    "message": result.message
                })
            else:
                return self._create_error_result(result.message or "执行命令失败")
        except Exception as e:
            logger.error(f"执行命令失败: {e}")
            return self._create_error_result(f"执行命令失败: {str(e)}")

    async def _handle_file_write(
        self,
        sandbox_id: str,
        file: str,
        content: str,
        append: bool = False,
        sudo: bool = False
    ) -> CallToolResult:
        """
        在指定的 sandbox 容器中写入文件内容
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
            - file (必填): 要写入的文件路径，建议使用用户主目录 /home/ubuntu/ 或 /tmp/
            - content (必填): 要写入的文件内容
            - append (选填): 是否在文件末尾追加内容，默认为 false（覆盖写入）
            - sudo (选填): 是否使用 sudo 权限写入，默认为 false
        
        返回:
            - success: 是否写入成功
            - data: 写入操作的详细信息
            - message: 操作结果的描述
        """
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not file or file.strip() == "":
                return self._create_error_result("缺少 file 参数，文件路径不能为空")
            if content is None:
                return self._create_error_result("缺少 content 参数")

            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.file_write(
                file=file,
                content=content,
                append=append,
                sudo=sudo
            )

            if result.success:
                return self._create_success_result({
                    "success": True,
                    "data": result.data,
                    "message": result.message
                })
            else:
                return self._create_error_result(result.message or "写入文件失败")
        except Exception as e:
            logger.error(f"写入文件失败: {e}")
            return self._create_error_result(f"写入文件失败: {str(e)}")

    async def _handle_file_read(
        self,
        sandbox_id: str,
        file: str,
        sudo: bool = False
    ) -> CallToolResult:
        """
        从指定的 sandbox 容器中读取文件内容
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
            - file (必填): 要读取的文件路径
            - sudo (选填): 是否使用 sudo 权限读取文件，默认为 false
        
        返回:
            - success: 是否读取成功
            - data: 文件内容
            - message: 操作结果的描述
        """
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not file or file.strip() == "":
                return self._create_error_result("缺少 file 参数，文件路径不能为空")

            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.file_read(file=file, sudo=sudo)

            if result.success:
                return self._create_success_result({
                    "success": True,
                    "data": result.data,
                    "message": result.message
                })
            else:
                return self._create_error_result(result.message or "读取文件失败")
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            return self._create_error_result(f"读取文件失败: {str(e)}")

    async def _handle_file_delete(
        self,
        sandbox_id: str,
        file: str,
        sudo: bool = False
    ) -> CallToolResult:
        """
        从指定的 sandbox 容器中删除文件
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
            - file (必填): 要删除的文件路径
            - sudo (选填): 是否使用 sudo 权限删除文件，默认为 false
        
        返回:
            - success: 是否删除成功
            - data: 删除操作的详细信息
            - message: 操作结果的描述
        """
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not file or file.strip() == "":
                return self._create_error_result("缺少 file 参数，文件路径不能为空")

            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.file_delete(path=file, sudo=sudo)

            if result.success:
                return self._create_success_result({
                    "success": True,
                    "data": result.data,
                    "message": result.message
                })
            else:
                return self._create_error_result(result.message or "删除文件失败")
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return self._create_error_result(f"删除文件失败: {str(e)}")

    async def _handle_file_list(
        self,
        sandbox_id: str,
        path: str,
        sudo: bool = False
    ) -> CallToolResult:
        """
        列出指定 sandbox 容器中目录的内容
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
            - path (必填): 要列出的目录路径
            - sudo (选填): 是否使用 sudo 权限列出目录，默认为 false
        
        返回:
            - success: 是否列出成功
            - data: 目录内容列表
            - message: 操作结果的描述
        """
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not path or path.strip() == "":
                return self._create_error_result("缺少 path 参数，目录路径不能为空")

            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.file_list(path=path, sudo=sudo)

            if result.success:
                return self._create_success_result({
                    "success": True,
                    "data": result.data,
                    "message": result.message
                })
            else:
                return self._create_error_result(result.message or "列出目录失败")
        except Exception as e:
            logger.error(f"列出目录失败: {e}")
            return self._create_error_result(f"列出目录失败: {str(e)}")

    def get_server(self):
        """获取 MCP 服务器实例"""
        return self.server

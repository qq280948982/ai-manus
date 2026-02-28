import logging
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from mcp.server import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, TextContent
from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
from app.core.config import get_settings

logger = logging.getLogger(__name__)


# ============ 工具参数模型定义 ============

class CreateSandboxParams(BaseModel):
    """创建 sandbox 参数"""
    pass


class ExecCommandParams(BaseModel):
    """执行命令参数"""
    sandbox_id: str = Field(..., description="sandbox 容器的唯一标识符")
    command: str = Field(..., description="要执行的 shell 命令")
    exec_dir: str = Field(default="/home/ubuntu", description="执行命令的工作目录，默认为 /home/ubuntu")
    sudo: bool = Field(default=False, description="是否使用 sudo 权限执行命令，默认为 false")


class FileWriteParams(BaseModel):
    """写入文件参数"""
    sandbox_id: str = Field(..., description="sandbox 容器的唯一标识符")
    file: str = Field(..., description="要写入的文件路径，建议使用用户主目录 /home/ubuntu/ 或 /tmp/")
    content: str = Field(..., description="要写入的文件内容")
    append: bool = Field(default=False, description="是否在文件末尾追加内容，默认为 false（覆盖写入）")
    sudo: bool = Field(default=False, description="是否使用 sudo 权限写入，默认为 false")


class FileReadParams(BaseModel):
    """读取文件参数"""
    sandbox_id: str = Field(..., description="sandbox 容器的唯一标识符")
    file: str = Field(..., description="要读取的文件路径")
    sudo: bool = Field(default=False, description="是否使用 sudo 权限读取文件，默认为 false")


class FileExistsParams(BaseModel):
    """检查文件是否存在参数"""
    sandbox_id: str = Field(..., description="sandbox 容器的唯一标识符")
    file: str = Field(..., description="要检查的文件路径")
    sudo: bool = Field(default=False, description="是否使用 sudo 权限检查文件，默认为 false")


class FileDeleteParams(BaseModel):
    """删除文件参数"""
    sandbox_id: str = Field(..., description="sandbox 容器的唯一标识符")
    file: str = Field(..., description="要删除的文件路径")
    sudo: bool = Field(default=False, description="是否使用 sudo 权限删除文件，默认为 false")


class FileListParams(BaseModel):
    """列出目录参数"""
    sandbox_id: str = Field(..., description="sandbox 容器的唯一标识符")
    path: str = Field(..., description="要列出的目录路径")
    sudo: bool = Field(default=False, description="是否使用 sudo 权限列出目录，默认为 false")


class FileSearchParams(BaseModel):
    """搜索文件内容参数"""
    sandbox_id: str = Field(..., description="sandbox 容器的唯一标识符")
    file: str = Field(..., description="要搜索的文件路径")
    regex: str = Field(..., description="正则表达式搜索模式")
    sudo: bool = Field(default=False, description="是否使用 sudo 权限搜索文件，默认为 false")


class FileReplaceParams(BaseModel):
    """替换文件内容参数"""
    sandbox_id: str = Field(..., description="sandbox 容器的唯一标识符")
    file: str = Field(..., description="要替换的文件路径")
    old_str: str = Field(..., description="要被替换的字符串")
    new_str: str = Field(..., description="替换后的新字符串")
    sudo: bool = Field(default=False, description="是否使用 sudo 权限修改文件，默认为 false")


class FileFindParams(BaseModel):
    """查找文件参数"""
    sandbox_id: str = Field(..., description="sandbox 容器的唯一标识符")
    path: str = Field(..., description="要查找的目录路径")
    glob_pattern: str = Field(..., description="通配符模式，如 *.py, test*, 等等")


class ShellViewParams(BaseModel):
    """查看 shell 会话参数"""
    sandbox_id: str = Field(..., description="sandbox 容器的唯一标识符")
    session_id: str = Field(..., description="shell 会话的唯一标识符")
    console: bool = Field(default=False, description="是否只查看控制台输出，默认为 false")


class ShellWaitParams(BaseModel):
    """等待进程参数"""
    sandbox_id: str = Field(..., description="sandbox 容器的唯一标识符")
    session_id: str = Field(..., description="shell 会话的唯一标识符")
    seconds: Optional[int] = Field(default=None, description="超时时间（秒），默认为 null（无限等待）")


class ShellWriteParams(BaseModel):
    """向进程写入参数"""
    sandbox_id: str = Field(..., description="sandbox 容器的唯一标识符")
    session_id: str = Field(..., description="shell 会话的唯一标识符")
    input: str = Field(..., description="要写入的输入文本")
    press_enter: bool = Field(default=True, description="是否在写入后按回车，默认为 true")


class ShellKillParams(BaseModel):
    """终止进程参数"""
    sandbox_id: str = Field(..., description="sandbox 容器的唯一标识符")
    session_id: str = Field(..., description="shell 会话的唯一标识符")


class SupervisorStatusParams(BaseModel):
    """获取服务状态参数"""
    sandbox_id: str = Field(..., description="sandbox 容器的唯一标识符")


class SupervisorRestartParams(BaseModel):
    """重启服务参数"""
    sandbox_id: str = Field(..., description="sandbox 容器的唯一标识符")


class BrowserNavigateParams(BaseModel):
    """浏览器导航参数"""
    sandbox_id: str = Field(..., description="sandbox 容器的唯一标识符")
    url: str = Field(..., description="要导航到的网址 URL")
    timeout_seconds: int = Field(default=15, description="超时时间（秒），默认为 15 秒")


class BrowserViewParams(BaseModel):
    """查看浏览器页面参数"""
    sandbox_id: str = Field(..., description="sandbox 容器的唯一标识符")


class BrowserClickParams(BaseModel):
    """浏览器点击参数"""
    sandbox_id: str = Field(..., description="sandbox 容器的唯一标识符")
    index: Optional[int] = Field(default=None, description="要点击的交互元素索引")
    x: Optional[int] = Field(default=None, description="点击的 X 坐标")
    y: Optional[int] = Field(default=None, description="点击的 Y 坐标")


class BrowserInputParams(BaseModel):
    """浏览器输入参数"""
    sandbox_id: str = Field(..., description="sandbox 容器的唯一标识符")
    index: int = Field(..., description="要输入的交互元素索引")
    content: str = Field(..., description="要输入的文本内容")
    submit: bool = Field(default=False, description="是否在输入后提交表单，默认为 false")


class BrowserScreenshotParams(BaseModel):
    """浏览器截图参数"""
    sandbox_id: str = Field(..., description="sandbox 容器的唯一标识符")


class BrowserScrollParams(BaseModel):
    """浏览器滚动参数"""
    sandbox_id: str = Field(..., description="sandbox 容器的唯一标识符")
    direction: str = Field(default="down", description="滚动方向，可选值: up, down, left, right，默认为 down")
    distance: int = Field(default=300, description="滚动距离（像素），默认为 300")


class BrowserConsoleExecParams(BaseModel):
    """执行 JavaScript 参数"""
    sandbox_id: str = Field(..., description="sandbox 容器的唯一标识符")
    script: str = Field(..., description="要执行的 JavaScript 代码")


class BrowserConsoleViewParams(BaseModel):
    """查看控制台输出参数"""
    sandbox_id: str = Field(..., description="sandbox 容器的唯一标识符")


def _build_input_schema(model_class: type[BaseModel]) -> dict:
    """从 Pydantic 模型构建符合 MCP 规范的 inputSchema"""
    schema = model_class.model_json_schema()
    return {
        "type": "object",
        "properties": schema.get("properties", {}),
        "required": schema.get("required", [])
    }


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
        """注册 MCP 工具 - 使用 add_tool 后修改 parameters"""
        tool_manager = self.server._tool_manager

        # 1. create_sandbox - 无参数
        tool = tool_manager.add_tool(
            fn=self._handle_create_sandbox,
            name="create_sandbox",
            title="创建 Sandbox",
            description="创建一个新的 Docker sandbox 容器，返回 sandbox_id 和 IP 地址"
        )
        tool.parameters = {"type": "object", "properties": {}, "required": []}

        # 2. exec_command
        tool = tool_manager.add_tool(
            fn=self._handle_exec_command,
            name="exec_command",
            title="执行命令",
            description="在指定的 sandbox 容器中执行 shell 命令。支持 sudo 权限执行系统命令"
        )
        tool.parameters = _build_input_schema(ExecCommandParams)

        # 3. file_write
        tool = tool_manager.add_tool(
            fn=self._handle_file_write,
            name="file_write",
            title="写入文件",
            description="在指定的 sandbox 容器中写入文件内容。建议使用用户主目录 /home/ubuntu/ 或 /tmp/，避免使用根目录 /"
        )
        tool.parameters = _build_input_schema(FileWriteParams)

        # 4. file_read
        tool = tool_manager.add_tool(
            fn=self._handle_file_read,
            name="file_read",
            title="读取文件",
            description="从指定的 sandbox 容器中读取文件内容。支持 sudo 权限读取系统文件"
        )
        tool.parameters = _build_input_schema(FileReadParams)

        # 5. file_exists
        tool = tool_manager.add_tool(
            fn=self._handle_file_exists,
            name="file_exists",
            title="检查文件存在",
            description="检查指定的 sandbox 容器中文件是否存在。支持 sudo 权限检查系统文件"
        )
        tool.parameters = _build_input_schema(FileExistsParams)

        # 6. file_delete
        tool = tool_manager.add_tool(
            fn=self._handle_file_delete,
            name="file_delete",
            title="删除文件",
            description="从指定的 sandbox 容器中删除文件。支持 sudo 权限删除系统文件"
        )
        tool.parameters = _build_input_schema(FileDeleteParams)

        # 7. file_list
        tool = tool_manager.add_tool(
            fn=self._handle_file_list,
            name="file_list",
            title="列出目录",
            description="列出指定 sandbox 容器中目录的内容。支持 sudo 权限列出系统目录"
        )
        tool.parameters = _build_input_schema(FileListParams)

        # 8. file_search
        tool = tool_manager.add_tool(
            fn=self._handle_file_search,
            name="file_search",
            title="搜索文件内容",
            description="在指定的 sandbox 容器文件中搜索内容。支持正则表达式搜索"
        )
        tool.parameters = _build_input_schema(FileSearchParams)

        # 9. file_replace
        tool = tool_manager.add_tool(
            fn=self._handle_file_replace,
            name="file_replace",
            title="替换文件内容",
            description="在指定的 sandbox 容器文件中替换字符串内容。支持 sudo 权限修改系统文件"
        )
        tool.parameters = _build_input_schema(FileReplaceParams)

        # 10. file_find
        tool = tool_manager.add_tool(
            fn=self._handle_file_find,
            name="file_find",
            title="查找文件",
            description="在指定的 sandbox 容器目录中根据模式查找文件。支持通配符模式"
        )
        tool.parameters = _build_input_schema(FileFindParams)

        # 11. shell_view
        tool = tool_manager.add_tool(
            fn=self._handle_shell_view,
            name="shell_view",
            title="查看 Shell 输出",
            description="查看指定 sandbox 容器 shell 会话的输出内容。可以查看控制台输出"
        )
        tool.parameters = _build_input_schema(ShellViewParams)

        # 12. shell_wait
        tool = tool_manager.add_tool(
            fn=self._handle_shell_wait,
            name="shell_wait",
            title="等待进程",
            description="等待指定 sandbox 容器 shell 会话中的进程执行完成"
        )
        tool.parameters = _build_input_schema(ShellWaitParams)

        # 13. shell_write
        tool = tool_manager.add_tool(
            fn=self._handle_shell_write,
            name="shell_write",
            title="写入进程输入",
            description="向指定 sandbox 容器 shell 会话的进程写入输入内容。可以模拟用户输入"
        )
        tool.parameters = _build_input_schema(ShellWriteParams)

        # 14. shell_kill
        tool = tool_manager.add_tool(
            fn=self._handle_shell_kill,
            name="shell_kill",
            title="终止进程",
            description="终止指定 sandbox 容器 shell 会话中的进程"
        )
        tool.parameters = _build_input_schema(ShellKillParams)

        # 15. supervisor_status
        tool = tool_manager.add_tool(
            fn=self._handle_supervisor_status,
            name="supervisor_status",
            title="获取服务状态",
            description="获取指定 sandbox 容器中所有服务的状态信息"
        )
        tool.parameters = _build_input_schema(SupervisorStatusParams)

        # 16. supervisor_restart
        tool = tool_manager.add_tool(
            fn=self._handle_supervisor_restart,
            name="supervisor_restart",
            title="重启服务",
            description="重启指定 sandbox 容器中的所有服务"
        )
        tool.parameters = _build_input_schema(SupervisorRestartParams)

        # 17. browser_navigate
        tool = tool_manager.add_tool(
            fn=self._handle_browser_navigate,
            name="browser_navigate",
            title="浏览器导航",
            description="在 sandbox 容器的浏览器中导航到指定网址。timeout_seconds 参数单位为秒，默认15秒"
        )
        tool.parameters = _build_input_schema(BrowserNavigateParams)

        # 18. browser_view
        tool = tool_manager.add_tool(
            fn=self._handle_browser_view,
            name="browser_view",
            title="查看浏览器页面",
            description="查看 sandbox 容器浏览器当前页面的内容和交互元素"
        )
        tool.parameters = _build_input_schema(BrowserViewParams)

        # 19. browser_click
        tool = tool_manager.add_tool(
            fn=self._handle_browser_click,
            name="browser_click",
            title="浏览器点击",
            description="在 sandbox 容器浏览器中点击页面元素或指定坐标"
        )
        tool.parameters = _build_input_schema(BrowserClickParams)

        # 20. browser_input
        tool = tool_manager.add_tool(
            fn=self._handle_browser_input,
            name="browser_input",
            title="浏览器输入",
            description="在 sandbox 容器浏览器中向页面元素输入文本"
        )
        tool.parameters = _build_input_schema(BrowserInputParams)

        # 21. browser_screenshot
        tool = tool_manager.add_tool(
            fn=self._handle_browser_screenshot,
            name="browser_screenshot",
            title="浏览器截图",
            description="对 sandbox 容器浏览器当前页面进行截图"
        )
        tool.parameters = _build_input_schema(BrowserScreenshotParams)

        # 22. browser_scroll
        tool = tool_manager.add_tool(
            fn=self._handle_browser_scroll,
            name="browser_scroll",
            title="浏览器滚动",
            description="在 sandbox 容器浏览器中滚动页面"
        )
        tool.parameters = _build_input_schema(BrowserScrollParams)

        # 23. browser_console_exec
        tool = tool_manager.add_tool(
            fn=self._handle_browser_console_exec,
            name="browser_console_exec",
            title="执行 JavaScript",
            description="在 sandbox 容器浏览器中执行 JavaScript 代码"
        )
        tool.parameters = _build_input_schema(BrowserConsoleExecParams)

        # 24. browser_console_view
        tool = tool_manager.add_tool(
            fn=self._handle_browser_console_view,
            name="browser_console_view",
            title="查看控制台输出",
            description="查看 sandbox 容器浏览器的控制台输出"
        )
        tool.parameters = _build_input_schema(BrowserConsoleViewParams)

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
        """创建一个新的 Docker sandbox 容器"""
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
        """在指定的 sandbox 容器中执行 shell 命令"""
        try:
            if not sandbox_id or sandbox_id.strip() == "":
                return self._create_error_result("缺少 sandbox_id 参数，sandbox ID 不能为空")
            if not command or command.strip() == "":
                return self._create_error_result("缺少 command 参数，命令不能为空")

            sandbox = await DockerSandbox.get(sandbox_id)
            if sudo:
                actual_command = f"sudo sh -c {json.dumps(command)}"
            else:
                actual_command = command
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
        """在指定的 sandbox 容器中写入文件内容"""
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
        """从指定的 sandbox 容器中读取文件内容"""
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

    async def _handle_file_exists(
        self,
        sandbox_id: str,
        file: str,
        sudo: bool = False
    ) -> CallToolResult:
        """检查指定的 sandbox 容器中文件是否存在"""
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not file or file.strip() == "":
                return self._create_error_result("缺少 file 参数，文件路径不能为空")

            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.file_exists(file=file)

            if result.success:
                exists = result.data.get("exists", False) if isinstance(result.data, dict) else False
                return self._create_success_result({
                    "success": True,
                    "data": {"exists": exists},
                    "message": f"文件 {file} {'存在' if exists else '不存在'}"
                })
            else:
                return self._create_error_result(result.message or "检查文件失败")
        except Exception as e:
            logger.error(f"检查文件失败: {e}")
            return self._create_error_result(f"检查文件失败: {str(e)}")

    async def _handle_file_delete(
        self,
        sandbox_id: str,
        file: str,
        sudo: bool = False
    ) -> CallToolResult:
        """从指定的 sandbox 容器中删除文件"""
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not file or file.strip() == "":
                return self._create_error_result("缺少 file 参数，文件路径不能为空")

            command = f"rm -f '{file}'"
            if sudo:
                command = f"sudo {command}"

            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.exec_command(sandbox.id, "/", command)

            if result.success:
                return self._create_success_result({
                    "success": True,
                    "message": "文件删除成功"
                })
            else:
                return self._create_error_result(f"删除文件失败: {result.message or '未知错误'}")
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return self._create_error_result(f"删除文件失败: {str(e)}")

    async def _handle_file_list(
        self,
        sandbox_id: str,
        path: str,
        sudo: bool = False
    ) -> CallToolResult:
        """列出指定 sandbox 容器中目录的内容"""
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not path or path.strip() == "":
                return self._create_error_result("缺少 path 参数，目录路径不能为空")

            command = f"ls -la '{path}'"
            if sudo:
                command = f"sudo {command}"

            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.exec_command(sandbox.id, "/", command)

            if result.success:
                command_output = result.data.get("output", "") if isinstance(result.data, dict) else ""
                if not command_output:
                    return self._create_success_result({
                        "success": True,
                        "data": [],
                        "message": "目录为空"
                    })

                entries = []
                lines = command_output.strip().split('\n')
                for line in lines[1:] if len(lines) > 1 else lines:
                    line = line.strip()
                    if not line or line.startswith('total'):
                        continue
                    parts = line.split()
                    if len(parts) >= 9:
                        permissions = parts[0]
                        name = parts[8]
                        if name in ['.', '..']:
                            continue
                        file_type = "directory" if permissions.startswith('d') else "file"
                        size = parts[4] if len(parts) > 4 else "0"
                        modified = " ".join(parts[5:8]) if len(parts) > 8 else ""
                        entries.append({
                            "name": name,
                            "type": file_type,
                            "size": size,
                            "permissions": permissions,
                            "modified": modified
                        })

                return self._create_success_result({
                    "success": True,
                    "data": entries,
                    "message": f"列出目录成功，共 {len(entries)} 个条目"
                })
            else:
                return self._create_error_result(f"列出目录失败: {result.message or '未知错误'}")
        except Exception as e:
            logger.error(f"列出目录失败: {e}")
            return self._create_error_result(f"列出目录失败: {str(e)}")

    async def _handle_file_search(
        self,
        sandbox_id: str,
        file: str,
        regex: str,
        sudo: bool = False
    ) -> CallToolResult:
        """在指定的 sandbox 容器文件中搜索内容"""
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not file or file.strip() == "":
                return self._create_error_result("缺少 file 参数，文件路径不能为空")
            if not regex or regex.strip() == "":
                return self._create_error_result("缺少 regex 参数，搜索模式不能为空")

            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.search_in_file(file, regex, sudo)

            if result.success:
                matches = result.data.get("matches", []) if isinstance(result.data, dict) else []
                return self._create_success_result({
                    "success": True,
                    "data": matches,
                    "message": f"搜索完成，找到 {len(matches)} 个匹配项"
                })
            else:
                return self._create_error_result(result.message or "搜索文件失败")
        except Exception as e:
            logger.error(f"搜索文件失败: {e}")
            return self._create_error_result(f"搜索文件失败: {str(e)}")

    async def _handle_file_replace(
        self,
        sandbox_id: str,
        file: str,
        old_str: str,
        new_str: str,
        sudo: bool = False
    ) -> CallToolResult:
        """在指定的 sandbox 容器文件中替换字符串内容"""
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not file or file.strip() == "":
                return self._create_error_result("缺少 file 参数，文件路径不能为空")
            if old_str is None or old_str == "":
                return self._create_error_result("缺少 old_str 参数，被替换字符串不能为空")

            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.str_replace_in_file(file, old_str, new_str, sudo)

            if result.success:
                replaced_count = result.data.get("replaced_count", 0) if isinstance(result.data, dict) else 0
                return self._create_success_result({
                    "success": True,
                    "data": {"replaced_count": replaced_count},
                    "message": f"替换完成，替换了 {replaced_count} 处"
                })
            else:
                return self._create_error_result(result.message or "替换文件失败")
        except Exception as e:
            logger.error(f"替换文件失败: {e}")
            return self._create_error_result(f"替换文件失败: {str(e)}")

    async def _handle_file_find(
        self,
        sandbox_id: str,
        path: str,
        glob_pattern: str
    ) -> CallToolResult:
        """在指定的 sandbox 容器目录中根据模式查找文件"""
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not path or path.strip() == "":
                return self._create_error_result("缺少 path 参数，目录路径不能为空")
            if not glob_pattern or glob_pattern.strip() == "":
                return self._create_error_result("缺少 glob_pattern 参数，文件模式不能为空")

            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.file_find(path, glob_pattern)

            if result.success:
                files = result.data.get("files", []) if isinstance(result.data, dict) else []
                return self._create_success_result({
                    "success": True,
                    "data": files,
                    "message": f"搜索完成，找到 {len(files)} 个文件"
                })
            else:
                return self._create_error_result(result.message or "查找文件失败")
        except Exception as e:
            logger.error(f"查找文件失败: {e}")
            return self._create_error_result(f"查找文件失败: {str(e)}")

    async def _handle_shell_view(
        self,
        sandbox_id: str,
        session_id: str,
        console: bool = False
    ) -> CallToolResult:
        """查看指定 sandbox 容器 shell 会话的输出内容"""
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not session_id:
                return self._create_error_result("缺少 session_id 参数")

            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.view_shell(session_id, console)

            if result.success:
                return self._create_success_result({
                    "success": True,
                    "data": result.data,
                    "message": result.message
                })
            else:
                return self._create_error_result(result.message or "查看 shell 失败")
        except Exception as e:
            logger.error(f"查看 shell 失败: {e}")
            return self._create_error_result(f"查看 shell 失败: {str(e)}")

    async def _handle_shell_wait(
        self,
        sandbox_id: str,
        session_id: str,
        seconds: Optional[int] = None
    ) -> CallToolResult:
        """等待指定 sandbox 容器 shell 会话中的进程执行完成"""
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not session_id:
                return self._create_error_result("缺少 session_id 参数")

            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.wait_for_process(session_id, seconds)

            if result.success:
                return self._create_success_result({
                    "success": True,
                    "data": result.data,
                    "message": result.message
                })
            else:
                return self._create_error_result(result.message or "等待进程失败")
        except Exception as e:
            logger.error(f"等待进程失败: {e}")
            return self._create_error_result(f"等待进程失败: {str(e)}")

    async def _handle_shell_write(
        self,
        sandbox_id: str,
        session_id: str,
        input: str,
        press_enter: bool = True
    ) -> CallToolResult:
        """向指定 sandbox 容器 shell 会话的进程写入输入内容"""
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not session_id:
                return self._create_error_result("缺少 session_id 参数")

            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.write_to_process(session_id, input, press_enter)

            if result.success:
                return self._create_success_result({
                    "success": True,
                    "data": result.data,
                    "message": result.message
                })
            else:
                return self._create_error_result(result.message or "写入进程失败")
        except Exception as e:
            logger.error(f"写入进程失败: {e}")
            return self._create_error_result(f"写入进程失败: {str(e)}")

    async def _handle_shell_kill(
        self,
        sandbox_id: str,
        session_id: str
    ) -> CallToolResult:
        """终止指定 sandbox 容器 shell 会话中的进程"""
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not session_id:
                return self._create_error_result("缺少 session_id 参数")

            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.kill_process(session_id)

            if result.success:
                return self._create_success_result({
                    "success": True,
                    "data": result.data,
                    "message": result.message or "进程已终止"
                })
            else:
                return self._create_error_result(result.message or "终止进程失败")
        except Exception as e:
            logger.error(f"终止进程失败: {e}")
            return self._create_error_result(f"终止进程失败: {str(e)}")

    async def _handle_supervisor_status(
        self,
        sandbox_id: str
    ) -> CallToolResult:
        """获取指定 sandbox 容器中所有服务的状态信息"""
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")

            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.get_supervisor_status()

            if result.success:
                return self._create_success_result({
                    "success": True,
                    "data": result.data,
                    "message": result.message
                })
            else:
                return self._create_error_result(result.message or "获取服务状态失败")
        except Exception as e:
            logger.error(f"获取服务状态失败: {e}")
            return self._create_error_result(f"获取服务状态失败: {str(e)}")

    async def _handle_supervisor_restart(
        self,
        sandbox_id: str
    ) -> CallToolResult:
        """重启指定 sandbox 容器中的所有服务"""
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")

            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.restart_all_services()

            if result.success:
                return self._create_success_result({
                    "success": True,
                    "data": result.data,
                    "message": result.message or "服务重启成功"
                })
            else:
                return self._create_error_result(result.message or "重启服务失败")
        except Exception as e:
            logger.error(f"重启服务失败: {e}")
            return self._create_error_result(f"重启服务失败: {str(e)}")

    async def _handle_browser_navigate(
        self,
        sandbox_id: str,
        url: str,
        timeout_seconds: int = 15
    ) -> CallToolResult:
        """在 sandbox 容器的浏览器中导航到指定网址"""
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not url:
                return self._create_error_result("缺少 url 参数")

            sandbox = await DockerSandbox.get(sandbox_id)
            browser = await sandbox.get_browser()
            result = await browser.navigate(url, timeout_seconds)

            return self._create_success_result(result)
        except Exception as e:
            logger.error(f"浏览器导航失败: {e}")
            return self._create_error_result(f"浏览器导航失败: {str(e)}")

    async def _handle_browser_view(
        self,
        sandbox_id: str
    ) -> CallToolResult:
        """查看 sandbox 容器浏览器当前页面的内容和交互元素"""
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")

            sandbox = await DockerSandbox.get(sandbox_id)
            browser = await sandbox.get_browser()
            result = await browser.view()

            return self._create_success_result(result)
        except Exception as e:
            logger.error(f"查看浏览器页面失败: {e}")
            return self._create_error_result(f"查看浏览器页面失败: {str(e)}")

    async def _handle_browser_click(
        self,
        sandbox_id: str,
        index: Optional[int] = None,
        x: Optional[int] = None,
        y: Optional[int] = None
    ) -> CallToolResult:
        """在 sandbox 容器浏览器中点击页面元素或指定坐标"""
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")

            sandbox = await DockerSandbox.get(sandbox_id)
            browser = await sandbox.get_browser()

            if index is not None:
                result = await browser.click(index=index)
            elif x is not None and y is not None:
                result = await browser.click(x=x, y=y)
            else:
                return self._create_error_result("必须提供 index 或 x,y 坐标参数")

            return self._create_success_result(result)
        except Exception as e:
            logger.error(f"浏览器点击失败: {e}")
            return self._create_error_result(f"浏览器点击失败: {str(e)}")

    async def _handle_browser_input(
        self,
        sandbox_id: str,
        index: int,
        content: str,
        submit: bool = False
    ) -> CallToolResult:
        """在 sandbox 容器浏览器中向页面元素输入文本"""
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")

            sandbox = await DockerSandbox.get(sandbox_id)
            browser = await sandbox.get_browser()
            result = await browser.input(index, content, submit)

            return self._create_success_result(result)
        except Exception as e:
            logger.error(f"浏览器输入失败: {e}")
            return self._create_error_result(f"浏览器输入失败: {str(e)}")

    async def _handle_browser_screenshot(
        self,
        sandbox_id: str
    ) -> CallToolResult:
        """对 sandbox 容器浏览器当前页面进行截图"""
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")

            sandbox = await DockerSandbox.get(sandbox_id)
            browser = await sandbox.get_browser()
            result = await browser.screenshot()

            return self._create_success_result(result)
        except Exception as e:
            logger.error(f"浏览器截图失败: {e}")
            return self._create_error_result(f"浏览器截图失败: {str(e)}")

    async def _handle_browser_scroll(
        self,
        sandbox_id: str,
        direction: str = "down",
        distance: int = 300
    ) -> CallToolResult:
        """在 sandbox 容器浏览器中滚动页面"""
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")

            sandbox = await DockerSandbox.get(sandbox_id)
            browser = await sandbox.get_browser()
            result = await browser.scroll(direction, distance)

            return self._create_success_result(result)
        except Exception as e:
            logger.error(f"浏览器滚动失败: {e}")
            return self._create_error_result(f"浏览器滚动失败: {str(e)}")

    async def _handle_browser_console_exec(
        self,
        sandbox_id: str,
        script: str
    ) -> CallToolResult:
        """在 sandbox 容器浏览器中执行 JavaScript 代码"""
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not script:
                return self._create_error_result("缺少 script 参数")

            sandbox = await DockerSandbox.get(sandbox_id)
            browser = await sandbox.get_browser()
            result = await browser.console_exec(script)

            return self._create_success_result(result)
        except Exception as e:
            logger.error(f"执行 JavaScript 失败: {e}")
            return self._create_error_result(f"执行 JavaScript 失败: {str(e)}")

    async def _handle_browser_console_view(
        self,
        sandbox_id: str
    ) -> CallToolResult:
        """查看 sandbox 容器浏览器的控制台输出"""
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")

            sandbox = await DockerSandbox.get(sandbox_id)
            browser = await sandbox.get_browser()
            result = await browser.console_view()

            return self._create_success_result(result)
        except Exception as e:
            logger.error(f"查看控制台输出失败: {e}")
            return self._create_error_result(f"查看控制台输出失败: {str(e)}")

    def get_server(self):
        """获取 MCP 服务器实例"""
        return self.server

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
            fn=self._handle_file_exists,
            name="file_exists",
            description="检查指定的 sandbox 容器中文件是否存在。支持 sudo 权限检查系统文件"
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

        self.server.add_tool(
            fn=self._handle_file_search,
            name="file_search",
            description="在指定的 sandbox 容器文件中搜索内容。支持正则表达式搜索"
        )

        self.server.add_tool(
            fn=self._handle_file_replace,
            name="file_replace",
            description="在指定的 sandbox 容器文件中替换字符串内容。支持 sudo 权限修改系统文件"
        )

        self.server.add_tool(
            fn=self._handle_file_find,
            name="file_find",
            description="在指定的 sandbox 容器目录中根据模式查找文件。支持通配符模式"
        )

        self.server.add_tool(
            fn=self._handle_shell_view,
            name="shell_view",
            description="查看指定 sandbox 容器 shell 会话的输出内容。可以查看控制台输出"
        )

        self.server.add_tool(
            fn=self._handle_shell_wait,
            name="shell_wait",
            description="等待指定 sandbox 容器 shell 会话中的进程执行完成"
        )

        self.server.add_tool(
            fn=self._handle_shell_write,
            name="shell_write",
            description="向指定 sandbox 容器 shell 会话的进程写入输入内容。可以模拟用户输入"
        )

        self.server.add_tool(
            fn=self._handle_shell_kill,
            name="shell_kill",
            description="终止指定 sandbox 容器 shell 会话中的进程"
        )

        self.server.add_tool(
            fn=self._handle_supervisor_status,
            name="supervisor_status",
            description="获取指定 sandbox 容器中所有服务的状态信息"
        )

        self.server.add_tool(
            fn=self._handle_supervisor_restart,
            name="supervisor_restart",
            description="重启指定 sandbox 容器中的所有服务"
        )

        self.server.add_tool(
            fn=self._handle_browser_navigate,
            name="browser_navigate",
            description="在 sandbox 容器的浏览器中导航到指定网址。timeout_seconds 参数单位为秒，默认15秒"
        )

        self.server.add_tool(
            fn=self._handle_browser_view,
            name="browser_view",
            description="查看 sandbox 容器浏览器当前页面的内容和交互元素"
        )

        self.server.add_tool(
            fn=self._handle_browser_click,
            name="browser_click",
            description="在 sandbox 容器浏览器中点击页面元素或指定坐标"
        )

        self.server.add_tool(
            fn=self._handle_browser_input,
            name="browser_input",
            description="在 sandbox 容器浏览器中向页面元素输入文本"
        )

        self.server.add_tool(
            fn=self._handle_browser_screenshot,
            name="browser_screenshot",
            description="对 sandbox 容器浏览器当前页面进行截图"
        )

        self.server.add_tool(
            fn=self._handle_browser_scroll,
            name="browser_scroll",
            description="在 sandbox 容器浏览器中滚动页面"
        )

        self.server.add_tool(
            fn=self._handle_browser_console_exec,
            name="browser_console_exec",
            description="在 sandbox 容器浏览器中执行 JavaScript 代码"
        )

        self.server.add_tool(
            fn=self._handle_browser_console_view,
            name="browser_console_view",
            description="查看 sandbox 容器浏览器的控制台输出"
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

    async def _handle_file_exists(
        self,
        sandbox_id: str,
        file: str,
        sudo: bool = False
    ) -> CallToolResult:
        """
        检查指定的 sandbox 容器中文件是否存在
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
            - file (必填): 要检查的文件路径
            - sudo (选填): 是否使用 sudo 权限检查文件，默认为 false
        
        返回:
            - success: 是否检查成功
            - data.exists: 文件是否存在
            - message: 检查结果的描述
        """
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
                    "data": {
                        "exists": exists
                    },
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
        """
        从指定的 sandbox 容器中删除文件
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
            - file (必填): 要删除的文件路径
            - sudo (选填): 是否使用 sudo 权限删除文件，默认为 false
        
        返回:
            - success: 是否删除成功
            - message: 删除结果的描述
        """
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not file or file.strip() == "":
                return self._create_error_result("缺少 file 参数，文件路径不能为空")

            # 使用 shell 命令删除文件，因为 sandbox 没有 file_delete API
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

            # 使用 shell 命令列出目录，因为 sandbox 没有 file_list API
            command = f"ls -la '{path}'"
            if sudo:
                command = f"sudo {command}"
            
            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.exec_command(sandbox.id, "/", command)

            if result.success:
                # 解析 shell 命令输出
                command_output = result.data.get("output", "") if isinstance(result.data, dict) else ""
                if not command_output:
                    return self._create_success_result({
                        "success": True,
                        "data": [],
                        "message": "目录为空"
                    })
                
                # 解析 ls -la 输出
                entries = []
                lines = command_output.strip().split('\n')
                
                # 跳过第一行 (total xxx)
                for line in lines[1:] if len(lines) > 1 else lines:
                    line = line.strip()
                    if not line or line.startswith('total'):
                        continue
                    
                    parts = line.split()
                    if len(parts) >= 9:
                        permissions = parts[0]
                        name = parts[8]
                        
                        # 跳过 . 和 ..
                        if name in ['.', '..']:
                            continue
                            
                        # 判断类型
                        file_type = "directory" if permissions.startswith('d') else "file"
                        
                        # 获取大小
                        size = parts[4] if len(parts) > 4 else "0"
                        
                        # 获取修改时间
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
        """
        在指定的 sandbox 容器文件中搜索内容
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
            - file (必填): 要搜索的文件路径
            - regex (必填): 正则表达式搜索模式
            - sudo (选填): 是否使用 sudo 权限搜索文件，默认为 false
        
        返回:
            - success: 是否搜索成功
            - data: 搜索结果列表，包含匹配的行号和内容
            - message: 搜索结果的描述
        """
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
        """
        在指定的 sandbox 容器文件中替换字符串内容
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
            - file (必填): 要替换的文件路径
            - old_str (必填): 要被替换的字符串
            - new_str (必填): 替换后的新字符串
            - sudo (选填): 是否使用 sudo 权限修改文件，默认为 false
        
        返回:
            - success: 是否替换成功
            - data: 替换结果，包含替换次数
            - message: 替换结果的描述
        """
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not file or file.strip() == "":
                return self._create_error_result("缺少 file 参数，文件路径不能为空")
            if old_str is None or old_str == "":
                return self._create_error_result("缺少 old_str 参数，被替换字符串不能为空")
            if new_str is None:
                new_str = ""  # 允许替换为空字符串

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
        """
        在指定的 sandbox 容器目录中根据模式查找文件
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
            - path (必填): 要查找的目录路径
            - glob_pattern (必填): 通配符模式，如 *.py, test*, 等等
        
        返回:
            - success: 是否查找成功
            - data: 找到的文件列表
            - message: 查找结果的描述
        """
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not path or path.strip() == "":
                return self._create_error_result("缺少 path 参数，目录路径不能为空")
            if not glob_pattern or glob_pattern.strip() == "":
                return self._create_error_result("缺少 glob_pattern 参数，文件模式不能为空")

            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.find_files_by_name(path, glob_pattern)

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
        """
        查看指定 sandbox 容器 shell 会话的输出内容
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
            - session_id (必填): shell 会话的唯一标识符
            - console (选填): 是否只查看控制台输出，默认为 false
        
        返回:
            - success: 是否查看成功
            - data: 会话输出内容
            - message: 查看结果的描述
        """
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not session_id or session_id.strip() == "":
                return self._create_error_result("缺少 session_id 参数，会话 ID 不能为空")

            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.view_shell_session(session_id, console)

            if result.success:
                return self._create_success_result({
                    "success": True,
                    "data": result.data,
                    "message": "会话内容获取成功"
                })
            else:
                return self._create_error_result(result.message or "查看会话失败")
        except Exception as e:
            logger.error(f"查看会话失败: {e}")
            return self._create_error_result(f"查看会话失败: {str(e)}")

    async def _handle_shell_wait(
        self,
        sandbox_id: str,
        session_id: str,
        seconds: int = 10
    ) -> CallToolResult:
        """
        等待指定 sandbox 容器 shell 会话中的进程执行完成
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
            - session_id (必填): shell 会话的唯一标识符
            - seconds (选填): 等待超时时间（秒），默认为 10 秒
        
        返回:
            - success: 是否等待成功
            - data: 进程执行结果，包含返回码
            - message: 等待结果的描述
        """
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not session_id or session_id.strip() == "":
                return self._create_error_result("缺少 session_id 参数，会话 ID 不能为空")

            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.wait_for_process(session_id, seconds)

            if result.success:
                return self._create_success_result({
                    "success": True,
                    "data": result.data,
                    "message": f"进程执行完成，返回码: {result.data.get('returncode', -1)}"
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
        input_text: str,
        press_enter: bool = True
    ) -> CallToolResult:
        """
        向指定 sandbox 容器 shell 会话的进程写入输入内容
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
            - session_id (必填): shell 会话的唯一标识符
            - input_text (必填): 要写入的输入内容
            - press_enter (选填): 是否在输入后按回车键，默认为 true
        
        返回:
            - success: 是否写入成功
            - data: 写入操作结果
            - message: 写入结果的描述
        """
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not session_id or session_id.strip() == "":
                return self._create_error_result("缺少 session_id 参数，会话 ID 不能为空")
            if input_text is None:
                input_text = ""  # 允许写入空内容

            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.write_to_process(session_id, input_text, press_enter)

            if result.success:
                return self._create_success_result({
                    "success": True,
                    "data": result.data,
                    "message": "输入写入成功"
                })
            else:
                return self._create_error_result(result.message or "写入输入失败")
        except Exception as e:
            logger.error(f"写入输入失败: {e}")
            return self._create_error_result(f"写入输入失败: {str(e)}")

    async def _handle_shell_kill(
        self,
        sandbox_id: str,
        session_id: str
    ) -> CallToolResult:
        """
        终止指定 sandbox 容器 shell 会话中的进程
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
            - session_id (必填): shell 会话的唯一标识符
        
        返回:
            - success: 是否终止成功
            - data: 终止操作结果
            - message: 终止结果的描述
        """
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not session_id or session_id.strip() == "":
                return self._create_error_result("缺少 session_id 参数，会话 ID 不能为空")

            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.kill_process(session_id)

            if result.success:
                status = result.data.get("status", "unknown") if isinstance(result.data, dict) else "unknown"
                message = "进程已终止" if status == "terminated" else "进程已结束"
                return self._create_success_result({
                    "success": True,
                    "data": result.data,
                    "message": message
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
        """
        获取指定 sandbox 容器中所有服务的状态信息
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
        
        返回:
            - success: 是否获取成功
            - data: 服务状态列表
            - message: 获取结果的描述
        """
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")

            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.get_supervisor_status()

            if result.success:
                processes = result.data if isinstance(result.data, list) else []
                return self._create_success_result({
                    "success": True,
                    "data": processes,
                    "message": f"获取服务状态成功，共 {len(processes)} 个服务"
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
        """
        重启指定 sandbox 容器中的所有服务
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
        
        返回:
            - success: 是否重启成功
            - data: 重启操作结果
            - message: 重启结果的描述
        """
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")

            sandbox = await DockerSandbox.get(sandbox_id)
            result = await sandbox.restart_all_services()

            if result.success:
                return self._create_success_result({
                    "success": True,
                    "data": result.data,
                    "message": "所有服务已重启"
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
        """
        在 sandbox 容器的浏览器中导航到指定网址
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
            - url (必填): 要导航到的网址
            - timeout_seconds (选填): 导航超时时间（秒），默认为 15 秒
        
        返回:
            - success: 是否导航成功
            - data: 导航结果，包含页面交互元素信息
            - message: 导航结果的描述
        """
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not url or url.strip() == "":
                return self._create_error_result("缺少 url 参数，网址不能为空")

            sandbox = await DockerSandbox.get(sandbox_id)
            browser = await sandbox.get_browser()
            # 将秒转换为毫秒传递给底层浏览器实现
            timeout_ms = timeout_seconds * 1000
            result = await browser.navigate(url, timeout_ms)

            if result.success:
                interactive_elements = result.data.get("interactive_elements", []) if isinstance(result.data, dict) else []
                actual_url = result.data.get("url", url) if isinstance(result.data, dict) else url
                element_count = result.data.get("element_count", len(interactive_elements)) if isinstance(result.data, dict) else len(interactive_elements)
                warning = result.data.get("warning", "") if isinstance(result.data, dict) else ""
                
                message = f"导航到 {actual_url} 成功"
                if warning:
                    message += f" (警告: {warning})"
                
                return self._create_success_result({
                    "success": True,
                    "data": {
                        "interactive_elements": interactive_elements,
                        "url": actual_url,
                        "element_count": element_count
                    },
                    "message": message
                })
            else:
                # Enhanced error handling for navigation failures
                error_message = result.message or "导航失败"
                
                if "about:blank" in error_message:
                    error_message += "\n\n可能的原因和解决方案："
                    error_message += "\n1. 网址格式不正确 - 确保网址以 http:// 或 https:// 开头"
                    error_message += "\n2. 网址被浏览器阻止 - 尝试使用不同的网址"
                    error_message += "\n3. 网络连接问题 - 检查 sandbox 容器的网络连接"
                    error_message += "\n4. 浏览器安全设置 - 某些网站可能被浏览器安全策略阻止"
                    error_message += "\n5. 尝试使用 IP 地址而不是域名访问"
                
                return self._create_error_result(error_message)
        except Exception as e:
            logger.error(f"浏览器导航失败: {e}")
            return self._create_error_result(f"浏览器导航失败: {str(e)}")

    async def _handle_browser_view(
        self,
        sandbox_id: str
    ) -> CallToolResult:
        """
        查看 sandbox 容器浏览器当前页面的内容和交互元素
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
        
        返回:
            - success: 是否查看成功
            - data: 页面内容和交互元素信息
            - message: 查看结果的描述
        """
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")

            sandbox = await DockerSandbox.get(sandbox_id)
            browser = await sandbox.get_browser()
            result = await browser.view_page()

            if result.success:
                content = result.data.get("content", "") if isinstance(result.data, dict) else ""
                interactive_elements = result.data.get("interactive_elements", []) if isinstance(result.data, dict) else []
                debug_info = result.data.get("debug_info", {}) if isinstance(result.data, dict) else {}
                
                # Log debug information
                if debug_info:
                    logger.info(f"browser_view debug info: {debug_info}")
                
                return self._create_success_result({
                    "success": True,
                    "data": {
                        "content": content,
                        "interactive_elements": interactive_elements,
                        "debug_info": debug_info
                    },
                    "message": f"页面查看成功，发现 {len(interactive_elements)} 个交互元素"
                })
            else:
                return self._create_error_result(result.message or "查看页面失败")
        except Exception as e:
            logger.error(f"浏览器查看失败: {e}")
            return self._create_error_result(f"浏览器查看失败: {str(e)}")

    async def _handle_browser_click(
        self,
        sandbox_id: str,
        index: Optional[int] = None,
        coordinate_x: Optional[float] = None,
        coordinate_y: Optional[float] = None
    ) -> CallToolResult:
        """
        在 sandbox 容器浏览器中点击页面元素或指定坐标
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
            - index (选填): 要点击的交互元素索引号
            - coordinate_x (选填): 点击的 X 坐标
            - coordinate_y (选填): 点击的 Y 坐标
        
        返回:
            - success: 是否点击成功
            - data: 点击操作结果
            - message: 点击结果的描述
        """
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            
            # 必须提供 index 或坐标
            if index is None and (coordinate_x is None or coordinate_y is None):
                return self._create_error_result("必须提供 index 参数或 coordinate_x 和 coordinate_y 坐标参数")

            sandbox = await DockerSandbox.get(sandbox_id)
            browser = await sandbox.get_browser()
            result = await browser.click(index=index, coordinate_x=coordinate_x, coordinate_y=coordinate_y)

            if result.success:
                return self._create_success_result({
                    "success": True,
                    "data": result.data,
                    "message": "点击操作成功"
                })
            else:
                # Enhanced error message with suggestions
                error_message = result.message or "点击失败"
                
                # If it's an index not found error, provide helpful suggestions
                if "Cannot find interactive element with index" in error_message:
                    error_message += "\n\n建议解决方案："
                    error_message += "\n1. 先使用 browser_view 工具重新获取最新的交互元素列表"
                    error_message += "\n2. 检查索引号是否在有效范围内（0到元素总数-1）"
                    error_message += "\n3. 考虑使用坐标点击（coordinate_x, coordinate_y）代替索引点击"
                    error_message += "\n4. 等待页面完全加载后再尝试点击"
                    error_message += "\n5. 检查元素是否被其他元素遮挡"
                    
                    # Try to get current page info for better debugging
                    try:
                        view_result = await browser.view_page()
                        if view_result.success and view_result.data:
                            elements = view_result.data.get("interactive_elements", [])
                            if elements:
                                error_message += f"\n\n当前页面有 {len(elements)} 个交互元素，索引范围：0-{len(elements)-1}"
                                error_message += "\n前几个可用元素："
                                for i, element in enumerate(elements[:5]):
                                    error_message += f"\n  [{i}]: {element}"
                    except Exception as debug_e:
                        logger.warning(f"Failed to get debug info for click error: {debug_e}")
                
                return self._create_error_result(error_message)
        except Exception as e:
            logger.error(f"浏览器点击失败: {e}")
            return self._create_error_result(f"浏览器点击失败: {str(e)}")

    async def _handle_browser_input(
        self,
        sandbox_id: str,
        text: str,
        press_enter: bool = True,
        index: Optional[int] = None,
        coordinate_x: Optional[float] = None,
        coordinate_y: Optional[float] = None
    ) -> CallToolResult:
        """
        在 sandbox 容器浏览器中向页面元素输入文本
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
            - text (必填): 要输入的文本内容
            - press_enter (选填): 输入后是否按回车键，默认为 true
            - index (选填): 要输入的交互元素索引号
            - coordinate_x (选填): 输入的 X 坐标
            - coordinate_y (选填): 输入的 Y 坐标
        
        返回:
            - success: 是否输入成功
            - data: 输入操作结果
            - message: 输入结果的描述
        """
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if text is None:
                return self._create_error_result("缺少 text 参数，输入文本不能为空")
            
            # 必须提供 index 或坐标
            if index is None and (coordinate_x is None or coordinate_y is None):
                return self._create_error_result("必须提供 index 参数或 coordinate_x 和 coordinate_y 坐标参数")

            sandbox = await DockerSandbox.get(sandbox_id)
            browser = await sandbox.get_browser()
            result = await browser.input(text=text, press_enter=press_enter, index=index, coordinate_x=coordinate_x, coordinate_y=coordinate_y)

            if result.success:
                return self._create_success_result({
                    "success": True,
                    "data": result.data,
                    "message": "文本输入成功"
                })
            else:
                return self._create_error_result(result.message or "输入失败")
        except Exception as e:
            logger.error(f"浏览器输入失败: {e}")
            return self._create_error_result(f"浏览器输入失败: {str(e)}")

    async def _handle_browser_screenshot(
        self,
        sandbox_id: str,
        full_page: bool = False
    ) -> CallToolResult:
        """
        对 sandbox 容器浏览器当前页面进行截图
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
            - full_page (选填): 是否截取整个页面，默认为 false（只截取当前视口）
        
        返回:
            - success: 是否截图成功
            - data: 截图结果（base64 编码的图片数据）
            - message: 截图结果的描述
        """
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")

            sandbox = await DockerSandbox.get(sandbox_id)
            browser = await sandbox.get_browser()
            screenshot_bytes = await browser.screenshot(full_page=full_page)

            # 将图片字节数据转换为 base64 编码
            import base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            return self._create_success_result({
                "success": True,
                "data": {
                    "screenshot": screenshot_base64,
                    "format": "png",
                    "full_page": full_page
                },
                "message": "页面截图成功"
            })
        except Exception as e:
            logger.error(f"浏览器截图失败: {e}")
            return self._create_error_result(f"浏览器截图失败: {str(e)}")

    async def _handle_browser_scroll(
        self,
        sandbox_id: str,
        direction: str = "down",
        to_top: bool = False,
        to_bottom: bool = False
    ) -> CallToolResult:
        """
        在 sandbox 容器浏览器中滚动页面
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
            - direction (选填): 滚动方向，可选 "up" 或 "down"，默认为 "down"
            - to_top (选填): 是否滚动到页面顶部，默认为 false
            - to_bottom (选填): 是否滚动到页面底部，默认为 false
        
        返回:
            - success: 是否滚动成功
            - data: 滚动操作结果
            - message: 滚动结果的描述
        """
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")

            sandbox = await DockerSandbox.get(sandbox_id)
            browser = await sandbox.get_browser()
            
            if to_top:
                result = await browser.scroll_up(to_top=True)
                message = "已滚动到页面顶部"
            elif to_bottom:
                result = await browser.scroll_down(to_bottom=True)
                message = "已滚动到页面底部"
            elif direction == "up":
                result = await browser.scroll_up()
                message = "页面上滚成功"
            else:  # direction == "down"
                result = await browser.scroll_down()
                message = "页面下滚成功"

            if result.success:
                return self._create_success_result({
                    "success": True,
                    "data": result.data,
                    "message": message
                })
            else:
                return self._create_error_result(result.message or "滚动失败")
        except Exception as e:
            logger.error(f"浏览器滚动失败: {e}")
            return self._create_error_result(f"浏览器滚动失败: {str(e)}")

    async def _handle_browser_console_exec(
        self,
        sandbox_id: str,
        javascript: str
    ) -> CallToolResult:
        """
        在 sandbox 容器浏览器中执行 JavaScript 代码
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
            - javascript (必填): 要执行的 JavaScript 代码
        
        返回:
            - success: 是否执行成功
            - data: 执行结果
            - message: 执行结果的描述
        """
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")
            if not javascript or javascript.strip() == "":
                return self._create_error_result("缺少 javascript 参数，JavaScript 代码不能为空")

            sandbox = await DockerSandbox.get(sandbox_id)
            browser = await sandbox.get_browser()
            result = await browser.console_exec(javascript)

            if result.success:
                return self._create_success_result({
                    "success": True,
                    "data": result.data,
                    "message": "JavaScript 代码执行成功"
                })
            else:
                return self._create_error_result(result.message or "JavaScript 执行失败")
        except Exception as e:
            logger.error(f"浏览器 JavaScript 执行失败: {e}")
            return self._create_error_result(f"浏览器 JavaScript 执行失败: {str(e)}")

    async def _handle_browser_console_view(
        self,
        sandbox_id: str,
        max_lines: Optional[int] = None
    ) -> CallToolResult:
        """
        查看 sandbox 容器浏览器的控制台输出
        
        参数:
            - sandbox_id (必填): sandbox 容器的唯一标识符
            - max_lines (选填): 最多显示的控制台输出行数，默认为显示所有
        
        返回:
            - success: 是否查看成功
            - data: 控制台输出内容
            - message: 查看结果的描述
        """
        try:
            if not sandbox_id:
                return self._create_error_result("缺少 sandbox_id 参数")

            sandbox = await DockerSandbox.get(sandbox_id)
            browser = await sandbox.get_browser()
            result = await browser.console_view(max_lines=max_lines)

            if result.success:
                logs = result.data.get("logs", []) if isinstance(result.data, dict) else []
                return self._create_success_result({
                    "success": True,
                    "data": {
                        "logs": logs,
                        "count": len(logs)
                    },
                    "message": f"控制台输出获取成功，共 {len(logs)} 条记录"
                })
            else:
                return self._create_error_result(result.message or "控制台输出获取失败")
        except Exception as e:
            logger.error(f"浏览器控制台输出获取失败: {e}")
            return self._create_error_result(f"浏览器控制台输出获取失败: {str(e)}")

    def get_server(self):
        """获取 MCP 服务器实例"""
        return self.server

import asyncio
from mcp import Client

async def test_mcp_server():
    """测试 MCP 服务器功能"""
    print("连接到 MCP 服务器...")
    
    # 创建 MCP 客户端
    client = Client(
        url="http://localhost:8081/mcp",
        transport="streamable-http"
    )
    
    try:
        # 连接到服务器
        await client.connect()
        print("连接成功！")
        
        # 列出可用工具
        tools = await client.list_tools()
        print("\n可用工具:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")
        
        # 测试创建 sandbox
        print("\n测试创建 sandbox...")
        create_result = await client.call_tool(
            name="create_sandbox",
            arguments={}
        )
        print(f"创建结果: {create_result}")
        
        if create_result.success:
            sandbox_id = create_result.content.get("sandbox_id")
            print(f"创建的 sandbox ID: {sandbox_id}")
            
            # 测试执行命令
            print("\n测试执行命令...")
            exec_result = await client.call_tool(
                name="exec_command",
                arguments={
                    "sandbox_id": sandbox_id,
                    "command": "echo 'Hello from MCP server!'",
                    "exec_dir": "/"
                }
            )
            print(f"执行结果: {exec_result}")
            
            # 测试写入文件
            print("\n测试写入文件...")
            write_result = await client.call_tool(
                name="file_write",
                arguments={
                    "sandbox_id": sandbox_id,
                    "file": "/tmp/test.txt",
                    "content": "This is a test file created via MCP",
                    "append": False
                }
            )
            print(f"写入结果: {write_result}")
            
            # 测试读取文件
            print("\n测试读取文件...")
            read_result = await client.call_tool(
                name="file_read",
                arguments={
                    "sandbox_id": sandbox_id,
                    "file": "/tmp/test.txt"
                }
            )
            print(f"读取结果: {read_result}")
        
    finally:
        # 关闭连接
        await client.disconnect()
        print("\n测试完成！")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())

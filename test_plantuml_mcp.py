#!/usr/bin/env python3
"""
简化版 PlantUML MCP 客户端测试工具

测试 PlantUML MCP 服务器的两个工具：
1. generate_diagram_base64 - 生成 PlantUML 图表
2. validate_plantuml - 验证 PlantUML 代码
"""

import asyncio
import sys
import base64
from pathlib import Path
from mcp import ClientSession
from mcp.client.sse import sse_client

# 测试用例
TEST_SEQUENCE_DIAGRAM = """
@startuml
Alice -> Bob: Hello
Bob --> Alice: Hi there
@enduml
"""

TEST_CLASS_DIAGRAM = """
@startuml
class User {
  +name: String
  +email: String
}
@enduml
"""

class PlantUMLTester:
    def __init__(self, server_url):
        self.server_url = server_url
        self.session = None
        self.output_dir = Path("./test_output")
        self.output_dir.mkdir(exist_ok=True)

    async def setup(self):
        print(f"连接到 MCP 服务器: {self.server_url}")
        
        # 创建 SSE 客户端和 MCP 会话
        self._streams_context = sse_client(url=self.server_url)
        streams = await self._streams_context.__aenter__()
        
        self._session_context = ClientSession(*streams)
        self.session = await self._session_context.__aenter__()
        
        # 初始化会话
        await self.session.initialize()
        
        # 获取可用工具列表
        response = await self.session.list_tools()
        tool_names = [tool.name for tool in response.tools]
        print(f"可用工具: {tool_names}")
        
        return True

    async def test_generate_diagram(self):
        print("\n测试 generate_diagram_base64 工具...")
        
        # 调用生成图表工具
        result = await self.session.call_tool(
            "generate_diagram_base64", 
            {"uml_code": TEST_SEQUENCE_DIAGRAM, "format_type": "svg"}
        )
        
        # 提取结果
        if hasattr(result, 'content'):
            content = "".join([item.text for item in result.content if hasattr(item, 'text')])
        else:
            content = str(result)
        
        # 保存图表
        if "base64" in content:
            # 提取 base64 数据
            if "," in content:
                _, data = content.split(",", 1)
            else:
                data = content
            
            # 保存到文件
            output_path = self.output_dir / "test_diagram.svg"
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(data))
            
            print(f"✅ 图表已保存到: {output_path}")
            return True
        else:
            print(f"❌ 生成图表失败: {content[:100]}")
            return False

    async def test_validate_plantuml(self):
        print("\n测试 validate_plantuml 工具...")
        
        # 调用验证工具
        result = await self.session.call_tool(
            "validate_plantuml", 
            {"uml_code": TEST_CLASS_DIAGRAM}
        )
        
        # 提取结果
        if hasattr(result, 'content'):
            content = "".join([item.text for item in result.content if hasattr(item, 'text')])
        else:
            content = str(result)
        
        print(f"验证结果: {content}")
        
        # 检查验证结果
        if "\"valid\": true" in content.lower() or "'valid': true" in content.lower():
            print("✅ PlantUML 代码验证通过")
            return True
        else:
            print("❌ PlantUML 代码验证失败")
            return False

    async def cleanup(self):
        # 清理资源
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
        
        if self._streams_context:
            await self._streams_context.__aexit__(None, None, None)

async def main():
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("用法: python test_plantuml_mcp.py <MCP服务器URL>")
        print("示例: python test_plantuml_mcp.py http://localhost:8765/sse")
        sys.exit(1)
    
    server_url = sys.argv[1]
    tester = PlantUMLTester(server_url)
    
    try:
        # 设置连接
        await tester.setup()
        
        # 测试工具
        diagram_result = await tester.test_generate_diagram()
        validate_result = await tester.test_validate_plantuml()
        
        # 输出总结果
        print("\n===== 测试结果 =====")
        print(f"生成图表: {'成功' if diagram_result else '失败'}")
        print(f"验证代码: {'成功' if validate_result else '失败'}")
        
        if diagram_result and validate_result:
            print("\n✅ 所有测试通过!")
        else:
            print("\n❌ 部分测试失败")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)
    finally:
        # 清理资源
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())

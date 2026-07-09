"""
Allure Helper 使用示例

演示如何使用 AllureHelper 类的各种功能
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.reporting.allure_helper import AllureHelper, allure_step


def demo_screenshot_attachment():
    """演示截图附件功能"""
    # 模拟截图数据（实际使用中会从 Playwright 获取）
    fake_screenshot = b"fake screenshot bytes"
    
    # 附加截图到 Allure 报告
    AllureHelper.attach_screenshot(fake_screenshot, "Demo Screenshot")
    print("✓ Screenshot attached to Allure report")


def demo_log_attachment():
    """演示日志附件功能"""
    log_content = """
    2024-01-01 10:00:00 - INFO - Test started
    2024-01-01 10:00:01 - INFO - Navigating to login page
    2024-01-01 10:00:02 - INFO - Entering credentials
    2024-01-01 10:00:03 - INFO - Login successful
    """
    
    # 附加日志到 Allure 报告
    AllureHelper.attach_log(log_content.strip(), "Test Execution Log")
    print("✓ Log attached to Allure report")


def demo_json_attachment():
    """演示 JSON 数据附件功能"""
    api_response = {
        "status": "success",
        "user_id": 12345,
        "username": "john_doe",
        "email": "john@example.com",
        "roles": ["user", "admin"]
    }
    
    # 附加 JSON 数据到 Allure 报告
    AllureHelper.attach_json(api_response, "API Response")
    print("✓ JSON data attached to Allure report")


def demo_test_steps():
    """演示测试步骤功能"""
    print("\n演示测试步骤:")
    
    # 使用上下文管理器创建步骤
    with AllureHelper.step("Step 1: Open application"):
        print("  - Opening application...")
        # 实际测试代码会在这里
    
    with AllureHelper.step("Step 2: Login"):
        print("  - Logging in...")
        # 实际测试代码会在这里
    
    with AllureHelper.step("Step 3: Verify dashboard"):
        print("  - Verifying dashboard...")
        # 实际测试代码会在这里
    
    print("✓ Test steps created in Allure report")


def demo_convenience_function():
    """演示便捷函数"""
    print("\n使用便捷函数:")
    
    with allure_step("Using convenience function"):
        print("  - This is a step created with the convenience function")
    
    print("✓ Convenience function works")


def demo_additional_features():
    """演示其他功能"""
    print("\n演示其他功能:")
    
    # 添加测试描述
    AllureHelper.add_description("This is a demo test showing AllureHelper features")
    print("  - Description added")
    
    # 设置测试标题
    AllureHelper.add_title("AllureHelper Demo Test")
    print("  - Title set")
    
    # 设置严重程度
    AllureHelper.add_severity("normal")
    print("  - Severity set")
    
    # 添加标签
    AllureHelper.add_tag("demo")
    AllureHelper.add_tag("allure")
    print("  - Tags added")
    
    # 添加链接
    AllureHelper.add_link("https://github.com/example/repo", "link", "GitHub Repo")
    print("  - Link added")
    
    # 附加文本
    AllureHelper.attach_text("Additional notes about this test", "Notes")
    print("  - Text attached")
    
    # 附加 HTML
    AllureHelper.attach_html("<h1>Test Results</h1><p>All tests passed!</p>", "HTML Report")
    print("  - HTML attached")
    
    print("✓ Additional features demonstrated")


def main():
    """主函数"""
    print("=" * 60)
    print("Allure Helper 功能演示")
    print("=" * 60)
    
    print("\n注意: 这些功能需要在 pytest 测试环境中运行才能看到效果")
    print("      在 Allure 报告中查看附件和步骤\n")
    
    demo_screenshot_attachment()
    demo_log_attachment()
    demo_json_attachment()
    demo_test_steps()
    demo_convenience_function()
    demo_additional_features()
    
    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)
    print("\n提示: 运行 pytest 测试并生成 Allure 报告来查看实际效果:")
    print("  1. pytest tests/ --alluredir=allure-results")
    print("  2. allure serve allure-results")


if __name__ == "__main__":
    main()

"""
Allure 辅助工具模块

该模块封装 Allure 报告相关的辅助功能，提供便捷的方法来附加各种类型的数据到测试报告中。
支持截图、日志、JSON 数据附件，以及测试步骤装饰器。
"""

import json
from contextlib import contextmanager
from typing import Any, Optional, Generator
import allure


class AllureHelper:
    """
    Allure 报告辅助工具类
    
    提供以下功能：
    - 附加截图到报告
    - 附加日志内容到报告
    - 附加 JSON 数据到报告
    - 测试步骤装饰器和上下文管理器
    
    所有方法都是静态方法，可以直接通过类名调用。
    """
    
    @staticmethod
    def attach_screenshot(screenshot_bytes: bytes, name: str = "Screenshot") -> None:
        """
        将截图附加到 Allure 报告
        
        Args:
            screenshot_bytes: 截图的字节数据
            name: 附件名称，默认为 "Screenshot"
        
        使用示例：
            screenshot = page.screenshot()
            AllureHelper.attach_screenshot(screenshot, "Login Page")
        """
        try:
            allure.attach(
                screenshot_bytes,
                name=name,
                attachment_type=allure.attachment_type.PNG
            )
        except Exception as e:
            # 如果附加失败，记录警告但不中断测试
            import logging
            logging.warning(f"Failed to attach screenshot '{name}' to Allure: {e}")
    
    @staticmethod
    def attach_log(log_content: str, name: str = "Log") -> None:
        """
        将日志内容附加到 Allure 报告
        
        Args:
            log_content: 日志文本内容
            name: 附件名称，默认为 "Log"
        
        使用示例:
            AllureHelper.attach_log("Test execution log content", "Execution Log")
        """
        try:
            allure.attach(
                log_content,
                name=name,
                attachment_type=allure.attachment_type.TEXT
            )
        except Exception as e:
            import logging
            logging.warning(f"Failed to attach log '{name}' to Allure: {e}")
    
    @staticmethod
    def attach_json(json_data: dict, name: str = "JSON Data") -> None:
        """
        将 JSON 数据附加到 Allure 报告
        
        Args:
            json_data: 要附加的字典数据
            name: 附件名称，默认为 "JSON Data"
        
        使用示例:
            response_data = {"status": "success", "user_id": 123}
            AllureHelper.attach_json(response_data, "API Response")
        """
        try:
            # 将字典转换为格式化的 JSON 字符串
            json_string = json.dumps(json_data, indent=2, ensure_ascii=False)
            allure.attach(
                json_string,
                name=name,
                attachment_type=allure.attachment_type.JSON
            )
        except (TypeError, ValueError) as e:
            # JSON 序列化失败
            import logging
            logging.warning(f"Failed to serialize JSON data for '{name}': {e}")
        except Exception as e:
            import logging
            logging.warning(f"Failed to attach JSON '{name}' to Allure: {e}")
    
    @staticmethod
    def attach_text(text_content: str, name: str = "Text") -> None:
        """
        将文本内容附加到 Allure 报告
        
        Args:
            text_content: 文本内容
            name: 附件名称，默认为 "Text"
            
        使用示例:
            AllureHelper.attach_text("Additional information", "Notes")
        """
        try:
            allure.attach(
                text_content,
                name=name,
                attachment_type=allure.attachment_type.TEXT
            )
        except Exception as e:
            import logging
            logging.warning(f"Failed to attach text '{name}' to Allure: {e}")
    
    @staticmethod
    def attach_html(html_content: str, name: str = "HTML") -> None:
        """
        将 HTML 内容附加到 Allure 报告
        
        Args:
            html_content: HTML 内容
            name: 附件名称，默认为 "HTML"
            
        使用示例:
            AllureHelper.attach_html("<h1>Test Results</h1>", "Results")
        """
        try:
            allure.attach(
                html_content,
                name=name,
                attachment_type=allure.attachment_type.HTML
            )
        except Exception as e:
            import logging
            logging.warning(f"Failed to attach HTML '{name}' to Allure: {e}")
    
    @staticmethod
    def attach_file(file_path: str, name: Optional[str] = None, 
                   attachment_type: allure.attachment_type = allure.attachment_type.TEXT) -> None:
        """
        将文件附加到 Allure 报告
        
        Args:
            file_path: 文件路径
            name: 附件名称，如果为 None 则使用文件名
            attachment_type: 附件类型，默认为 TEXT
            
        使用示例:
            AllureHelper.attach_file("logs/test.log", "Test Log", allure.attachment_type.TEXT)
        """
        import os
        
        if not os.path.exists(file_path):
            import logging
            logging.warning(f"File not found: {file_path}")
            return
        
        try:
            if name is None:
                name = os.path.basename(file_path)
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            allure.attach(
                file_content,
                name=name,
                attachment_type=attachment_type
            )
        except Exception as e:
            import logging
            logging.warning(f"Failed to attach file '{file_path}' to Allure: {e}")
    
    @staticmethod
    @contextmanager
    def step(step_name: str) -> Generator[None, None, None]:
        """
        测试步骤上下文管理器
        
        在 Allure 报告中创建一个测试步骤，用于组织测试逻辑和提高报告可读性。
        
        Args:
            step_name: 步骤名称
            
        Yields:
            None
            
        使用示例:
            with AllureHelper.step("Login to application"):
                page.goto("https://example.com/login")
                page.fill("#username", "user")
                page.fill("#password", "pass")
                page.click("#login-button")
        """
        with allure.step(step_name):
            yield
    
    @staticmethod
    def add_description(description: str) -> None:
        """
        为当前测试添加描述
        
        Args:
            description: 测试描述文本
            
        使用示例:
            AllureHelper.add_description("This test verifies the login functionality")
        """
        try:
            allure.dynamic.description(description)
        except Exception as e:
            import logging
            logging.warning(f"Failed to add description to Allure: {e}")
    
    @staticmethod
    def add_title(title: str) -> None:
        """
        为当前测试设置标题
        
        Args:
            title: 测试标题
            
        使用示例:
            AllureHelper.add_title("User Login Test")
        """
        try:
            allure.dynamic.title(title)
        except Exception as e:
            import logging
            logging.warning(f"Failed to add title to Allure: {e}")
    
    @staticmethod
    def add_severity(severity: str) -> None:
        """
        为当前测试设置严重程度
        
        Args:
            severity: 严重程度 (blocker, critical, normal, minor, trivial)
            
        使用示例:
            AllureHelper.add_severity("critical")
        """
        try:
            allure.dynamic.severity(severity)
        except Exception as e:
            import logging
            logging.warning(f"Failed to add severity to Allure: {e}")
    
    @staticmethod
    def add_tag(tag: str) -> None:
        """
        为当前测试添加标签
        
        Args:
            tag: 标签名称
            
        使用示例:
            AllureHelper.add_tag("smoke")
        """
        try:
            allure.dynamic.tag(tag)
        except Exception as e:
            import logging
            logging.warning(f"Failed to add tag to Allure: {e}")
    
    @staticmethod
    def add_link(url: str, link_type: str = "link", name: Optional[str] = None) -> None:
        """
        为当前测试添加链接
        
        Args:
            url: 链接 URL
            link_type: 链接类型 (link, issue, test_case)
            name: 链接显示名称，如果为 None 则使用 URL
            
        使用示例:
            AllureHelper.add_link("https://jira.example.com/ISSUE-123", "issue", "ISSUE-123")
        """
        try:
            if name is None:
                name = url
            allure.dynamic.link(url, link_type=link_type, name=name)
        except Exception as e:
            import logging
            logging.warning(f"Failed to add link to Allure: {e}")


# 便捷函数：创建测试步骤
def allure_step(step_name: str) -> Generator[None, None, None]:
    """
    创建 Allure 测试步骤的便捷函数
    
    Args:
        step_name: 步骤名称
        
    Returns:
        contextmanager: 步骤上下文管理器
        
    使用示例:
        with allure_step("Verify user profile"):
            assert user.name == "John Doe"
    """
    return AllureHelper.step(step_name)

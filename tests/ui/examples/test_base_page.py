"""
BasePage 基本功能测试

验证 BasePage 类的核心功能
"""

import pytest
from playwright.sync_api import Page
from base.ui.pages.base_page import BasePage
from core.log import get_logger

logger = get_logger(__name__)


@pytest.mark.ui
class TestBasePage:
    """BasePage 基本功能测试"""

    @pytest.fixture(autouse=True)
    def setup_logger(self):
        """设置日志"""
        # logger auto-initialized by get_logger

    def test_initialization(self, page: Page):
        """测试 BasePage 初始化"""
        base_page = BasePage(page)

        assert base_page.page is page
        assert base_page.logger is not None

    def test_navigate(self, page: Page):
        """测试页面导航功能 """
        base_page = BasePage(page)

        # 导航到测试页面
        base_page.navigate("https://example.com")

        # 验证 URL
        assert "example.com" in base_page.get_current_url()

    def test_get_title(self, page: Page):
        """测试获取页面标题"""
        base_page = BasePage(page)
        base_page.navigate("https://example.com")

        title = base_page.get_title()
        assert title is not None
        assert len(title) > 0

    def test_get_current_url(self, page: Page):
        """测试获取当前 URL"""
        base_page = BasePage(page)
        test_url = "https://example.com"

        base_page.navigate(test_url)
        current_url = base_page.get_current_url()

        assert test_url in current_url

    def test_wait_for_element(self, page: Page):
        """测试元素等待机制 """
        base_page = BasePage(page)
        base_page.navigate("https://example.com")

        # 等待 h1 元素
        locator = base_page.wait_for_element("h1")
        assert locator is not None

    def test_get_text(self, page: Page):
        """测试获取元素文本 """
        base_page = BasePage(page)
        base_page.navigate("https://example.com")

        # 获取 h1 文本
        text = base_page.get_text("h1")
        assert text is not None
        assert len(text) > 0

    def test_is_visible(self, page: Page):
        """测试检查元素可见性"""
        base_page = BasePage(page)
        base_page.navigate("https://example.com")

        # h1 应该可见
        assert base_page.is_visible("h1")

        # 不存在的元素应该不可见
        assert not base_page.is_visible("#nonexistent-element")

    def test_take_screenshot(self, page: Page):
        """测试截图功能 """
        base_page = BasePage(page)
        base_page.navigate("https://example.com")

        # 截图
        screenshot_bytes = base_page.take_screenshot("test_screenshot", attach_to_allure=False)

        # 验证截图数据
        assert screenshot_bytes is not None
        assert len(screenshot_bytes) > 0

    def test_execute_script(self, page: Page):
        """测试执行 JavaScript"""
        base_page = BasePage(page)
        base_page.navigate("https://example.com")

        # 执行简单的 JavaScript (evaluate requires expression or function, not bare return statement)
        result = base_page.execute_script("document.title")
        assert result is not None

    def test_get_attribute(self, page: Page):
        """测试获取元素属性"""
        base_page = BasePage(page)
        base_page.navigate("https://example.com")

        # 获取链接的 href 属性
        href = base_page.get_attribute("a", "href")
        assert href is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Example Page UI 测试

演示完整的 UI 测试用例，包括日志记录、截图和报告功能。

运行方式：
    # 运行所有测试
    pytest tests/ui/test_example_page.py -v

    # 并行运行
    pytest tests/ui/test_example_page.py -n auto -v

    # 生成 Allure 报告
    pytest tests/ui/test_example_page.py --alluredir=allure-results
    allure serve allure-results
"""

import pytest
import allure
from playwright.sync_api import Page

from base.ui.pages.example_page import ExamplePage
from core.log.logger import TestLogger
from core.reporting.allure_helper import AllureHelper
from core.cache.data_cache import DataCache


@pytest.mark.ui
@allure.feature("Example Page")
@allure.story("Page Navigation and Content")
class TestExamplePageBasics:
    """
    Example 页面基础功能测试

    测试页面导航、元素定位和内容验证。
    """

    @allure.title("验证页面可以成功打开")
    @allure.description("测试页面导航功能，确保页面能够正确加载")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_page_opens_successfully(self, page: Page):
        """
        测试页面打开功能

        验证：
        1. 页面能够成功导航
        2. 页面 URL 正确
        3. 页面标题正确
        """
        logger = TestLogger.get_logger("test_page_opens_successfully")
        logger.info("=== Starting test: Page opens successfully ===")

        # 步骤 1: 创建页面对象并打开页面
        with AllureHelper.step("创建 ExamplePage 对象并打开页面"):
            example_page = ExamplePage(page)
            example_page.open()
            logger.info("Page opened successfully")

        # 步骤 2: 验证 URL
        with AllureHelper.step("验证页面 URL"):
            current_url = example_page.get_current_url()
            logger.info(f"Current URL: {current_url}")
            assert "example.com" in current_url, f"Expected example.com in URL, got: {current_url}"

        # 步骤 3: 验证页面标题
        with AllureHelper.step("验证页面标题"):
            title = example_page.get_title()
            logger.info(f"Page title: {title}")
            assert "Example Domain" in title, f"Expected 'Example Domain' in title, got: {title}"

        # 步骤 4: 截图
        with AllureHelper.step("截取页面截图"):
            example_page.take_screenshot("page_opened")
            logger.info("Screenshot captured")

        logger.info("=== Test completed successfully ===")

    @allure.title("验证页面标题元素")
    @allure.description("测试页面 H1 标题元素的可见性和内容")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_page_heading(self, page: Page):
        """
        测试页面标题元素

        验证：
        1. H1 元素可见
        2. H1 文本内容正确
        """
        logger = TestLogger.get_logger("test_page_heading")
        logger.info("=== Starting test: Page heading ===")

        # 打开页面
        with AllureHelper.step("打开 Example 页面"):
            example_page = ExamplePage(page)
            example_page.open()

        # 验证标题可见
        with AllureHelper.step("验证标题元素可见"):
            is_visible = example_page.is_heading_visible()
            logger.info(f"Heading visible: {is_visible}")
            assert is_visible, "Heading should be visible"

        # 获取并验证标题文本
        with AllureHelper.step("获取并验证标题文本"):
            heading_text = example_page.get_heading_text()
            logger.info(f"Heading text: {heading_text}")

            assert "Example Domain" in heading_text, \
                f"Expected 'Example Domain' in heading, got: {heading_text}"

        # 将标题文本存储到缓存
        with AllureHelper.step("存储标题到数据缓存"):
            cache = DataCache.get_instance()
            cache.set("example_page_heading", heading_text)
            logger.info(f"Stored heading in cache: {heading_text}")

        logger.info("=== Test completed successfully ===")

    @allure.title("验证页面描述内容")
    @allure.description("测试页面描述段落的存在和内容")
    @allure.severity(allure.severity_level.NORMAL)
    def test_page_description(self, page: Page):
        """
        测试页面描述

        验证：
        1. 描述段落存在
        2. 描述文本不为空
        3. 描述包含预期关键词
        """
        logger = TestLogger.get_logger("test_page_description")
        logger.info("=== Starting test: Page description ===")

        # 打开页面
        with AllureHelper.step("打开页面"):
            example_page = ExamplePage(page)
            example_page.open()

        # 获取描述文本
        with AllureHelper.step("获取描述文本"):
            description = example_page.get_description_text()
            logger.info(f"Description length: {len(description)} characters")
            logger.info(f"Description: {description}")

        # 验证描述
        with AllureHelper.step("验证描述内容"):
            assert len(description) > 0, "Description should not be empty"
            assert "domain" in description.lower(), "Description should mention 'domain'"
            assert "examples" in description.lower(), "Description should mention 'examples'"
            logger.info("Description validation passed")

        # 附加描述到 Allure 报告
        AllureHelper.attach_json(
            {"description": description, "length": len(description)},
            "Page Description Data"
        )

        logger.info("=== Test completed successfully ===")

    @allure.title("验证 More Information 链接")
    @allure.description("测试页面上的外部链接")
    @allure.severity(allure.severity_level.NORMAL)
    def test_more_info_link(self, page: Page):
        """
        测试 More Information 链接

        验证：
        1. 链接元素存在
        2. 链接 href 属性正确
        3. 链接指向 IANA 网站
        """
        logger = TestLogger.get_logger("test_more_info_link")
        logger.info("=== Starting test: More info link ===")

        # 打开页面
        with AllureHelper.step("打开页面"):
            example_page = ExamplePage(page)
            example_page.open()

        # 获取链接 href
        with AllureHelper.step("获取链接 href 属性"):
            href = example_page.get_more_info_link_href()
            logger.info(f"Link href: {href}")

        # 验证链接
        with AllureHelper.step("验证链接 URL"):
            assert href is not None, "Link href should not be None"
            assert "iana.org" in href, f"Expected iana.org in href, got: {href}"
            logger.info("Link validation passed")

        # 存储链接到缓存
        with AllureHelper.step("存储链接到缓存"):
            cache = DataCache.get_instance()
            cache.set("more_info_link", href)
            logger.info(f"Stored link in cache: {href}")

        logger.info("=== Test completed successfully ===")


@pytest.mark.ui
@allure.feature("Example Page")
@allure.story("Page Verification")
class TestExamplePageVerification:
    """
    Example 页面完整性验证测试

    测试页面的整体状态和完整性。
    """

    @allure.title("验证页面完整性")
    @allure.description("验证页面所有关键元素都正确加载")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_page_integrity(self, page: Page):
        """
        测试页面完整性

        验证：
        1. 所有关键元素都存在
        2. 页面 URL 正确
        3. 页面状态正常
        """
        logger = TestLogger.get_logger("test_page_integrity")
        logger.info("=== Starting test: Page integrity ===")

        # 打开页面
        with AllureHelper.step("打开页面"):
            example_page = ExamplePage(page)
            example_page.open()

        # 执行完整性验证
        with AllureHelper.step("执行页面完整性验证"):
            is_valid = example_page.verify_page_loaded()
            logger.info(f"Page integrity check result: {is_valid}")

        # 断言验证结果
        with AllureHelper.step("断言验证结果"):
            assert is_valid, "Page integrity verification failed"
            logger.info("Page integrity verification passed")

        # 截取完整页面截图
        with AllureHelper.step("截取完整页面截图"):
            example_page.take_screenshot("page_integrity_full", full_page=True)
            logger.info("Full page screenshot captured")

        logger.info("=== Test completed successfully ===")

    @allure.title("验证页面元素可见性")
    @allure.description("验证所有关键元素的可见性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_elements_visibility(self, page: Page):
        """
        测试页面元素可见性

        验证：
        1. 标题元素可见
        2. 描述元素可见
        3. 链接元素可见
        """
        logger = TestLogger.get_logger("test_elements_visibility")
        logger.info("=== Starting test: Elements visibility ===")

        # 打开页面
        with AllureHelper.step("打开页面"):
            example_page = ExamplePage(page)
            example_page.open()

        # 检查标题可见性
        with AllureHelper.step("检查标题可见性"):
            heading_visible = example_page.is_visible(example_page.HEADING)
            logger.info(f"Heading visible: {heading_visible}")
            assert heading_visible, "Heading should be visible"

        # 检查描述可见性
        with AllureHelper.step("检查描述可见性"):
            description_visible = example_page.is_visible(example_page.DESCRIPTION)
            logger.info(f"Description visible: {description_visible}")
            assert description_visible, "Description should be visible"

        # 检查链接可见性
        with AllureHelper.step("检查链接可见性"):
            link_visible = example_page.is_visible(example_page.MORE_INFO_LINK)
            logger.info(f"Link visible: {link_visible}")
            assert link_visible, "Link should be visible"

        logger.info("=== All elements are visible ===")
        logger.info("=== Test completed successfully ===")


@pytest.mark.ui
@allure.feature("Framework Features")
@allure.story("Logging and Reporting")
class TestFrameworkFeatures:
    """
    框架功能演示测试

    演示日志记录、截图、数据缓存等框架功能。
    """

    @allure.title("演示日志记录功能")
    @allure.description("演示框架的多级别日志记录功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_logging_demo(self, page: Page):
        """
        演示日志记录功能

        展示：
        1. 不同级别的日志记录
        2. 日志自动附加到 Allure
        3. 日志格式化
        """
        logger = TestLogger.get_logger("test_logging_demo")

        # 记录不同级别的日志
        logger.debug("This is a DEBUG level log message")
        logger.info("This is an INFO level log message")
        logger.warning("This is a WARNING level log message")

        # 打开页面并记录操作
        with AllureHelper.step("执行页面操作并记录日志"):
            example_page = ExamplePage(page)
            logger.info("Opening example page...")
            example_page.open()
            logger.info("Page opened successfully")

            logger.info("Getting page title...")
            title = example_page.get_title()
            logger.info(f"Page title retrieved: {title}")

            logger.info("Getting heading text...")
            heading = example_page.get_heading_text()
            logger.info(f"Heading text retrieved: {heading}")

        logger.info("Logging demo completed")

    @allure.title("演示截图功能")
    @allure.description("演示框架的截图捕获和附加功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_screenshot_demo(self, page: Page):
        """
        演示截图功能

        展示：
        1. 手动截图
        2. 截图附加到 Allure
        3. 完整页面截图
        """
        logger = TestLogger.get_logger("test_screenshot_demo")
        logger.info("=== Starting screenshot demo ===")

        # 打开页面
        with AllureHelper.step("打开页面"):
            example_page = ExamplePage(page)
            example_page.open()

        # 截取普通截图
        with AllureHelper.step("截取普通截图"):
            example_page.take_screenshot("demo_normal_screenshot")
            logger.info("Normal screenshot captured")

        # 截取完整页面截图
        with AllureHelper.step("截取完整页面截图"):
            example_page.take_screenshot("demo_full_page_screenshot", full_page=True)
            logger.info("Full page screenshot captured")

        # 滚动页面后截图
        with AllureHelper.step("滚动后截图"):
            example_page.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            example_page.take_screenshot("demo_after_scroll")
            logger.info("Screenshot after scroll captured")

        logger.info("=== Screenshot demo completed ===")

    @allure.title("演示数据缓存功能")
    @allure.description("演示框架的数据缓存和共享功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_data_cache_demo(self, page: Page):
        """
        演示数据缓存功能

        展示：
        1. 数据存储到缓存
        2. 数据从缓存检索
        3. 缓存数据验证
        """
        logger = TestLogger.get_logger("test_data_cache_demo")
        logger.info("=== Starting data cache demo ===")

        # 获取缓存实例
        cache = DataCache.get_instance()

        # 打开页面并提取数据
        with AllureHelper.step("提取页面数据"):
            example_page = ExamplePage(page)
            example_page.open()

            heading = example_page.get_heading_text()
            description = example_page.get_description_text()
            url = example_page.get_current_url()

        # 存储数据到缓存
        with AllureHelper.step("存储数据到缓存"):
            cache.set("demo_heading", heading)
            cache.set("demo_description", description)
            cache.set("demo_url", url)
            logger.info("Data stored in cache")

        # 验证数据存在
        with AllureHelper.step("验证数据存在于缓存"):
            assert cache.has("demo_heading"), "Heading should be in cache"
            assert cache.has("demo_description"), "Description should be in cache"
            assert cache.has("demo_url"), "URL should be in cache"
            logger.info("All data exists in cache")

        # 检索并验证数据
        with AllureHelper.step("检索并验证缓存数据"):
            cached_heading = cache.get("demo_heading")
            cached_description = cache.get("demo_description")
            cached_url = cache.get("demo_url")

            assert cached_heading == heading, "Cached heading should match original"
            assert cached_description == description, "Cached description should match original"
            assert cached_url == url, "Cached URL should match original"
            logger.info("All cached data matches original data")

        # 附加缓存数据到 Allure
        AllureHelper.attach_json({
            "heading": cached_heading,
            "description": cached_description[:100] + "...",
            "url": cached_url
        }, "Cached Data")

        logger.info("=== Data cache demo completed ===")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--alluredir=allure-results"])

"""
UI 测试示例

演示如何使用测试框架编写 UI 自动化测试。
包含完整的测试用例，展示日志记录、截图、报告等功能。

运行方式：
    # 运行所有 UI 测试示例
    pytest examples/ui_test_example.py -v
    
    # 运行特定测试
    pytest examples/ui_test_example.py::TestExamplePage::test_page_title -v
    
    # 并行运行
    pytest examples/ui_test_example.py -n auto -v
    
    # 生成 Allure 报告
    pytest examples/ui_test_example.py --alluredir=allure-results
    allure serve allure-results
"""

import pytest
import allure
from playwright.sync_api import Page

from base.ui.pages.example_page import ExamplePage, SearchPage
from core.log.logger import TestLogger
from core.reporting.allure_helper import AllureHelper
from core.cache.data_cache import DataCache


@allure.feature("Example.com 页面测试")
@allure.story("基本页面功能")
class TestExamplePage:
    """
    Example.com 页面测试套件
    
    演示基本的页面对象使用和测试编写方法。
    """
    
    @allure.title("测试页面标题")
    @allure.description("验证 Example.com 页面标题是否正确显示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_page_title(self, page: Page):
        """
        测试页面标题
        
        验证：
        1. 页面能够成功加载
        2. 页面标题包含 "Example Domain"
        """
        logger = TestLogger.get_logger("test_page_title")
        logger.info("Starting test: test_page_title")
        
        with AllureHelper.step("打开 Example.com 页面"):
            example_page = ExamplePage(page)
            example_page.open()
        
        with AllureHelper.step("获取页面标题"):
            title = example_page.get_title()
            logger.info(f"Page title: {title}")
        
        with AllureHelper.step("验证标题内容"):
            assert "Example Domain" in title, f"Expected 'Example Domain' in title, got: {title}"
            logger.info("Title verification passed")
        
        # 截图
        with AllureHelper.step("截取页面截图"):
            example_page.take_screenshot("example_page_title")
    
    @allure.title("测试页面标题文本")
    @allure.description("验证页面 H1 标题文本内容")
    @allure.severity(allure.severity_level.NORMAL)
    def test_heading_text(self, page: Page):
        """
        测试页面 H1 标题文本
        
        验证：
        1. H1 元素可见
        2. H1 文本内容正确
        """
        logger = TestLogger.get_logger("test_heading_text")
        
        with AllureHelper.step("打开页面"):
            example_page = ExamplePage(page)
            example_page.open()
        
        with AllureHelper.step("检查标题可见性"):
            assert example_page.is_heading_visible(), "Heading should be visible"
            logger.info("Heading is visible")
        
        with AllureHelper.step("获取并验证标题文本"):
            heading_text = example_page.get_heading_text()
            assert "Example Domain" in heading_text, f"Expected 'Example Domain', got: {heading_text}"
            logger.info(f"Heading text verified: {heading_text}")
    
    @allure.title("测试页面描述")
    @allure.description("验证页面描述段落的内容")
    @allure.severity(allure.severity_level.NORMAL)
    def test_description_text(self, page: Page):
        """
        测试页面描述文本
        
        验证：
        1. 描述段落存在
        2. 描述文本不为空
        """
        logger = TestLogger.get_logger("test_description_text")
        
        with AllureHelper.step("打开页面"):
            example_page = ExamplePage(page)
            example_page.open()
        
        with AllureHelper.step("获取描述文本"):
            description = example_page.get_description_text()
            logger.info(f"Description: {description}")
        
        with AllureHelper.step("验证描述不为空"):
            assert len(description) > 0, "Description should not be empty"
            assert "illustrative examples" in description.lower(), "Description should mention examples"
            logger.info("Description verification passed")
    
    @allure.title("测试 More Information 链接")
    @allure.description("验证 More Information 链接的存在和属性")
    @allure.severity(allure.severity_level.NORMAL)
    def test_more_info_link(self, page: Page):
        """
        测试 More Information 链接
        
        验证：
        1. 链接存在且可见
        2. 链接 href 属性正确
        """
        logger = TestLogger.get_logger("test_more_info_link")
        
        with AllureHelper.step("打开页面"):
            example_page = ExamplePage(page)
            example_page.open()
        
        with AllureHelper.step("获取链接 href"):
            href = example_page.get_more_info_link_href()
            logger.info(f"Link href: {href}")
        
        with AllureHelper.step("验证链接 URL"):
            assert href is not None, "Link href should not be None"
            assert "iana.org" in href, f"Expected iana.org in href, got: {href}"
            logger.info("Link verification passed")
        
        # 将链接 URL 存储到缓存中，供其他测试使用
        cache = DataCache.get_instance()
        cache.set("more_info_url", href)
        logger.info(f"Stored URL in cache: {href}")
    
    @allure.title("测试页面完整性验证")
    @allure.description("验证页面所有关键元素都正确加载")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_page_verification(self, page: Page):
        """
        测试页面完整性
        
        验证：
        1. 所有关键元素都存在
        2. 页面 URL 正确
        3. 页面状态正常
        """
        logger = TestLogger.get_logger("test_page_verification")
        
        with AllureHelper.step("打开页面"):
            example_page = ExamplePage(page)
            example_page.open()
        
        with AllureHelper.step("执行页面验证"):
            is_valid = example_page.verify_page_loaded()
            logger.info(f"Page verification result: {is_valid}")
        
        with AllureHelper.step("断言验证结果"):
            assert is_valid, "Page verification failed"
            logger.info("Page verification passed")
        
        # 截取完整页面截图
        with AllureHelper.step("截取完整页面截图"):
            example_page.take_screenshot("page_verification_full", full_page=True)
    
    @allure.title("测试页面 URL")
    @allure.description("验证页面 URL 是否正确")
    @allure.severity(allure.severity_level.NORMAL)
    def test_current_url(self, page: Page):
        """
        测试当前页面 URL
        
        验证：
        1. 导航后 URL 正确
        2. URL 包含预期的域名
        """
        logger = TestLogger.get_logger("test_current_url")
        
        with AllureHelper.step("打开页面"):
            example_page = ExamplePage(page)
            example_page.open()
        
        with AllureHelper.step("获取当前 URL"):
            current_url = example_page.get_current_url()
            logger.info(f"Current URL: {current_url}")
        
        with AllureHelper.step("验证 URL"):
            assert "example.com" in current_url, f"Expected example.com in URL, got: {current_url}"
            logger.info("URL verification passed")


@allure.feature("搜索功能测试")
@allure.story("DuckDuckGo 搜索")
class TestSearchPage:
    """
    搜索页面测试套件
    
    演示表单交互、搜索功能和结果验证。
    """
    
    @allure.title("测试基本搜索功能")
    @allure.description("验证搜索功能能够正常工作并返回结果")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_basic_search(self, page: Page):
        """
        测试基本搜索功能
        
        验证：
        1. 搜索页面能够打开
        2. 能够输入搜索关键词
        3. 能够执行搜索
        4. 能够获取搜索结果
        """
        logger = TestLogger.get_logger("test_basic_search")
        logger.info("Starting basic search test")
        
        with AllureHelper.step("打开搜索页面"):
            search_page = SearchPage(page)
            search_page.open()
        
        with AllureHelper.step("执行搜索"):
            search_query = "Playwright Python"
            search_page.search(search_query)
            logger.info(f"Searched for: {search_query}")
        
        with AllureHelper.step("验证搜索结果"):
            has_results = search_page.has_search_results()
            assert has_results, "Search should return results"
            logger.info("Search results found")
        
        with AllureHelper.step("获取结果数量"):
            results_count = search_page.get_search_results_count()
            logger.info(f"Found {results_count} results")
            assert results_count > 0, "Should have at least one result"
        
        # 截图
        with AllureHelper.step("截取搜索结果页面"):
            search_page.take_screenshot("search_results")
    
    @allure.title("测试搜索结果内容")
    @allure.description("验证搜索结果包含相关内容")
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_results_content(self, page: Page):
        """
        测试搜索结果内容
        
        验证：
        1. 第一个搜索结果不为空
        2. 搜索结果与关键词相关
        """
        logger = TestLogger.get_logger("test_search_results_content")
        
        with AllureHelper.step("打开搜索页面并搜索"):
            search_page = SearchPage(page)
            search_page.open()
            search_page.search("Python automation")
        
        with AllureHelper.step("获取第一个结果"):
            first_result = search_page.get_first_result_text()
            logger.info(f"First result: {first_result[:100]}...")
        
        with AllureHelper.step("验证结果内容"):
            assert len(first_result) > 0, "First result should not be empty"
            logger.info("Result content verification passed")
        
        # 将第一个结果存储到缓存
        cache = DataCache.get_instance()
        cache.set("first_search_result", first_result)
        logger.info("Stored first result in cache")
    
    @allure.title("测试多次搜索")
    @allure.description("验证能够执行多次搜索操作")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize("search_query", [
        "Python",
        "Playwright",
        "Test Automation"
    ])
    def test_multiple_searches(self, page: Page, search_query: str):
        """
        测试多次搜索
        
        使用参数化测试验证不同搜索关键词。
        
        Args:
            search_query: 搜索关键词
        """
        logger = TestLogger.get_logger(f"test_multiple_searches_{search_query}")
        logger.info(f"Testing search with query: {search_query}")
        
        with AllureHelper.step(f"搜索: {search_query}"):
            search_page = SearchPage(page)
            search_page.open()
            search_page.search(search_query)
        
        with AllureHelper.step("验证有搜索结果"):
            has_results = search_page.has_search_results()
            assert has_results, f"Search for '{search_query}' should return results"
            logger.info(f"Search for '{search_query}' completed successfully")


@allure.feature("数据缓存演示")
@allure.story("跨测试数据共享")
class TestDataCacheDemo:
    """
    数据缓存演示测试套件
    
    演示如何使用 DataCache 在测试之间共享数据。
    """
    
    @allure.title("测试数据存储")
    @allure.description("演示如何将数据存储到缓存中")
    @allure.severity(allure.severity_level.NORMAL)
    def test_store_data(self, page: Page):
        """
        测试数据存储
        
        演示：
        1. 从页面提取数据
        2. 将数据存储到缓存
        """
        logger = TestLogger.get_logger("test_store_data")
        
        with AllureHelper.step("打开页面并提取数据"):
            example_page = ExamplePage(page)
            example_page.open()
            
            heading = example_page.get_heading_text()
            description = example_page.get_description_text()
        
        with AllureHelper.step("存储数据到缓存"):
            cache = DataCache.get_instance()
            cache.set("page_heading", heading)
            cache.set("page_description", description)
            
            logger.info(f"Stored heading: {heading}")
            logger.info(f"Stored description: {description[:50]}...")
        
        with AllureHelper.step("验证数据已存储"):
            assert cache.has("page_heading"), "Heading should be in cache"
            assert cache.has("page_description"), "Description should be in cache"
            logger.info("Data stored successfully")
    
    @allure.title("测试数据检索")
    @allure.description("演示如何从缓存中检索数据")
    @allure.severity(allure.severity_level.NORMAL)
    def test_retrieve_data(self, page: Page):
        """
        测试数据检索
        
        演示：
        1. 从缓存中检索之前存储的数据
        2. 验证数据的完整性
        
        注意：此测试依赖于 test_store_data 先执行
        """
        logger = TestLogger.get_logger("test_retrieve_data")
        
        with AllureHelper.step("从缓存检索数据"):
            cache = DataCache.get_instance()
            
            # 检查数据是否存在
            if cache.has("page_heading"):
                heading = cache.get("page_heading")
                logger.info(f"Retrieved heading: {heading}")
            else:
                logger.warning("Heading not found in cache")
                heading = None
            
            if cache.has("page_description"):
                description = cache.get("page_description")
                logger.info(f"Retrieved description: {description[:50]}...")
            else:
                logger.warning("Description not found in cache")
                description = None
        
        with AllureHelper.step("验证检索的数据"):
            # 如果数据存在，验证其有效性
            if heading:
                assert len(heading) > 0, "Heading should not be empty"
                logger.info("Heading data is valid")
            
            if description:
                assert len(description) > 0, "Description should not be empty"
                logger.info("Description data is valid")


@allure.feature("错误处理演示")
@allure.story("失败场景测试")
class TestErrorHandling:
    """
    错误处理演示测试套件
    
    演示框架如何处理各种错误情况。
    """
    
    @allure.title("测试元素不存在")
    @allure.description("演示当元素不存在时的错误处理")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.xfail(reason="Intentionally testing error handling")
    def test_element_not_found(self, page: Page):
        """
        测试元素不存在的情况
        
        这个测试预期会失败，用于演示错误处理和自动截图功能。
        """
        logger = TestLogger.get_logger("test_element_not_found")
        logger.info("Testing element not found scenario")
        
        with AllureHelper.step("打开页面"):
            example_page = ExamplePage(page)
            example_page.open()
        
        with AllureHelper.step("尝试查找不存在的元素"):
            # 这将触发超时错误和自动截图
            example_page.wait_for_element("#nonexistent-element", timeout=5000)
    
    @allure.title("测试超时处理")
    @allure.description("演示超时情况的处理")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="Skip timeout test to save time")
    def test_timeout_handling(self, page: Page):
        """
        测试超时处理
        
        演示当操作超时时框架的行为。
        """
        logger = TestLogger.get_logger("test_timeout_handling")
        
        with AllureHelper.step("设置短超时时间"):
            example_page = ExamplePage(page)
            example_page.open()
        
        with AllureHelper.step("执行可能超时的操作"):
            # 使用很短的超时时间
            try:
                example_page.wait_for_element("body", timeout=1)
            except Exception as e:
                logger.error(f"Timeout occurred as expected: {e}")
                raise


if __name__ == "__main__":
    # 运行测试
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--alluredir=allure-results"
    ])

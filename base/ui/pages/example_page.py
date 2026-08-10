"""
示例页面对象类

演示如何使用 BasePage 创建具体的页面对象类。
该示例使用 example.com 作为测试目标网站。
"""

from typing import Optional
from playwright.sync_api import Page
from base.ui.pages.base_page import BasePage
from core.log import get_logger

logger = get_logger(__name__)


class ExamplePage(BasePage):
    """
    Example.com 页面对象
    
    演示 Page Object Model 模式的实现。
    包含页面元素定位器和页面操作方法。
    """
    
    # ==================== 页面元素定位器 ====================
    
    # 页面标题
    HEADING = "h1"
    
    # 页面描述段落（第一个段落）
    DESCRIPTION = "div > p:first-of-type"
    
    # "More information" 链接
    MORE_INFO_LINK = "a"
    
    # ==================== 页面 URL ====================
    
    PAGE_URL = "https://example.com"
    
    def __init__(self, page: Page):
        """
        初始化 Example 页面对象
        
        Args:
            page: Playwright Page 对象
        """
        super().__init__(page)
        logger.info("ExamplePage initialized")
    
    def open(self) -> 'ExamplePage':
        """
        打开 Example.com 页面
        
        Returns:
            ExamplePage: 当前页面对象（支持链式调用）
        """
        self.navigate(self.PAGE_URL)
        self.wait_for_page_load()
        return self
    
    def wait_for_page_load(self) -> None:
        """
        等待页面完全加载
        """
        self.wait_for_element(self.HEADING)
        self.wait_for_load_state("networkidle")
        logger.info("Example page loaded successfully")
    
    def get_heading_text(self) -> str:
        """
        获取页面标题文本
        
        Returns:
            str: 标题文本
        """
        text = self.get_text(self.HEADING)
        logger.info(f"Heading text: {text}")
        return text
    
    def get_description_text(self) -> str:
        """
        获取页面描述文本
        
        Returns:
            str: 描述文本
        """
        text = self.get_text(self.DESCRIPTION)
        logger.info(f"Description text: {text}")
        return text
    
    def click_more_info_link(self) -> None:
        """
        点击 "More information" 链接
        """
        logger.info("Clicking 'More information' link")
        self.click(self.MORE_INFO_LINK)
    
    def is_heading_visible(self) -> bool:
        """
        检查标题是否可见
        
        Returns:
            bool: 标题是否可见
        """
        return self.is_visible(self.HEADING)
    
    def get_more_info_link_href(self) -> Optional[str]:
        """
        获取 "More information" 链接的 href 属性
        
        Returns:
            Optional[str]: 链接 URL
        """
        href = self.get_attribute(self.MORE_INFO_LINK, "href")
        logger.info(f"More info link href: {href}")
        return href
    
    def verify_page_loaded(self) -> bool:
        """
        验证页面是否正确加载
        
        Returns:
            bool: 页面是否正确加载
        """
        try:
            # 检查关键元素是否存在
            heading_visible = self.is_heading_visible()
            description_visible = self.is_visible(self.DESCRIPTION)
            link_visible = self.is_visible(self.MORE_INFO_LINK)
            
            # 检查 URL
            current_url = self.get_current_url()
            url_correct = "example.com" in current_url
            
            all_checks_passed = all([
                heading_visible,
                description_visible,
                link_visible,
                url_correct
            ])
            
            if all_checks_passed:
                logger.info("Page verification passed")
            else:
                logger.warning("Page verification failed")
            
            return all_checks_passed
            
        except Exception as e:
            logger.error(f"Page verification error: {e}")
            return False


class SearchPage(BasePage):
    """
    搜索页面对象示例
    
    演示如何创建包含表单交互的页面对象。
    使用 DuckDuckGo 作为示例。
    """
    
    # ==================== 页面元素定位器 ====================
    
    # 搜索输入框
    SEARCH_INPUT = "input[name='q']"
    
    # 搜索按钮
    SEARCH_BUTTON = "button[type='submit']"
    
    # 搜索结果
    SEARCH_RESULTS = "#links .result"
    
    # 第一个搜索结果
    FIRST_RESULT = "#links .result:first-child"
    
    # ==================== 页面 URL ====================
    
    PAGE_URL = "https://duckduckgo.com"
    
    def __init__(self, page: Page):
        """
        初始化搜索页面对象
        
        Args:
            page: Playwright Page 对象
        """
        super().__init__(page)
        logger.info("SearchPage initialized")
    
    def open(self) -> 'SearchPage':
        """
        打开搜索页面
        
        Returns:
            SearchPage: 当前页面对象（支持链式调用）
        """
        self.navigate(self.PAGE_URL)
        self.wait_for_element(self.SEARCH_INPUT)
        return self
    
    def search(self, query: str) -> 'SearchPage':
        """
        执行搜索
        
        Args:
            query: 搜索关键词
            
        Returns:
            SearchPage: 当前页面对象（支持链式调用）
        """
        logger.info(f"Searching for: {query}")
        
        # 填充搜索框
        self.fill(self.SEARCH_INPUT, query)
        
        # 点击搜索按钮
        self.click(self.SEARCH_BUTTON)
        
        # 等待搜索结果加载
        self.wait_for_element(self.SEARCH_RESULTS, timeout=10000)
        
        logger.info("Search completed")
        return self
    
    def get_search_results_count(self) -> int:
        """
        获取搜索结果数量
        
        Returns:
            int: 搜索结果数量
        """
        try:
            results = self.page.locator(self.SEARCH_RESULTS)
            count = results.count()
            logger.info(f"Found {count} search results")
            return count
        except Exception as e:
            logger.error(f"Failed to count search results: {e}")
            return 0
    
    def get_first_result_text(self) -> str:
        """
        获取第一个搜索结果的文本
        
        Returns:
            str: 第一个搜索结果的文本
        """
        text = self.get_text(self.FIRST_RESULT)
        logger.info(f"First result text: {text[:50]}...")
        return text
    
    def has_search_results(self) -> bool:
        """
        检查是否有搜索结果
        
        Returns:
            bool: 是否有搜索结果
        """
        return self.is_visible(self.SEARCH_RESULTS, timeout=5000)

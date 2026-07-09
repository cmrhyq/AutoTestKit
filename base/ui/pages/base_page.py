"""
UI 测试基础页面类

该模块实现 Page Object Model (POM) 模式的基础页面类，提供所有页面对象的通用功能。
包括页面导航、元素等待、常用操作、截图和日志记录等功能。
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union
from playwright.sync_api import Page, Locator, TimeoutError as PlaywrightTimeoutError

from core.config import Settings
from core.log.logger import TestLogger
from core.reporting.allure_helper import AllureHelper


class BasePage:
    """
    基础页面类
    
    实现 Page Object Model 模式，提供所有页面对象的通用功能：
    - 页面导航
    - 智能元素等待机制
    - 常用页面操作（点击、填充、获取文本等）
    - 自动截图功能
    - 集成日志记录
    
    所有具体的页面对象类都应该继承此类。
    """
    
    def __init__(self, page: Page, logger: Optional[logging.Logger] = None):
        """
        初始化基础页面对象
        
        Args:
            page: Playwright Page 对象
            logger: 日志记录器，如果为 None 则创建默认日志记录器
        """
        self.page = page
        self.logger = logger or TestLogger.get_logger(self.__class__.__name__)
        self.dialog_text = None  # 存储弹窗文本
        
        # 设置默认超时时间
        self.page.set_default_timeout(Settings.BROWSER_TIMEOUT)
        
        self.logger.debug(f"Initialized {self.__class__.__name__}")
    
    def navigate(self, url: str, wait_until: str = "domcontentloaded") -> None:
        """
        导航到指定 URL
        
        Args:
            url: 目标 URL
            wait_until: 等待条件，可选值：
                - 'load': 等待 load 事件触发
                - 'domcontentloaded': 等待 DOMContentLoaded 事件触发（默认）
                - 'networkidle': 等待网络空闲
                - 'commit': 等待网络响应接收完成
        
        使用示例:
            page.navigate("https://example.com")
            page.navigate("https://example.com/login", wait_until="load")
        """
        try:
            self.logger.info(f"Navigating to URL: {url}")
            
            with AllureHelper.step(f"Navigate to {url}"):
                self.page.goto(url, wait_until=wait_until, timeout=Settings.PAGE_LOAD_TIMEOUT)
            
            self.logger.info(f"Successfully navigated to: {url}")
            
        except PlaywrightTimeoutError as e:
            self.logger.error(f"Timeout while navigating to {url}: {e}")
            self._capture_failure_screenshot(f"navigation_timeout_{self._get_timestamp()}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to navigate to {url}: {e}")
            self._capture_failure_screenshot(f"navigation_error_{self._get_timestamp()}")
            raise
    
    def wait_for_element(
        self, 
        selector: str, 
        timeout: Optional[int] = None,
        state: str = "visible"
    ) -> Locator:
        """
        等待元素出现并返回定位器
        
        实现智能等待机制，在元素可用之前自动等待。
        
        Args:
            selector: 元素选择器（CSS、XPath 等）
            timeout: 超时时间（毫秒），如果为 None 则使用默认超时
            state: 元素状态，可选值：
                - 'attached': 元素已附加到 DOM
                - 'detached': 元素已从 DOM 分离
                - 'visible': 元素可见（默认）
                - 'hidden': 元素隐藏
        
        Returns:
            Locator: Playwright 定位器对象
        
        使用示例:
            element = page.wait_for_element("#login-button")
            element = page.wait_for_element("//button[@id='submit']", timeout=5000)
        """
        if timeout is None:
            timeout = Settings.BROWSER_TIMEOUT
        
        try:
            self.logger.debug(f"Waiting for element: {selector} (state: {state}, timeout: {timeout}ms)")
            
            locator = self.page.locator(selector)
            locator.wait_for(state=state, timeout=timeout)
            
            self.logger.debug(f"Element found: {selector}")
            return locator
            
        except PlaywrightTimeoutError as e:
            self.logger.error(f"Timeout waiting for element: {selector} (state: {state})")
            self._capture_failure_screenshot(f"element_timeout_{self._get_timestamp()}")
            raise
        except Exception as e:
            self.logger.error(f"Error waiting for element {selector}: {e}")
            self._capture_failure_screenshot(f"element_error_{self._get_timestamp()}")
            raise
    
    def click(
        self, 
        selector: str, 
        timeout: Optional[int] = None,
        force: bool = False,
        wait_before_click: bool = True
    ) -> None:
        """
        点击元素
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
            force: 是否强制点击（跳过可操作性检查）
            wait_before_click: 是否在点击前等待元素可见
        
        使用示例:
            page.click("#submit-button")
            page.click("button.primary", force=True)
        """
        try:
            self.logger.info(f"Clicking element: {selector}")
            
            with AllureHelper.step(f"Click element: {selector}"):
                if wait_before_click:
                    locator = self.wait_for_element(selector, timeout=timeout)
                else:
                    locator = self.page.locator(selector)
                
                locator.click(force=force, timeout=timeout or Settings.BROWSER_TIMEOUT)
            
            self.logger.info(f"Successfully clicked: {selector}")
            
        except PlaywrightTimeoutError as e:
            self.logger.error(f"Timeout while clicking element: {selector}")
            self._capture_failure_screenshot(f"click_timeout_{self._get_timestamp()}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to click element {selector}: {e}")
            self._capture_failure_screenshot(f"click_error_{self._get_timestamp()}")
            raise
    
    def fill(
        self, 
        selector: str, 
        text: str, 
        timeout: Optional[int] = None,
        clear_first: bool = True
    ) -> None:
        """
        填充文本到输入框
        
        Args:
            selector: 元素选择器
            text: 要填充的文本
            timeout: 超时时间（毫秒）
            clear_first: 是否先清空输入框
        
        使用示例:
            page.fill("#username", "testuser")
            page.fill("input[name='email']", "test@example.com", clear_first=False)
        """
        try:
            self.logger.info(f"Filling element {selector} with text: {text}")
            
            with AllureHelper.step(f"Fill '{selector}' with '{text}'"):
                locator = self.wait_for_element(selector, timeout=timeout)
                
                if clear_first:
                    locator.clear(timeout=timeout or Settings.BROWSER_TIMEOUT)
                
                locator.fill(text, timeout=timeout or Settings.BROWSER_TIMEOUT)
            
            self.logger.info(f"Successfully filled {selector}")
            
        except PlaywrightTimeoutError as e:
            self.logger.error(f"Timeout while filling element: {selector}")
            self._capture_failure_screenshot(f"fill_timeout_{self._get_timestamp()}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to fill element {selector}: {e}")
            self._capture_failure_screenshot(f"fill_error_{self._get_timestamp()}")
            raise
    
    def get_text(
        self, 
        selector: str, 
        timeout: Optional[int] = None
    ) -> str:
        """
        获取元素的文本内容
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
            
        Returns:
            str: 元素的文本内容
        
        使用示例:
            text = page.get_text("#welcome-message")
            error_msg = page.get_text(".error-message")
        """
        try:
            self.logger.debug(f"Getting text from element: {selector}")
            
            locator = self.wait_for_element(selector, timeout=timeout)
            text = locator.inner_text(timeout=timeout or Settings.BROWSER_TIMEOUT)
            
            self.logger.debug(f"Got text from {selector}: {text}")
            return text
            
        except PlaywrightTimeoutError as e:
            self.logger.error(f"Timeout while getting text from element: {selector}")
            self._capture_failure_screenshot(f"get_text_timeout_{self._get_timestamp()}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to get text from element {selector}: {e}")
            self._capture_failure_screenshot(f"get_text_error_{self._get_timestamp()}")
            raise
    
    def get_attribute(
        self, 
        selector: str, 
        attribute: str,
        timeout: Optional[int] = None
    ) -> Optional[str]:
        """
        获取元素的属性值
        
        Args:
            selector: 元素选择器
            attribute: 属性名称
            timeout: 超时时间（毫秒）
            
        Returns:
            Optional[str]: 属性值，如果属性不存在则返回 None
            
        使用示例:
            href = page.get_attribute("a.link", "href")
            value = page.get_attribute("input#email", "value")
        """
        try:
            self.logger.debug(f"Getting attribute '{attribute}' from element: {selector}")
            
            locator = self.wait_for_element(selector, timeout=timeout)
            value = locator.get_attribute(attribute, timeout=timeout or Settings.BROWSER_TIMEOUT)
            
            self.logger.debug(f"Got attribute '{attribute}' from {selector}: {value}")
            return value
            
        except Exception as e:
            self.logger.error(f"Failed to get attribute '{attribute}' from {selector}: {e}")
            self._capture_failure_screenshot(f"get_attribute_error_{self._get_timestamp()}")
            raise
    
    def is_visible(self, selector: str, timeout: int = 1000) -> bool:
        """
        检查元素是否可见
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒），默认 1 秒
            
        Returns:
            bool: 元素是否可见
            
        使用示例:
            if page.is_visible("#error-message"):
                print("Error message is displayed")
        """
        try:
            locator = self.page.locator(selector)
            return locator.is_visible(timeout=timeout)
        except Exception:
            return False
    
    def is_enabled(self, selector: str, timeout: Optional[int] = None) -> bool:
        """
        检查元素是否启用
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
            
        Returns:
            bool: 元素是否启用
            
        使用示例:
            if page.is_enabled("#submit-button"):
                page.click("#submit-button")
        """
        try:
            locator = self.wait_for_element(selector, timeout=timeout)
            return locator.is_enabled(timeout=timeout or Settings.BROWSER_TIMEOUT)
        except Exception:
            return False
    
    def wait_for_url(
        self, 
        url_pattern: Union[str, object], 
        timeout: Optional[int] = None
    ) -> None:
        """
        等待 URL 匹配指定模式
        
        Args:
            url_pattern: URL 模式（字符串或正则表达式）
            timeout: 超时时间（毫秒）
            
        使用示例:
            page.wait_for_url("**/dashboard")
            page.wait_for_url(re.compile(r".*/profile/\d+"))
        """
        try:
            self.logger.info(f"Waiting for URL pattern: {url_pattern}")
            self.page.wait_for_url(url_pattern, timeout=timeout or Settings.BROWSER_TIMEOUT)
            self.logger.info(f"URL matched pattern: {url_pattern}")
        except PlaywrightTimeoutError as e:
            self.logger.error(f"Timeout waiting for URL pattern: {url_pattern}")
            self._capture_failure_screenshot(f"url_timeout_{self._get_timestamp()}")
            raise
    
    def take_screenshot(
        self, 
        name: Optional[str] = None,
        full_page: bool = False,
        attach_to_allure: bool = True
    ) -> bytes:
        """
        截取当前页面的截图
        
        Args:
            name: 截图名称，如果为 None 则自动生成
            full_page: 是否截取整个页面（包括滚动区域）
            attach_to_allure: 是否附加到 Allure 报告
            
        Returns:
            bytes: 截图的字节数据
        
        使用示例:
            screenshot = page.take_screenshot("login_page")
            screenshot = page.take_screenshot(full_page=True)
        """
        try:
            # 生成截图名称
            if name is None:
                name = f"screenshot_{self._get_timestamp()}"
            
            self.logger.info(f"Taking screenshot: {name}")
            
            # 截取截图
            screenshot_bytes = self.page.screenshot(
                full_page=full_page,
                type=Settings.SCREENSHOT_FORMAT
            )
            
            # 保存到文件
            screenshot_dir = Path(Settings.SCREENSHOT_DIR)
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            
            screenshot_filename = f"{name}.{Settings.SCREENSHOT_FORMAT}"
            screenshot_path = screenshot_dir / screenshot_filename
            
            with open(screenshot_path, 'wb') as f:
                f.write(screenshot_bytes)
            
            self.logger.info(f"Screenshot saved: {screenshot_path}")
            
            # 附加到 Allure 报告
            if attach_to_allure:
                AllureHelper.attach_screenshot(screenshot_bytes, name)
            
            return screenshot_bytes
            
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            raise
    
    def scroll_to_element(self, selector: str, timeout: Optional[int] = None) -> None:
        """
        滚动到指定元素
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
            
        使用示例:
            page.scroll_to_element("#footer")
        """
        try:
            self.logger.debug(f"Scrolling to element: {selector}")
            locator = self.wait_for_element(selector, timeout=timeout)
            locator.scroll_into_view_if_needed(timeout=timeout or Settings.BROWSER_TIMEOUT)
            self.logger.debug(f"Scrolled to element: {selector}")
        except Exception as e:
            self.logger.error(f"Failed to scroll to element {selector}: {e}")
            raise
    
    def select_option(
        self, 
        selector: str, 
        value: Optional[str] = None,
        label: Optional[str] = None,
        index: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> None:
        """
        从下拉列表中选择选项
        
        Args:
            selector: 下拉列表选择器
            value: 选项的 value 属性
            label: 选项的文本内容
            index: 选项的索引
            timeout: 超时时间（毫秒）
            
        注意：value、label、index 三者至少提供一个
        
        使用示例:
            page.select_option("#country", value="US")
            page.select_option("#country", label="United States")
            page.select_option("#country", index=0)
        """
        try:
            self.logger.info(f"Selecting option from {selector}")
            locator = self.wait_for_element(selector, timeout=timeout)
            
            if value is not None:
                locator.select_option(value=value, timeout=timeout or Settings.BROWSER_TIMEOUT)
            elif label is not None:
                locator.select_option(label=label, timeout=timeout or Settings.BROWSER_TIMEOUT)
            elif index is not None:
                locator.select_option(index=index, timeout=timeout or Settings.BROWSER_TIMEOUT)
            else:
                raise ValueError("Must provide value, label, or index")
            
            self.logger.info(f"Successfully selected option from {selector}")
        except Exception as e:
            self.logger.error(f"Failed to select option from {selector}: {e}")
            self._capture_failure_screenshot(f"select_error_{self._get_timestamp()}")
            raise
    
    def check(self, selector: str, timeout: Optional[int] = None) -> None:
        """
        勾选复选框或单选按钮
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
            
        使用示例:
            page.check("#agree-terms")
        """
        try:
            self.logger.info(f"Checking element: {selector}")
            locator = self.wait_for_element(selector, timeout=timeout)
            locator.check(timeout=timeout or Settings.BROWSER_TIMEOUT)
            self.logger.info(f"Successfully checked: {selector}")
        except Exception as e:
            self.logger.error(f"Failed to check element {selector}: {e}")
            self._capture_failure_screenshot(f"check_error_{self._get_timestamp()}")
            raise
    
    def uncheck(self, selector: str, timeout: Optional[int] = None) -> None:
        """
        取消勾选复选框
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
            
        使用示例:
            page.uncheck("#newsletter")
        """
        try:
            self.logger.info(f"Unchecking element: {selector}")
            locator = self.wait_for_element(selector, timeout=timeout)
            locator.uncheck(timeout=timeout or Settings.BROWSER_TIMEOUT)
            self.logger.info(f"Successfully unchecked: {selector}")
        except Exception as e:
            self.logger.error(f"Failed to uncheck element {selector}: {e}")
            self._capture_failure_screenshot(f"uncheck_error_{self._get_timestamp()}")
            raise
    
    def get_current_url(self) -> str:
        """
        获取当前页面 URL
        
        Returns:
            str: 当前页面的 URL
            
        使用示例:
            current_url = page.get_current_url()
        """
        url = self.page.url
        self.logger.debug(f"Current URL: {url}")
        return url
    
    def get_title(self) -> str:
        """
        获取当前页面标题
        
        Returns:
            str: 页面标题
            
        使用示例:
            title = page.get_title()
        """
        title = self.page.title()
        self.logger.debug(f"Page title: {title}")
        return title
    
    def reload(self, timeout: Optional[int] = None) -> None:
        """
        重新加载当前页面
        
        Args:
            timeout: 超时时间（毫秒）
            
        使用示例:
            page.reload()
        """
        try:
            self.logger.info("Reloading page")
            self.page.reload(timeout=timeout or Settings.PAGE_LOAD_TIMEOUT)
            self.logger.info("Page reloaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to reload page: {e}")
            raise
    
    def go_back(self, timeout: Optional[int] = None) -> None:
        """
        返回上一页
        
        Args:
            timeout: 超时时间（毫秒）
            
        使用示例:
            page.go_back()
        """
        try:
            self.logger.info("Going back to previous page")
            self.page.go_back(timeout=timeout or Settings.PAGE_LOAD_TIMEOUT)
            self.logger.info("Navigated back successfully")
        except Exception as e:
            self.logger.error(f"Failed to go back: {e}")
            raise
    
    def go_forward(self, timeout: Optional[int] = None) -> None:
        """
        前进到下一页
        
        Args:
            timeout: 超时时间（毫秒）
            
        使用示例:
            page.go_forward()
        """
        try:
            self.logger.info("Going forward to next page")
            self.page.go_forward(timeout=timeout or Settings.PAGE_LOAD_TIMEOUT)
            self.logger.info("Navigated forward successfully")
        except Exception as e:
            self.logger.error(f"Failed to go forward: {e}")
            raise
    
    def wait_for_load_state(
        self, 
        state: str = "load",
        timeout: Optional[int] = None
    ) -> None:
        """
        等待页面加载到指定状态
        
        Args:
            state: 加载状态，可选值：
                - 'load': 等待 load 事件
                - 'domcontentloaded': 等待 DOMContentLoaded 事件
                - 'networkidle': 等待网络空闲
            timeout: 超时时间（毫秒）
            
        使用示例:
            page.wait_for_load_state("networkidle")
        """
        try:
            self.logger.debug(f"Waiting for load state: {state}")
            self.page.wait_for_load_state(state, timeout=timeout or Settings.PAGE_LOAD_TIMEOUT)
            self.logger.debug(f"Page reached load state: {state}")
        except Exception as e:
            self.logger.error(f"Timeout waiting for load state {state}: {e}")
            raise

    def post_add_locator_handler(self, selector):
        """
        添加元素定位器处理器,selector是定位器，用于关闭系统中随意弹出的弹窗
        """
        def handler(locator):
            self.logger.info(f"Element locator handler closes the popup and locates the element: {locator}")
            locator.click()

        self.page.add_locator_handler(selector, handler)

    # ==================== 多级菜单导航 ====================
    
    def open_menu(
        self,
        first_level: str,
        second_level: str = None,
        third_level: str = None,
        fourth_level: str = None,
        first_level_index: int = 0,
        second_level_index: int = 0,
        third_level_index: int = 0,
        fourth_level_index: int = 0,
        wait_after_click: bool = True
    ) -> None:
        """
        打开多级菜单导航
        
        支持最多4级菜单导航，智能判断菜单是否已展开避免重复点击导致收缩。
        当同名菜单存在多个时，通过 index 参数定位到第几个。
        
        Args:
            first_level: 一级菜单名称
            second_level: 二级菜单名称（可选）
            third_level: 三级菜单名称（可选）
            fourth_level: 四级菜单名称（可选）
            first_level_index: 一级菜单同名时的索引（0=第1个）
            second_level_index: 二级菜单同名时的索引
            third_level_index: 三级菜单同名时的索引
            fourth_level_index: 四级菜单同名时的索引
            wait_after_click: 点击后是否等待页面加载
        
        使用示例：
            # 只点击一级菜单
            page.open_menu("系统权限")
            
            # 点击二级菜单
            page.open_menu("系统权限", "用户管理")
            
            # 点击三级菜单
            page.open_menu("微服务", "服务治理", "路由规则")
            
            # 点击四级菜单
            page.open_menu("运维中心", "监控", "告警", "告警规则")
            
            # 同名菜单选择第2个
            page.open_menu("配置", second_level_index=1)
        """
        menu_path = ' > '.join(filter(None, [first_level, second_level, third_level, fourth_level]))
        self.logger.info(f"Opening menu: {menu_path}")
        
        try:
            with AllureHelper.step(f"Navigate menu: {menu_path}"):
                levels = [
                    (first_level, first_level_index),
                    (second_level, second_level_index),
                    (third_level, third_level_index),
                    (fourth_level, fourth_level_index),
                ]
                
                for i, (level_name, level_index) in enumerate(levels):
                    if level_name is None:
                        break
                    
                    locator = self.page.get_by_text(level_name, exact=True).nth(level_index)
                    
                    # 智能判断：如果下一级菜单已可见，跳过当前级的点击
                    next_level = levels[i + 1][0] if i + 1 < len(levels) else None
                    
                    if next_level is not None:
                        next_locator = self.page.get_by_text(next_level, exact=True).nth(levels[i + 1][1])
                        try:
                            if next_locator.is_visible(timeout=500):
                                self.logger.debug(f"Menu '{level_name}' already expanded, skipping")
                                continue
                        except Exception:
                            pass
                    
                    locator.click()
                    if wait_after_click:
                        self.page.wait_for_load_state(state="load")
                    self.logger.debug(f"Clicked menu: {level_name}")
                
                self.logger.info("Menu navigation completed")
                
        except PlaywrightTimeoutError as e:
            self.logger.error(f"Timeout while navigating menu: {e}")
            self._capture_failure_screenshot(f"menu_timeout_{self._get_timestamp()}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to navigate menu: {e}")
            self._capture_failure_screenshot(f"menu_error_{self._get_timestamp()}")
            raise

    # ==================== 文件上传 ====================
    
    def upload_file_by_input(
        self,
        locator: Locator,
        file_path: str,
        description: str = "Upload"
    ) -> None:
        """
        通过 input[type=file] 标签上传文件
        
        适用于页面上有 <input type="file"> 元素的场景。
        
        Args:
            locator: 文件输入框的定位器
            file_path: 文件的绝对路径或相对于项目 data 目录的路径
            description: 操作描述（用于日志和 Allure 报告）
        
        Raises:
            FileNotFoundError: 文件不存在
            PlaywrightTimeoutError: 操作超时
            
        使用示例：
            page.upload_file_by_input(
                page.page.locator("input[type='file']"),
                "test_data.csv",
                description="上传测试数据"
            )
        """
        resolved_path = self._resolve_file_path(file_path)
        self.logger.info(f"{description}: uploading file via input - {resolved_path}")
        
        try:
            with AllureHelper.step(f"{description}: {Path(resolved_path).name}"):
                locator.set_input_files(resolved_path)
            self.logger.info(f"{description}: file uploaded successfully")
        except Exception as e:
            self.logger.error(f"{description}: file upload failed - {e}")
            self._capture_failure_screenshot(f"upload_input_error_{self._get_timestamp()}")
            raise
    
    def upload_file_by_chooser(
        self,
        trigger_locator: Locator,
        file_path: str,
        description: str = "Upload"
    ) -> None:
        """
        通过文件选择器对话框上传文件
        
        适用于点击按钮后弹出系统文件选择器的场景。
        
        Args:
            trigger_locator: 触发文件选择器的按钮/元素定位器
            file_path: 文件的绝对路径或相对于项目 data 目录的路径
            description: 操作描述
            
        使用示例：
            page.upload_file_by_chooser(
                page.page.get_by_text("选择文件"),
                "document.pdf",
                description="上传合同文档"
            )
        """
        resolved_path = self._resolve_file_path(file_path)
        self.logger.info(f"{description}: uploading file via chooser - {resolved_path}")
        
        try:
            with AllureHelper.step(f"{description}: {Path(resolved_path).name}"):
                with self.page.expect_file_chooser() as fc_info:
                    trigger_locator.click()
                file_chooser = fc_info.value
                file_chooser.set_files(resolved_path)
            self.logger.info(f"{description}: file uploaded via chooser successfully")
        except Exception as e:
            self.logger.error(f"{description}: file chooser upload failed - {e}")
            self._capture_failure_screenshot(f"upload_chooser_error_{self._get_timestamp()}")
            raise

    # ==================== 文件下载 ====================
    
    def download_file(
        self,
        trigger_locator: Locator,
        save_dir: str = None,
        description: str = "Download"
    ) -> str:
        """
        下载文件
        
        监听下载事件，点击触发元素，等待下载完成并保存。
        
        Args:
            trigger_locator: 触发下载的按钮/链接定位器
            save_dir: 保存目录，默认为项目 data 目录
            description: 操作描述
            
        Returns:
            str: 下载文件的完整保存路径
            
        使用示例：
            path = page.download_file(page.page.get_by_text("下载报告"))
            print(f"File saved to: {path}")
        """
        if save_dir is None:
            save_dir = str(Settings.PROJECT_ROOT / "data")
        
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        self.logger.info(f"{description}: starting file download to {save_dir}")
        
        try:
            with AllureHelper.step(f"{description}"):
                with self.page.expect_download() as download_info:
                    trigger_locator.click()
                download = download_info.value
                save_path = str(Path(save_dir) / download.suggested_filename)
                download.save_as(save_path)
                
            self.logger.info(f"{description}: file saved - {save_path} (from {download.url})")
            return save_path
        except Exception as e:
            self.logger.error(f"{description}: file download failed - {e}")
            self._capture_failure_screenshot(f"download_error_{self._get_timestamp()}")
            raise

    # ==================== Dialog 弹窗处理 ====================
    
    def handle_dialog(
        self,
        action: str = "accept",
        dialog_type: str = None,
        prompt_text: str = None
    ) -> None:
        """
        注册原生弹窗（alert/confirm/prompt）处理器
        
        必须在触发弹窗的操作之前调用。处理完成后弹窗文本存储在 self.dialog_text。
        
        Args:
            action: 弹窗处理动作
                - "accept": 点击确定/OK
                - "dismiss": 点击取消/Cancel  
                - "text": 获取弹窗文本后点击确定
            dialog_type: 限制处理的弹窗类型（"alert"/"confirm"/"prompt"），
                         None 表示处理所有类型
            prompt_text: 当弹窗为 prompt 且 action="accept" 时填入的文本
            
        使用示例：
            # 处理删除确认弹窗
            page.handle_dialog(action="accept")
            page.page.locator("#delete-btn").click()
            
            # 取消确认弹窗
            page.handle_dialog(action="dismiss", dialog_type="confirm")
            page.page.locator("#dangerous-btn").click()
            
            # 获取弹窗文本
            page.handle_dialog(action="text")
            page.page.locator("#show-info").click()
            print(page.dialog_text)  # 获取弹窗内容
            
            # 处理 prompt 并输入内容
            page.handle_dialog(action="accept", prompt_text="new name")
            page.page.locator("#rename-btn").click()
        """
        self.dialog_text = None
        
        def _handler(dialog):
            if dialog_type and dialog.type != dialog_type:
                dialog.accept()
                return
            
            self.logger.info(f"Dialog detected: type={dialog.type}, message={dialog.message}")
            
            if action == "text":
                self.dialog_text = dialog.message
                dialog.accept()
            elif action == "dismiss":
                dialog.dismiss()
            else:  # accept
                if prompt_text and dialog.type == "prompt":
                    dialog.accept(prompt_text)
                else:
                    dialog.accept()
            
            self.logger.info(f"Dialog handled: action={action}")
        
        self.page.once("dialog", _handler)
        self.logger.info(f"Dialog handler registered: action={action}, type_filter={dialog_type}")

    # ==================== Tab/窗口切换 ====================
    
    def switch_to_tab(
        self,
        tab_index: int = -1,
        wait_timeout: int = 3000,
        description: str = "Switch tab"
    ) -> 'Page':
        """
        切换到指定标签页
        
        Args:
            tab_index: 标签页索引，0=第一个，-1=最后一个（新打开的）
            wait_timeout: 切换后等待时间（毫秒）
            description: 操作描述
            
        Returns:
            Page: 切换后的页面对象
            
        使用示例：
            # 切换到新打开的标签页
            new_page = page.switch_to_tab(-1)
            
            # 切换回第一个标签页
            page.switch_to_tab(0)
        """
        context = self.page.context
        
        try:
            self.page.wait_for_timeout(wait_timeout)
            pages = context.pages
            
            if abs(tab_index) > len(pages):
                raise IndexError(
                    f"Tab index {tab_index} out of range. "
                    f"Available tabs: {len(pages)} (index 0-{len(pages) - 1})"
                )
            
            target_page = pages[tab_index]
            target_page.bring_to_front()
            target_page.wait_for_load_state("load", timeout=Settings.PAGE_LOAD_TIMEOUT)
            
            self.logger.info(
                f"{description}: switched to tab[{tab_index}], "
                f"total: {len(pages)}, title: {target_page.title()}"
            )
            
            self.page = target_page
            return target_page
            
        except IndexError:
            raise
        except Exception as e:
            self.logger.error(f"{description}: tab switch failed - {e}")
            self._capture_failure_screenshot(f"tab_switch_error_{self._get_timestamp()}")
            raise
    
    def wait_for_new_tab(self, trigger_action, timeout: int = 10000) -> 'Page':
        """
        等待新标签页打开并返回新页面对象
        
        Args:
            trigger_action: 触发新标签页打开的可调用对象
            timeout: 等待超时时间（毫秒）
            
        Returns:
            Page: 新打开的页面对象
            
        使用示例：
            new_page = page.wait_for_new_tab(
                lambda: page.page.locator("a[target='_blank']").click()
            )
            print(f"New page: {new_page.title()}")
        """
        context = self.page.context
        
        try:
            with context.expect_page(timeout=timeout) as new_page_info:
                trigger_action()
            
            new_page = new_page_info.value
            new_page.wait_for_load_state("load", timeout=Settings.PAGE_LOAD_TIMEOUT)
            
            self.logger.info(f"New tab opened: {new_page.title()}")
            return new_page
        except Exception as e:
            self.logger.error(f"Failed to wait for new tab: {e}")
            raise

    # ==================== 内部辅助方法 ====================
    
    def _resolve_file_path(self, file_path: str) -> str:
        """
        解析文件路径，支持绝对路径和相对路径（相对于 data 目录）
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 解析后的绝对路径
            
        Raises:
            FileNotFoundError: 文件不存在
        """
        path = Path(file_path)
        
        if path.is_absolute():
            resolved = str(path)
        else:
            resolved = str(Settings.PROJECT_ROOT / "data" / file_path)
        
        if not Path(resolved).exists():
            raise FileNotFoundError(f"File not found: {resolved}")
        
        return resolved

    def execute_script(self, script: str, *args) -> Any:
        """
        执行 JavaScript 代码
        
        Args:
            script: JavaScript 代码
            *args: 传递给脚本的参数
            
        Returns:
            any: 脚本执行结果
            
        使用示例:
            result = page.execute_script("return document.title")
            page.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        """
        try:
            self.logger.debug(f"Executing script: {script[:50]}...")
            result = self.page.evaluate(script, *args)
            self.logger.debug("Script executed successfully")
            return result
        except Exception as e:
            self.logger.error(f"Failed to execute script: {e}")
            raise
    
    def _capture_failure_screenshot(self, name: str) -> None:
        """
        捕获失败时的截图（内部方法）
        
        Args:
            name: 截图名称
        """
        try:
            self.take_screenshot(name, full_page=False, attach_to_allure=True)
        except Exception as e:
            self.logger.warning(f"Failed to capture failure screenshot: {e}")
    
    @staticmethod
    def _get_timestamp() -> str:
        """
        获取当前时间戳字符串（内部方法）
        
        Returns:
            str: 格式化的时间戳
        """
        return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

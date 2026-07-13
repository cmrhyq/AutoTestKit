"""
UI 测试 Fixtures 模块

该模块定义 Playwright UI 测试所需的 fixtures，包括：
- 浏览器初始化 fixture
- 页面 fixture
- 保持登录 session fixture（避免重复登录）
- 失败时自动截图的 fixture
- Trace/视频录制清理
- 资源清理逻辑
"""
import os
import shutil
from logging import Logger

import pytest
from datetime import datetime
from typing import Generator
from playwright.sync_api import (
    sync_playwright, 
    Playwright,
    Browser, 
    BrowserContext, 
    Page
)

from core.config import env_manager
from core.config import Settings
from core.log.logger import TestLogger
from core.reporting.allure_helper import AllureHelper


@pytest.fixture(scope="session")
def playwright_instance() -> Generator[Playwright, None, None]:
    """
    Session-scoped Playwright 实例 fixture
    
    在整个测试会话中创建一个 Playwright 实例，所有测试共享。
    会话结束时自动清理资源。
    
    Yields:
        Playwright: Playwright 实例
    """
    logger = TestLogger.get_logger("PlaywrightFixture")
    logger.info("Initializing Playwright instance")
    
    with sync_playwright() as playwright:
        yield playwright
    
    logger.info("Playwright instance closed")


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright) -> Generator[Browser, None, None]:
    """
    Session-scoped 浏览器 fixture
    
    根据配置创建浏览器实例，在整个测试会话中共享。
    支持配置浏览器类型、无头模式、启动参数等。
    
    Args:
        playwright_instance: Playwright 实例
        
    Yields:
        Browser: 浏览器实例
    """
    logger = TestLogger.get_logger("BrowserFixture")
    
    # 根据配置选择浏览器类型
    browser_type = getattr(playwright_instance, Settings.BROWSER_TYPE)
    
    logger.info(f"Launching {Settings.BROWSER_TYPE} browser (headless={Settings.HEADLESS})")
    
    # 准备浏览器启动参数
    launch_options = {
        "headless": Settings.HEADLESS,
        "timeout": Settings.BROWSER_TIMEOUT,
        "slow_mo": Settings.SLOW_MODE,
    }
    
    # 添加浏览器启动参数
    if Settings.BROWSER_ARGS:
        launch_options["args"] = Settings.BROWSER_ARGS
    
    # 添加开发者工具选项
    if Settings.DEVTOOLS:
        launch_options["devtools"] = Settings.DEVTOOLS
    
    # 启动浏览器
    browser = browser_type.launch(**launch_options)
    
    logger.info(f"Browser launched successfully: {Settings.BROWSER_TYPE}")
    
    yield browser
    
    # 清理：关闭浏览器
    logger.info("Closing browser")
    browser.close()
    logger.info("Browser closed successfully")


@pytest.fixture(scope="session")
def ui_env():
    env = env_manager.get_config()
    return env


@pytest.fixture(scope="function")
def context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """
    Function-scoped 浏览器上下文 fixture
    
    为每个测试创建独立的浏览器上下文，确保测试之间的隔离。
    上下文包含独立的 cookies、localStorage 等状态。
    
    Args:
        browser: 浏览器实例
        
    Yields:
        BrowserContext: 浏览器上下文
    """
    logger = TestLogger.get_logger("ContextFixture")
    logger.debug("Creating new browser context")
    
    # 创建浏览器上下文，配置视口大小
    context = browser.new_context(
        # viewport={
        #     "width": Settings.VIEWPORT_WIDTH,
        #     "height": Settings.VIEWPORT_HEIGHT
        # },
        no_viewport=Settings.NO_VIEWPORT,
        ignore_https_errors=not Settings.VERIFY_SSL,
    )
    
    # 设置默认超时
    context.set_default_timeout(Settings.BROWSER_TIMEOUT)
    context.set_default_navigation_timeout(Settings.PAGE_LOAD_TIMEOUT)
    
    logger.debug(f"Browser context created with viewport {Settings.VIEWPORT_WIDTH}x{Settings.VIEWPORT_HEIGHT}")
    
    yield context
    
    # 清理：关闭上下文
    logger.debug("Closing browser context")
    context.close()
    logger.debug("Browser context closed")


@pytest.fixture(scope="function")
def page(context: BrowserContext, request: pytest.FixtureRequest) -> Generator[Page, None, None]:
    """
    Function-scoped 页面 fixture
    
    为每个测试创建新的页面实例。
    测试失败或异常时自动截图并附加到 Allure 报告。
    
    Args:
        context: 浏览器上下文
        request: Pytest 请求对象，用于获取测试信息
        
    Yields:
        Page: 页面实例
    """
    logger = TestLogger.get_logger("PageFixture")
    test_name = request.node.name
    
    logger.debug(f"Creating new page for test: {test_name}")
    
    # 创建新页面
    page = context.new_page()
    
    logger.debug(f"Page created for test: {test_name}")
    
    # 执行测试
    yield page
    
    # 测试结束后的处理
    try:
        # 检查测试是否失败
        if request.node.rep_call.failed if hasattr(request.node, 'rep_call') else False:
            logger.warning(f"Test failed: {test_name}")
            _capture_failure_screenshot(page, test_name, "test_failure")
    except Exception as e:
        logger.error(f"Error in page fixture teardown: {e}")
    finally:
        # 清理：关闭页面
        logger.debug(f"Closing page for test: {test_name}")
        page.close()
        logger.debug(f"Page closed for test: {test_name}")


@pytest.fixture(scope="function")
def auto_screenshot_on_failure(request: pytest.FixtureRequest, page: Page) -> Generator[None, None, None]:
    """
    自动截图 fixture（失败时）
    
    当测试失败或抛出异常时，自动捕获截图并附加到 Allure 报告。
    此 fixture 自动应用于所有使用 page fixture 的测试。
    
    Args:
        request: Pytest 请求对象
        page: 页面实例
        
    Yields:
        None
    """
    logger = TestLogger.get_logger("AutoScreenshot")
    test_name = request.node.name
    
    # 测试执行前不做任何操作
    yield
    
    # 测试执行后检查是否需要截图
    if not Settings.SCREENSHOT_ON_FAILURE:
        return
    
    try:
        # 检查测试是否失败或出错
        if hasattr(request.node, 'rep_call'):
            if request.node.rep_call.failed:
                logger.info(f"Test failed, capturing screenshot: {test_name}")
                _capture_failure_screenshot(page, test_name, "failure")
            elif request.node.rep_call.outcome == 'failed':
                logger.info(f"Test failed with exception, capturing screenshot: {test_name}")
                _capture_failure_screenshot(page, test_name, "exception")
    except Exception as e:
        logger.warning(f"Failed to capture automatic screenshot for {test_name}: {e}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Pytest hook: 在测试报告生成时捕获测试结果
    
    此 hook 用于在测试执行的各个阶段（setup, call, teardown）捕获测试结果，
    以便在 fixture 中判断测试是否失败。
    
    Args:
        item: 测试项
        call: 测试调用信息
    """
    # 执行所有其他 hooks
    outcome = yield
    rep = outcome.get_result()
    
    # 将测试结果附加到测试项，以便 fixture 可以访问
    setattr(item, f"rep_{rep.when}", rep)


def _capture_failure_screenshot(page: Page, test_name: str, failure_type: str) -> None:
    """
    捕获失败截图的辅助函数
    
    生成唯一的截图文件名（包含时间戳和测试名称），
    捕获截图并附加到 Allure 报告。
    
    Args:
        page: 页面实例
        test_name: 测试名称
        failure_type: 失败类型（failure, exception 等）
    """
    logger = TestLogger.get_logger("ScreenshotCapture")
    
    try:
        # 生成唯一的截图文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        screenshot_name = f"{test_name}_{failure_type}_{timestamp}"
        
        logger.info(f"Capturing screenshot: {screenshot_name}")
        
        # 捕获截图
        screenshot_bytes = page.screenshot(
            type=Settings.SCREENSHOT_FORMAT,
            full_page=False
        )
        
        # 附加到 Allure 报告
        AllureHelper.attach_screenshot(
            screenshot_bytes,
            name=f"Failure Screenshot - {test_name}"
        )
        
        logger.info(f"Screenshot captured and attached to Allure: {screenshot_name}")
        
    except Exception as e:
        logger.error(f"Failed to capture failure screenshot for {test_name}: {e}")


@pytest.fixture(scope="function")
def ui_logger(request: pytest.FixtureRequest) -> Logger:
    """
    UI 测试日志记录器 fixture
    
    为每个测试提供独立的日志记录器实例。
    
    Args:
        request: Pytest 请求对象
        
    Returns:
        TestLogger: 日志记录器实例
    """
    test_name = request.node.name
    return TestLogger.get_logger(f"UITest.{test_name}")


# ==================== 保持登录 Session Fixture ====================

@pytest.fixture(scope="session")
def authenticated_context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """
    Session-scoped 已认证的浏览器上下文 fixture
    
    在整个测试会话中只登录一次，后续所有测试复用已登录的 context。
    适用于需要登录后测试多个页面的场景，避免每个测试重复登录。
    
    用法：在测试类/模块中使用此 fixture，然后通过 context 创建 page。
    登录逻辑通过子类或外部 conftest 注入。
    
    Args:
        browser: 浏览器实例
        
    Yields:
        BrowserContext: 已认证的浏览器上下文
        
    使用示例（在 conftest.py 中）：
        @pytest.fixture(scope="session")
        def authenticated_context(browser, ui_env):
            context = browser.new_context(
                viewport={"width": 1440, "height": 960}
            )
            page = context.new_page()
            # 执行登录操作
            page.goto(ui_env.get("paas_url") + "/#/login")
            page.fill("#username", ui_env.get("admin_user"))
            page.fill("#password", ui_env.get("admin_password"))
            page.click("#login-btn")
            page.wait_for_load_state("networkidle")
            page.close()  # 关闭登录页面，保留 context 的认证状态
            yield context
            context.close()
    """
    logger = TestLogger.get_logger("AuthenticatedContext")
    logger.info("Creating authenticated browser context")
    
    # 创建带配置的 context
    context_options = {
        "viewport": {
            "width": Settings.VIEWPORT_WIDTH,
            "height": Settings.VIEWPORT_HEIGHT
        },
        "ignore_https_errors": not Settings.VERIFY_SSL,
    }
    
    # 如果无头模式需要指定分辨率
    if Settings.HEADLESS:
        context_options["viewport"] = {"width": 1440, "height": 960}
    
    context = browser.new_context(**context_options)
    context.set_default_timeout(Settings.BROWSER_TIMEOUT)
    context.set_default_navigation_timeout(Settings.PAGE_LOAD_TIMEOUT)
    
    logger.info("Authenticated context created (login should be performed by override)")
    
    yield context
    
    logger.info("Closing authenticated browser context")
    context.close()


@pytest.fixture(scope="module")
def module_page(authenticated_context: BrowserContext) -> Generator[Page, None, None]:
    """
    Module-scoped 页面 fixture（使用已认证的 context）
    
    每个测试模块共享一个页面实例，基于已登录的 context 创建。
    适用于同一模块内的多个测试需要共享登录状态的场景。
    
    Args:
        authenticated_context: 已认证的浏览器上下文
        
    Yields:
        Page: 页面实例
        
    使用示例：
        class TestDashboard:
            def test_view_stats(self, module_page):
                module_page.goto("/dashboard")
                assert module_page.title() == "Dashboard"
            
            def test_export_report(self, module_page):
                module_page.locator("#export").click()
    """
    logger = TestLogger.get_logger("ModulePage")
    logger.debug("Creating module-scoped page from authenticated context")
    
    page = authenticated_context.new_page()
    yield page
    page.close()
    
    logger.debug("Module page closed")


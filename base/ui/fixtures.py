"""
UI 测试 Fixtures 模块

该模块定义 Playwright UI 测试所需的 fixtures，包括：
- 浏览器初始化 fixture
- 页面 fixture
- 保持登录 session fixture（避免重复登录）
- 失败时自动截图的 fixture
- Trace/视频录制清理
- 资源清理逻辑

说明：与本模块配套的 `pytest_runtest_makereport` hook 定义在
`tests/ui/conftest.py` 中，用于将测试结果（rep_setup / rep_call / rep_teardown）
挂载到 test item 上，供本模块的 fixture 判断测试是否失败。
"""
import pytest
from datetime import datetime
from typing import Any, Dict, Generator
from playwright.sync_api import (
    sync_playwright,
    Playwright,
    Browser,
    BrowserContext,
    Page,
)

from core.config import Settings
from core.log import get_logger
from core.reporting.allure_helper import AllureHelper


logger = get_logger(__name__)


def _build_context_options() -> Dict[str, Any]:
    """
    构建 browser.new_context 的通用参数

    统一 `context` 与 `authenticated_context` 的创建行为，避免两处配置漂移。

    Returns:
        Dict[str, Any]: 传递给 browser.new_context 的关键字参数
    """
    options: Dict[str, Any] = {
        "no_viewport": Settings.NO_VIEWPORT,
        "ignore_https_errors": not Settings.VERIFY_SSL,
    }

    # 无头模式下强制指定视口，保证渲染尺寸一致
    if Settings.HEADLESS and not Settings.NO_VIEWPORT:
        options["viewport"] = {"width": 1920, "height": 1080}

    return options


def _test_failed(request: pytest.FixtureRequest) -> bool:
    """
    判断当前测试的 call 阶段是否失败

    Args:
        request: Pytest 请求对象

    Returns:
        bool: 若 call 阶段失败返回 True，否则 False
    """
    rep_call = getattr(request.node, "rep_call", None)
    return bool(rep_call is not None and rep_call.failed)


@pytest.fixture(scope="session")
def playwright_instance() -> Generator[Playwright, None, None]:
    """
    Session-scoped Playwright 实例 fixture

    在整个测试会话中创建一个 Playwright 实例，所有测试共享。
    会话结束时自动清理资源。

    Yields:
        Playwright: Playwright 实例
    """
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

    browser_type = getattr(playwright_instance, Settings.BROWSER_TYPE)

    logger.info(f"Launching {Settings.BROWSER_TYPE} browser (headless={Settings.HEADLESS})")

    launch_options: Dict[str, Any] = {
        "headless": Settings.HEADLESS,
        "timeout": Settings.BROWSER_TIMEOUT,
        "slow_mo": Settings.SLOW_MODE,
    }

    if Settings.BROWSER_ARGS:
        launch_options["args"] = Settings.BROWSER_ARGS

    if Settings.DEVTOOLS:
        launch_options["devtools"] = Settings.DEVTOOLS

    browser = browser_type.launch(**launch_options)

    logger.info(f"Browser launched successfully: {Settings.BROWSER_TYPE}")

    yield browser

    logger.info("Closing browser")
    browser.close()
    logger.info("Browser closed successfully")


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
    logger.debug("Creating new browser context")

    context = browser.new_context(**_build_context_options())

    context.set_default_timeout(Settings.BROWSER_TIMEOUT)
    context.set_default_navigation_timeout(Settings.PAGE_LOAD_TIMEOUT)

    yield context

    logger.debug("Closing browser context")
    context.close()
    logger.debug("Browser context closed")


@pytest.fixture(scope="function")
def page(context: BrowserContext, request: pytest.FixtureRequest) -> Generator[Page, None, None]:
    """
    Function-scoped 页面 fixture

    为每个测试创建新的页面实例。测试失败或异常时自动截图并附加到
    Allure 报告（仅在 Settings.SCREENSHOT_ON_FAILURE 为 True 时生效）。

    Args:
        context: 浏览器上下文
        request: Pytest 请求对象，用于获取测试信息

    Yields:
        Page: 页面实例
    """
    test_name = request.node.name

    logger.debug(f"Creating new page for test: {test_name}")

    page = context.new_page()

    logger.debug(f"Page created for test: {test_name}")

    yield page

    try:
        if Settings.SCREENSHOT_ON_FAILURE and _test_failed(request):
            logger.warning(f"Test failed: {test_name}")
            _capture_failure_screenshot(page, test_name, "test_failure")
    except Exception as e:
        logger.error(f"Error in page fixture teardown: {e}")
    finally:
        logger.debug(f"Closing page for test: {test_name}")
        page.close()
        logger.debug(f"Page closed for test: {test_name}")


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
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        screenshot_name = f"{test_name}_{failure_type}_{timestamp}"

        logger.info(f"Capturing screenshot: {screenshot_name}")

        screenshot_bytes = page.screenshot(
            type=Settings.SCREENSHOT_FORMAT,
            full_page=False,
        )

        AllureHelper.attach_screenshot(
            screenshot_bytes,
            name=f"Failure Screenshot - {test_name}",
        )

        logger.info(f"Screenshot captured and attached to Allure: {screenshot_name}")

    except Exception as e:
        logger.error(f"Failed to capture failure screenshot for {test_name}: {e}")


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
        def authenticated_context(browser, test_env):
            context = browser.new_context(
                viewport={"width": 1440, "height": 960}
            )
            page = context.new_page()
            page.goto(test_env.get("paas_url") + "/#/login")
            page.fill("#username", test_env.get("admin_user"))
            page.fill("#password", test_env.get("admin_password"))
            page.click("#login-btn")
            page.wait_for_load_state("networkidle")
            page.close()
            yield context
            context.close()
    """
    logger.info("Creating authenticated browser context")

    context = browser.new_context(**_build_context_options())
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
    logger.debug("Creating module-scoped page from authenticated context")

    page = authenticated_context.new_page()
    yield page
    page.close()

    logger.debug("Module page closed")

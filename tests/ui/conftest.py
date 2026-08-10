"""
UI 测试专用的 conftest 配置

该文件仅在运行 UI 测试时加载 UI fixtures，
避免在 API 测试时初始化浏览器。

同时在此定义 `pytest_runtest_makereport` hook，将测试各阶段结果
（rep_setup / rep_call / rep_teardown）挂载到 test item 上，
供 base/ui/fixtures.py 中的 fixture 判断测试是否失败以触发截图。
"""

from base.ui.fixtures import *  # noqa: F401,F403
from base.ui.fixtures import _build_context_options
from base.ui.pages.sandbox.login_page import LoginPage


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Pytest hook: 在测试报告生成时捕获测试结果

    在 setup / call / teardown 三个阶段分别把 report 对象挂载到 test item 上，
    命名为 rep_setup / rep_call / rep_teardown，供 fixture teardown 阶段读取。

    Args:
        item: 测试项
        call: 测试调用信息
    """
    outcome = yield
    rep = outcome.get_result()

    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(scope="session")
def login_context(browser, test_env):
    """
    Sandbox UI 登录方法
    Args:
        browser: 浏览器实例
        test_env: 测试环境变量

    Returns: None

    """
    context = browser.new_context(**_build_context_options())
    page = context.new_page()

    assert test_env.get("ui_base_url"), f"config/env_*.yaml 中未配置 ui_base_url"
    assert test_env.get("ui_username"), f"config/env_*.yaml 中未配置 ui_username"
    assert test_env.get("ui_password"), f"config/env_*.yaml 中未配置 ui_password"

    login_page = LoginPage(page)
    with AllureHelper.step("创建 Sandbox Login 对象并打开页面"):
        login_page.navigate(str(test_env.get("ui_base_url")))
        logger.info("Page opened successfully")

    with AllureHelper.step("验证页面 URL"):
        current_url = login_page.get_current_url()
        logger.info(f"Current URL: {current_url}")
        assert str(test_env.get("ui_base_url")) in current_url, f"Expected {test_env.get('ui_base_url')} in URL, got: {current_url}"

    with AllureHelper.step("输入账号密码登陆"):
        logger.debug(f"Current Username: {test_env.get('ui_username')}, Password: {test_env.get('ui_password')}")
        login_page.login(str(test_env.get("ui_username")), str(test_env.get("ui_password")))

    with AllureHelper.step("截取页面截图"):
        login_page.take_screenshot("sandbox_login_page")
        logger.info("Screenshot captured")

    yield context
    context.close()

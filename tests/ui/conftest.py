"""
UI 测试专用的 conftest 配置

该文件仅在运行 UI 测试时加载 UI fixtures，
避免在 API 测试时初始化浏览器。
"""

from base.ui.fixtures import *  # noqa: F401,F403
from base.ui.fixtures import _build_context_options
from base.ui.pages.login import LoginPage


@pytest.fixture(scope="session")
def login_context(browser, test_env, username: str = None, password: str = None):
    """
    Sandbox UI 登录方法
    Args:
        browser: 浏览器实例
        test_env: 测试环境变量
        username: 登录的用户账号
        password: 登录的用户密码

    Returns: None

    """
    context = browser.new_context(**_build_context_options())
    page = context.new_page()

    assert test_env.get("ui_base_url"), f"config/env_*.yaml 中未配置 ui_base_url"

    if username is None or password is None:
        logger.warning(f"Username 或 Password 为空，将使用 env_*.yaml 配置的用户")
        username = str(test_env.get("ui_username"))
        assert username, f"config/env_*.yaml 中未配置 ui_username"
        password = str(test_env.get("ui_password"))
        assert password, f"config/env_*.yaml 中未配置 ui_password"

    login_page = LoginPage(page)
    with AllureHelper.step("创建 Sandbox Login 对象并打开页面"):
        login_page.navigate(str(test_env.get("ui_base_url")))
        logger.info("Page opened successfully")

    with AllureHelper.step("验证页面 URL"):
        current_url = login_page.get_current_url()
        logger.info(f"Current URL: {current_url}")
        assert str(test_env.get("ui_base_url")) in current_url, f"Expected {test_env.get('ui_base_url')} in URL, got: {current_url}"

    with AllureHelper.step("输入账号密码登陆"):
        logger.debug(f"Current Username: {username}, Password: {password}")
        login_page.login(username, password)

    with AllureHelper.step("截取页面截图"):
        login_page.take_screenshot("sandbox_login_page")
        logger.info("Screenshot captured")

    yield context, page
    context.close()

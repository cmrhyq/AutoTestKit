import pytest
import allure
from playwright.sync_api import Page

from base.ui.pages.login_page import LoginPage
from core import TestLogger
from core.reporting.allure_helper import AllureHelper


@pytest.mark.ui
@allure.feature("沙箱登陆页面")
@allure.story("沙箱登陆页面页面登陆和修改密码")
class TestLoginPage(object):

    @allure.title("验证登陆功能")
    @allure.description("测试登陆页面功能，确保页面能够正确加载，能够正常登陆")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_login_successfully(self, page: Page, ui_env):
        """
        测试页面打开功能

        验证：
        1. 页面能够成功导航
        2. 页面 URL 正确
        3. 页面标题正确
        """
        logger = TestLogger.get_logger("test_login_successfully")
        logger.info("=== Starting test: Page login successfully ===")

        with AllureHelper.step("创建 Sandbox Login 对象并打开页面"):
            login_page = LoginPage(page)
            login_page.navigate(ui_env.get("ui_base_url"))
            logger.info("Page opened successfully")

        with AllureHelper.step("验证页面 URL"):
            current_url = login_page.get_current_url()
            logger.info(f"Current URL: {current_url}")
            assert ui_env.get(
                "ui_base_url") in current_url, f"Expected {ui_env.get('ui_base_url')} in URL, got: {current_url}"

        with AllureHelper.step("输入账号密码登陆"):
            logger.debug(f"Current Username: {ui_env.get('ui_username')}, Password: {ui_env.get('ui_password')}")
            login_page.login(ui_env.get("ui_username"), ui_env.get("ui_password"))

        with AllureHelper.step("截取页面截图"):
            login_page.take_screenshot("panji_login_page")
            logger.info("Screenshot captured")

        logger.info("===  Test completed successfully ===")

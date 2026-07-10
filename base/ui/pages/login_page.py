from base.ui.pages.base_page import BasePage
from playwright.sync_api import Page, expect


class LoginPage(BasePage):

    # ==================== 页面 URL ====================
    def __init__(self, page: Page):
        """
        初始化 Login Page 页面对象

        Args:
            page: Playwright Page 对象
        """
        super().__init__(page)
        self.logger.info("Login Page Initialized")

        self.input_username = page.get_by_placeholder("请输入用户名")
        self.input_password = page.get_by_placeholder("请输入密码")
        self.btn_login = page.get_by_role("button", name="登录")

        # 修改密码窗口
        self.input_old_password = page.get_by_placeholder("请输入旧密码")
        self.input_new_password = page.get_by_placeholder("请输入新密码")
        self.input_confirm_password = page.get_by_placeholder("请输入确认密码")
        self.btn_confirm_password = page.get_by_role("button", name="确定")

        # 弹窗继续登录按钮
        self.btn_continue_login = self.page.get_by_role("button", name="继续登录")

        # 告警
        self.alert = page.locator(".el-message__content").first  # 告警框

    def login(self, username: str, password: str):
        # 元素定位器处理器关闭弹窗定位元素
        self.post_add_locator_handler(self.btn_continue_login)

        # 输入帐号和密码
        self.input_username.fill(username)
        self.input_password.fill(password)
        self.btn_login.click()

        self.page.wait_for_load_state(state="load")
        # 登录后等待直到期望的首页出现
        expect(self.page.get_by_text("首页").first).to_be_visible(timeout=30000)

    def login_change_password(self, username: str, old_password: str, new_password: str):
        """
        新用户首次登陆更新密码
        """
        self.input_username.fill(username)
        self.input_password.fill(old_password)
        self.btn_login.click()
        self.page.wait_for_load_state(state="load")
        expect(self.page).to_have_title("修改密码")
        self.input_old_password.fill(old_password)
        self.input_new_password.fill(new_password)
        self.input_confirm_password.fill(new_password)
        self.btn_confirm_password.click()
"""
登录页 Page Object（沙箱平台登录）。

页面结构：
    - 登录表单: 用户名 + 密码 + 登录按钮
    - 首次登录弹窗: 强制修改密码（旧密码/新密码/确认密码 + 确定）
    - 二次弹窗: "继续登录"（同一账号已在其它地方登录时的确认弹窗）
    - 告警区: 顶部 toast（登录失败等）

设计要点：
    - **登录续弹处理**：使用 :meth:`BasePage.post_add_locator_handler`
      注册"继续登录"按钮的**元素定位器处理器**，Playwright 会在任何操作前
      自动检测并点击掉该弹窗，避免手写 try/except 竞态。
"""
from playwright.sync_api import Page, expect

from base.ui.pages.base import BasePage
from core import get_logger
from core.constants import PlaywrightLoadState

logger = get_logger(__name__)


class LoginPage(BasePage):
    """登录页 Page Object。

    覆盖普通登录与首次登录强制改密两条主要流程。
    """

    def __init__(self, page: Page):
        """初始化登录页元素定位器。

        Args:
            page: Playwright 的 :class:`~playwright.sync_api.Page` 对象。
        """
        super().__init__(page)
        logger.info("Login Page Initialized")

        # ==================== 登录表单 ====================
        self.input_username = page.get_by_placeholder("请输入用户名")
        self.input_password = page.get_by_placeholder("请输入密码")
        self.btn_login = page.get_by_role("button", name="登录")

        # ==================== 修改密码弹窗（首次登录） ====================
        self.input_old_password = page.get_by_placeholder("请输入旧密码")
        self.input_new_password = page.get_by_placeholder("请输入新密码")
        self.input_confirm_password = page.get_by_placeholder("请输入确认密码")
        self.btn_confirm_password = page.get_by_role("button", name="确定")

        # ==================== 二次登录确认弹窗 ====================
        # Note: 用户已在其它端登录时才会出现，通过 locator_handler 自动关闭
        self.btn_continue_login = self.page.get_by_role("button", name="继续登录")

        # ==================== 告警提示 ====================
        # 登录失败/网络异常时顶部 toast
        self.alert = page.locator(".el-message__content").first

    def login(self, username: str, password: str) -> None:
        """执行登录：填写用户名/密码 → 点击登录 → 等待首页可见。

        流程细节：
            1. 通过 ``post_add_locator_handler`` 注册"继续登录"弹窗的自动处理器，
               避免多端登录竞态；
            2. 依次填写用户名、密码；
            3. 点击"登录"，等待页面 ``load``；
            4. 等待首页文本"首页"可见，超时 30s。

        Args:
            username: 登录用户名。
            password: 登录密码（明文传入，日志中绝不输出）。
        """
        # 注册"继续登录"弹窗自动处理器（Playwright 会在遇到该元素时自动点击）
        self.post_add_locator_handler(self.btn_continue_login)

        # 输入账号密码并提交
        self.input_username.fill(username)
        self.input_password.fill(password)
        self.btn_login.click()

        self.page.wait_for_load_state(state=PlaywrightLoadState.LOAD)
        # 首页文本可见 == 登录成功且路由到主页
        # Note: 30s 超时覆盖登录后的一系列 SPA 路由 + iframe 初始加载
        expect(self.page.get_by_text("首页").first).to_be_visible(timeout=30000)

    def login_change_password(
            self, username: str, old_password: str, new_password: str
    ) -> None:
        """新用户首次登录强制修改密码。

        流程：
            1. 用旧密码尝试登录；
            2. 系统跳转"修改密码"页；
            3. 依次填写旧密码、新密码、确认密码；
            4. 点击"确定"提交。

        Args:
            username: 用户名。
            old_password: 旧密码（首次登录密码）。
            new_password: 新密码（同时用于"确认密码"字段）。

        Note:
            本方法**不校验修改是否成功**，也不做后续跳转判断；调用方需自行处理
            （例如接着调用 :meth:`login` 用新密码重新登录）。
        """
        self.input_username.fill(username)
        self.input_password.fill(old_password)
        self.btn_login.click()
        self.page.wait_for_load_state(state=PlaywrightLoadState.LOAD)

        # 断言进入"修改密码"页
        expect(self.page).to_have_title("修改密码")

        # 填写并提交新密码
        self.input_old_password.fill(old_password)
        self.input_new_password.fill(new_password)
        self.input_confirm_password.fill(new_password)
        self.btn_confirm_password.click()

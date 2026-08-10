import re

from playwright.sync_api import Page, expect

from base.ui.pages.base_page import BasePage
from constants.bussiness import SystemMenu, SandboxMenu
from core import get_logger

logger = get_logger(__name__)


class HomePage(BasePage):

    def __init__(self, page: Page):
        """
        初始化 Home Page 页面对象

        Args:
            page: Playwright Page 对象
        """
        super().__init__(page)
        logger.info("Home Page Initialized")

        # 左侧菜单栏
        self.menubar = page.get_by_role("menubar")

        # 顶部导航栏
        self.breadcrumb = page.get_by_role("navigation", name="面包屑")

        # 用户菜单
        self.btn_user_menu = page.locator("header div[role='button']").first  # 右上角用户按钮

        self.menuitem_personal_settings = page.get_by_role("menuitem", name="个人设置")
        self.menuitem_change_password = page.get_by_role("menuitem", name="修改密码")
        self.menuitem_logout = page.get_by_role("menuitem", name="退出登录")

        # 个人设置中的租户下拉切换
        self.tenant_switch = page.get_by_role("dialog", name=re.compile(r"个人设置")).locator(
            ".ep-select__wrapper, .ep-select__wrapper").first

    def open_personal_settings(self):
        """
        打开个人设置弹框
        """
        expect(self.btn_user_menu).to_be_visible()
        self.btn_user_menu.click()
        self.page.wait_for_timeout(500)
        self.page.get_by_role("menuitem", name="个人设置").click()
        self.page.wait_for_timeout(500)

    def verify_sandbox_menu(self, is_admin_view: bool = False):
        """
        验证沙箱菜单（用户视图 / 管理视图）

        用户和管理角色的菜单可见度：
        1.相同点：沙箱管理/镜像管理/模板管理/SDK示例
        2.差异点：
            - 用户视图：不显示沙箱集群、不展开沙箱集群
            - 管理视图：显示沙箱集群、并展开校验其下级（集群管理、节点管理）
        Args:
            is_admin_view: True 为管理视图（含沙箱集群），False 为用户视图（无沙箱集群）
        """
        # 顶部切换到沙箱菜单
        self.switch_top_menu(SystemMenu.SANDBOX)
        expect(self.page).to_have_title(SandboxMenu.SANDBOX_MANAGER)

        # 校验左侧一级菜单
        expect(self.page.get_by_text(SandboxMenu.SANDBOX_MANAGER).first).to_be_visible()
        expect(self.page.get_by_text(SandboxMenu.IMAGE_MANAGER).first).to_be_visible()
        expect(self.page.get_by_text(SandboxMenu.TEMPLATE_MANAGER).first).to_be_visible()
        expect(self.page.get_by_text(SandboxMenu.SDK_EXAMPLE).first).to_be_visible()

        # 沙箱集群：管理视图可见，用户视图不可见
        sandbox_cluster = self.page.get_by_text(SandboxMenu.SANDBOX_CLUSTER).first
        if is_admin_view:
            expect(sandbox_cluster).to_be_visible()
        else:
            expect(sandbox_cluster).not_to_be_visible()

        # 点击展开沙箱管理，校验下级：沙箱管理、运维看板
        # self.home_page.open_menu("沙箱管理")
        expect(self.page.get_by_text(SandboxMenu.SANDBOX_MANAGER).nth(1)).to_be_visible()
        expect(self.page.get_by_text(SandboxMenu.MAINTENANCE_DASHBOARD).first).to_be_visible()

        # 管理视图：点击展开沙箱集群，校验下级：沙箱集群、节点管理
        if is_admin_view:
            self.open_menu(SandboxMenu.SANDBOX_CLUSTER)
            expect(self.page.get_by_text(SandboxMenu.CLUSTER_MANAGER).first).to_be_visible()
            expect(self.page.get_by_text(SandboxMenu.NODE_MANAGER).first).to_be_visible()

        # 点击展开镜像管理，校验下级：镜像库管理、镜像管理
        self.open_menu(SandboxMenu.IMAGE_MANAGER)
        expect(self.page.get_by_text(SandboxMenu.IMAGE_LIBRARY_MANAGER).first).to_be_visible()
        expect(self.page.get_by_text(SandboxMenu.IMAGE_MANAGER).nth(1)).to_be_visible()

        # 点击展开模板管理，校验下级：模板管理、构建记录
        self.open_menu(SandboxMenu.TEMPLATE_MANAGER)
        expect(self.page.get_by_text(SandboxMenu.TEMPLATE_MANAGER).nth(1)).to_be_visible()
        expect(self.page.get_by_text(SandboxMenu.BUILD_RECORD).first).to_be_visible()

        # 点击展开SDK使用示例，校验下级：SDK使用示例
        self.open_menu(SandboxMenu.SDK_EXAMPLE)
        expect(self.page.get_by_text(SandboxMenu.SDK_EXAMPLE).nth(1)).to_be_visible()
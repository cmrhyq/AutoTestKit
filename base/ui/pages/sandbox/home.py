import re

from playwright.sync_api import Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from base.ui.pages.base import BasePage
from core import get_logger
from core.constants import UITimeout
from core.constants.bussiness import SystemMenu, SandboxMenu

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

    def switch_top_menu(self, menu_name: SystemMenu):
        """
        沙箱切换顶部导航菜单（首页/沙箱/AI可观测）
        Args:
            menu_name: 菜单名称

        Returns: None
        """
        top_menu_items = self.page.locator("div.layout-top-menu > div.top-menu-item")
        top_menu_active_item = self.page.locator("div.layout-top-menu > div.top-menu-item.is-active")
        if top_menu_active_item.count() > 0:
            current_name = top_menu_active_item.first.text_content()
            if current_name and menu_name in current_name:
                logger.info(f"当前已处于【{menu_name}】菜单，无须切换")
                return

        target = top_menu_items.filter(has_text=re.compile(rf"^{re.escape(menu_name)}$")).first
        expect(target).to_be_visible(timeout=UITimeout.TOP_MENU_SWITCH_TIMEOUT)
        target.click()
        self.page.wait_for_load_state(state="load")
        # 顶部菜单切换后侧边栏动画需要一小段稳定时间
        self.page.wait_for_timeout(UITimeout.STABILIZE)
        logger.info(f"切换顶部导航菜单到【{menu_name}】完成")

    def open_personal_settings(self):
        """
        打开个人设置弹框
        """
        expect(self.btn_user_menu).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)
        self.btn_user_menu.click()
        # 等待菜单项可见，避免固定 sleep
        expect(self.menuitem_personal_settings).to_be_visible(
            timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT
        )
        self.menuitem_personal_settings.click()
        # 弹框渐入动画
        self.page.wait_for_timeout(UITimeout.ANIMATION)

    def expand_sidebar(self):
        """展开侧边栏菜单（如果处于折叠状态）"""
        unfold_btn = self.page.locator(".ri-menu-unfold-fill")
        try:
            if unfold_btn.is_visible(timeout=UITimeout.ANIMATION):
                unfold_btn.click()
                self.page.wait_for_timeout(UITimeout.ANIMATION)
                logger.info("侧边栏已展开")
        except PlaywrightTimeoutError:
            logger.debug("侧边栏展开按钮不可见，跳过")

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
        expect(self.page).to_have_title(SandboxMenu.SANDBOX_MANAGE)

        # 校验左侧一级菜单
        expect(self.page.get_by_text(SandboxMenu.SANDBOX_MANAGE).first).to_be_visible()
        expect(self.page.get_by_text(SandboxMenu.IMAGE_MANAGE).first).to_be_visible()
        expect(self.page.get_by_text(SandboxMenu.TEMPLATE_MANAGE).first).to_be_visible()
        expect(self.page.get_by_text(SandboxMenu.SDK_EXAMPLE).first).to_be_visible()

        # 沙箱集群：管理视图可见，用户视图不可见
        sandbox_cluster = self.page.get_by_text(SandboxMenu.SANDBOX_CLUSTER).first
        if is_admin_view:
            expect(sandbox_cluster).to_be_visible()
        else:
            expect(sandbox_cluster).not_to_be_visible()

        # 点击展开沙箱管理，校验下级：沙箱管理、运维看板
        # self.home_page.open_menu("沙箱管理")
        expect(self.page.get_by_text(SandboxMenu.SANDBOX_MANAGE).nth(1)).to_be_visible()
        expect(self.page.get_by_text(SandboxMenu.MAINTENANCE_DASHBOARD).first).to_be_visible()

        # 管理视图：点击展开沙箱集群，校验下级：沙箱集群、节点管理
        if is_admin_view:
            self.open_menu(SandboxMenu.SANDBOX_CLUSTER)
            expect(self.page.get_by_text(SandboxMenu.CLUSTER_MANAGE).first).to_be_visible()
            expect(self.page.get_by_text(SandboxMenu.NODE_MANAGE).first).to_be_visible()

        # 点击展开镜像管理，校验下级：镜像库管理、镜像管理
        self.open_menu(SandboxMenu.IMAGE_MANAGE)
        expect(self.page.get_by_text(SandboxMenu.IMAGE_LIBRARY_MANAGE).first).to_be_visible()
        expect(self.page.get_by_text(SandboxMenu.IMAGE_MANAGE).nth(1)).to_be_visible()

        # 点击展开模板管理，校验下级：模板管理、构建记录
        self.open_menu(SandboxMenu.TEMPLATE_MANAGE)
        expect(self.page.get_by_text(SandboxMenu.TEMPLATE_MANAGE).nth(1)).to_be_visible()
        expect(self.page.get_by_text(SandboxMenu.BUILD_RECORD).first).to_be_visible()

        # 点击展开SDK使用示例，校验下级：SDK使用示例
        self.open_menu(SandboxMenu.SDK_EXAMPLE)
        expect(self.page.get_by_text(SandboxMenu.SDK_EXAMPLE).nth(1)).to_be_visible()

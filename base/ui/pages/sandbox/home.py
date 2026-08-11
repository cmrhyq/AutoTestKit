"""
主页（首页）Page Object。

覆盖沙箱平台登录后跳转的主页面，主要能力：

- **顶部导航切换**：首页 / 沙箱 / AI 可观测（:meth:`HomePage.switch_top_menu`）
- **用户菜单与个人设置弹框**（:meth:`HomePage.open_personal_settings`）
- **侧边栏折叠/展开**（:meth:`HomePage.expand_sidebar`）
- **左侧菜单可见性验证**：区分"用户视图"与"管理视图"
  （:meth:`HomePage.verify_sandbox_menu`）

多级菜单的具体点击（一级/二级/三级）由 :meth:`BasePage.open_menu` 统一实现，
本页面对象不再重复封装。
"""
import re

from playwright.sync_api import Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from base.ui.pages.base import BasePage
from core import get_logger
from core.constants import UITimeout
from core.constants.bussiness import SystemMenu, SandboxMenu

logger = get_logger(__name__)


class HomePage(BasePage):
    """主页 Page Object。

    提供全局导航所需的元素定位器与操作方法。所有可复用的元素
    在 :meth:`__init__` 中集中定义，便于查阅与维护。
    """

    def __init__(self, page: Page):
        """初始化主页元素定位器。

        Args:
            page: Playwright 的 :class:`~playwright.sync_api.Page` 对象，
                由测试 fixture 注入。
        """
        super().__init__(page)
        logger.info("Home Page Initialized")

        # 左侧一级菜单栏（role=menubar）
        self.menubar = page.get_by_role("menubar")

        # 顶部面包屑导航（当前定位在"页面标题下方"）
        self.breadcrumb = page.get_by_role("navigation", name="面包屑")

        # 右上角用户菜单入口按钮（头像/用户名的可点击区域）
        # Note: header 内首个 role=button 元素即用户菜单入口
        self.btn_user_menu = page.locator("header div[role='button']").first

        # 用户菜单下拉项
        self.menuitem_personal_settings = page.get_by_role("menuitem", name="个人设置")
        self.menuitem_change_password = page.get_by_role("menuitem", name="修改密码")
        self.menuitem_logout = page.get_by_role("menuitem", name="退出登录")

        # 个人设置弹框中的租户下拉切换
        # Note: 兼容 Element Plus (ep-*) 与 Element UI (el-*) 的 class 前缀
        self.tenant_switch = page.get_by_role(
            "dialog", name=re.compile(r"个人设置")
        ).locator(".ep-select__wrapper, .ep-select__wrapper").first

    # ==================== 顶部导航 ====================

    def switch_top_menu(self, menu_name: SystemMenu) -> None:
        """切换顶部导航菜单（首页 / 沙箱 / AI 可观测）。

        实现细节：
            1. 先读取当前激活项（``.is-active``），若已处于目标菜单则直接返回，
               避免不必要的点击导致 SPA 路由抖动；
            2. 使用精确文本匹配（``^{name}$``）以避免 "沙箱" 与 "沙箱管理" 冲突；
            3. 点击后等待页面 ``load``，再补一段短稳定等待覆盖侧边栏动画。

        Args:
            menu_name: 目标顶部菜单枚举值（:class:`SystemMenu`）。

        Returns:
            None
        """
        # 顶部菜单容器（Vue SPA 的顶部横向导航）
        top_menu_items = self.page.locator("div.layout-top-menu > div.top-menu-item")
        top_menu_active_item = self.page.locator(
            "div.layout-top-menu > div.top-menu-item.is-active"
        )

        # 若当前已激活目标菜单，直接跳过（幂等）
        if top_menu_active_item.count() > 0:
            current_name = top_menu_active_item.first.text_content()
            if current_name and menu_name in current_name:
                logger.info(f"当前已处于【{menu_name}】菜单，无须切换")
                return

        # 使用锚定正则精确匹配文本，防止 "沙箱" 命中 "沙箱管理"
        target = top_menu_items.filter(
            has_text=re.compile(rf"^{re.escape(menu_name)}$")
        ).first
        expect(target).to_be_visible(timeout=UITimeout.TOP_MENU_SWITCH_TIMEOUT)
        target.click()

        # 等待路由完成 + 顶部菜单切换后侧边栏动画的短稳定
        self.page.wait_for_load_state(state="load")
        self.page.wait_for_timeout(UITimeout.STABILIZE)
        logger.info(f"切换顶部导航菜单到【{menu_name}】完成")

    # ==================== 用户菜单 ====================

    def open_personal_settings(self) -> None:
        """打开右上角用户菜单中的"个人设置"弹框。

        流程：点击用户菜单入口 → 等待下拉出现 → 点击"个人设置" → 等待弹框渐入。
        """
        # 等待用户菜单入口可见（避免页面还没渲染完就点空）
        expect(self.btn_user_menu).to_be_visible(
            timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT
        )
        self.btn_user_menu.click()

        # 等待下拉菜单项渲染，避免固定 sleep 造成 flake
        expect(self.menuitem_personal_settings).to_be_visible(
            timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT
        )
        self.menuitem_personal_settings.click()

        # 弹框渐入动画：短稳定等待覆盖过渡时间
        self.page.wait_for_timeout(UITimeout.ANIMATION)

    def expand_sidebar(self) -> None:
        """展开侧边栏菜单（如果处于折叠状态）。

        顶部菜单切换后侧边栏可能被折叠，测试前调用一次可保证左侧菜单可见。
        若展开按钮已隐藏（表示当前已经是展开状态）则静默跳过。
        """
        unfold_btn = self.page.locator(".ri-menu-unfold-fill")
        try:
            # 短探测：折叠图标不可见即视为已展开，无须操作
            if unfold_btn.is_visible(timeout=UITimeout.ANIMATION):
                unfold_btn.click()
                # 侧边栏展开动画
                self.page.wait_for_timeout(UITimeout.ANIMATION)
                logger.info("侧边栏已展开")
        except PlaywrightTimeoutError:
            logger.debug("侧边栏展开按钮不可见，跳过")

    # ==================== 沙箱菜单验证 ====================

    def verify_sandbox_menu(self, is_admin_view: bool = False) -> None:
        """验证左侧沙箱菜单在指定角色视图下的可见性。

        用户角色与管理角色对沙箱菜单的可见度差异：

        - **相同点**：沙箱管理 / 镜像管理 / 模板管理 / SDK 使用示例
        - **差异点**：
            * 用户视图：**不显示**沙箱集群（一级菜单不可见）；
            * 管理视图：**显示**沙箱集群，并可展开其下级
              （集群管理、节点管理）。

        Args:
            is_admin_view: True 表示管理视图（含沙箱集群），
                False 表示用户视图（无沙箱集群）。
        """
        # ---- Step 1: 顶部切换到"沙箱"菜单，校验页面标题
        self.switch_top_menu(SystemMenu.SANDBOX)
        expect(self.page).to_have_title(SandboxMenu.SANDBOX_MANAGE)

        # ---- Step 2: 校验左侧一级菜单可见性（共有项）
        expect(self.page.get_by_text(SandboxMenu.SANDBOX_MANAGE).first).to_be_visible()
        expect(self.page.get_by_text(SandboxMenu.IMAGE_MANAGE).first).to_be_visible()
        expect(self.page.get_by_text(SandboxMenu.TEMPLATE_MANAGE).first).to_be_visible()
        expect(self.page.get_by_text(SandboxMenu.SDK_EXAMPLE).first).to_be_visible()

        # ---- Step 3: 沙箱集群一级菜单可见性（视图差异点）
        sandbox_cluster = self.page.get_by_text(SandboxMenu.SANDBOX_CLUSTER).first
        if is_admin_view:
            expect(sandbox_cluster).to_be_visible()
        else:
            expect(sandbox_cluster).not_to_be_visible()

        # ---- Step 4: 校验"沙箱管理"下级：沙箱管理、运维看板
        # Note: 一级菜单本身文本 = "沙箱管理"，因此二级同名项通过 nth(1) 定位第二处
        expect(self.page.get_by_text(SandboxMenu.SANDBOX_MANAGE).nth(1)).to_be_visible()
        expect(
            self.page.get_by_text(SandboxMenu.MAINTENANCE_DASHBOARD).first
        ).to_be_visible()

        # ---- Step 5: 管理视图独有 —— 展开"沙箱集群"并校验下级
        if is_admin_view:
            self.open_menu(SandboxMenu.SANDBOX_CLUSTER)
            expect(
                self.page.get_by_text(SandboxMenu.CLUSTER_MANAGE).first
            ).to_be_visible()
            expect(
                self.page.get_by_text(SandboxMenu.NODE_MANAGE).first
            ).to_be_visible()

        # ---- Step 6: 展开"镜像管理"并校验下级：镜像库管理、镜像管理
        self.open_menu(SandboxMenu.IMAGE_MANAGE)
        expect(
            self.page.get_by_text(SandboxMenu.IMAGE_LIBRARY_MANAGE).first
        ).to_be_visible()
        expect(self.page.get_by_text(SandboxMenu.IMAGE_MANAGE).nth(1)).to_be_visible()

        # ---- Step 7: 展开"模板管理"并校验下级：模板管理、构建记录
        self.open_menu(SandboxMenu.TEMPLATE_MANAGE)
        expect(
            self.page.get_by_text(SandboxMenu.TEMPLATE_MANAGE).nth(1)
        ).to_be_visible()
        expect(self.page.get_by_text(SandboxMenu.BUILD_RECORD).first).to_be_visible()

        # ---- Step 8: 展开"SDK 使用示例"并校验下级
        self.open_menu(SandboxMenu.SDK_EXAMPLE)
        expect(self.page.get_by_text(SandboxMenu.SDK_EXAMPLE).nth(1)).to_be_visible()

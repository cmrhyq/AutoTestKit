"""
沙箱管理 Page Object（沙箱 -> 沙箱管理）。

页面结构：
    - Tab: **存活沙箱** / **历史沙箱**
    - 存活沙箱：租户名称 + 沙箱ID/模板名称 + 查询 + 数据表格 + 自动刷新
    - 历史沙箱：租户名称 + 开始日期 + 结束日期 + 查询 + 数据表格

关键约定：
    - **iframe 定位**：主内容在 iframe 内，通过 ``page.locator("iframe").first.content_frame``
      获取 FrameLocator（每次访问自动重新解析，避免 iframe 重载后引用失效）。
    - **表格定位**：iframe 内第 1 个 ``<table>`` 是表头，第 2 个是数据行，
      因此使用 ``get_by_role("table").nth(1)``。
    - **兼容 Element Plus / Element UI**：所有 CSS class 前缀同时匹配 ``.ep-*`` 与 ``.el-*``。
"""
import re
from typing import Optional

from playwright.sync_api import Locator, Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from base.ui.pages.base import BasePage
from core import get_logger
from core.constants import UITimeout
from core.constants.bussiness import SandboxFramePath

logger = get_logger(__name__)


class SandboxManagePage(BasePage):
    """沙箱管理 Page Object。

    覆盖存活沙箱查询/删除、历史沙箱查询、统计指标读取、自动刷新等操作。
    所有可复用元素在 :meth:`__init__` 中集中定义。
    """

    def __init__(self, page: Page):
        """初始化沙箱管理页元素定位器。

        Args:
            page: Playwright 的 :class:`~playwright.sync_api.Page` 对象。
        """
        super().__init__(page)
        logger.info("Sandbox Manage Page Initialized")

        # 沙箱主内容iframe（FrameLocator 每次访问时自动重新解析）
        self.frame = page.locator("iframe").first.content_frame

        # tab 切换
        self.tab_alive = self.frame.get_by_role("tab", name="存活沙箱")
        self.tab_history = self.frame.get_by_role("tab", name="历史沙箱")

        # 存活沙箱搜索区域（实际无"模板类别"下拉，仅租户名称+沙箱ID两个textbox）
        self.input_tenant_alive = self.frame.get_by_placeholder("请输入租户名称")
        self.input_sandbox_id = self.frame.get_by_placeholder("请输入沙箱ID或模板名称")
        self.btn_search_alive = self.frame.get_by_role("button", name="查询")

        # 历史沙箱搜索区域（租户名称+开始日期+结束日期+查询）
        self.input_tenant_history = self.frame.get_by_placeholder("请输入租户名称")
        self.input_start_date = self.frame.get_by_placeholder("开始日期")
        self.input_end_date = self.frame.get_by_placeholder("结束日期")
        self.btn_search_history = self.frame.get_by_role("button", name="查询")

        # 数据表格（第2个table，第1个为表头；存活/历史共用定位方式）
        self.table_data = self.frame.get_by_role("table").nth(1)

        # 删除确认弹窗
        self.msg_box = self.frame.locator(".ep-message-box, .el-message-box, .message-box").first
        self.alert = self.frame.locator(".ep-message__content, .el-message__content").first

        # 自动刷新
        self.link_auto_refresh = self.frame.get_by_text("自动刷新")
        self.item_refresh_5s = self.frame.get_by_text("5s", exact=True)

    def navigate_to(self, base_url: str) -> None:
        """通过 URL 直接导航进入沙箱管理页面。

        菜单点击有时不刷新 iframe，稳定性要求高的用例应优先使用本方法。
        末尾通过 ``expect(self.tab_alive).to_be_visible`` 等待首次渲染完成，
        代替固定 sleep。

        Args:
            base_url: 站点根 URL（``http[s]://host[:port]``），不含 iframe 路径。
        """
        logger.info(f"导航到沙箱管理: {SandboxFramePath.SANDBOX_MANAGE}")
        self.page.goto(base_url + SandboxFramePath.SANDBOX_MANAGE, timeout=UITimeout.NAVIGATION_TIMEOUT)
        self.page.wait_for_load_state(state="load")
        expect(self.tab_alive).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)

    # ==================== tab 切换 ====================

    def switch_to_alive(self) -> None:
        """切换到"存活沙箱"tab，并等待 tab 变为激活状态。"""
        logger.info("切换到存活沙箱tab")
        self.tab_alive.click()
        self._wait_tab_active(self.tab_alive, "存活沙箱")

    def switch_to_history(self) -> None:
        """切换到"历史沙箱"tab，并等待 tab 变为激活状态。"""
        logger.info("切换到历史沙箱tab")
        self.tab_history.click()
        self._wait_tab_active(self.tab_history, "历史沙箱")

    def _wait_tab_active(self, tab: Locator, tab_name: str) -> None:
        """等待 tab 变为激活状态。

        优先通过 ``aria-selected="true"`` 属性判定；无法判定时退化为短稳定等待
        （避免脆弱地依赖前端具体实现）。

        Args:
            tab: tab 元素定位器。
            tab_name: 用于日志的 tab 名称。
        """
        try:
            expect(tab).to_have_attribute(
                "aria-selected", "true", timeout=UITimeout.STABILIZE
            )
        except (PlaywrightTimeoutError, AssertionError):
            logger.debug(f"tab【{tab_name}】未通过 aria-selected 判定激活，退化为短稳定等待")
            self.page.wait_for_timeout(UITimeout.SHORT)

    def auto_refresh(self) -> None:
        """开启表格 5s 自动刷新。

        点击"自动刷新"下拉入口 → 等待菜单渲染 → 选择"5s"选项。
        """
        self.link_auto_refresh.click()
        expect(self.item_refresh_5s).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)
        self.item_refresh_5s.click()

    # ==================== 存活沙箱搜索 ====================

    def search_alive_sandbox(
            self,
            tenant_name: Optional[str] = None,
            sandbox_id_or_template: Optional[str] = None,
    ) -> None:
        """在"存活沙箱"tab 按条件搜索。

        前端实际只有租户名称 + 沙箱ID/模板名称两个 textbox（无"模板类别"下拉）。
        参数为 ``None`` 或空串时对应输入框不填写；输入框在某些页面状态下可能不可见，
        此时静默跳过、不抛异常。

        Args:
            tenant_name: 租户名称。
            sandbox_id_or_template: 沙箱 ID 或模板名称。
        """
        logger.info(f"搜索存活沙箱: tenant={tenant_name}, id/template={sandbox_id_or_template}")
        if tenant_name:
            try:
                if self.input_tenant_alive.is_visible(timeout=UITimeout.ANIMATION):
                    self.input_tenant_alive.fill(tenant_name)
            except PlaywrightTimeoutError:
                logger.debug("存活沙箱-租户名称输入框不可见，跳过填写")
        if sandbox_id_or_template:
            try:
                if self.input_sandbox_id.is_visible(timeout=UITimeout.ANIMATION):
                    self.input_sandbox_id.fill(sandbox_id_or_template)
            except PlaywrightTimeoutError:
                logger.debug("存活沙箱-沙箱ID输入框不可见，跳过填写")
        self.btn_search_alive.click()
        # 等待表格刷新可见，避免读取旧数据（表格空时无法命中，忽略）
        try:
            expect(self.table_data).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)
        except (PlaywrightTimeoutError, AssertionError):
            logger.debug("查询后表格未可见，忽略")

    def get_alive_sandbox_count(self) -> int:
        """获取存活沙箱数据行数。

        Returns:
            int: 数据行数；探测异常时返回 ``0``。
        """
        try:
            return self.table_data.get_by_role("row").count()
        except PlaywrightTimeoutError:
            logger.debug("读取存活沙箱行数超时，返回 0")
            return 0

    def is_sandbox_alive(self, sandbox_id: str) -> bool:
        """检查指定沙箱 ID 是否在存活沙箱列表中。

        执行方式：先按 ID 搜索定位到目标行，再判断行可见性。

        Args:
            sandbox_id: 沙箱 ID。

        Returns:
            bool: True 表示存活；False 表示不存在或探测超时。
        """
        try:
            self.search_alive_sandbox(sandbox_id_or_template=sandbox_id)
            row = self.table_data.get_by_role(
                "row", name=re.compile(re.escape(sandbox_id))
            ).first
            return row.is_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)
        except PlaywrightTimeoutError:
            return False

    # ==================== 删除沙箱实例 ====================

    def click_delete_sandbox(self, sandbox_id: str) -> None:
        """点击指定沙箱的"删除"按钮。

        点击后需要在弹出的确认弹窗上二次确认，具体确认动作见 :meth:`confirm_delete`。

        Args:
            sandbox_id: 沙箱 ID。
        """
        logger.info(f"点击沙箱【{sandbox_id}】的删除按钮")
        row = self.table_data.get_by_role("row", name=re.compile(re.escape(sandbox_id))).first
        expect(row).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)
        row.get_by_role("button", name="删除").click()
        # 等待确认弹窗渲染完成
        expect(self.msg_box).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)

    def confirm_delete(self) -> None:
        """在删除确认弹窗上点击"删除"，并等待弹窗关闭。

        使用 ``.last`` 是因为部分弹窗右上角还有一个"关闭"图标 button，
        ``last`` 命中底部主按钮。若弹窗未渲染出来则静默跳过。
        """
        try:
            if self.msg_box.is_visible(timeout=UITimeout.ANIMATION):
                self.msg_box.get_by_role(
                    "button", name=re.compile(r"删除")
                ).last.click()
                expect(self.msg_box).to_be_hidden(
                    timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT
                )
        except PlaywrightTimeoutError:
            logger.debug("确认删除弹窗不可见，跳过")

    # ==================== 历史沙箱 ====================

    def search_history_sandbox(self, tenant_name: Optional[str] = None) -> None:
        """在"历史沙箱"tab 按条件搜索。

        当前仅按租户名称过滤（日期区间预留占位，未启用）。

        Args:
            tenant_name: 租户名称，可空。
        """
        logger.info(f"搜索历史沙箱: tenant={tenant_name}")
        if tenant_name:
            try:
                if self.input_tenant_history.is_visible(timeout=UITimeout.ANIMATION):
                    self.input_tenant_history.fill(tenant_name)
            except PlaywrightTimeoutError:
                logger.debug("历史沙箱-租户名称输入框不可见，跳过填写")
        self.btn_search_history.click()
        try:
            expect(self.table_data).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)
        except (PlaywrightTimeoutError, AssertionError):
            logger.debug("查询后表格未可见，忽略")

    def get_history_sandbox_count(self) -> int:
        """获取历史沙箱数据行数。

        Returns:
            int: 数据行数；探测异常时返回 ``0``。
        """
        try:
            return self.table_data.get_by_role("row").count()
        except PlaywrightTimeoutError:
            logger.debug("读取历史沙箱行数超时，返回 0")
            return 0

    # ==================== 指标统计 ====================

    def get_alive_metrics(self) -> dict:
        """读取存活沙箱 tab 顶部统计卡片数据（CPU / 内存 / 磁盘 / 运行中数量）。

        实现：对每个已知 label（如 "CPU使用率"）用文本正则匹配包含数字的元素，
        取其文本作为该指标的展示值。**读取不到的指标不会出现在 key 中**，
        调用方需自行判断字段存在性。

        Returns:
            dict: 形如 ``{"CPU使用率": "CPU使用率 12%", ...}`` 的字典。
        """
        metrics: dict = {}
        # Note: 统计卡片文本一般是 "CPU使用率 12%" 这种带数字的形式，
        #       用 /label.*\d+/ 正则匹配可避免误命中导航文本
        for label in ("CPU使用率", "内存使用率", "磁盘", "正在运行"):
            try:
                el = self.frame.locator(f"text=/{re.escape(label)}.*\\d+/").first
                if el.is_visible(timeout=UITimeout.ANIMATION):
                    # Note: text_content() 可能为 None，需 `or ""` 兜底
                    metrics[label] = (el.text_content() or "").strip()
            except PlaywrightTimeoutError:
                logger.debug(f"指标【{label}】不可见，跳过")
        return metrics

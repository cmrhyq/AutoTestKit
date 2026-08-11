import re
from typing import Optional

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator, Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from base.ui.pages.base import BasePage
from core import get_logger
from core.constants import UITimeout
from core.constants.bussiness import SandboxFramePath, SandboxTemplateStatus

logger = get_logger(__name__)


class TemplateManagePage(BasePage):

    def __init__(self, page: Page):
        """
        初始化 Template Manage Page 页面对象

        Args:
            page: Playwright Page 对象
        """
        super().__init__(page)
        logger.info("Template Manage Page Initialized")

        # 沙箱主内容iframe（FrameLocator 每次访问时自动重新解析）
        self.frame = page.locator("iframe").first.content_frame

        # tab 切换
        self.tab_system = self.frame.get_by_role("tab", name="系统模板")
        self.tab_custom = self.frame.get_by_role("tab", name="自定义模板")

        # 自定义模板tab 列表页搜索区域（镜像仓库下拉 + 场景分类下拉 + 模板名称/ID输入 + 查询 + 创建模板）
        # Note: `*_search` 前缀区分创建子页面同名下拉，避免与 dropdown_image_repo_create 命名混淆
        self.dropdown_image_repo_search = self.frame.locator(
            ".ep-select__wrapper:has-text('请选择镜像仓库'), .el-select__wrapper:has-text('请选择镜像仓库')"
        ).first
        self.dropdown_scene_search = self.frame.locator(
            ".ep-select__wrapper:has-text('请选择场景分类'), .el-select__wrapper:has-text('请选择场景分类')"
        ).first
        self.input_search = self.frame.get_by_placeholder("请输入模板名称或ID")
        self.btn_search = self.frame.get_by_role("button", name="查询")
        self.btn_create_template = self.frame.get_by_role("button", name="创建模板")

        # 数据表格（第2个table，第1个为表头）
        self.table_data = self.frame.get_by_role("table").nth(1)

        # 创建模板子页面元素（点击"创建模板"后在iframe内部切换的子页面）
        self.link_breadcrumb_create = self.frame.get_by_role("link", name="创建模板")
        # 基本配置
        self.input_template_name = self.frame.get_by_role("textbox", name="* 模板名称")
        self.input_remark = self.frame.get_by_role("textbox", name="备注")
        # 沙箱镜像
        self.dropdown_image_repo_create = self.frame.locator(
            ".ep-select__wrapper:has-text('选择镜像仓库'), .el-select__wrapper:has-text('选择镜像仓库')"
        ).first
        self.input_start_command = self.frame.get_by_role("textbox", name="启动命令")
        self.input_ready_command = self.frame.get_by_role("textbox", name="就绪命令")
        # 高级配置
        self.input_vcpu = self.frame.get_by_placeholder("vCPU")
        self.input_gib = self.frame.get_by_placeholder("GIB")
        # 底部按钮
        self.btn_back = self.frame.get_by_role("button", name="返回")
        self.btn_create = self.frame.get_by_role("button", name="创建")
        self.btn_create_confirm = self.frame.get_by_role("button", name="确定")

        # 删除确认弹窗
        self.msg_box = self.frame.locator(".ep-message-box, .el-message-box, .message-box").first
        self.alert = self.frame.locator(".ep-message__content, .el-message__content").first

    def navigate_to(self, base_url: str) -> None:
        """
        通过URL直接导航进入模板管理页面（菜单点击可能不刷新iframe）
        """
        logger.info(f"导航到模板管理: {SandboxFramePath.TEMPLATE_MANAGE}")
        self.page.goto(base_url + SandboxFramePath.TEMPLATE_MANAGE, timeout=UITimeout.NAVIGATION_TIMEOUT)
        self.page.wait_for_load_state(state="load")
        # 等待 iframe 内主要内容可见（首个 tab 出现），避免固定 sleep 造成 flake
        expect(self.tab_custom).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)

    def switch_to_custom_template(self) -> None:
        """切换到自定义模板tab，并等待 tab 激活。"""
        logger.info("切换到自定义模板tab")
        self.tab_custom.click()
        self._wait_tab_active(self.tab_custom, "自定义模板")

    def switch_to_system_template(self) -> None:
        """切换到系统模板tab，并等待 tab 激活。"""
        logger.info("切换到系统模板tab")
        self.tab_system.click()
        self._wait_tab_active(self.tab_system, "系统模板")

    def _wait_tab_active(self, tab: Locator, tab_name: str) -> None:
        """等待 tab 变为激活状态；无法通过属性判定时退化为短稳定等待。"""
        try:
            expect(tab).to_have_attribute(
                "aria-selected", "true", timeout=UITimeout.STABILIZE
            )
        except (PlaywrightTimeoutError, AssertionError):
            logger.debug(f"tab【{tab_name}】未通过 aria-selected 判定激活，退化为短稳定等待")
            self.page.wait_for_timeout(UITimeout.SHORT)

    def click_create_template(self) -> None:
        """点击创建模板按钮，切换到创建模板子页面（非弹窗）。"""
        logger.info("点击创建模板按钮")
        self.btn_create_template.click()
        # 等待面包屑上的“创建模板”链接可见 = 已进入创建子页面
        expect(self.link_breadcrumb_create).to_be_visible(
            timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT
        )

    def is_create_page_active(self) -> bool:
        """检测是否已切换到"创建模板"子页面（通过面包屑"创建模板"链接判断）。"""
        try:
            return self.link_breadcrumb_create.is_visible(timeout=UITimeout.ANIMATION)
        except PlaywrightTimeoutError:
            return False

    def fill_create_form(
            self,
            template_name: str,
            remark: Optional[str] = None,
            image_repo: Optional[str] = None,
            cpu: Optional[str] = None,
            memory: Optional[str] = None,
            scene: Optional[str] = None,
            start_command: Optional[str] = None,
            ready_command: Optional[str] = None,
    ) -> None:
        """填写创建模板子页面表单。

        3 个配置区：基本配置、沙箱镜像、高级配置。
        必填项（前端带 *）：模板名称、选择镜像仓库、规格配置(vCPU+GIB)、场景分类。
        """
        logger.info(f"填写创建模板: {template_name}")
        # 验证已进入创建模板子页面
        expect(self.link_breadcrumb_create).to_be_visible(
            timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT
        )

        # === 基本配置 ===
        # * 模板名称
        self.input_template_name.fill(template_name)
        # 备注（非必填）
        if remark:
            self.input_remark.fill(remark)

        # === 沙箱镜像 ===
        # * 选择镜像仓库（下拉：系统仓库/自定义仓库，两步法）
        if image_repo:
            self.dropdown_image_repo_create.click()
            option = self.frame.get_by_role("option", name=image_repo, exact=True)
            expect(option).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)
            option.click()
            # 选中后镜像列表异步刷新，等待表格出现或短稳定
            self.page.wait_for_timeout(UITimeout.STABILIZE)

        # 启动命令（非必填）
        if start_command:
            self.input_start_command.fill(start_command)

        # 就绪命令（非必填）
        if ready_command:
            self.input_ready_command.fill(ready_command)

        # === 高级配置 ===
        # * 规格配置 - vCPU（spinbutton，placeholder="vCPU"）
        if cpu:
            self.input_vcpu.fill(str(cpu))

        # * 规格配置 - GIB内存（spinbutton，placeholder="GIB"）
        if memory:
            self.input_gib.fill(str(memory))

        # * 场景分类（radiogroup：代码/桌面/浏览器/其它）
        if scene:
            # 点击对应radio的label文本（更稳定）
            self.frame.get_by_role("radio", name=scene).click(force=True)
            self.page.wait_for_timeout(UITimeout.ANIMATION)

    def select_base_image(self, base_image: str) -> None:
        """在创建模板子页面中勾选镜像列表中的指定行（必须在选择了镜像仓库后调用）。"""
        logger.info(f"勾选镜像: {base_image}")
        row = self.table_data.get_by_role("row", name=base_image).first
        expect(row).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)
        # 行内第 2 个 span 对应 checkbox
        row.locator("span").nth(1).click()

    def select_first_image(self) -> bool:
        """勾选镜像列表第一行；列表为空返回 False。

        必须在选择了镜像仓库后调用。
        """
        logger.info("勾选第一个镜像")
        rows = self.table_data.get_by_role("row")
        try:
            expect(rows.first).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)
        except (PlaywrightTimeoutError, AssertionError):
            logger.info("镜像列表为空，无法勾选")
            return False

        rows.first.locator("label.ep-checkbox, label.el-checkbox").first.click()
        return True

    def confirm_create(self) -> None:
        """点击"创建"按钮提交模板，并在二次确认弹窗上点“确定”。"""
        logger.info("点击创建按钮提交模板")
        self.btn_create.click()
        expect(self.btn_create_confirm).to_be_visible(
            timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT
        )
        self.btn_create_confirm.click()

    def cancel_create(self) -> None:
        """点击"返回"按钮退出创建模板子页面。"""
        self.btn_back.click()
        # 返回后面包屑“创建模板”应消失
        expect(self.link_breadcrumb_create).to_be_hidden(
            timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT
        )

    def create_template_if_not_exists(
            self,
            template_name: str,
            remark: Optional[str] = None,
            image_repo: Optional[str] = None,
            base_image: Optional[str] = None,
            cpu: Optional[str] = None,
            memory: Optional[str] = None,
            scene: Optional[str] = None,
    ) -> bool:
        """
        创建自定义模板（幂等：已存在则跳过）。
        完整流程：检查存在 → 点击创建 → 填表单 → 勾选镜像 → 提交 → 轮询等待构建成功。
        返回True表示新创建，False表示已存在跳过。
        """
        # 幂等：模板已存在则跳过
        if self.is_template_exists(template_name):
            logger.info(f"自定义模板【{template_name}】已存在，跳过创建")
            return False
        # 点击"创建模板"按钮（切换到子页面）
        self.click_create_template()
        # 填写表单
        self.fill_create_form(
            template_name=template_name,
            remark=remark,
            image_repo=image_repo,
            cpu=cpu,
            memory=memory,
            scene=scene,
        )
        # 选择镜像仓库后勾选base镜像
        if base_image:
            self.select_base_image(base_image)
        # 点击"创建"按钮提交
        self.confirm_create()
        # 验证已返回自定义模板列表
        expect(self.link_breadcrumb_create).to_be_hidden(
            timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT
        )
        row = self._get_row_by_name(template_name)
        expect(row).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)
        # 轮询等待模板构建完成（成功/失败为终态）
        self._poll_until_build_terminal(template_name)
        expect(row.get_by_text(SandboxTemplateStatus.SUCCESS.value)).to_be_visible()
        logger.info(f"自定义模板【{template_name}】创建成功")
        return True

    def _poll_until_build_terminal(self, template_name: str) -> None:
        """在自定义模板列表页点击"查询"轮询，直到某行进入终态（成功/失败）。"""
        max_rounds = UITimeout.BUILD_MAX_WAIT // UITimeout.POLL_INTERVAL
        row = self._get_row_by_name(template_name)
        terminal_values = SandboxTemplateStatus.terminal_values()
        for round_idx in range(max_rounds):
            self.btn_search.click()
            self.page.wait_for_timeout(UITimeout.POLL_INTERVAL)
            for status_value in terminal_values:
                try:
                    if row.get_by_text(status_value).is_visible(
                            timeout=UITimeout.ANIMATION
                    ):
                        logger.info(
                            f"模板【{template_name}】在第 {round_idx + 1} 轮进入终态: {status_value}"
                        )
                        return
                except PlaywrightTimeoutError:
                    continue
        logger.warning(f"模板【{template_name}】轮询完成仍未进入终态")

    # ==================== 自定义模板列表操作 ====================

    def search_custom_template(self, template_name: str) -> None:
        """在自定义模板 tab 按模板名称搜索；搜索框不可见时静默跳过。"""
        logger.info(f"搜索自定义模板: {template_name}")
        try:
            if self.input_search.is_visible(timeout=UITimeout.ANIMATION):
                self.input_search.fill(template_name)
                self.btn_search.click()
                self.page.wait_for_timeout(UITimeout.QUERY)
        except PlaywrightTimeoutError:
            logger.debug("搜索输入框不可见，跳过搜索")

    def _get_row_by_name(self, template_name: str) -> Locator:
        """按模板名称获取行。"""
        return self.table_data.get_by_role(
            "row", name=re.compile(re.escape(template_name))
        ).first

    def is_template_exists(self, template_name: str) -> bool:
        """检查自定义模板是否已存在。"""
        try:
            self.search_custom_template(template_name)
            return self._get_row_by_name(template_name).is_visible(
                timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT
            )
        except PlaywrightTimeoutError:
            return False

    def get_template_status(self, template_name: str) -> str:
        """获取模板构建状态文本；找不到或未匹配返回空串。"""
        try:
            row = self._get_row_by_name(template_name)
            if not row.is_visible(timeout=UITimeout.ANIMATION):
                return ""
            cells = row.locator("td")
            valid_values = SandboxTemplateStatus.all_values()
            for i in range(cells.count()):
                txt = (cells.nth(i).text_content() or "").strip()
                if txt in valid_values:
                    return txt
        except PlaywrightTimeoutError:
            logger.debug(f"读取模板【{template_name}】状态超时")
        return ""

    def wait_template_visible(
            self,
            template_name: str,
            timeout_ms: int = UITimeout.BUILD_MAX_WAIT,
    ) -> bool:
        """轮询等待模板出现在自定义模板列表中。

        本方法只判定"模板是否已出现在列表"，不判定构建终态；
        用于创建后确认列表可查到（例如 JC009 场景）。若需要等待构建成功/失败，
        请使用 ``create_template_if_not_exists`` 内的完整流程。

        Args:
            template_name: 模板名
            timeout_ms: 总等待时长（毫秒），默认 ``UITimeout.BUILD_MAX_WAIT``

        Returns:
            bool: True 表示模板已出现；False 表示超时仍未出现。
        """
        logger.info(
            f"等待模板【{template_name}】出现在列表，最长 {timeout_ms // 1000}s"
        )
        elapsed = 0
        base_url = self.page.url.split('/iframe')[0]
        while elapsed < timeout_ms:
            self.navigate(base_url)
            self.switch_to_custom_template()
            self.search_custom_template(template_name)
            if self.is_template_exists(template_name):
                logger.info(f"模板【{template_name}】已出现在列表")
                return True
            self.page.wait_for_timeout(UITimeout.POLL_INTERVAL)
            elapsed += UITimeout.POLL_INTERVAL
        logger.warning(f"模板【{template_name}】等待超时仍未出现")
        return False

    def wait_template_build_success(
            self,
            template_name: str,
            timeout_ms: int = UITimeout.BUILD_MAX_WAIT,
    ) -> bool:
        """等待模板出现在自定义模板列表（旧接口，语义等同于 ``wait_template_visible``）。

        .. deprecated::
            请改用 :meth:`wait_template_visible`，命名更准确。
        """
        return self.wait_template_visible(template_name, timeout_ms)

    # ==================== 删除模板 ====================

    def click_delete_template(self, template_name: str) -> None:
        """点击指定自定义模板的删除按钮。"""
        logger.info(f"点击模板【{template_name}】的删除按钮")
        row = self._get_row_by_name(template_name)
        expect(row).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)
        row.get_by_role("button", name="删除").click()
        # 等待确认弹窗出现
        expect(self.msg_box).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)

    def confirm_delete(self) -> None:
        """在删除确认弹窗上点击"确定/删除"。"""
        try:
            if self.msg_box.is_visible(timeout=UITimeout.ANIMATION):
                self.msg_box.get_by_role(
                    "button", name=re.compile(r"确定|删除")
                ).last.click()
                # 等待弹窗关闭
                expect(self.msg_box).to_be_hidden(
                    timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT
                )
        except PlaywrightTimeoutError:
            logger.debug("确认删除弹窗不可见，跳过")

    def cleanup_template(self, template_name: str) -> None:
        """幂等清理指定自定义模板（不存在则跳过）。"""
        logger.info(f"清理自定义模板: {template_name}")
        try:
            self.switch_to_custom_template()
            self.search_custom_template(template_name)
            row = self._get_row_by_name(template_name)
            if row.is_visible(timeout=UITimeout.ANIMATION):
                self.click_delete_template(template_name)
                self.confirm_delete()
                logger.info(f"模板【{template_name}】删除成功")
            else:
                logger.info(f"模板【{template_name}】不存在，无需清理")
        except (PlaywrightTimeoutError, AssertionError) as e:
            logger.warning(f"清理模板【{template_name}】异常: {e}")
            self._safe_press_escape()

    def _safe_press_escape(self) -> None:
        """尽力关闭可能残留的弹窗（按 ESC）；失败仅记录，不再抛出。"""
        try:
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(UITimeout.ANIMATION)
        except PlaywrightError as e:
            logger.debug(f"按 ESC 关闭残留弹窗失败: {e}")

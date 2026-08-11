"""
模板管理 Page Object（沙箱 -> 模板管理）。

页面结构：
    - Tab: 系统模板 / 自定义模板
    - 自定义模板列表：镜像仓库下拉 + 场景分类下拉 + 名称搜索 + 查询 + 创建模板
    - 点击"创建模板"进入 **同 iframe 内** 的子页面（非弹窗）：
        * 基本配置：模板名称、备注
        * 沙箱镜像：选择镜像仓库（下拉）、镜像列表勾选、启动命令、就绪命令
        * 高级配置：vCPU / GIB / 场景分类
        * 底部按钮：返回 / 创建 / 创建二次确认

关键约定：
    - **表格定位**：iframe 内第 1 个 ``<table>`` 是表头容器，第 2 个才是数据行，
      因此 ``self.table_data`` 使用 ``.nth(1)``。
    - **兼容 Element Plus / Element UI**：所有 CSS class 前缀同时兼容 ``.ep-*``
      与 ``.el-*``（前端处于迁移过渡期）。
    - **命名区分列表页 vs 创建子页**：``dropdown_image_repo_search`` /
      ``dropdown_image_repo_create`` 通过 ``_search`` / ``_create`` 后缀避免混淆。

流程概览（``create_template_if_not_exists``）::

    is_template_exists?
        └── yes → 直接返回 False
        └── no  → click_create_template
                → fill_create_form
                → select_base_image (可选)
                → confirm_create
                → 等待面包屑消失、模板行出现
                → 轮询构建终态 (成功 / 失败)
                → 断言 SUCCESS 可见
"""
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
    """模板管理 Page Object。

    覆盖模板列表（系统 / 自定义）、创建模板子页面、构建轮询、清理删除
    等全生命周期操作。所有可复用的元素在 :meth:`__init__` 中集中定义。
    """

    def __init__(self, page: Page):
        """初始化模板管理页元素定位器。

        Args:
            page: Playwright 的 :class:`~playwright.sync_api.Page` 对象。
        """
        super().__init__(page)
        logger.info("Template Manage Page Initialized")

        # 沙箱主内容 iframe
        # Note: 使用 FrameLocator，每次访问自动重新解析，避免 iframe 重载后引用失效
        self.frame = page.locator("iframe").first.content_frame

        # ==================== Tab ====================
        self.tab_system = self.frame.get_by_role("tab", name="系统模板")
        self.tab_custom = self.frame.get_by_role("tab", name="自定义模板")

        # ==================== 自定义模板列表页搜索区 ====================
        # Note: `_search` 后缀区分创建子页面同名下拉，避免命名混淆
        self.dropdown_image_repo_search = self.frame.locator(
            ".ep-select__wrapper:has-text('请选择镜像仓库'), "
            ".el-select__wrapper:has-text('请选择镜像仓库')"
        ).first
        self.dropdown_scene_search = self.frame.locator(
            ".ep-select__wrapper:has-text('请选择场景分类'), "
            ".el-select__wrapper:has-text('请选择场景分类')"
        ).first
        self.input_search = self.frame.get_by_placeholder("请输入模板名称或ID")
        self.btn_search = self.frame.get_by_role("button", name="查询")
        self.btn_create_template = self.frame.get_by_role("button", name="创建模板")

        # 数据表格：iframe 内第 2 个 table（第 1 个是表头容器）
        self.table_data = self.frame.get_by_role("table").nth(1)

        # ==================== 创建模板子页面元素 ====================
        # 面包屑上的"创建模板"链接，用于判断是否处于创建子页面
        self.link_breadcrumb_create = self.frame.get_by_role("link", name="创建模板")

        # ---- 基本配置
        self.input_template_name = self.frame.get_by_role(
            "textbox", name="* 模板名称"
        )
        self.input_remark = self.frame.get_by_role("textbox", name="备注")

        # ---- 沙箱镜像
        self.dropdown_image_repo_create = self.frame.locator(
            ".ep-select__wrapper:has-text('选择镜像仓库'), "
            ".el-select__wrapper:has-text('选择镜像仓库')"
        ).first
        self.input_start_command = self.frame.get_by_role(
            "textbox", name="启动命令"
        )
        self.input_ready_command = self.frame.get_by_role(
            "textbox", name="就绪命令"
        )

        # ---- 高级配置
        self.input_vcpu = self.frame.get_by_placeholder("vCPU")
        self.input_gib = self.frame.get_by_placeholder("GIB")

        # ---- 底部按钮
        self.btn_back = self.frame.get_by_role("button", name="返回")
        self.btn_create = self.frame.get_by_role("button", name="创建")
        self.btn_create_confirm = self.frame.get_by_role("button", name="确定")

        # ==================== 弹窗/告警 ====================
        # 删除确认弹窗
        self.msg_box = self.frame.locator(
            ".ep-message-box, .el-message-box, .message-box"
        ).first
        # 全局 toast 提示（非 message box）
        self.alert = self.frame.locator(
            ".ep-message__content, .el-message__content"
        ).first

    # ==================== 导航 ====================

    def navigate_to(self, base_url: str) -> None:
        """通过 URL 直接导航进入模板管理页面。

        菜单点击有时不会重新加载 iframe，因此对稳定性要求高的用例应优先使用本方法。

        Args:
            base_url: 站点根 URL（``http[s]://host[:port]``），不含 iframe 路径。
        """
        logger.info(f"导航到模板管理: {SandboxFramePath.TEMPLATE_MANAGE}")
        self.page.goto(
            base_url + SandboxFramePath.TEMPLATE_MANAGE,
            timeout=UITimeout.NAVIGATION_TIMEOUT,
        )
        self.page.wait_for_load_state(state="load")
        # 等待 iframe 内首个 tab 可见 = 页面初始渲染完成，避免固定 sleep
        expect(self.tab_custom).to_be_visible(
            timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT
        )

    # ==================== Tab 切换 ====================

    def switch_to_custom_template(self) -> None:
        """切换到"自定义模板"tab，并等待 tab 变为激活状态。"""
        logger.info("切换到自定义模板tab")
        self.tab_custom.click()
        self._wait_tab_active(self.tab_custom, "自定义模板")

    def switch_to_system_template(self) -> None:
        """切换到"系统模板"tab，并等待 tab 变为激活状态。"""
        logger.info("切换到系统模板tab")
        self.tab_system.click()
        self._wait_tab_active(self.tab_system, "系统模板")

    def _wait_tab_active(self, tab: Locator, tab_name: str) -> None:
        """等待 tab 变为激活状态。

        优先通过 ``aria-selected="true"`` 属性判定；无法判定时退化为
        短稳定等待（避免脆弱地依赖前端具体实现）。

        Args:
            tab: tab 元素定位器。
            tab_name: 用于日志的 tab 名称。
        """
        try:
            expect(tab).to_have_attribute(
                "aria-selected", "true", timeout=UITimeout.STABILIZE
            )
        except (PlaywrightTimeoutError, AssertionError):
            logger.debug(
                f"tab【{tab_name}】未通过 aria-selected 判定激活，退化为短稳定等待"
            )
            self.page.wait_for_timeout(UITimeout.SHORT)

    # ==================== 创建模板 ====================

    def click_create_template(self) -> None:
        """点击"创建模板"按钮，切换到创建模板子页面（**非弹窗**）。

        创建模板是同一 iframe 内的子页面切换，通过判断面包屑上的
        "创建模板"链接是否出现来确认已进入。
        """
        logger.info("点击创建模板按钮")
        self.btn_create_template.click()
        # 面包屑"创建模板"链接可见 == 已进入创建子页面
        expect(self.link_breadcrumb_create).to_be_visible(
            timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT
        )

    def is_create_page_active(self) -> bool:
        """检测当前是否处于"创建模板"子页面。

        通过面包屑上的"创建模板"链接可见性判断，避免与列表页混淆。

        Returns:
            bool: True 表示当前在创建子页面；False 表示不在或探测超时。
        """
        try:
            return self.link_breadcrumb_create.is_visible(
                timeout=UITimeout.ANIMATION
            )
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

        分三个配置区依次填写：

        1. **基本配置**：模板名称（必填）、备注（可选）
        2. **沙箱镜像**：选择镜像仓库（必填，两步法：点开下拉 → 选选项）、
           启动/就绪命令（可选）
        3. **高级配置**：vCPU、GIB 内存、场景分类（三者均为必填）

        前端带 ``*`` 的必填项：模板名称、镜像仓库、规格配置 (vCPU + GIB)、场景分类。
        本方法**不做必填校验**，仅按传入参数填写；未传的字段保持前端默认或空。

        Args:
            template_name: 模板名称（必填）。
            remark: 备注（可选）。
            image_repo: 要选择的镜像仓库名（如 "系统仓库"）；传入后会自动展开下拉并点选。
            cpu: vCPU 规格（字符串或数字，会转为 ``str`` 后填入）。
            memory: GIB 内存规格。
            scene: 场景分类文本（如 "代码"/"桌面"/"浏览器"/"其它"），通过 radio 点选。
            start_command: 启动命令（可选）。
            ready_command: 就绪命令（可选）。
        """
        logger.info(f"填写创建模板: {template_name}")
        # 前置校验：必须已进入创建子页面
        expect(self.link_breadcrumb_create).to_be_visible(
            timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT
        )

        # ---- 基本配置 ----
        self.input_template_name.fill(template_name)
        if remark:
            self.input_remark.fill(remark)

        # ---- 沙箱镜像 ----
        # 选择镜像仓库（两步法）：click wrapper 展开下拉，再点具体 option
        if image_repo:
            self.dropdown_image_repo_create.click()
            option = self.frame.get_by_role(
                "option", name=image_repo, exact=True
            )
            expect(option).to_be_visible(
                timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT
            )
            option.click()
            # 选中仓库后镜像列表异步刷新，等待表格稳定
            self.page.wait_for_timeout(UITimeout.STABILIZE)

        if start_command:
            self.input_start_command.fill(start_command)
        if ready_command:
            self.input_ready_command.fill(ready_command)

        # ---- 高级配置 ----
        # vCPU / GIB 是 spinbutton，直接 fill 数字字符串即可
        if cpu:
            self.input_vcpu.fill(str(cpu))
        if memory:
            self.input_gib.fill(str(memory))

        # 场景分类是 radiogroup：点击对应 radio 的 label 文本
        # Note: 有的实现中 radio 是 hidden input + 装饰 label，用 force=True 更稳
        if scene:
            self.frame.get_by_role("radio", name=scene).click(force=True)
            self.page.wait_for_timeout(UITimeout.ANIMATION)

    def select_base_image(self, base_image: str) -> None:
        """在创建模板子页面勾选镜像列表的指定行。

        必须在 :meth:`fill_create_form` 选择了镜像仓库之后调用，
        否则镜像列表可能为空。

        Args:
            base_image: 镜像名称（accessible name 精确匹配）。
        """
        logger.info(f"勾选镜像: {base_image}")
        row = self.table_data.get_by_role("row", name=base_image).first
        expect(row).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)
        # Note: 行内第 2 个 <span> 对应勾选框（第 1 个是排序图标等装饰元素）
        row.locator("span").nth(1).click()

    def select_first_image(self) -> bool:
        """勾选镜像列表的第一行。

        必须在选择了镜像仓库之后调用；列表为空时返回 False 而非抛错。

        Returns:
            bool: True 表示已成功勾选；False 表示列表为空。
        """
        logger.info("勾选第一个镜像")
        rows = self.table_data.get_by_role("row")
        try:
            expect(rows.first).to_be_visible(
                timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT
            )
        except (PlaywrightTimeoutError, AssertionError):
            logger.info("镜像列表为空，无法勾选")
            return False

        rows.first.locator("label.ep-checkbox, label.el-checkbox").first.click()
        return True

    def confirm_create(self) -> None:
        """点击"创建"按钮提交模板，并在二次确认弹窗上点"确定"。

        流程：主按钮"创建" → 弹窗渲染 → 二次确认"确定"。
        两次点击之间通过 ``expect(...).to_be_visible()`` 等待弹窗渲染，
        避免固定 sleep。
        """
        logger.info("点击创建按钮提交模板")
        self.btn_create.click()
        expect(self.btn_create_confirm).to_be_visible(
            timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT
        )
        self.btn_create_confirm.click()

    def cancel_create(self) -> None:
        """点击"返回"按钮退出创建模板子页面。

        通过等待面包屑"创建模板"链接消失来确认已回到列表页。
        """
        self.btn_back.click()
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
        """幂等创建自定义模板：已存在则跳过，不存在则完整走一遍创建流程。

        完整流程：

        1. 检查模板是否已存在（存在直接返回 ``False``）
        2. 点击"创建模板"进入子页面
        3. 填写表单
        4. （可选）勾选 base 镜像
        5. 点击"创建"并在弹窗上确认
        6. 等待返回列表 + 模板行出现
        7. 轮询等待构建进入终态（成功 / 失败）
        8. 断言模板行内出现"成功"文案

        Args:
            template_name: 模板名称（必填，用于幂等键）。
            remark: 备注。
            image_repo: 镜像仓库名。
            base_image: 镜像仓库勾选后再勾选的具体镜像名。
            cpu: vCPU 数量。
            memory: GIB 内存数量。
            scene: 场景分类。

        Returns:
            bool: ``True`` 表示新创建成功；``False`` 表示模板已存在、跳过创建。

        Raises:
            AssertionError: 构建终态非"成功"，或轮询完成仍未进入终态。
        """
        # ---- Step 1: 幂等短路
        if self.is_template_exists(template_name):
            logger.info(f"自定义模板【{template_name}】已存在，跳过创建")
            return False

        # ---- Step 2-5: 创建
        self.click_create_template()
        self.fill_create_form(
            template_name=template_name,
            remark=remark,
            image_repo=image_repo,
            cpu=cpu,
            memory=memory,
            scene=scene,
        )
        if base_image:
            self.select_base_image(base_image)
        self.confirm_create()

        # ---- Step 6: 已返回列表，模板行出现
        expect(self.link_breadcrumb_create).to_be_hidden(
            timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT
        )
        row = self._get_row_by_name(template_name)
        expect(row).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)

        # ---- Step 7-8: 轮询构建终态，断言"成功"
        self._poll_until_build_terminal(template_name)
        expect(row.get_by_text(SandboxTemplateStatus.SUCCESS.value)).to_be_visible()
        logger.info(f"自定义模板【{template_name}】创建成功")
        return True

    def _poll_until_build_terminal(self, template_name: str) -> None:
        """在自定义模板列表页点击"查询"轮询，直到目标行进入终态（成功/失败）。

        每轮点击"查询"触发前端重新请求数据，然后短探测目标行内是否出现
        终态文本；两轮之间用 ``UITimeout.POLL_INTERVAL`` 隔开。
        总轮次 = ``BUILD_MAX_WAIT // POLL_INTERVAL``。

        Args:
            template_name: 模板名称（用于定位表格行）。

        Note:
            方法**不会**抛异常表示"超时"，只会记录 warning；调用方
            （如 :meth:`create_template_if_not_exists`）会在后续用
            ``expect(...).to_be_visible()`` 做最终断言。
        """
        max_rounds = UITimeout.BUILD_MAX_WAIT // UITimeout.POLL_INTERVAL
        row = self._get_row_by_name(template_name)
        terminal_values = SandboxTemplateStatus.terminal_values()

        for round_idx in range(max_rounds):
            # 每轮点击"查询"触发前端刷新
            self.btn_search.click()
            self.page.wait_for_timeout(UITimeout.POLL_INTERVAL)

            # 短探测：任一终态文本出现即视为终止
            for status_value in terminal_values:
                try:
                    if row.get_by_text(status_value).is_visible(
                            timeout=UITimeout.ANIMATION
                    ):
                        logger.info(
                            f"模板【{template_name}】在第 {round_idx + 1} 轮"
                            f"进入终态: {status_value}"
                        )
                        return
                except PlaywrightTimeoutError:
                    # 本轮该终态未匹配，尝试下一个终态或下一轮
                    continue
        logger.warning(f"模板【{template_name}】轮询完成仍未进入终态")

    # ==================== 自定义模板列表操作 ====================

    def search_custom_template(self, template_name: str) -> None:
        """在"自定义模板"tab 按模板名称搜索。

        搜索框在某些页面状态下可能不可见（例如尚未选择镜像仓库过滤时），
        此时静默跳过，不抛异常。

        Args:
            template_name: 模板名。
        """
        logger.info(f"搜索自定义模板: {template_name}")
        try:
            if self.input_search.is_visible(timeout=UITimeout.ANIMATION):
                self.input_search.fill(template_name)
                self.btn_search.click()
                self.page.wait_for_timeout(UITimeout.QUERY)
        except PlaywrightTimeoutError:
            logger.debug("搜索输入框不可见，跳过搜索")

    def _get_row_by_name(self, template_name: str) -> Locator:
        """按模板名称获取表格行定位器（正则转义后精确到具体行）。

        Args:
            template_name: 模板名。

        Returns:
            Locator: 目标行的 Playwright Locator（``.first``，避免多命中）。
        """
        return self.table_data.get_by_role(
            "row", name=re.compile(re.escape(template_name))
        ).first

    def is_template_exists(self, template_name: str) -> bool:
        """检查自定义模板是否已存在。

        执行方式：先搜索定位到目标行，再判断行可见性。

        Args:
            template_name: 模板名。

        Returns:
            bool: True 表示存在；False 表示不存在或探测超时。
        """
        try:
            self.search_custom_template(template_name)
            return self._get_row_by_name(template_name).is_visible(
                timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT
            )
        except PlaywrightTimeoutError:
            return False

    def get_template_status(self, template_name: str) -> str:
        """获取模板当前的构建/发布状态文本。

        实现：遍历目标行的 ``<td>`` 单元格，取第一个命中
        :class:`SandboxTemplateStatus` 枚举值的单元格文本。
        若目标行不存在/未匹配任何已知状态，返回空串。

        Args:
            template_name: 模板名。

        Returns:
            str: 状态文本（例如 "构建中"/"成功"），未找到时返回 ``""``。
        """
        try:
            row = self._get_row_by_name(template_name)
            if not row.is_visible(timeout=UITimeout.ANIMATION):
                return ""
            cells = row.locator("td")
            valid_values = SandboxTemplateStatus.all_values()
            # 逐格取文本，与已知状态集合做成员判断
            for i in range(cells.count()):
                # Note: text_content() 可能返回 None；用 `or ""` 兜底避免 AttributeError
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

        本方法**只判定模板是否出现在列表**，不判定构建终态；
        典型用途：创建后跨页刷新，确认列表可查到（例如 JC009 用例）。
        若需要等待构建成功/失败，请使用 :meth:`create_template_if_not_exists`
        中的完整流程。

        实现细节：每轮通过 URL 重新导航到列表页（避免 iframe 内 SPA 状态残留），
        再切到自定义模板 tab 后搜索。

        Args:
            template_name: 模板名。
            timeout_ms: 总等待时长（毫秒），默认 ``UITimeout.BUILD_MAX_WAIT``。

        Returns:
            bool: ``True`` 表示已出现；``False`` 表示超时仍未出现。
        """
        logger.info(
            f"等待模板【{template_name}】出现在列表，最长 {timeout_ms // 1000}s"
        )
        elapsed = 0
        # Note: 从当前 URL 剥出 base_url（截取到 /iframe 之前），用于跨页导航
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
        """等待模板出现在自定义模板列表（**语义等同于** :meth:`wait_template_visible`）。

        Args:
            template_name: 模板名。
            timeout_ms: 总等待时长（毫秒）。

        Returns:
            bool: 是否在超时前出现。

        .. deprecated::
            方法名不能准确描述"仅判定出现"这一语义。请改用
            :meth:`wait_template_visible`。此方法仅为向后兼容保留。
        """
        return self.wait_template_visible(template_name, timeout_ms)

    # ==================== 删除模板 ====================

    def click_delete_template(self, template_name: str) -> None:
        """点击指定自定义模板的"删除"按钮。

        点击后需要在弹出的确认弹窗上二次确认，具体确认动作见 :meth:`confirm_delete`。

        Args:
            template_name: 模板名。
        """
        logger.info(f"点击模板【{template_name}】的删除按钮")
        row = self._get_row_by_name(template_name)
        expect(row).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)
        row.get_by_role("button", name="删除").click()
        # 等待确认弹窗渲染完成
        expect(self.msg_box).to_be_visible(
            timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT
        )

    def confirm_delete(self) -> None:
        """在删除确认弹窗上点击"确定/删除"，并等待弹窗关闭。

        兼容不同项目里按钮文案的差异（正则匹配"确定|删除"）；
        如果弹窗未渲染出来则静默跳过。
        """
        try:
            if self.msg_box.is_visible(timeout=UITimeout.ANIMATION):
                # Note: 使用 .last 是因为部分弹窗右上角还有一个"关闭"图标 button，
                #       last 命中底部主按钮
                self.msg_box.get_by_role(
                    "button", name=re.compile(r"确定|删除")
                ).last.click()
                expect(self.msg_box).to_be_hidden(
                    timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT
                )
        except PlaywrightTimeoutError:
            logger.debug("确认删除弹窗不可见，跳过")

    def cleanup_template(self, template_name: str) -> None:
        """幂等清理指定自定义模板：存在则删除，不存在则跳过。

        典型用法：pytest 用例的 teardown 阶段调用，保证测试数据干净。
        异常仅记录 warning，不重新抛出（避免影响其他 teardown 步骤）。

        Args:
            template_name: 模板名。
        """
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
            # 清理路径吞并具体异常，避免污染主流程；但一定要 log 记录
            logger.warning(f"清理模板【{template_name}】异常: {e}")
            self._safe_press_escape()

    def _safe_press_escape(self) -> None:
        """尽力关闭可能残留的弹窗（发送 ESC 键）。

        用于 cleanup 阶段兜底恢复现场；发送失败仅记录 debug，不再抛出。
        """
        try:
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(UITimeout.ANIMATION)
        except PlaywrightError as e:
            logger.debug(f"按 ESC 关闭残留弹窗失败: {e}")

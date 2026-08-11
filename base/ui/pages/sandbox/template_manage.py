import re

from playwright.sync_api import Page, expect, Locator

from base.ui.pages.base import BasePage
from constants.bussiness import SandboxFramePath
from core import get_logger

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

        # 自定义模板tab搜索区域（镜像仓库下拉 + 场景分类下拉 + 模板名称/ID输入 + 查询 + 创建模板）
        self.dropdown_image_repo = self.frame.locator(
            ".ep-select__wrapper:has-text('请选择镜像仓库'), .el-select__wrapper:has-text('请选择镜像仓库')"
        ).first
        self.dropdown_scene = self.frame.locator(
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
        self.page.goto(base_url + SandboxFramePath.TEMPLATE_MANAGE, timeout=60000)
        self.page.wait_for_load_state(state="load")
        self.page.wait_for_timeout(1000)

    def switch_to_custom_template(self):
        # 切换到自定义模板tab
        logger.info("切换到自定义模板tab")
        self.tab_custom.click()
        self.page.wait_for_timeout(1000)

    def switch_to_system_template(self):
        # 切换到系统模板tab
        logger.info("切换到系统模板tab")
        self.tab_system.click()
        self.page.wait_for_timeout(1000)

    def click_create_template(self):
        # 点击创建模板按钮（自定义模板tab），切换到创建模板子页面（非弹窗）
        logger.info("点击创建模板按钮")
        self.btn_create_template.click()
        self.page.wait_for_timeout(1000)

    def is_create_page_active(self) -> bool:
        # 检测是否已切换到"创建模板"子页面（通过面包屑"创建模板"链接判断）
        try:
            return self.link_breadcrumb_create.is_visible()
        except Exception:
            return False

    def fill_create_form(self, template_name: str, remark: str = None,
                         image_repo: str = None, cpu: str = None,
                         memory: str = None, scene: str = None,
                         start_command: str = None, ready_command: str = None):
        # 填写创建模板子页面表单（基于实际采集的字段结构）
        # 分3个配置区：基本配置、沙箱镜像、高级配置
        # 必填项（带*）：模板名称、选择镜像仓库、规格配置(vCPU+GIB)、场景分类
        logger.info(f"填写创建模板: {template_name}")
        # 验证已进入创建模板子页面
        expect(self.link_breadcrumb_create).to_be_visible()

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
            self.page.wait_for_timeout(500)
            self.frame.get_by_role("option", name=image_repo, exact=True).click()
            self.page.wait_for_timeout(1000)
            # self.frame.get_by_role("row", name="base").locator("span").nth(1).check() #base镜像

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
            self.page.wait_for_timeout(300)

    def select_base_image(self, base_image):
        # 在创建模板子页面中勾选镜像列表的base（必须在选择了镜像仓库后调用）
        logger.info("勾选base镜像")
        # 镜像列表是iframe内的第2个table（第1个是表头）
        row = self.table_data.get_by_role("row", name=base_image).first
        # 点击行的checkbox
        row.locator("span").nth(1).click()
        self.page.wait_for_timeout(500)

    def select_first_image(self):
        # 在创建模板子页面中勾选镜像列表的第一行（必须在选择了镜像仓库后调用）
        logger.info("勾选第一个镜像")
        # 镜像列表是iframe内的第2个table（第1个是表头）
        rows = self.table_data.get_by_role("row")
        if rows.count() > 0:
            first_row = rows.first
            # 点击行首的checkbox
            first_row.locator("label.ep-checkbox, label.el-checkbox").first.click()
            self.page.wait_for_timeout(500)
            return True
        logger.info("镜像列表为空，无法勾选")
        return False

    def confirm_create(self):
        # 点击"创建"按钮提交模板（创建模板子页面底部）
        logger.info("点击创建按钮提交模板")
        self.btn_create.click()
        self.btn_create_confirm.click()

    def cancel_create(self):
        # 点击"返回"按钮退出创建模板子页面
        self.btn_back.click()
        self.page.wait_for_timeout(800)

    def is_create_page_visible(self) -> bool:
        # 创建模板子页面是否可见（用于检测验证错误未返回列表）
        return self.is_create_page_active()

    def create_template_if_not_exists(self, template_name: str, remark: str = None,
                                      image_repo: str = None, base_image: str = None,
                                      cpu: str = None, memory: str = None,
                                      scene: str = None) -> bool:
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
        expect(self.link_breadcrumb_create).to_be_visible()
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
        self.page.wait_for_timeout(2000)
        # 验证已返回自定义模板列表
        expect(self.link_breadcrumb_create).to_be_hidden()
        expect(self._get_row_by_name(template_name)).to_be_visible()
        # 轮询等待模板构建成功
        for i in range(20):
            self.btn_search.click()
            self.page.wait_for_timeout(5000)
            if self._get_row_by_name(template_name).get_by_text("成功").is_visible() or self._get_row_by_name(
                    template_name).get_by_text("失败").is_visible():
                break
        expect(self._get_row_by_name(template_name).get_by_text("成功")).to_be_visible()
        logger.info(f"自定义模板【{template_name}】创建成功")
        return True

    # ==================== 自定义模板列表操作 ====================

    def search_custom_template(self, template_name: str):
        # 在自定义模板tab按模板名称搜索
        logger.info(f"搜索自定义模板: {template_name}")
        # 自定义模板tab可能无搜索框，使用全局刷新策略
        try:
            if self.input_search.is_visible():
                self.input_search.fill(template_name)
                self.btn_search.click()
                self.page.wait_for_timeout(800)
        except Exception:
            pass

    def _get_row_by_name(self, template_name: str) -> Locator:
        # 按模板名称获取行
        return self.table_data.get_by_role(
            "row", name=re.compile(re.escape(template_name))
        ).first

    def is_template_exists(self, template_name: str) -> bool:
        # 检查自定义模板是否已存在
        try:
            self.search_custom_template(template_name)
            return self._get_row_by_name(template_name).is_visible()
        except Exception:
            return False

    def get_template_status(self, template_name: str) -> str:
        # 获取模板构建状态（如"构建中"/"成功"/"失败"）
        try:
            row = self._get_row_by_name(template_name)
            if not row.is_visible():
                return ""
            cells = row.locator("td")
            for i in range(cells.count()):
                txt = cells.nth(i).text_content().strip()
                if txt in ("构建中", "成功", "失败", "可用", "已发布", "未发布", "正常"):
                    return txt
        except Exception:
            pass
        return ""

    def wait_template_build_success(self, template_name: str, timeout_ms: int = 120000):
        # 轮询等待模板构建完成（默认最长120s）
        # 注意：自定义模板可能无"构建状态"概念，创建后即生效，主要用于JC009
        logger.info(f"等待模板【{template_name}】创建生效，最长 {timeout_ms // 1000}s")
        interval = 5000
        elapsed = 0
        base_url = self.page.url.split('/iframe')[0]
        while elapsed < timeout_ms:
            self.navigate(base_url)
            self.switch_to_custom_template()
            self.search_custom_template(template_name)
            if self.is_template_exists(template_name):
                logger.info(f"模板【{template_name}】已存在")
                return True
            self.page.wait_for_timeout(interval)
            elapsed += interval
        return False

    # ==================== 删除模板 ====================

    def click_delete_template(self, template_name: str):
        # 点击模板的删除按钮（自定义模板tab）
        logger.info(f"点击模板【{template_name}】的删除按钮")
        row = self._get_row_by_name(template_name)
        expect(row).to_be_visible()
        row.get_by_role("button", name="删除").click()
        self.page.wait_for_timeout(800)

    def confirm_delete(self):
        # 确认删除模板
        if self.msg_box.is_visible():
            self.msg_box.get_by_role("button", name=re.compile(r"确定|删除")).last.click()
            self.page.wait_for_timeout(800)

    def cleanup_template(self, template_name: str):
        # 幂等清理自定义模板
        logger.info(f"清理自定义模板: {template_name}")
        try:
            self.switch_to_custom_template()
            self.search_custom_template(template_name)
            row = self._get_row_by_name(template_name)
            if row.is_visible():
                self.click_delete_template(template_name)
                self.confirm_delete()
                logger.info(f"模板【{template_name}】删除成功")
            else:
                logger.info(f"模板【{template_name}】不存在，无需清理")
        except Exception as e:
            logger.info(f"清理模板【{template_name}】异常: {e}")
            try:
                self.page.keyboard.press("Escape")
                self.page.wait_for_timeout(300)
            except Exception:
                pass

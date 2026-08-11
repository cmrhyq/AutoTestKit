from playwright.sync_api import Page

from base.ui.pages.base import BasePage
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
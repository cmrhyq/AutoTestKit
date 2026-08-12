"""
节点管理 Page Object（沙箱 -> 沙箱集群 -> 节点管理）。

页面结构：
    - 搜索区: 节点ID输入框 + 状态下拉(全部状态/就绪/离线/异常/下线中/连接中)
              + 集群下拉 + 查询按钮 + 刷新按钮 + 同步节点信息按钮
    - 数据表格: 节点ID、所属集群、状态、节点类型、CPU(已用/共计)、内存(已用/共计)、存储(已用/共计)、操作
    - 分页: 条数切换(10/20/50/100) + 上一页/下一页 + 跳转
    - 抽屉: "节点详情"抽屉 / "同步节点"抽屉（含新增/变更/待删除统计 + 取消/确定按钮）

iframe src: /sandbox-web/cluster/node?envCode=PROD&tenantCode=tenant_admin&viewType=1
UI 框架: Element Plus (el- 前缀)
"""
from playwright.sync_api import Page, expect

from base.ui.pages.base import BasePage
from core import get_logger
from core.constants import UITimeout
from core.constants.bussiness import SandboxFramePath, SandboxNodeStatus, PageSize

logger = get_logger(__name__)


class NodeManagePage(BasePage):
    """节点管理 Page Object。"""

    def __init__(self, page: Page):
        """初始化节点管理页元素定位器。

        Args:
            page: Playwright 的 :class:`~playwright.sync_api.Page` 对象。
        """
        super().__init__(page)
        logger.info("Node Manage Page Initialized")

        # 沙箱主内容 iframe
        self.frame = page.locator("iframe").first.content_frame

        # ==================== 搜索区 ====================
        self.input_node_id = self.frame.get_by_placeholder("请输入节点ID")
        # 状态下拉：使用第一个 el-select 组件（宽度200px的那个）
        self.dropdown_status = self.frame.locator(
            ".el-form .el-select"
        ).first.locator(".el-select__wrapper")
        # 集群下拉：使用第二个 el-select 组件（宽度240px的那个，支持搜索）
        self.dropdown_cluster = self.frame.locator(
            ".el-form .el-select"
        ).nth(1).locator(".el-select__wrapper")
        self.btn_search = self.frame.get_by_role("button", name="查询")
        self.btn_refresh = self.frame.get_by_role("button", name="刷新")
        self.btn_sync_nodes = self.frame.get_by_role("button", name="同步节点信息")

        # ==================== 数据表格 ====================
        # iframe 内第 1 个 table 是表头，第 2 个是数据行
        self.table_header = self.frame.get_by_role("table").first
        self.table_data = self.frame.get_by_role("table").nth(1)

        # 表头列（通过 columnheader role 定位，更稳定）
        self.col_node_id = self.frame.get_by_role("columnheader", name="节点ID")
        self.col_cluster = self.frame.get_by_role("columnheader", name="所属集群")
        self.col_status = self.frame.get_by_role("columnheader", name="状态")
        self.col_node_type = self.frame.get_by_role("columnheader", name="节点类型")
        self.col_cpu = self.frame.get_by_role("columnheader", name="CPU(已用/共计)")
        self.col_memory = self.frame.get_by_role("columnheader", name="内存(已用/共计)")
        self.col_storage = self.frame.get_by_role("columnheader", name="存储(已用/共计)")
        self.col_operation = self.frame.get_by_role("columnheader", name="操作")

        # ==================== 分页 ====================
        self.pagination_total = self.frame.locator(".el-pagination__total")
        self.btn_prev_page = self.frame.get_by_role("button", name="上一页")
        self.btn_next_page = self.frame.get_by_role("button", name="下一页")

        # ==================== 抽屉：节点详情 ====================
        self.drawer_node_detail = self.frame.locator(
            ".el-drawer"
        ).filter(has_text="节点详情")
        self.btn_close_detail = self.drawer_node_detail.get_by_role(
            "button", name="关闭此对话框"
        )

        # ==================== 抽屉：同步节点 ====================
        self.drawer_sync = self.frame.locator(
            ".el-drawer"
        ).filter(has_text="同步节点")
        self.btn_close_sync = self.drawer_sync.get_by_role(
            "button", name="关闭此对话框"
        )
        self.btn_sync_cancel = self.drawer_sync.get_by_role("button", name="取消")
        self.btn_sync_confirm = self.drawer_sync.get_by_role("button", name="确定")

    # ==================== 导航 ====================

    def navigate_to(self, base_url: str) -> None:
        """通过 URL 直接导航进入节点管理页面。

        Args:
            base_url: 站点根 URL（``http[s]://host[:port]``），不含 iframe 路径。
        """
        logger.info(f"导航到节点管理: {SandboxFramePath.NODE_MANAGE}")
        self.page.goto(base_url + SandboxFramePath.NODE_MANAGE, timeout=UITimeout.NAVIGATION_TIMEOUT)
        self.page.wait_for_load_state(state="load")
        expect(self.input_node_id).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)

    # ==================== 搜索操作 ====================

    def select_status(self, status: SandboxNodeStatus) -> None:
        """选择节点状态下拉选项。

        Args:
            status: 状态文本，可选值: "全部状态"、"就绪"、"离线"、"异常"、"下线中"、"连接中"
        """
        logger.info(f"选择节点状态：{status}")
        self.dropdown_status.click()
        self.frame.get_by_role("option", name=status).click()
        self.page.wait_for_timeout(UITimeout.ANIMATION)

    def select_cluster(self, cluster_name: str) -> None:
        """选择集群下拉选项。

        Args:
            cluster_name: 集群名称，如 "cluster01"、"sit5-01"
        """
        logger.info(f"选择集群：{cluster_name}")
        self.dropdown_cluster.click()
        self.frame.get_by_role("option", name=cluster_name).click()
        self.page.wait_for_timeout(UITimeout.ANIMATION)

    def search(self, node_id: str = "", status: SandboxNodeStatus = None, cluster: str = None) -> None:
        """执行搜索操作。

        Args:
            node_id: 节点ID关键词（可选）
            status: 状态筛选（可选）
            cluster: 集群筛选（可选）
        """
        if node_id:
            self.input_node_id.fill(node_id)
        if status:
            self.select_status(status)
        if cluster:
            self.select_cluster(cluster)
        self.btn_search.click()
        self.page.wait_for_timeout(UITimeout.QUERY)

    # ==================== 表格操作 ====================

    def click_detail_button(self, row_index: int = 0) -> None:
        """点击指定行的"详情"按钮打开节点详情抽屉。

        Args:
            row_index: 行索引，从0开始
        """
        logger.info(f"点击第 {row_index + 1} 行的详情按钮")
        self.frame.locator(".el-table__body .el-table__row").nth(
            row_index
        ).get_by_role("button", name="详情").click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    # ==================== 同步节点操作 ====================

    def sync_node_info(self) -> None:
        """点击同步节点信息按钮，等待同步抽屉出现。"""
        logger.info("同步节点信息")
        self.btn_sync_nodes.click()
        expect(self.btn_close_sync).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)

    def close_sync_drawer(self) -> None:
        """关闭同步节点抽屉。"""
        self.btn_close_sync.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def close_detail_drawer(self) -> None:
        """关闭节点详情抽屉。"""
        self.btn_close_detail.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    # ==================== 分页操作 ====================

    def change_page_size(self, size: PageSize) -> None:
        """切换每页显示条数。

        Args:
            size: 每页条数文本，如 "10条/页"、"20条/页"、"50条/页"、"100条/页"
        """
        logger.info(f"切换每页条数: {size}")
        self.frame.locator(".el-pagination .el-select__wrapper").click()
        self.frame.get_by_role("option", name=size).click()
        self.page.wait_for_timeout(UITimeout.QUERY)

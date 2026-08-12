"""
Sandbox UI 功能测试

基于 Page Object 编写的功能级测试用例，覆盖：
- 节点管理：状态筛选、集群筛选、同步节点、节点详情
- 构建记录：状态筛选、查询、分页切换
- SDK使用示例：章节完整性、查看示例弹窗
- 沙箱管理：Tab切换、搜索
- 镜像管理：Tab切换、搜索
"""
import allure
import pytest
from playwright.sync_api import expect

from base.ui.pages.sandbox.build_record import BuildRecordPage
from base.ui.pages.sandbox.home import HomePage
from base.ui.pages.sandbox.image_library import ImageLibraryPage
from base.ui.pages.sandbox.node_manage import NodeManagePage
from base.ui.pages.sandbox.sandbox_manage import SandboxManagePage
from base.ui.pages.sandbox.sdk_example import SdkExamplePage
from core import get_logger
from core.constants import UITimeout
from core.constants.bussiness import (
    BuildRecordStatus,
    PageSize,
    SandboxMenu,
    SandboxNodeStatus,
    SandboxType,
    SystemMenu,
)
from core.reporting import AllureHelper

logger = get_logger(__name__)


@pytest.mark.ui
@allure.epic("Sandbox UI自动化测试")
@allure.feature("节点管理")
class TestNodeManage:
    """沙箱集群 - 节点管理 功能测试"""

    @pytest.fixture(autouse=True)
    def setup(self, login_context):
        self.context, self.page = login_context
        self.home_page = HomePage(self.page)
        self.home_page.switch_top_menu(SystemMenu.SANDBOX)
        self.home_page.expand_sidebar()
        self.page.wait_for_timeout(500)  # 等待侧边栏展开动画完成
        self.node_manage_page = NodeManagePage(self.page)

        # 导航到节点管理页面
        self.home_page.open_menu(SandboxMenu.SANDBOX_CLUSTER, SandboxMenu.NODE_MANAGE)
        self.home_page.wait_frame_ready()

        yield
        self.home_page.wait_alert_hidden()

    @allure.story("页面元素验证")
    @allure.title("节点管理页面元素完整性检查")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_page_elements(self):
        """验证节点管理页面所有核心元素可见"""
        with AllureHelper.step("验证搜索区元素"):
            self.node_manage_page.assert_no_alert(retries=6)
            expect(self.node_manage_page.input_node_id).to_be_visible()
            expect(self.node_manage_page.dropdown_status).to_be_visible()
            expect(self.node_manage_page.dropdown_cluster).to_be_visible()
            expect(self.node_manage_page.btn_search).to_be_visible()
            expect(self.node_manage_page.btn_refresh).to_be_visible()
            expect(self.node_manage_page.btn_sync_nodes).to_be_visible()

        with AllureHelper.step("验证表格表头"):
            expect(self.node_manage_page.col_node_id).to_be_visible()
            expect(self.node_manage_page.col_cluster).to_be_visible()
            expect(self.node_manage_page.col_status).to_be_visible()
            expect(self.node_manage_page.col_node_type).to_be_visible()
            expect(self.node_manage_page.col_cpu).to_be_visible()
            expect(self.node_manage_page.col_memory).to_be_visible()
            expect(self.node_manage_page.col_storage).to_be_visible()

        self.node_manage_page.assert_no_alert()
        self.node_manage_page.take_screenshot("节点管理-元素完整性", True)

    @allure.story("状态筛选")
    @allure.title("按就绪状态筛选节点")
    @allure.severity(allure.severity_level.NORMAL)
    def test_filter_by_ready_status(self):
        """选择'就绪'状态后查询，验证表格正常显示"""
        with AllureHelper.step("选择就绪状态并查询"):
            self.node_manage_page.assert_no_alert(retries=6)
            self.node_manage_page.select_status(SandboxNodeStatus.READY)
            self.node_manage_page.btn_search.click()
            self.page.wait_for_timeout(UITimeout.QUERY)

        with AllureHelper.step("验证表格数据展示"):
            expect(self.node_manage_page.table_data).to_be_visible()
            self.node_manage_page.assert_no_alert()

        self.node_manage_page.take_screenshot("节点管理-就绪状态筛选", True)

    @allure.story("同步节点")
    @allure.title("同步节点信息抽屉打开与关闭")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sync_node_drawer(self):
        """验证同步节点信息抽屉能正常打开和关闭"""
        with AllureHelper.step("打开同步节点抽屉"):
            self.node_manage_page.assert_no_alert(retries=6)
            self.node_manage_page.sync_node_info()

        with AllureHelper.step("验证同步抽屉已打开"):
            expect(self.node_manage_page.drawer_sync).to_be_visible()
            expect(self.node_manage_page.btn_sync_cancel).to_be_visible()
            expect(self.node_manage_page.btn_sync_confirm).to_be_visible()
            self.node_manage_page.take_screenshot("节点管理-同步抽屉", True)

        with AllureHelper.step("关闭同步抽屉"):
            self.node_manage_page.close_sync_drawer()
            self.node_manage_page.assert_no_alert()

    @allure.story("节点详情")
    @allure.title("查看首个节点的详情抽屉")
    @allure.severity(allure.severity_level.NORMAL)
    def test_node_detail_drawer(self):
        """点击第一行详情按钮，验证详情抽屉打开"""
        with AllureHelper.step("点击首行详情按钮"):
            self.node_manage_page.assert_no_alert(retries=6)
            self.node_manage_page.click_detail_button(row_index=0)

        with AllureHelper.step("验证详情抽屉已打开"):
            expect(self.node_manage_page.drawer_node_detail).to_be_visible()
            self.node_manage_page.take_screenshot("节点管理-节点详情", True)

        with AllureHelper.step("关闭详情抽屉"):
            self.node_manage_page.close_detail_drawer()
            self.node_manage_page.assert_no_alert()

    @allure.story("刷新")
    @allure.title("点击刷新按钮不报错")
    @allure.severity(allure.severity_level.MINOR)
    def test_refresh(self):
        """点击刷新按钮，验证页面无报错"""
        with AllureHelper.step("点击刷新"):
            self.node_manage_page.assert_no_alert(retries=6)
            self.node_manage_page.btn_refresh.click()
            self.page.wait_for_timeout(UITimeout.QUERY)

        with AllureHelper.step("验证无报错"):
            self.node_manage_page.assert_no_alert()
            self.node_manage_page.take_screenshot("节点管理-刷新", True)


@pytest.mark.ui
@allure.epic("Sandbox UI自动化测试")
@allure.feature("构建记录")
class TestBuildRecord:
    """模板管理 - 构建记录 功能测试"""

    @pytest.fixture(autouse=True)
    def setup(self, login_context):
        self.context, self.page = login_context
        self.home_page = HomePage(self.page)
        self.home_page.switch_top_menu(SystemMenu.SANDBOX)
        self.home_page.expand_sidebar()
        self.build_record_page = BuildRecordPage(self.page)

        # 导航到构建记录页面
        self.home_page.open_menu(SandboxMenu.TEMPLATE_MANAGE, SandboxMenu.BUILD_RECORD)
        self.home_page.wait_frame_ready()

        yield
        self.home_page.wait_alert_hidden()

    @allure.story("页面元素验证")
    @allure.title("构建记录页面元素完整性检查")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_page_elements(self):
        """验证构建记录页面所有核心元素可见"""
        with AllureHelper.step("验证搜索区元素"):
            self.build_record_page.assert_no_alert(retries=6)
            expect(self.build_record_page.input_search).to_be_visible()
            expect(self.build_record_page.dropdown_build_status).to_be_visible()
            expect(self.build_record_page.btn_search).to_be_visible()

        with AllureHelper.step("验证表格表头"):
            expect(self.build_record_page.col_template_id).to_be_visible()
            expect(self.build_record_page.col_template).to_be_visible()
            expect(self.build_record_page.col_status).to_be_visible()
            expect(self.build_record_page.col_start_time).to_be_visible()

        with AllureHelper.step("验证分页"):
            expect(self.build_record_page.btn_next_page).to_be_visible()

        self.build_record_page.assert_no_alert()
        self.build_record_page.take_screenshot("构建记录-元素完整性", True)

    @allure.story("状态筛选")
    @allure.title("按成功状态筛选构建记录")
    @allure.severity(allure.severity_level.NORMAL)
    def test_filter_by_success(self):
        """选择'成功'状态查询构建记录"""
        with AllureHelper.step("选择成功状态"):
            self.build_record_page.assert_no_alert(retries=6)
            self.build_record_page.chose_build_status(BuildRecordStatus.SUCCESS)

        with AllureHelper.step("点击查询"):
            self.build_record_page.btn_search.click()
            self.page.wait_for_timeout(UITimeout.QUERY)

        with AllureHelper.step("验证结果无报错"):
            self.build_record_page.assert_no_alert()
            expect(self.build_record_page.table_data).to_be_visible()

        self.build_record_page.take_screenshot("构建记录-成功筛选", True)

    @allure.story("分页")
    @allure.title("切换每页显示20条")
    @allure.severity(allure.severity_level.MINOR)
    def test_change_page_size(self):
        """切换分页大小为20条/页"""
        with AllureHelper.step("切换为20条/页"):
            self.build_record_page.assert_no_alert(retries=6)
            self.build_record_page.change_page_size(PageSize.PAGE_20)

        with AllureHelper.step("验证无报错"):
            self.build_record_page.assert_no_alert()
            expect(self.build_record_page.table_data).to_be_visible()

        self.build_record_page.take_screenshot("构建记录-20条每页", True)


@pytest.mark.ui
@allure.epic("Sandbox UI自动化测试")
@allure.feature("SDK使用示例")
class TestSdkExample:
    """SDK使用示例 功能测试"""

    @pytest.fixture(autouse=True)
    def setup(self, login_context):
        self.context, self.page = login_context
        self.home_page = HomePage(self.page)
        self.home_page.switch_top_menu(SystemMenu.SANDBOX)
        self.home_page.expand_sidebar()
        self.sdk_example_page = SdkExamplePage(self.page)

        # 导航到SDK使用示例页面
        self.home_page.open_menu(SandboxMenu.SDK_EXAMPLE, SandboxMenu.SDK_EXAMPLE, second_level_index=1)
        self.home_page.wait_frame_ready()

        yield
        self.home_page.wait_alert_hidden()

    @allure.story("页面元素验证")
    @allure.title("SDK使用示例页面完整性检查")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_page_elements(self):
        """验证页面标题、按钮、章节、表格均可见"""
        with AllureHelper.step("验证页头"):
            self.sdk_example_page.assert_no_alert(retries=6)
            expect(self.sdk_example_page.title_sdk_example).to_be_visible()
            expect(self.sdk_example_page.btn_download_pdf).to_be_visible()

        with AllureHelper.step("验证三个章节标题"):
            expect(self.sdk_example_page.title_sdk_install).to_be_visible()
            expect(self.sdk_example_page.title_env_config).to_be_visible()
            expect(self.sdk_example_page.title_usage_example).to_be_visible()

        with AllureHelper.step("验证代码块存在"):
            expect(self.sdk_example_page.code_block_pypi).to_be_visible()
            expect(self.sdk_example_page.code_block_install).to_be_visible()
            expect(self.sdk_example_page.code_block_env).to_be_visible()

        with AllureHelper.step("验证使用示例表格"):
            expect(self.sdk_example_page.table_example).to_be_visible()
            expect(self.sdk_example_page.col_scenario).to_be_visible()
            expect(self.sdk_example_page.col_template_id).to_be_visible()

        self.sdk_example_page.assert_no_alert()
        self.sdk_example_page.take_screenshot("SDK示例-元素完整性", True)

    @allure.story("查看示例")
    @allure.title("查看代码沙箱示例弹窗")
    @allure.severity(allure.severity_level.NORMAL)
    def test_view_code_sandbox_example(self):
        """点击代码沙箱的查看示例，验证弹窗弹出"""
        with AllureHelper.step("点击查看示例"):
            self.sdk_example_page.assert_no_alert(retries=6)
            self.sdk_example_page.click_view_example(SandboxType.CODE)

        with AllureHelper.step("验证示例代码弹窗"):
            expect(self.sdk_example_page.dialog_code).to_be_visible()
            self.sdk_example_page.take_screenshot("SDK示例-代码沙箱弹窗", True)
            self.sdk_example_page.btn_close_dialog.click()

    @allure.story("查看示例")
    @allure.title("查看桌面沙箱示例弹窗")
    @allure.severity(allure.severity_level.NORMAL)
    def test_view_desktop_sandbox_example(self):
        """点击桌面沙箱的查看示例"""
        with AllureHelper.step("点击查看示例"):
            self.sdk_example_page.assert_no_alert(retries=6)
            self.sdk_example_page.click_view_example(SandboxType.DESKTOP)

        with AllureHelper.step("验证示例代码弹窗"):
            expect(self.sdk_example_page.dialog_desktop).to_be_visible()
            self.sdk_example_page.take_screenshot("SDK示例-桌面沙箱弹窗", True)
            self.sdk_example_page.btn_close_dialog.click()


@pytest.mark.ui
@allure.epic("Sandbox UI自动化测试")
@allure.feature("沙箱管理")
class TestSandboxManage:
    """沙箱管理 功能测试"""

    @pytest.fixture(autouse=True)
    def setup(self, login_context):
        self.context, self.page = login_context
        self.home_page = HomePage(self.page)
        self.home_page.switch_top_menu(SystemMenu.SANDBOX)
        self.home_page.expand_sidebar()
        self.sandbox_manage_page = SandboxManagePage(self.page)

        # 显式导航到沙箱管理页面
        self.home_page.open_menu(SandboxMenu.SANDBOX_MANAGE, SandboxMenu.SANDBOX_MANAGE, second_level_index=1)
        self.sandbox_manage_page.wait_frame_ready()

        yield
        self.home_page.wait_alert_hidden()

    @allure.story("Tab切换")
    @allure.title("切换到历史沙箱tab")
    @allure.severity(allure.severity_level.NORMAL)
    def test_switch_to_history_tab(self):
        """切换到历史沙箱tab，验证tab状态和页面无报错"""
        with AllureHelper.step("切换到历史沙箱"):
            self.sandbox_manage_page.assert_no_alert(retries=6)
            self.sandbox_manage_page.switch_to_history()

        with AllureHelper.step("验证历史沙箱内容"):
            self.sandbox_manage_page.assert_no_alert()
            self.sandbox_manage_page.take_screenshot("沙箱管理-历史沙箱tab", True)

    @allure.story("Tab切换")
    @allure.title("切换回存活沙箱tab")
    @allure.severity(allure.severity_level.NORMAL)
    def test_switch_to_alive_tab(self):
        """先切换到历史tab，再切回存活tab"""
        with AllureHelper.step("先切换到历史沙箱"):
            self.sandbox_manage_page.assert_no_alert(retries=6)
            self.sandbox_manage_page.switch_to_history()

        with AllureHelper.step("切回存活沙箱"):
            self.sandbox_manage_page.switch_to_alive()
            expect(self.sandbox_manage_page.input_tenant_alive).to_be_visible()
            self.sandbox_manage_page.assert_no_alert()

        self.sandbox_manage_page.take_screenshot("沙箱管理-存活沙箱tab", True)


@pytest.mark.ui
@allure.epic("Sandbox UI自动化测试")
@allure.feature("镜像管理")
class TestImageLibrary:
    """镜像管理 - 镜像库管理 功能测试"""

    @pytest.fixture(autouse=True)
    def setup(self, login_context):
        self.context, self.page = login_context
        self.home_page = HomePage(self.page)
        self.home_page.switch_top_menu(SystemMenu.SANDBOX)
        self.home_page.expand_sidebar()
        self.image_library_page = ImageLibraryPage(self.page)

        # 导航到镜像管理页面
        self.home_page.open_menu(SandboxMenu.IMAGE_MANAGE, SandboxMenu.IMAGE_LIBRARY_MANAGE)
        self.home_page.wait_frame_ready()

        yield
        self.home_page.wait_alert_hidden()

    @allure.story("Tab切换")
    @allure.title("切换到自定义镜像tab")
    @allure.severity(allure.severity_level.NORMAL)
    def test_switch_to_custom_image(self):
        """切换到自定义镜像tab"""
        with AllureHelper.step("切换tab"):
            self.image_library_page.assert_no_alert(retries=6)
            self.image_library_page.switch_to_custom_image()

        with AllureHelper.step("验证无报错"):
            self.image_library_page.assert_no_alert()
            self.image_library_page.take_screenshot("镜像管理-自定义镜像", True)

    @allure.story("Tab切换")
    @allure.title("切换回系统镜像tab")
    @allure.severity(allure.severity_level.NORMAL)
    def test_switch_to_system_image(self):
        """先切到自定义，再切回系统镜像"""
        with AllureHelper.step("切换到自定义镜像"):
            self.image_library_page.assert_no_alert(retries=6)
            self.image_library_page.switch_to_custom_image()

        with AllureHelper.step("切回系统镜像"):
            self.image_library_page.switch_to_system_image()
            self.image_library_page.assert_no_alert()

        self.image_library_page.take_screenshot("镜像管理-系统镜像", True)

    @allure.story("搜索")
    @allure.title("搜索镜像名称")
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_image(self):
        """输入镜像名称关键词搜索"""
        with AllureHelper.step("搜索镜像"):
            self.image_library_page.assert_no_alert(retries=6)
            self.image_library_page.search_image("base")

        with AllureHelper.step("验证搜索无报错"):
            self.image_library_page.assert_no_alert()
            expect(self.image_library_page.table_body).to_be_visible()

        self.image_library_page.take_screenshot("镜像管理-搜索base", True)

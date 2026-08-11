import allure
import pytest
from playwright.sync_api import expect

from base.ui.pages.sandbox.build_record import BuildRecordPage
from base.ui.pages.sandbox.home import HomePage
from base.ui.pages.sandbox.image_library import ImageLibraryPage
from base.ui.pages.sandbox.node_manage import NodeManagePage
from base.ui.pages.sandbox.sandbox_manage import SandboxManagePage
from base.ui.pages.sandbox.sdk_example import SdkExamplePage
from base.ui.pages.sandbox.template_manage import TemplateManagePage
from core import get_logger
from core.constants import PlaywrightLoadState
from core.constants.bussiness import SandboxMenu, SystemMenu
from core.reporting import AllureHelper

logger = get_logger(__name__)


@pytest.mark.ui
@allure.epic("Sandbox UI自动化测试")
@allure.feature("Sandbox 平台页面走查")
@allure.story("沙箱管理")
class TestSandboxPage:

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, login_context):
        self.context, self.page = login_context
        self.home_page = HomePage(self.page)

        self.home_page.switch_top_menu(SystemMenu.SANDBOX)
        # 切换顶部菜单后侧边栏可能折叠，重新展开
        self.home_page.expand_sidebar()

        self.sandbox_manage_page = SandboxManagePage(self.page)
        self.image_library_page = ImageLibraryPage(self.page)
        self.template_manage_page = TemplateManagePage(self.page)
        self.node_manage_page = NodeManagePage(self.page)
        self.build_record_page = BuildRecordPage(self.page)
        self.sdk_example_page = SdkExamplePage(self.page)

        yield
        logger.info("------------单条测试用执行结束--------------")
        self.home_page.wait_alert_hidden()

    @pytest.mark.dependency()
    @allure.title("沙箱管理 - 沙箱管理")
    @allure.description("""检查页面元素（iframe内）：存活沙箱tab、历史沙箱tab、租户名称搜索框、查询按钮""")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sandbox_manage(self):
        with AllureHelper.step("沙箱管理页面检查"):
            logger.info("进入沙箱管理页面")
            self.sandbox_manage_page.wait_for_load_state(state=PlaywrightLoadState.LOAD)
            self.sandbox_manage_page.wait_frame_ready()

            logger.info("断言：页面是否有报错")
            self.sandbox_manage_page.assert_no_alert(retries=6)

            logger.info("断言：检查存活沙箱tab")
            expect(self.sandbox_manage_page.tab_alive).to_be_visible()

            logger.info("断言：检查历史沙箱tab")
            expect(self.sandbox_manage_page.tab_history).to_be_visible()

            logger.info("断言：检查租户名称搜索框")
            expect(self.sandbox_manage_page.input_tenant_alive).to_be_visible()

            logger.info("断言：检查查询按钮")
            expect(self.sandbox_manage_page.btn_search_alive).to_be_visible()

            self.sandbox_manage_page.assert_no_alert()
            self.sandbox_manage_page.take_screenshot("沙箱-沙箱管理-沙箱管理", True)

    @pytest.mark.dependency()
    @allure.title("沙箱集群 - 节点管理")
    @allure.description("""检查页面元素（iframe内）：节点ID搜索框、全部状态下拉、集群选择下拉、查询按钮、刷新按钮""")
    @allure.severity(allure.severity_level.NORMAL)
    def test_node_manage(self):
        with AllureHelper.step("沙箱管理页面检查"):
            logger.info("进入节点管理页面")
            self.home_page.open_menu(SandboxMenu.SANDBOX_CLUSTER, SandboxMenu.NODE_MANAGE)
            self.home_page.wait_frame_ready()

            logger.info("断言：页面是否有报错")
            self.node_manage_page.assert_no_alert(retries=6)

            logger.info("断言：检查节点ID搜索框")
            expect(self.node_manage_page.input_node_id).to_be_visible()

            logger.info("断言：检查查询按钮")
            expect(self.node_manage_page.btn_search).to_be_visible()

            logger.info("断言：检查刷新按钮")
            expect(self.node_manage_page.btn_refresh).to_be_visible()

            self.node_manage_page.assert_no_alert()
            self.node_manage_page.take_screenshot("沙箱-沙箱集群-节点管理", True)

    @pytest.mark.dependency()
    @allure.title("镜像管理 - 镜像库管理")
    @allure.description("""检查页面元素（iframe内）：系统镜像tab、自定义镜像tab、镜像名称搜索框、查询按钮""")
    @allure.severity(allure.severity_level.NORMAL)
    def test_image_repo(self):
        with AllureHelper.step("页面检查"):
            logger.info("进入【镜像管理 - 镜像库管理】页面")
            self.home_page.open_menu(SandboxMenu.IMAGE_MANAGE, SandboxMenu.IMAGE_LIBRARY_MANAGE)
            self.home_page.wait_frame_ready()

            logger.info("断言：页面是否有报错")
            self.image_library_page.assert_no_alert(retries=6)

            logger.info("断言：检查系统镜像tab")
            expect(self.image_library_page.tab_system_image).to_be_visible()

            logger.info("断言：检查自定义镜像tab")
            expect(self.image_library_page.tab_custom_image).to_be_visible()

            logger.info("断言：检查镜像名称搜索框")
            expect(self.image_library_page.input_search).to_be_visible()

            logger.info("断言：检查查询按钮")
            expect(self.image_library_page.btn_search).to_be_visible()

            self.image_library_page.assert_no_alert()
            self.home_page.take_screenshot("沙箱-镜像管理-镜像库管理", True)

    @pytest.mark.dependency()
    @allure.title("模板管理 - 模板管理")
    @allure.description("""检查页面元素（iframe内）：系统模板tab、自定义模板tab、模板名称搜索框、查询按钮""")
    @allure.severity(allure.severity_level.NORMAL)
    def test_template_manage(self):
        with allure.step("页面检查"):
            logger.info("进入【模板管理 - 模板管理】页面")
            self.home_page.open_menu(SandboxMenu.TEMPLATE_MANAGE, SandboxMenu.TEMPLATE_MANAGE, second_level_index=1)
            self.home_page.wait_frame_ready()

            logger.info("断言：页面是否有报错")
            self.template_manage_page.assert_no_alert(retries=6)

            logger.info("断言：检查系统模板tab")
            expect(self.template_manage_page.tab_system).to_be_visible()

            logger.info("断言：检查自定义模板tab")
            expect(self.template_manage_page.tab_custom).to_be_visible()

            logger.info("断言：检查模板名称/ID搜索框")
            expect(self.template_manage_page.input_search).to_be_visible()

            logger.info("断言：检查查询按钮")
            expect(self.template_manage_page.btn_search).to_be_visible()

            self.template_manage_page.assert_no_alert()
            self.home_page.take_screenshot("沙箱-模板管理-模板管理", True)

    @pytest.mark.dependency()
    @allure.title("模板管理 - 构建记录")
    @allure.description("""检查页面元素（iframe内）：构建状态下拉、模板名称或ID搜索框、查询按钮、构建记录列表表格""")
    @allure.severity(allure.severity_level.NORMAL)
    def test_build_record(self) -> None:
        with allure.step("页面检查"):
            logger.info("进入【模板管理 - 构建记录】页面")
            self.home_page.open_menu(SandboxMenu.TEMPLATE_MANAGE, SandboxMenu.BUILD_RECORD)
            self.home_page.wait_frame_ready()

            logger.info("断言：页面是否有报错")
            self.build_record_page.assert_no_alert(retries=6)

            logger.info("断言：检查模板名称或ID搜索框")
            expect(self.build_record_page.input_search).to_be_visible()

            logger.info("断言：检查查询按钮")
            expect(self.build_record_page.btn_search).to_be_visible()

            logger.info("断言：检查构建记录列表表格")
            expect(self.build_record_page.table_data).to_be_visible()

            self.build_record_page.assert_no_alert()
            self.build_record_page.take_screenshot("沙箱-模板管理-构建记录", True)

    @allure.title("SDK使用示例")
    @allure.description("""检查页面元素（iframe内）：SDK使用示例标题、下载SDK使用pdf按钮、SDK安装章节标题、使用示例表格""")
    def test_sdk_example(self) -> None:
        with allure.step("页面检查"):
            logger.info("进入【SDK使用示例】页面")
            self.home_page.open_menu(SandboxMenu.SDK_EXAMPLE, SandboxMenu.SDK_EXAMPLE, second_level_index=1)
            self.home_page.wait_frame_ready()

            logger.info("断言：页面是否有报错")
            self.sdk_example_page.assert_no_alert(retries=6)

            logger.info("断言：检查SDK使用示例标题")
            expect(self.sdk_example_page.title_sdk_example).to_be_visible()

            logger.info("断言：检查下载SDK使用pdf按钮")
            expect(self.sdk_example_page.btn_download_pdf).to_be_visible()

            logger.info("断言：检查SDK安装章节标题")
            expect(self.sdk_example_page.title_sdk_install).to_be_visible()

            logger.info("断言：检查使用示例表格")
            expect(self.sdk_example_page.table_example).to_be_visible()

            self.sdk_example_page.assert_no_alert()
            self.sdk_example_page.take_screenshot("沙箱-SDK使用示例-SDK使用示例", True)

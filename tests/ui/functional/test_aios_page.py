"""
AIOS 页面元素检查测试

基于 Page Object 校验 AIOS 各功能页面的核心元素可见性，覆盖：
- 消费者应用：搜索区（所属租户下拉、应用名称搜索框、查询/刷新缓存/新增按钮）与数据表格
- 消费者应用详情：应用信息头部（AppSecret）、已订阅API搜索区、API订阅/取消订阅按钮
- 角色管理：角色名称搜索框、查询/新增按钮、树形表格
- 租户管理：租户名称搜索框、查询/用户关联按钮、数据表格
- 用户管理：租户/来源下拉、关键字搜索框、查询/新增按钮、数据表格与分页

说明：
- AIOS 页面渲染在主文档中（非 iframe），直接使用 ``page`` 定位，无需等待 iframe；
- 消费者应用详情页依赖列表数据，无数据时跳过详情检查。
"""
import allure
import pytest
from playwright.sync_api import expect

from base.ui.pages.aios.consumer_app import ConsumerAppPage
from base.ui.pages.aios.consumer_app_detail import ConsumerAppDetailPage
from base.ui.pages.aios.role_manage import RoleManagePage
from base.ui.pages.aios.tenant_manage import TenantManagePage
from base.ui.pages.aios.user_manage import UserManagePage
from base.ui.pages.home import HomePage
from core import get_logger
from core.constants.bussiness import AiosMenu, SystemMenu
from core.reporting import AllureHelper

logger = get_logger(__name__)


@pytest.mark.ui
@allure.epic("沙箱UI自动化测试")
@allure.feature("页面检查")
class TestAiosPage:
    """AIOS 各功能页面元素完整性检查（主文档渲染，非 iframe）。"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, login_context):
        self.context, self.page = login_context
        self.home_page = HomePage(self.page)

        self.home_page.switch_top_menu(SystemMenu.INDEX)
        # 切换顶部菜单后侧边栏可能折叠，重新展开
        self.home_page.expand_sidebar()

        self.consumer_app_page = ConsumerAppPage(self.page)
        self.consumer_app_detail_page = ConsumerAppDetailPage(self.page)
        self.role_manage_page = RoleManagePage(self.page)
        self.tenant_manage_page = TenantManagePage(self.page)
        self.user_manage_page = UserManagePage(self.page)

        yield
        logger.info("------------单条测试用执行结束--------------")
        self.home_page.wait_alert_hidden()

    # ==================== 内部辅助 ====================

    def _first_app_name(self) -> str:
        """获取消费者应用列表第一行的应用名称（数据行表为第 2 个 table）。"""
        data_table = self.page.get_by_role("table").nth(1)
        return data_table.get_by_role("row").first.get_by_role("cell").nth(0).inner_text().strip()

    # ==================== 消费者应用 ====================

    @allure.story("消费者应用")
    @allure.title("检查消费者应用页面元素")
    @allure.description("""检查搜索区（所属租户下拉、应用名称搜索框、查询/刷新缓存/新增按钮）与数据表格""")
    @allure.severity(allure.severity_level.NORMAL)
    def test_consumer_app(self):
        with AllureHelper.step("进入消费者应用页面"):
            logger.info("进入【AIOS - 消费者应用】页面")
            self.home_page.open_menu(AiosMenu.CONSUMER_APP)

        with AllureHelper.step("断言：页面是否有报错"):
            self.consumer_app_page.assert_no_alert(retries=6)

        with AllureHelper.step("断言：检查所属租户下拉"):
            expect(self.consumer_app_page.dropdown_tenant).to_be_visible()

        with AllureHelper.step("断言：检查应用名称搜索框"):
            expect(self.consumer_app_page.input_app_name).to_be_visible()

        with AllureHelper.step("断言：检查查询按钮"):
            expect(self.consumer_app_page.btn_search).to_be_visible()

        with AllureHelper.step("断言：检查刷新缓存按钮"):
            expect(self.consumer_app_page.btn_refresh_cache).to_be_visible()

        with AllureHelper.step("断言：检查新增按钮"):
            expect(self.consumer_app_page.btn_add).to_be_visible()

        with AllureHelper.step("断言：检查数据表格"):
            expect(self.consumer_app_page.table).to_be_visible()

        self.consumer_app_page.assert_no_alert()
        self.consumer_app_page.take_screenshot("AIOS-消费者应用-页面检查", True)

    @allure.story("消费者应用详情")
    @allure.title("检查消费者应用详情页面元素")
    @allure.description("""进入详情页检查应用信息头部（AppSecret）、已订阅API搜索区、API订阅/取消订阅按钮""")
    @allure.severity(allure.severity_level.NORMAL)
    def test_consumer_app_detail(self):
        with AllureHelper.step("进入消费者应用列表并搜索"):
            logger.info("进入【AIOS - 消费者应用】页面")
            self.home_page.open_menu(AiosMenu.CONSUMER_APP)
            self.consumer_app_page.search_by_name("test")

        with AllureHelper.step("检查是否存在应用数据"):
            if self.consumer_app_page.get_row_count() == 0:
                pytest.skip("当前环境无消费者应用数据，跳过详情页检查")

        with AllureHelper.step("点击第一行查看进入详情页"):
            self.consumer_app_page.click_row_view(self._first_app_name())

        with AllureHelper.step("断言：页面是否有报错"):
            self.consumer_app_detail_page.assert_no_alert(retries=6)

        with AllureHelper.step("断言：检查 AppSecret 信息"):
            expect(self.consumer_app_detail_page.text_app_secret).to_be_visible()

        with AllureHelper.step("断言：检查API名称搜索框"):
            expect(self.consumer_app_detail_page.input_api_name).to_be_visible()

        with AllureHelper.step("断言：检查URL关键字搜索框"):
            expect(self.consumer_app_detail_page.input_url).to_be_visible()

        with AllureHelper.step("断言：检查所属产品下拉"):
            expect(self.consumer_app_detail_page.dropdown_product).to_be_visible()

        with AllureHelper.step("断言：检查查询按钮"):
            expect(self.consumer_app_detail_page.btn_search_api).to_be_visible()

        with AllureHelper.step("断言：检查API订阅按钮"):
            expect(self.consumer_app_detail_page.btn_subscribe).to_be_visible()

        with AllureHelper.step("断言：检查取消订阅按钮"):
            expect(self.consumer_app_detail_page.btn_unsubscribe).to_be_visible()

        with AllureHelper.step("断言：检查已订阅API表格"):
            expect(self.consumer_app_detail_page.table_subscribed).to_be_visible()

        self.consumer_app_detail_page.assert_no_alert()
        self.consumer_app_detail_page.take_screenshot("AIOS-消费者应用-详情页检查", True)

        with AllureHelper.step("通过面包屑返回列表页"):
            self.consumer_app_detail_page.navigate_back()
            expect(self.consumer_app_page.table).to_be_visible()

    # ==================== 角色管理 ====================

    @allure.story("角色管理")
    @allure.title("检查角色管理页面元素")
    @allure.description("""检查角色名称搜索框、查询/新增按钮与角色树形表格""")
    @allure.severity(allure.severity_level.NORMAL)
    def test_role_manage(self):
        with AllureHelper.step("进入角色管理页面"):
            logger.info("进入【AIOS - 角色管理】页面")
            self.home_page.open_menu(AiosMenu.PERMISSION_MANAGE, AiosMenu.ROLE_MANAGE)

        with AllureHelper.step("断言：页面是否有报错"):
            self.role_manage_page.assert_no_alert(retries=6)

        with AllureHelper.step("断言：检查角色名称搜索框"):
            expect(self.role_manage_page.filter_role).to_be_visible()

        with AllureHelper.step("断言：检查查询按钮"):
            expect(self.role_manage_page.btn_search).to_be_visible()

        with AllureHelper.step("断言：检查新增按钮"):
            expect(self.role_manage_page.btn_add).to_be_visible()

        with AllureHelper.step("断言：检查角色列表表格"):
            expect(self.role_manage_page.table_body_rows.first).to_be_visible()

        self.role_manage_page.assert_no_alert()
        self.role_manage_page.take_screenshot("AIOS-角色管理-页面检查", True)

    # ==================== 租户管理 ====================

    @allure.story("租户管理")
    @allure.title("检查租户管理页面元素")
    @allure.description("""检查租户名称搜索框、查询/用户关联按钮与租户树形表格""")
    @allure.severity(allure.severity_level.NORMAL)
    def test_tenant_manage(self):
        with AllureHelper.step("进入租户管理页面"):
            logger.info("进入【AIOS - 租户管理】页面")
            self.home_page.open_menu(AiosMenu.PERMISSION_MANAGE, AiosMenu.TENANT_MANAGE)

        with AllureHelper.step("断言：页面是否有报错"):
            self.tenant_manage_page.assert_no_alert(retries=6)

        with AllureHelper.step("断言：检查租户名称搜索框"):
            expect(self.tenant_manage_page.filter_tenant).to_be_visible()

        with AllureHelper.step("断言：检查查询按钮"):
            expect(self.tenant_manage_page.btn_search).to_be_visible()

        with AllureHelper.step("断言：检查用户关联按钮"):
            expect(self.tenant_manage_page.btn_user_relation).to_be_visible()

        with AllureHelper.step("断言：检查租户列表表格"):
            expect(self.tenant_manage_page.table).to_be_visible()

        self.tenant_manage_page.assert_no_alert()
        self.tenant_manage_page.take_screenshot("AIOS-租户管理-页面检查", True)

    # ==================== 用户管理 ====================

    @allure.story("用户管理")
    @allure.title("检查用户管理页面元素")
    @allure.description("""检查租户/来源下拉、关键字搜索框、查询/新增按钮、数据表格与分页""")
    @allure.severity(allure.severity_level.NORMAL)
    def test_user_manage(self):
        with AllureHelper.step("进入用户管理页面"):
            logger.info("进入【AIOS - 用户管理】页面")
            self.home_page.open_menu(AiosMenu.PERMISSION_MANAGE, AiosMenu.USER_MANAGE)

        with AllureHelper.step("断言：页面是否有报错"):
            self.user_manage_page.assert_no_alert(retries=6)

        with AllureHelper.step("断言：检查关键字搜索框"):
            expect(self.user_manage_page.input_search).to_be_visible()

        with AllureHelper.step("断言：检查查询按钮"):
            expect(self.user_manage_page.btn_search).to_be_visible()

        with AllureHelper.step("断言：检查新增按钮"):
            expect(self.user_manage_page.btn_add).to_be_visible()

        with AllureHelper.step("断言：检查数据表格"):
            expect(self.user_manage_page.table_body_rows.first).to_be_visible()

        with AllureHelper.step("断言：检查分页组件"):
            expect(self.user_manage_page.pagination).to_be_visible()

        self.user_manage_page.assert_no_alert()
        self.user_manage_page.take_screenshot("AIOS-用户管理-页面检查", True)

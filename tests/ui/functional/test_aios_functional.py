"""
AIOS UI 功能测试

基于 Page Object 编写的功能级测试用例，覆盖：
- 消费者应用：关键字搜索、新增弹窗开合、刷新缓存
- 消费者应用详情：API订阅弹窗开合、取消订阅弹窗开合、面包屑返回列表
- 角色管理：关键字搜索、新增角色弹窗开合、列表展开/收起
- 租户管理：关键字搜索、清空搜索、用户关联弹窗开合
- 用户管理：关键字搜索、新增用户弹窗开合、分页信息

设计原则：
- 用例尽量不依赖具体业务数据，弹窗类用例只做「打开-验证-关闭」，不提交数据；
- 依赖列表数据的用例（如详情页）在无数据时 ``skip``，避免污染真实环境。
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
from core.constants import UITimeout
from core.constants.bussiness import AiosMenu, SystemMenu
from core.reporting import AllureHelper

logger = get_logger(__name__)


@pytest.mark.ui
@allure.epic("沙箱UI自动化测试")
@allure.feature("消费者应用")
class TestConsumerAppFunctional:
    """消费者应用 功能测试"""

    @pytest.fixture(autouse=True)
    def setup(self, login_context):
        self.context, self.page = login_context
        self.home_page = HomePage(self.page)
        self.home_page.switch_top_menu(SystemMenu.INDEX)
        self.home_page.expand_sidebar()
        self.page.wait_for_timeout(UITimeout.ANIMATION)
        self.consumer_app_page = ConsumerAppPage(self.page)

        # 导航到消费者应用页面
        self.home_page.open_menu(AiosMenu.CONSUMER_APP)

        yield
        self.home_page.wait_alert_hidden()

    @allure.story("搜索")
    @allure.title("按应用名称关键字搜索")
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_app_by_name(self):
        """输入应用名称关键字搜索，验证页面无报错"""
        with AllureHelper.step("搜索应用名称关键字"):
            self.consumer_app_page.assert_no_alert(retries=6)
            self.consumer_app_page.search_by_name("a")

        with AllureHelper.step("验证查询无报错"):
            self.consumer_app_page.assert_no_alert()
            expect(self.consumer_app_page.table).to_be_visible()

        self.consumer_app_page.take_screenshot("AIOS-消费者应用-关键字搜索", True)

    @allure.story("新增")
    @allure.title("新增消费者应用弹窗打开与取消")
    @allure.severity(allure.severity_level.NORMAL)
    def test_add_dialog_open_and_cancel(self):
        """打开新增消费者应用弹窗，填写表单后取消"""
        with AllureHelper.step("打开新增弹窗"):
            self.consumer_app_page.assert_no_alert(retries=6)
            self.consumer_app_page.click_add()

        with AllureHelper.step("验证弹窗已打开"):
            expect(self.consumer_app_page.dialog_add).to_be_visible()
            expect(self.consumer_app_page.input_add_name).to_be_visible()
            expect(self.consumer_app_page.input_add_desc).to_be_visible()
            self.consumer_app_page.take_screenshot("AIOS-消费者应用-新增弹窗", True)

        with AllureHelper.step("填写表单并取消"):
            self.consumer_app_page.fill_add_form("自动化临时应用", "自动化测试-取消不提交")
            self.consumer_app_page.cancel_add()
            expect(self.consumer_app_page.dialog_add).to_be_hidden()

        self.consumer_app_page.assert_no_alert()

    @allure.story("缓存刷新")
    @allure.title("点击刷新缓存按钮")
    @allure.severity(allure.severity_level.MINOR)
    def test_refresh_cache(self):
        """点击刷新缓存按钮，验证页面无报错"""
        with AllureHelper.step("点击刷新缓存"):
            self.consumer_app_page.assert_no_alert(retries=6)
            self.consumer_app_page.btn_refresh_cache.click()
            self.page.wait_for_timeout(UITimeout.QUERY)

        with AllureHelper.step("验证无报错"):
            self.consumer_app_page.assert_no_alert()
            self.consumer_app_page.take_screenshot("AIOS-消费者应用-刷新缓存", True)


@pytest.mark.ui
@allure.epic("沙箱UI自动化测试")
@allure.feature("消费者应用详情")
class TestConsumerAppDetailFunctional:
    """消费者应用详情 功能测试（依赖列表数据，无数据时跳过）"""

    @pytest.fixture(autouse=True)
    def setup(self, login_context):
        self.context, self.page = login_context
        self.home_page = HomePage(self.page)
        self.home_page.switch_top_menu(SystemMenu.INDEX)
        self.home_page.expand_sidebar()
        self.page.wait_for_timeout(UITimeout.ANIMATION)
        self.consumer_app_page = ConsumerAppPage(self.page)
        self.detail_page = ConsumerAppDetailPage(self.page)

        # 进入消费者应用列表，搜索后进入第一个应用详情页
        self.home_page.open_menu(AiosMenu.CONSUMER_APP)
        self.consumer_app_page.search_by_name("a")
        if self.consumer_app_page.get_row_count() == 0:
            pytest.skip("当前环境无消费者应用数据，跳过详情功能测试")

        data_table = self.page.get_by_role("table").nth(1)
        first_app_name = data_table.get_by_role("row").first.get_by_role("cell").nth(0).inner_text().strip()
        self.consumer_app_page.click_row_view(first_app_name)

        yield
        self.home_page.wait_alert_hidden()

    @allure.story("API订阅")
    @allure.title("API订阅弹窗打开与取消")
    @allure.severity(allure.severity_level.NORMAL)
    def test_subscribe_dialog_open_and_cancel(self):
        """点击API订阅打开弹窗，验证弹窗元素后取消"""
        with AllureHelper.step("打开API订阅弹窗"):
            self.detail_page.assert_no_alert(retries=6)
            self.detail_page.click_subscribe()

        with AllureHelper.step("验证弹窗已打开"):
            expect(self.detail_page.dialog_subscribe).to_be_visible()
            expect(self.detail_page.input_subscribe_search).to_be_visible()
            self.detail_page.take_screenshot("AIOS-消费者应用详情-API订阅弹窗", True)

        with AllureHelper.step("取消订阅"):
            self.detail_page.cancel_subscribe()
            expect(self.detail_page.dialog_subscribe).to_be_hidden()

        self.detail_page.assert_no_alert()

    @allure.story("取消订阅")
    @allure.title("取消API订阅弹窗打开与取消")
    @allure.severity(allure.severity_level.NORMAL)
    def test_unsubscribe_dialog_open_and_cancel(self):
        """点击取消订阅打开弹窗，验证后取消（无已订阅API时跳过）"""
        with AllureHelper.step("检查取消订阅按钮状态"):
            self.detail_page.assert_no_alert(retries=6)
            if not self.detail_page.btn_unsubscribe.is_enabled():
                pytest.skip("无已订阅API，跳过取消订阅弹窗测试")

        with AllureHelper.step("打开取消订阅弹窗"):
            self.detail_page.click_unsubscribe()

        with AllureHelper.step("验证弹窗已打开"):
            expect(self.detail_page.dialog_unsubscribe).to_be_visible()
            self.detail_page.take_screenshot("AIOS-消费者应用详情-取消订阅弹窗", True)

        with AllureHelper.step("取消操作"):
            self.detail_page.cancel_unsubscribe()
            expect(self.detail_page.dialog_unsubscribe).to_be_hidden()

        self.detail_page.assert_no_alert()

    @allure.story("导航")
    @allure.title("通过面包屑返回消费者应用列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_navigate_back_to_list(self):
        """点击面包屑返回列表页，验证列表表格可见"""
        with AllureHelper.step("点击面包屑返回"):
            self.detail_page.assert_no_alert(retries=6)
            self.detail_page.navigate_back()

        with AllureHelper.step("验证已返回列表页"):
            expect(self.consumer_app_page.table).to_be_visible()
            self.consumer_app_page.assert_no_alert()
            self.consumer_app_page.take_screenshot("AIOS-消费者应用-返回列表", True)


@pytest.mark.ui
@allure.epic("沙箱UI自动化测试")
@allure.feature("角色管理")
class TestRoleManageFunctional:
    """角色管理 功能测试"""

    @pytest.fixture(autouse=True)
    def setup(self, login_context):
        self.context, self.page = login_context
        self.home_page = HomePage(self.page)
        self.home_page.switch_top_menu(SystemMenu.INDEX)
        self.home_page.expand_sidebar()
        self.page.wait_for_timeout(UITimeout.ANIMATION)
        self.role_manage_page = RoleManagePage(self.page)

        # 导航到角色管理页面
        self.home_page.open_menu(AiosMenu.PERMISSION_MANAGE, AiosMenu.ROLE_MANAGE)

        yield
        self.home_page.wait_alert_hidden()

    @allure.story("搜索")
    @allure.title("按角色名称关键字搜索")
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_role(self):
        """输入角色名称关键字搜索，验证页面无报错"""
        with AllureHelper.step("搜索角色关键字"):
            self.role_manage_page.assert_no_alert(retries=6)
            self.role_manage_page.search_role("平台")

        with AllureHelper.step("验证查询无报错"):
            self.role_manage_page.assert_no_alert()
            self.role_manage_page.take_screenshot("AIOS-角色管理-关键字搜索", True)

    @allure.story("新增")
    @allure.title("新增角色弹窗打开与取消")
    @allure.severity(allure.severity_level.NORMAL)
    def test_add_role_dialog_open_and_cancel(self):
        """打开新增角色弹窗，填写表单后取消"""
        with AllureHelper.step("打开新增角色弹窗"):
            self.role_manage_page.assert_no_alert(retries=6)
            self.role_manage_page.click_add()

        with AllureHelper.step("验证弹窗已打开"):
            expect(self.role_manage_page.dialog_add_role).to_be_visible()
            expect(self.role_manage_page.input_add_role_name).to_be_visible()
            self.role_manage_page.take_screenshot("AIOS-角色管理-新增弹窗", True)

        with AllureHelper.step("填写表单并取消"):
            self.role_manage_page.fill_add_form("自动化临时角色", "AUTO_TEMP_ROLE")
            self.role_manage_page.click_cancel("新增角色")
            expect(self.role_manage_page.dialog_add_role).to_be_hidden()

        self.role_manage_page.assert_no_alert()

    @allure.story("列表")
    @allure.title("角色列表展开与收起")
    @allure.severity(allure.severity_level.MINOR)
    def test_expand_collapse_role_list(self):
        """点击展开/收起按钮，验证页面无报错"""
        with AllureHelper.step("点击展开/收起"):
            self.role_manage_page.assert_no_alert(retries=6)
            self.role_manage_page.click_expand_collapse_all()
            self.page.wait_for_timeout(UITimeout.QUERY)

        with AllureHelper.step("验证无报错"):
            self.role_manage_page.assert_no_alert()
            self.role_manage_page.take_screenshot("AIOS-角色管理-展开收起", True)


@pytest.mark.ui
@allure.epic("沙箱UI自动化测试")
@allure.feature("租户管理")
class TestTenantManageFunctional:
    """租户管理 功能测试"""

    @pytest.fixture(autouse=True)
    def setup(self, login_context):
        self.context, self.page = login_context
        self.home_page = HomePage(self.page)
        self.home_page.switch_top_menu(SystemMenu.INDEX)
        self.home_page.expand_sidebar()
        self.page.wait_for_timeout(UITimeout.ANIMATION)
        self.tenant_manage_page = TenantManagePage(self.page)

        # 导航到租户管理页面
        self.home_page.open_menu(AiosMenu.PERMISSION_MANAGE, AiosMenu.TENANT_MANAGE)

        yield
        self.home_page.wait_alert_hidden()

    @allure.story("搜索")
    @allure.title("按租户名称关键字搜索")
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_tenant(self):
        """输入租户名称关键字搜索，验证页面无报错"""
        with AllureHelper.step("搜索租户关键字"):
            self.tenant_manage_page.assert_no_alert(retries=6)
            self.tenant_manage_page.search_tenant("a")

        with AllureHelper.step("验证查询无报错"):
            self.tenant_manage_page.assert_no_alert()
            expect(self.tenant_manage_page.table).to_be_visible()
            self.tenant_manage_page.take_screenshot("AIOS-租户管理-关键字搜索", True)

    @allure.story("搜索")
    @allure.title("清空搜索条件恢复完整列表")
    @allure.severity(allure.severity_level.MINOR)
    def test_clear_search(self):
        """清空搜索条件并重新查询，验证页面无报错"""
        with AllureHelper.step("先执行一次搜索"):
            self.tenant_manage_page.assert_no_alert(retries=6)
            self.tenant_manage_page.search_tenant("不存在的租户xyz")

        with AllureHelper.step("清空搜索条件"):
            self.tenant_manage_page.clear_search()
            self.tenant_manage_page.assert_no_alert()
            self.tenant_manage_page.take_screenshot("AIOS-租户管理-清空搜索", True)

    @allure.story("用户关联")
    @allure.title("用户关联弹窗打开与关闭")
    @allure.severity(allure.severity_level.NORMAL)
    def test_user_relation_dialog_open_and_close(self):
        """点击顶部用户关联按钮，验证弹窗元素后关闭"""
        with AllureHelper.step("打开用户关联弹窗"):
            self.tenant_manage_page.assert_no_alert(retries=6)
            self.tenant_manage_page.open_user_relation_dialog()

        with AllureHelper.step("验证弹窗已打开"):
            expect(self.tenant_manage_page.dialog_user_relation).to_be_visible()
            expect(self.tenant_manage_page.input_relation_tenant_search).to_be_visible()
            self.tenant_manage_page.take_screenshot("AIOS-租户管理-用户关联弹窗", True)

        with AllureHelper.step("关闭弹窗"):
            self.tenant_manage_page.close_user_relation_dialog()
            expect(self.tenant_manage_page.dialog_user_relation).to_be_hidden()

        self.tenant_manage_page.assert_no_alert()


@pytest.mark.ui
@allure.epic("沙箱UI自动化测试")
@allure.feature("用户管理")
class TestUserManageFunctional:
    """用户管理 功能测试"""

    @pytest.fixture(autouse=True)
    def setup(self, login_context):
        self.context, self.page = login_context
        self.home_page = HomePage(self.page)
        self.home_page.switch_top_menu(SystemMenu.INDEX)
        self.home_page.expand_sidebar()
        self.page.wait_for_timeout(UITimeout.ANIMATION)
        self.user_manage_page = UserManagePage(self.page)

        # 导航到用户管理页面
        self.home_page.open_menu(AiosMenu.PERMISSION_MANAGE, AiosMenu.USER_MANAGE)

        yield
        self.home_page.wait_alert_hidden()

    @allure.story("搜索")
    @allure.title("按用户账号/姓名关键字搜索")
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_user(self):
        """输入用户关键字搜索，验证页面无报错"""
        with AllureHelper.step("搜索用户关键字"):
            self.user_manage_page.assert_no_alert(retries=6)
            self.user_manage_page.search_user("a")

        with AllureHelper.step("验证查询无报错"):
            self.user_manage_page.assert_no_alert()
            self.user_manage_page.take_screenshot("AIOS-用户管理-关键字搜索", True)

    @allure.story("新增")
    @allure.title("新增用户弹窗打开与取消")
    @allure.severity(allure.severity_level.NORMAL)
    def test_add_user_dialog_open_and_cancel(self):
        """打开新增用户弹窗，验证表单元素后取消"""
        with AllureHelper.step("打开新增用户弹窗"):
            self.user_manage_page.assert_no_alert(retries=6)
            self.user_manage_page.click_add()

        with AllureHelper.step("验证弹窗已打开"):
            expect(self.user_manage_page.dialog_add_user).to_be_visible()
            expect(self.user_manage_page.input_add_useraccount).to_be_visible()
            expect(self.user_manage_page.input_add_username).to_be_visible()
            self.user_manage_page.take_screenshot("AIOS-用户管理-新增弹窗", True)

        with AllureHelper.step("取消新增"):
            self.user_manage_page.click_cancel("新增用户")
            expect(self.user_manage_page.dialog_add_user).to_be_hidden()

        self.user_manage_page.assert_no_alert()

    @allure.story("分页")
    @allure.title("读取分页信息")
    @allure.severity(allure.severity_level.MINOR)
    def test_pagination_info(self):
        """读取分页总条数文本，验证分页组件正常"""
        with AllureHelper.step("读取分页信息"):
            self.user_manage_page.assert_no_alert(retries=6)
            pagination_text = self.user_manage_page.get_pagination_text()

        with AllureHelper.step("验证分页文本非空"):
            assert pagination_text, "分页组件文本为空"
            logger.info(f"用户管理分页信息: {pagination_text}")
            self.user_manage_page.assert_no_alert()
            self.user_manage_page.take_screenshot("AIOS-用户管理-分页信息", True)

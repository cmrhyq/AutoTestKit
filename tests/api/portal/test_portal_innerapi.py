"""
磐基门户 InnerAPI 接口测试
"""

import allure
import pytest

from base.api.entity.portal import PortalInnerPublicParams
from base.api.services.portal_inner_service import (
    ApplicationEntity,
    InnerSystemEntity,
    InnerUserEntity,
    MenuEntity,
    PortalInnerService,
    RoleEntity,
    TenantEntity,
)
from core.log import get_logger
from core.reporting.allure_helper import AllureHelper
from core.constants import Tenant

logger = get_logger(__name__)

@pytest.mark.api
@pytest.mark.portal
@allure.epic("磐基API自动化测试")
@allure.feature("磐基门户InnerAPI接口")
@allure.story("Portal Inner 门户内部接口")
class TestPortalInnerAPI:

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def portal_inner_service(self, test_env):
        """创建 Portal Inner API 服务实例"""
        service = PortalInnerService(
            base_url=test_env.get("apiInnerBaseUrl"),
        )
        yield service
        service.close()

    @pytest.fixture(scope="class")
    def public_params(self, test_env):
        """提取 Portal InnerAPI 测试所需的公共参数。"""
        return PortalInnerPublicParams(
            portal_user_id=test_env.get("portalUserId"),
            portal_username=test_env.get("portalUsername"),
        )

    # ==================== 基础数据查询接口 ====================

    @pytest.mark.run(order=1)
    @allure.title("获取用户全量数据")
    @allure.description("拉取平台全量用户数据用于后续绑定/授权，断言响应为字典且 code=0 或包含 data 字段")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_user_full_data(self, portal_inner_service, api_cache):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取用户全量数据"):
                response_json = portal_inner_service.get_user_full_data()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert response_json.get("code") == 0 or "data" in response_json, "响应应包含有效数据"
                logger.info(f"获取用户全量数据成功, code={response_json.get('code')}")

    @allure.title("获取租户全量数据")
    @allure.description("拉取平台全量租户数据，断言响应为字典且 code=0 或包含 data 字段")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_tenant_full_data(self, portal_inner_service, api_cache):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取租户全量数据"):
                response_json = portal_inner_service.get_tenant_full_data()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert response_json.get("code") == 0 or "data" in response_json, "响应应包含有效数据"
                logger.info(f"获取租户全量数据成功, code={response_json.get('code')}")

    @allure.title("获取角色全量数据")
    @allure.description("拉取平台全量角色数据，断言响应为字典且 code=0 或包含 data 字段")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_role_full_data(self, portal_inner_service, api_cache):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取角色全量数据"):
                response_json = portal_inner_service.get_role_full_data()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert response_json.get("code") == 0 or "data" in response_json, "响应应包含有效数据"
                logger.info(f"获取角色全量数据成功, code={response_json.get('code')}")

    @allure.title("根据模块名称查询字典数据")
    @allure.description("按模块名称查询指定类型的字典数据")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_dict_by_module(self, portal_inner_service, public_params, api_cache):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求查询字典数据"):
                response_json = portal_inner_service.get_dict_by_module(
                    module_name=public_params.module_name,
                    dict_type="ENVIRONMENT"
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert response_json.get("code") == 0 or "data" in response_json, "响应应包含有效数据"
                logger.info(f"查询字典数据成功, code={response_json.get('code')}")

    @allure.title("获取API全量数据")
    @allure.description("拉取平台全量 API 元数据，断言响应为字典")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_role_api_full_data(self, portal_inner_service, api_cache):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取API全量数据"):
                response_json = portal_inner_service.get_role_api_full_data()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                logger.info(f"获取API全量数据成功, code={response_json.get('code')}")

    @allure.title("获取系统参数")
    @allure.description("按 key 查询系统参数配置")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_system_config(self, portal_inner_service, api_cache):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取系统参数"):
                response_json = portal_inner_service.get_system_config(key="platformCode")

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert response_json.get("code") == 0 or "data" in response_json, "响应应包含有效数据"
                logger.info(f"获取系统参数成功, code={response_json.get('code')}")

    # ==================== 版本与License接口 ====================

    @allure.title("添加组件版本信息")
    @allure.description("向组件版本库注册一条测试版本（component_code=test1, version=testV.2.0），断言响应为字典")
    @allure.severity(allure.severity_level.NORMAL)
    def test_add_version_info(self, portal_inner_service, api_cache):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 POST 请求添加组件版本信息"):
                response_json = portal_inner_service.add_version_info(
                    component_name="测试修改2",
                    component_code="test1",
                    component_version="testV.2.0"
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                logger.info(f"添加组件版本信息成功, code={response_json.get('code')}")

    @allure.title("获取license信息")
    @allure.description("按 moduleCode 获取 license 信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_license_info(self, portal_inner_service, api_cache):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取license信息"):
                response_json = portal_inner_service.get_license_info(
                    module_code="mesh"
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                logger.info(f"获取license信息成功, code={response_json.get('code')}")

    @allure.title("获取平台版本信息")
    @allure.description("查询平台整体版本信息，断言响应为字典")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_platform_version(self, portal_inner_service, api_cache):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取平台版本信息"):
                response_json = portal_inner_service.get_platform_version()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                logger.info(f"获取平台版本信息成功, code={response_json.get('code')}")

    # ==================== 平台信息接口 ====================

    @allure.title("获取平台基本信息")
    @allure.description("查询平台名称/标识等基本信息，断言响应为字典")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_platform_base_info(self, portal_inner_service, api_cache):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取平台基本信息"):
                response_json = portal_inner_service.get_platform_base_info()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                logger.info(f"获取平台基本信息成功, code={response_json.get('code')}")

    @allure.title("获取平台开启模块信息")
    @allure.description("查询平台开启的模块列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_platform_enable_modules(self, portal_inner_service, api_cache):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取平台开启模块信息"):
                response_json = portal_inner_service.get_platform_enable_modules()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                logger.info(f"获取平台开启模块信息成功, code={response_json.get('code')}")

    # ==================== 全局配置接口 ====================

    @allure.title("全局配置接口查询")
    @allure.description("查询平台当前全局配置项，断言响应为字典")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_paas_config(self, portal_inner_service, api_cache):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取全局配置"):
                response_json = portal_inner_service.get_paas_config()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                logger.info(f"获取全局配置成功, code={response_json.get('code')}")

    @allure.title("全局配置修改与还原")
    @allure.description("修改全局配置并在测试结束后还原")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_global_config(self, portal_inner_service, api_cache):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 POST 请求修改全局配置（禁用component模块）"):
                response_json = portal_inner_service.update_global_config(
                    modules=[{"moduleCode": "component", "enabled": False}]
                )

            with AllureHelper.step("验证修改响应"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                logger.info(f"修改全局配置成功(禁用component), code={response_json.get('code')}")

            with AllureHelper.step("发送 POST 请求还原全局配置（启用component模块）"):
                restore_response = portal_inner_service.update_global_config(
                    modules=[{"moduleCode": "component", "enabled": True}]
                )

            with AllureHelper.step("验证还原响应"):
                assert isinstance(restore_response, dict), "还原响应应该是字典类型"
                logger.info(f"还原全局配置成功(启用component), code={restore_response.get('code')}")

    # ==================== 授权与消息接口 ====================

    @allure.title("获取系统应用全量授权信息")
    @allure.description("查询系统应用的全量授权信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_auth_info(self, portal_inner_service, api_cache):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取授权信息"):
                response_json = portal_inner_service.get_auth_info()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                logger.info(f"获取授权信息成功, code={response_json.get('code')}")

    @allure.title("站内消息发送")
    @allure.description("向指定 portalUsername 发送一条站内消息，断言响应为字典")
    @allure.severity(allure.severity_level.NORMAL)
    def test_send_message(self, portal_inner_service, public_params, api_cache):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 POST 请求发送站内消息"):
                response_json = portal_inner_service.send_message(
                    users=[public_params.portal_username],
                    content="切换失败，请关注手工处理"
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                logger.info(f"站内消息发送成功, code={response_json.get('code')}")

    # ==================== 域查询接口 ====================

    @allure.title("查询一级域列表")
    @allure.description("查询一级域列表并将首条 systemId 缓存为 api_cache['first1'] 供后续用例使用，断言响应含 data 字段")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_first_field_list(self, portal_inner_service, api_cache):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求查询一级域列表"):
                response_json = portal_inner_service.get_first_field_list()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert "data" in response_json, "响应应包含 data 字段"

            with AllureHelper.step("缓存一级域数据，供后续测试使用"):
                api_cache.set("first1", response_json["data"][0]["systemId"])
                logger.info(f"已缓存一级域Id: {response_json['data'][0]['systemId']}")

    @allure.title("查询二级域列表")
    @allure.description("基于上游缓存 first1 查询二级域列表，并将首条 moduleId 缓存为 api_cache['moduleId'] 供后续用例使用，断言响应含 data 字段")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_second_field_list(self, portal_inner_service, api_cache):
        first1 = api_cache.get("first1")
        if not first1:
            pytest.skip("未获取到一级域 systemId，跳过二级域查询")

        logger.info(f"开始测试: 查询二级域列表, systemId={first1}")
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求查询二级域列表"):
                response_json = portal_inner_service.get_second_field_list(system_id=first1)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert "data" in response_json, "响应应包含 data 字段"

            with AllureHelper.step("缓存二级域数据"):
                data = response_json.get("data", [])
                if data:
                    module_id = data[0].get("moduleId")
                    api_cache.set("moduleId", module_id)
                    logger.info(f"已缓存二级域moduleId: {module_id}")

    # ==================== 系统管理接口 ====================

    @allure.title("创建系统")
    @allure.description("消费缓存中的一级域/二级域 ID 创建测试系统 portal_inner_api_test_sys，断言响应为字典")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_system(self, portal_inner_service, public_params, api_cache):
        first1 = api_cache.get("first1")
        module_id = api_cache.get("moduleId")
        if not first1 or not module_id:
            pytest.skip("未获取到一级域/二级域ID，跳过创建系统")

        logger.info(f"开始测试: 创建系统, first1={first1}, moduleId={module_id}")
        system = InnerSystemEntity(
            system_name="portal_inner_api_test_sys",
            system_code="portal_inner_api_test_sys",
            field_one=first1,
            field_two=module_id,
            create_id=public_params.portal_user_id,
            username=public_params.portal_username,
        )

        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 POST 请求创建系统"):
                response_json = portal_inner_service.create_system(system)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                logger.info(f"创建系统成功, code={response_json.get('code')}")

    @allure.title("获取系统全量数据")
    @allure.description("查询系统全量数据并提取 systemId 供后续用例使用")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_system_full_data(self, portal_inner_service, api_cache):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取系统全量数据"):
                response_json = portal_inner_service.get_system_full_data()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert "data" in response_json, "响应应包含 data 字段"

            with AllureHelper.step("提取并缓存 systemId"):
                data = response_json.get("data", [])
                system_id = None
                for item in data:
                    if item.get("systemCode") == "portal_inner_api_test_sys":
                        system_id = item.get("systemId")
                        break
                api_cache.set("systemId", system_id)
                logger.info(f"已缓存systemId: {system_id}")

    # ==================== 应用管理接口 ====================

    @allure.title("创建应用")
    @allure.description("消费缓存中的 systemId 创建测试应用 portal_inner_api_test_app，断言响应为字典")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_application(self, portal_inner_service, public_params, api_cache):
        system_id = api_cache.get("systemId")
        if not system_id:
            pytest.skip("未获取到 systemId，跳过创建应用")

        logger.info(f"开始测试: 创建应用, systemId={system_id}")
        app = ApplicationEntity(
            app_name="portal_inner_api_test_app",
            app_code="portal_inner_api_test_app",
            app_type="web_type",
            system_id=system_id,
            create_id=public_params.portal_user_id,
            username=public_params.portal_username,
            workload_type="Deployment",
        )

        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 POST 请求创建应用"):
                response_json = portal_inner_service.create_application(app)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                logger.info(f"创建应用成功, code={response_json.get('code')}")

    @allure.title("获取应用全量数据")
    @allure.description("查询应用全量数据并提取应用信息供后续用例使用")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_application_full_data(self, portal_inner_service, api_cache):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取应用全量数据"):
                response_json = portal_inner_service.get_application_full_data()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert "data" in response_json, "响应应包含 data 字段"

            with AllureHelper.step("提取并缓存应用数据"):
                data = response_json.get("data", [])
                for item in data:
                    if item.get("applicationSourceCode") == "portal_inner_api_test_app":
                        api_cache.set("systemId2", item.get("systemId"))
                        api_cache.set("appSourceId", item.get("applicationSourceId"))
                        logger.info(f"已缓存appSourceId: {item.get('applicationSourceId')}")
                        break

    # ==================== 实例查询接口 ====================

    @allure.title("环境查询接口（全量查询）")
    @allure.description("按 ENVIRONMENT 模型全量查询环境实例")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_all_instances_environment(self, portal_inner_service, api_cache):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 POST 请求查询环境全量数据"):
                response_json = portal_inner_service.get_all_instances(model_code="ENVIRONMENT")

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                logger.info(f"环境全量查询成功, code={response_json.get('code')}")

    @allure.title("平面查询接口（全量查询）")
    @allure.description("按 PLANE 模型全量查询平面实例")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_all_instances_plane(self, portal_inner_service, api_cache):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 POST 请求查询平面全量数据"):
                response_json = portal_inner_service.get_all_instances(model_code="PLANE")

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                logger.info(f"平面全量查询成功, code={response_json.get('code')}")

    @allure.title("单元查询接口（全量查询）")
    @allure.description("按 CELL 模型全量查询单元实例")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_all_instances_cell(self, portal_inner_service, api_cache):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 POST 请求查询单元全量数据"):
                response_json = portal_inner_service.get_all_instances(model_code="CELL")

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                logger.info(f"单元全量查询成功, code={response_json.get('code')}")

    @allure.title("产品实例查询接口（全量查询）")
    @allure.description("按 PROD_INST 模型全量查询产品实例")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_all_instances_prod_inst(self, portal_inner_service, api_cache):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 POST 请求查询产品实例全量数据"):
                response_json = portal_inner_service.get_all_instances(model_code="PROD_INST")

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert "data" in response_json, "响应应包含 data 字段"

            with AllureHelper.step("提取产品实例编码"):
                data = response_json.get("data", [])
                if len(data) > 1:
                    prod_inst_code = data[0].get("prodInstCode")
                    api_cache.set("prodInstCode", prod_inst_code)
                    logger.info(f"已缓存prodInstCode: {prod_inst_code}")

    @allure.title("按条件查询接口（产品实例）")
    @allure.description("按 prodInstCode 条件查询产品实例")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_instances_by_example(self, portal_inner_service, api_cache):
        prod_inst_code = api_cache.get("prodInstCode")
        if not prod_inst_code:
            pytest.skip("未获取到 prodInstCode，跳过条件查询")

        logger.info(f"开始测试: 按条件查询产品实例, prodInstCode={prod_inst_code}")
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 POST 请求按条件查询产品实例"):
                response_json = portal_inner_service.get_instances_by_example(
                    model_code="PROD_INST",
                    prod_inst_code=prod_inst_code
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                logger.info(f"按条件查询产品实例成功, code={response_json.get('code')}")

    # ==================== 菜单权限管理接口 ====================

    @pytest.mark.run(order=80)
    @allure.title("[菜单管理-01] 查询菜单列表并定位旧测试菜单")
    @allure.description("按 sourceCode 查询菜单权限数据，若已存在同名旧测试菜单则将其 menuId 写入 api_cache 供清理步骤使用")
    @allure.severity(allure.severity_level.NORMAL)
    def test_menu_mgmt_query_menu_list(self, portal_inner_service, public_params, api_cache):
        logger.info(f"[菜单管理-01] 查询菜单列表, sourceCode={public_params.source_code}")

        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("查询菜单权限数据"):
                response_json = portal_inner_service.get_menu_list(
                    source_code=public_params.source_code, all_menu=1
                )
                assert isinstance(response_json, dict), "响应应该是字典类型"
                logger.info(f"查询菜单权限数据成功, code={response_json.get('code')}")

            data = response_json.get("data", []) or []
            existing_menu_id = None
            for item in data:
                if item.get("menuName") == public_params.menu_name:
                    existing_menu_id = item.get("menuId")
                    break

            api_cache.set("menu_mgmt_existing_menu_id", existing_menu_id)
            logger.info(f"[菜单管理-01] 旧测试菜单 menuId={existing_menu_id}")

    @pytest.mark.run(order=81)
    @allure.title("[菜单管理-02] 清理已存在的旧菜单")
    @allure.description("依据 api_cache 中记录的旧菜单 menuId，如存在则先删除，避免新增时冲突")
    @allure.severity(allure.severity_level.NORMAL)
    def test_menu_mgmt_cleanup_existing(self, portal_inner_service, api_cache):
        existing_menu_id = api_cache.get("menu_mgmt_existing_menu_id")
        if not existing_menu_id:
            logger.info("[菜单管理-02] 未发现旧测试菜单，跳过清理")
            pytest.skip("未发现旧测试菜单，无需清理")

        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step(f"删除已存在的测试菜单, menuId={existing_menu_id}"):
                del_response = portal_inner_service.delete_menu(menu_ids=[str(existing_menu_id)])
                assert isinstance(del_response, dict), "删除响应应该是字典类型"
                logger.info(f"删除已存在的测试菜单成功, menuId={existing_menu_id}")

    @pytest.mark.run(order=82)
    @allure.title("[菜单管理-03] 新增插件菜单")
    @allure.description("新增测试插件菜单，并把返回或补查得到的 menuId 写入 api_cache 供后续步骤使用")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_menu_mgmt_add_menu(self, portal_inner_service, public_params, api_cache):
        menu = MenuEntity(
            menu_name=public_params.menu_name,
            url_path="/iframe/plugin/t",
            plugin_url="/ec/test1111/tt",
            source_code=public_params.source_code,
            roles=["platform_manager"],
            plugin_flag=public_params.source_code,
        )

        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("新增插件菜单"):
                add_response = portal_inner_service.add_menu(menu)
                assert isinstance(add_response, dict), "新增响应应该是字典类型"
                logger.info(f"新增插件菜单成功, code={add_response.get('code')}")

            menu_id = None
            if add_response.get("data"):
                menu_id = add_response["data"].get("menuId")

            if not menu_id:
                with AllureHelper.step("重新查询菜单列表以获取 menuId"):
                    query_resp = portal_inner_service.get_menu_list(
                        source_code=public_params.source_code, all_menu=1
                    )
                    for item in query_resp.get("data", []) or []:
                        if item.get("menuName") == public_params.menu_name:
                            menu_id = item.get("menuId")
                            break

            assert menu_id is not None, "应成功获取新增菜单的menuId"
            api_cache.set("menu_mgmt_new_menu_id", menu_id)
            logger.info(f"[菜单管理-03] 新增菜单 menuId={menu_id}")

    @pytest.mark.run(order=83)
    @allure.title("[菜单管理-04] 停用插件菜单")
    @allure.description("从 api_cache 读取新增菜单的 menuId，调用停用接口")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_menu_mgmt_disable_menu(self, portal_inner_service, api_cache):
        menu_id = api_cache.get("menu_mgmt_new_menu_id")
        assert menu_id is not None, "api_cache 中未找到新增菜单的 menuId，请检查前置用例是否成功"

        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step(f"停用插件菜单, menuId={menu_id}"):
                disable_response = portal_inner_service.disable_menu(menu_ids=[str(menu_id)])
                assert isinstance(disable_response, dict), "停用响应应该是字典类型"
                logger.info(f"停用插件菜单成功, menuId={menu_id}")

    @pytest.mark.run(order=84)
    @allure.title("[菜单管理-05] 启用插件菜单")
    @allure.description("从 api_cache 读取新增菜单的 menuId，调用启用接口")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_menu_mgmt_enable_menu(self, portal_inner_service, api_cache):
        menu_id = api_cache.get("menu_mgmt_new_menu_id")
        assert menu_id is not None, "api_cache 中未找到新增菜单的 menuId，请检查前置用例是否成功"

        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step(f"启用插件菜单, menuId={menu_id}"):
                enable_response = portal_inner_service.enable_menu(menu_ids=[str(menu_id)])
                assert isinstance(enable_response, dict), "启用响应应该是字典类型"
                logger.info(f"启用插件菜单成功, menuId={menu_id}")

    @pytest.mark.run(order=85)
    @allure.title("[菜单管理-06] 删除插件菜单（清理）")
    @allure.description("从 api_cache 读取新增菜单的 menuId，调用删除接口收尾清理")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_menu_mgmt_delete_menu(self, portal_inner_service, api_cache):
        menu_id = api_cache.get("menu_mgmt_new_menu_id")
        assert menu_id is not None, "api_cache 中未找到新增菜单的 menuId，请检查前置用例是否成功"

        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step(f"删除插件菜单, menuId={menu_id}"):
                delete_response = portal_inner_service.delete_menu(menu_ids=[str(menu_id)])
                assert isinstance(delete_response, dict), "删除响应应该是字典类型"
                logger.info(f"删除插件菜单成功, menuId={menu_id}")

    # ==================== 角色管理接口 ====================

    @pytest.mark.run(order=90)
    @allure.title("[角色管理-01] 查询角色列表并判断目标角色是否存在")
    @allure.description("查询当前角色列表，判断目标 roleCode 是否已存在，并将结果写入 api_cache 供后续步骤决策")
    @allure.severity(allure.severity_level.NORMAL)
    def test_role_mgmt_query_roles(self, portal_inner_service, public_params, api_cache):
        role_code = public_params.role_code
        logger.info(f"[角色管理-01] 查询角色列表, roleCode={role_code}")

        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("查询当前角色列表"):
                response_json = portal_inner_service.get_roles()
                assert isinstance(response_json, dict), "响应应该是字典类型"
                logger.info(f"查询角色列表成功, code={response_json.get('code')}")

            data = response_json.get("data", []) or []
            role_exists = any(item.get("roleCode") == role_code for item in data)
            api_cache.set("role_mgmt_role_exists", role_exists)
            logger.info(f"[角色管理-01] 目标角色是否已存在: {role_exists}")

    @pytest.mark.run(order=91)
    @allure.title("[角色管理-02] 清理已存在的旧角色")
    @allure.description("依据 api_cache 中记录的存在状态，如果目标角色已存在则先删除，避免创建冲突")
    @allure.severity(allure.severity_level.NORMAL)
    def test_role_mgmt_cleanup_existing(self, portal_inner_service, public_params, api_cache):
        role_code = public_params.role_code
        role_exists = api_cache.get("role_mgmt_role_exists")

        if not role_exists:
            logger.info(f"[角色管理-02] 角色 {role_code} 不存在，跳过清理")
            pytest.skip(f"角色 {role_code} 不存在，无需清理")
            return

        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step(f"删除已存在的角色: {role_code}"):
                del_response = portal_inner_service.delete_role(role_code=role_code)
                assert isinstance(del_response, dict), "删除响应应该是字典类型"
                logger.info(f"删除已存在角色成功, roleCode={role_code}")

    @pytest.mark.run(order=92)
    @allure.title("[角色管理-03] 创建角色")
    @allure.description("以 roleType=1 创建测试角色")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_role_mgmt_create_role(self, portal_inner_service, public_params, api_cache):
        role_code = public_params.role_code
        role = RoleEntity(
            role_name=role_code,
            role_code=role_code,
            role_type=1,
            has_edit=1,
        )

        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step(f"创建角色: {role_code}"):
                create_response = portal_inner_service.create_role(role)
                assert isinstance(create_response, dict), "创建响应应该是字典类型"
                logger.info(f"创建角色成功, roleCode={role_code}")

    @pytest.mark.run(order=93)
    @allure.title("[角色管理-04] 修改角色类型为 2")
    @allure.description("将上一步创建的角色 roleType 由 1 修改为 2，验证修改接口")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_role_mgmt_update_role(self, portal_inner_service, public_params, api_cache):
        role_code = public_params.role_code
        updated_role = RoleEntity(
            role_name=role_code,
            role_code=role_code,
            role_desc=None,
            role_type=2,
            has_edit=1,
        )

        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step(f"修改角色类型为2: {role_code}"):
                update_response = portal_inner_service.update_role(updated_role)
                assert isinstance(update_response, dict), "修改响应应该是字典类型"
                logger.info(f"修改角色成功, roleCode={role_code}, roleType=2")

    @pytest.mark.run(order=94)
    @allure.title("[角色管理-05] 删除角色（清理）")
    @allure.description("删除本流程创建的测试角色，作为流程收尾清理")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_role_mgmt_delete_role(self, portal_inner_service, public_params, api_cache):
        role_code = public_params.role_code
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step(f"删除角色: {role_code}"):
                delete_response = portal_inner_service.delete_role(role_code=role_code)
                assert isinstance(delete_response, dict), "删除响应应该是字典类型"
                logger.info(f"删除角色成功(清理), roleCode={role_code}")

    # ==================== 用户/租户/角色绑定管理接口 ====================

    @pytest.mark.run(order=100)
    @allure.title("[绑定流程-01] 查询用户并缓存已有绑定关系")
    @allure.description("查询目标用户，若已存在则解析出当前绑定的 tenantCode / roleCode 并写入 api_cache 供后续清理使用")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_bindflow_query_user(self, portal_inner_service, public_params, api_cache):
        username = public_params.username
        logger.info(f"[绑定流程-01] 查询用户, username={username}")

        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step(f"查询用户: {username}"):
                user_response = portal_inner_service.get_user_by_username(username=username)
                assert isinstance(user_response, dict), "响应应该是字典类型"

            user_data = user_response.get("data")
            user_exists = user_data is not None and user_data.get("userName") == username
            api_cache.set("bindflow_user_exists", user_exists)

            current_tenant_code = None
            current_role_code = None
            if user_exists:
                tenant_list = user_data.get("tenantList", []) or []
                if tenant_list:
                    current_tenant_code = tenant_list[0].get("tenantCode")
                    role_list = tenant_list[0].get("roleList", []) or []
                    if role_list:
                        current_role_code = role_list[0].get("roleCode")

            api_cache.set("bindflow_current_tenant_code", current_tenant_code)
            api_cache.set("bindflow_current_role_code", current_role_code)
            logger.info(
                f"[绑定流程-01] 用户存在={user_exists}, "
                f"当前绑定 tenant={current_tenant_code}, role={current_role_code}"
            )

    @pytest.mark.run(order=101)
    @allure.title("[绑定流程-02] 清理已存在的旧数据（解绑/删除旧租户角色用户）")
    @allure.description("依据 api_cache 中记录的用户状态，若用户已存在则解绑租户角色关系、租户关系，并删除旧租户/角色/用户")
    @allure.severity(allure.severity_level.NORMAL)
    def test_bindflow_cleanup_existing(self, portal_inner_service, public_params, api_cache):
        username = public_params.username
        role_code = public_params.role_code
        tenant_code = public_params.tenant_code

        user_exists = api_cache.get("bindflow_user_exists")
        if not user_exists:
            logger.info(f"[绑定流程-02] 用户 {username} 不存在，跳过清理")
            pytest.skip(f"用户 {username} 不存在，无需清理旧数据")
            return

        current_tenant_code = api_cache.get("bindflow_current_tenant_code")
        current_role_code = api_cache.get("bindflow_current_role_code")

        with AllureHelper.api_test(portal_inner_service):
            if current_role_code and current_tenant_code:
                with AllureHelper.step("解绑用户已有的租户角色关系"):
                    portal_inner_service.unbind_user_tenant_role(
                        username=username,
                        tenant_code=current_tenant_code,
                        role_code=current_role_code,
                    )
                    logger.info(
                        f"解绑用户租户角色关系成功, tenant={current_tenant_code}, role={current_role_code}"
                    )

                with AllureHelper.step("解绑用户已有的租户关系"):
                    portal_inner_service.unbind_user_tenant(
                        username=username,
                        tenant_code=current_tenant_code,
                    )
                    logger.info(f"解绑用户租户关系成功, tenant={current_tenant_code}")

            with AllureHelper.step(f"删除租户: {tenant_code}"):
                portal_inner_service.delete_tenant(tenant_code=tenant_code)
                logger.info(f"删除租户成功, tenantCode={tenant_code}")

            with AllureHelper.step(f"删除角色: {role_code}"):
                portal_inner_service.delete_role(role_code=role_code)
                logger.info(f"删除角色成功, roleCode={role_code}")

            with AllureHelper.step(f"删除用户: {username}"):
                portal_inner_service.delete_user(username=username)
                logger.info(f"删除用户成功, username={username}")

    @pytest.mark.run(order=102)
    @allure.title("[绑定流程-03] 创建角色")
    @allure.description("创建测试用角色，作为后续用户绑定与 API 授权的载体")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_bindflow_create_role(self, portal_inner_service, public_params, api_cache):
        role_code = public_params.role_code
        role = RoleEntity(
            role_name=role_code,
            role_code=role_code,
            role_desc=None,
            role_type=2,
            has_edit=1,
            create_id=None,
        )

        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step(f"创建角色: {role_code}"):
                create_role_resp = portal_inner_service.create_role(role)
                assert isinstance(create_role_resp, dict), "创建角色响应应该是字典类型"
                logger.info(f"创建角色成功, roleCode={role_code}")

    @pytest.mark.run(order=103)
    @allure.title("[绑定流程-04] 创建租户")
    @allure.description("创建测试用租户，作为后续用户归属与绑定的目标")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_bindflow_create_tenant(self, portal_inner_service, public_params, api_cache):
        tenant_code = public_params.tenant_code
        tenant = TenantEntity(
            tenant_code=tenant_code,
            tenant_name=tenant_code,
            tenant_lever=2,
            tenant_parent_id=1,
            tenant_area=1,
            dept_code="b39a802ef7834b17b3cd9e76dd6e20231023",
            source_code="plugin-center",
            create_user_id=1,
        )

        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step(f"创建租户: {tenant_code}"):
                create_tenant_resp = portal_inner_service.create_tenant(tenant)
                assert isinstance(create_tenant_resp, dict), "创建租户响应应该是字典类型"
                logger.info(f"创建租户成功, tenantCode={tenant_code}")

    @pytest.mark.run(order=104)
    @allure.title("[绑定流程-05] 创建用户")
    @allure.description("创建绑定到目标租户与角色的测试用户")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_bindflow_create_user(self, portal_inner_service, public_params, api_cache):
        username = public_params.username
        tenant_code = public_params.tenant_code
        role_code = public_params.role_code
        user = InnerUserEntity(
            username="xeqHSRNJnN0tBjWTFuA+Qg==",
            alias="测试0930",
            phone="qrlAscZatvSyYi1Uh49cEw==",
            email="ZSOS5ICOFj+hZj72q53jIQ==",
            tenant_code=tenant_code,
            role_code=role_code,
            create_id=1,
        )

        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step(f"创建用户: {username}"):
                create_user_resp = portal_inner_service.create_user(user)
                assert isinstance(create_user_resp, dict), "创建用户响应应该是字典类型"
                logger.info(f"创建用户成功, username={username}")

    @pytest.mark.run(order=105)
    @allure.title("[绑定流程-06] 查询 API 列表并缓存待授权 API")
    @allure.description("查询指定模块的 API 列表，取前两项写入 api_cache 供后续批量授权/解除授权使用")
    @allure.severity(allure.severity_level.NORMAL)
    def test_bindflow_query_api_list(self, portal_inner_service, public_params, api_cache):
        module_name = public_params.module_name
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step(f"查询API列表, moduleName={module_name}"):
                api_list_resp = portal_inner_service.get_api_list(module_name=module_name)
                assert isinstance(api_list_resp, dict), "API列表响应应该是字典类型"

            api_data = api_list_resp.get("data", []) or []
            api_list_for_auth = []
            if len(api_data) >= 2:
                api_list_for_auth = [
                    {
                        "apiId": str(api_data[0].get("id")),
                        "authorizedMethod": api_data[0].get("method"),
                    },
                    {
                        "apiId": str(api_data[1].get("id")),
                        "authorizedMethod": api_data[0].get("method"),
                    },
                ]
            api_cache.set("bindflow_api_list_for_auth", api_list_for_auth)
            logger.info(
                f"查询API列表成功, moduleName={module_name}, "
                f"authApiCount={len(api_list_for_auth)}"
            )

    @pytest.mark.run(order=106)
    @allure.title("[绑定流程-07] API 批量授权")
    @allure.description("将 api_cache 中缓存的 API 列表批量授权给测试角色")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_bindflow_api_bulk_authorization(self, portal_inner_service, public_params, api_cache):
        role_code = public_params.role_code
        api_list_for_auth = api_cache.get("bindflow_api_list_for_auth") or []
        if not api_list_for_auth:
            pytest.skip("api_cache 中无待授权 API 列表，跳过批量授权")
            return

        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step(f"API批量授权, roleCode={role_code}"):
                auth_resp = portal_inner_service.api_bulk_authorization(
                    role_code=role_code,
                    api_list=api_list_for_auth,
                )
                assert isinstance(auth_resp, dict), "授权响应应该是字典类型"
                logger.info(
                    f"API批量授权成功, roleCode={role_code}, apiCount={len(api_list_for_auth)}"
                )

    @pytest.mark.run(order=107)
    @allure.title("[绑定流程-08] API 批量解除授权")
    @allure.description("将之前批量授权给测试角色的 API 全部解除授权")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_bindflow_api_bulk_reauthorization(self, portal_inner_service, public_params, api_cache):
        role_code = public_params.role_code
        api_list_for_auth = api_cache.get("bindflow_api_list_for_auth") or []
        if not api_list_for_auth:
            pytest.skip("api_cache 中无待解除授权 API 列表，跳过批量解除授权")
            return

        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step(f"API批量解除授权, roleCode={role_code}"):
                unauth_resp = portal_inner_service.api_bulk_reauthorization(
                    role_code=role_code,
                    api_list=api_list_for_auth,
                )
                assert isinstance(unauth_resp, dict), "解除授权响应应该是字典类型"
                logger.info(f"API批量解除授权成功, roleCode={role_code}")

    @pytest.mark.run(order=108)
    @allure.title("[绑定流程-09] 查询验证-用户存在")
    @allure.description("再次查询用户，验证前面创建流程的产物已生效")
    @allure.severity(allure.severity_level.NORMAL)
    def test_bindflow_verify_user(self, portal_inner_service, public_params, api_cache):
        username = public_params.username
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step(f"查询用户: {username}"):
                query_user_resp = portal_inner_service.get_user_by_username(username=username)
                assert isinstance(query_user_resp, dict), "查询用户响应应该是字典类型"
                logger.info(f"查询验证用户成功, username={username}")

    @pytest.mark.run(order=109)
    @allure.title("[绑定流程-10] 查询验证-租户存在")
    @allure.description("再次查询租户，验证前面创建流程的产物已生效")
    @allure.severity(allure.severity_level.NORMAL)
    def test_bindflow_verify_tenant(self, portal_inner_service, public_params, api_cache):
        tenant_code = public_params.tenant_code
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step(f"查询租户: {tenant_code}"):
                query_tenant_resp = portal_inner_service.get_tenant(tenant_code=tenant_code)
                assert isinstance(query_tenant_resp, dict), "查询租户响应应该是字典类型"
                logger.info(f"查询验证租户成功, tenantCode={tenant_code}")

    @pytest.mark.run(order=110)
    @allure.title("[绑定流程-11] 查询验证-角色存在")
    @allure.description("从角色全量列表中断言目标角色存在")
    @allure.severity(allure.severity_level.NORMAL)
    def test_bindflow_verify_role(self, portal_inner_service, public_params, api_cache):
        role_code = public_params.role_code
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("查询角色列表验证角色存在"):
                query_roles_resp = portal_inner_service.get_roles()
                assert isinstance(query_roles_resp, dict), "查询角色响应应该是字典类型"
                roles_data = query_roles_resp.get("data", []) or []
                role_exists = any(
                    item.get("roleCode") == role_code for item in roles_data
                )
                assert role_exists, f"角色 {role_code} 应该存在于角色列表中"
                logger.info(f"查询验证角色存在成功, roleCode={role_code}")

    @pytest.mark.run(order=111)
    @allure.title("[绑定流程-12] 用户-租户绑定")
    @allure.description("将测试用户绑定到测试租户")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_bindflow_bind_user_tenant(self, portal_inner_service, public_params, api_cache):
        username = public_params.username
        tenant_code = public_params.tenant_code
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step(f"用户 {username} 绑定租户 {tenant_code}"):
                bind_tenant_resp = portal_inner_service.bind_user_tenant(
                    username=username, tenant_code=tenant_code
                )
                assert isinstance(bind_tenant_resp, dict), "绑定租户响应应该是字典类型"
                logger.info(f"用户租户绑定成功, username={username}, tenant={tenant_code}")

    @pytest.mark.run(order=112)
    @allure.title("[绑定流程-13] 用户-租户-角色绑定")
    @allure.description("在用户-租户绑定完成后，进一步绑定角色，形成完整的三元关系")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_bindflow_bind_user_tenant_role(self, portal_inner_service, public_params, api_cache):
        username = public_params.username
        tenant_code = public_params.tenant_code
        role_code = public_params.role_code
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step(f"用户 {username} 绑定租户 {tenant_code} 角色 {role_code}"):
                bind_role_resp = portal_inner_service.bind_user_tenant_role(
                    username=username, tenant_code=tenant_code, role_code=role_code
                )
                assert isinstance(bind_role_resp, dict), "绑定角色响应应该是字典类型"
                logger.info(
                    f"用户租户角色绑定成功, username={username}, tenant={tenant_code}, role={role_code}"
                )


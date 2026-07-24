"""
磐基门户 InnerAPI 接口测试
"""

from typing import Dict, Any

import allure
import pytest

from base.api.fixtures import api_cache
from base.api.services.portal_inner_service import (
    PanJiPortalInnerService,
    InnerSystemEntity,
    ApplicationEntity,
    MenuEntity,
    RoleEntity,
    TenantEntity,
    InnerUserEntity,
)
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@allure.feature("磐基门户InnerAPI接口")
@allure.story("Portal Inner 门户内部接口")
class TestPortalInnerAPI:

    TENANT = "monitor-group"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        """每个用例前自动切换到本测试类声明的租户 token。"""
        get_token(self.TENANT)

    @pytest.fixture(scope="class")
    def portal_inner_service(self, api_env, api_logger):
        """创建 Portal Inner API 服务实例"""
        service = PanJiPortalInnerService(
            base_url=api_env.get("apiInnerBaseUrl"), logger=api_logger
        )
        yield service
        service.close()

    # ==================== 基础数据查询接口 ====================

    @allure.title("获取用户全量数据")
    @allure.description("GET /portal/api/user/list - 验证能够成功获取用户全量数据")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_user_full_data(self, portal_inner_service, api_cache, api_logger):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取用户全量数据"):
                response_json = portal_inner_service.get_user_full_data()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert response_json.get("code") == 0 or "data" in response_json, "响应应包含有效数据"
                api_logger.info(f"获取用户全量数据成功, code={response_json.get('code')}")

    @allure.title("获取租户全量数据")
    @allure.description("GET /portal/api/tenant/list - 验证能够成功获取租户全量数据")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_tenant_full_data(self, portal_inner_service, api_cache, api_logger):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取租户全量数据"):
                response_json = portal_inner_service.get_tenant_full_data()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert response_json.get("code") == 0 or "data" in response_json, "响应应包含有效数据"
                api_logger.info(f"获取租户全量数据成功, code={response_json.get('code')}")

    @allure.title("获取角色全量数据")
    @allure.description("GET /portal/api/role/list - 验证能够成功获取角色全量数据")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_role_full_data(self, portal_inner_service, api_cache, api_logger):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取角色全量数据"):
                response_json = portal_inner_service.get_role_full_data()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert response_json.get("code") == 0 or "data" in response_json, "响应应包含有效数据"
                api_logger.info(f"获取角色全量数据成功, code={response_json.get('code')}")

    @allure.title("根据模块名称查询字典数据")
    @allure.description("GET /portal/api/dict/list/{moduleName}?dictType=ENVIRONMENT - 验证能够根据模块名称查询字典数据")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_dict_by_module(self, portal_inner_service, api_env, api_cache, api_logger):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求查询字典数据"):
                response_json = portal_inner_service.get_dict_by_module(
                    module_name=api_env.get("moduleName"),
                    dict_type="ENVIRONMENT"
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert response_json.get("code") == 0 or "data" in response_json, "响应应包含有效数据"
                api_logger.info(f"查询字典数据成功, code={response_json.get('code')}")

    @allure.title("获取API全量数据")
    @allure.description("GET /portal/api/roleApi/list - 验证能够成功获取API全量数据")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_role_api_full_data(self, portal_inner_service, api_cache, api_logger):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取API全量数据"):
                response_json = portal_inner_service.get_role_api_full_data()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                api_logger.info(f"获取API全量数据成功, code={response_json.get('code')}")

    @allure.title("获取系统参数")
    @allure.description("GET /portal/api/systemConfig/list?key=platformCode - 验证能够成功获取系统参数")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_system_config(self, portal_inner_service, api_cache, api_logger):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取系统参数"):
                response_json = portal_inner_service.get_system_config(key="platformCode")

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert response_json.get("code") == 0 or "data" in response_json, "响应应包含有效数据"
                api_logger.info(f"获取系统参数成功, code={response_json.get('code')}")

    # ==================== 版本与License接口 ====================

    @allure.title("添加组件版本信息")
    @allure.description("POST /portal/api/version/addVersionInfo - 验证能够添加组件版本信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_add_version_info(self, portal_inner_service, api_cache, api_logger):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 POST 请求添加组件版本信息"):
                response_json = portal_inner_service.add_version_info(
                    component_name="测试修改2",
                    component_code="test1",
                    component_version="testV.2.0"
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                api_logger.info(f"添加组件版本信息成功, code={response_json.get('code')}")

    @allure.title("获取license信息")
    @allure.description("GET /portal/api/license/{moduleCode} - 验证能够获取license信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_license_info(self, portal_inner_service, api_env, api_cache, api_logger):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取license信息"):
                response_json = portal_inner_service.get_license_info(
                    module_code="mesh"
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                api_logger.info(f"获取license信息成功, code={response_json.get('code')}")

    @allure.title("获取平台版本信息")
    @allure.description("GET /portal/api/v1/version - 验证能够获取平台版本信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_platform_version(self, portal_inner_service, api_cache, api_logger):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取平台版本信息"):
                response_json = portal_inner_service.get_platform_version()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                api_logger.info(f"获取平台版本信息成功, code={response_json.get('code')}")

    # ==================== 平台信息接口 ====================

    @allure.title("获取平台基本信息")
    @allure.description("GET /portal/api/v1/platform/baseInfo - 验证能够获取平台基本信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_platform_base_info(self, portal_inner_service, api_cache, api_logger):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取平台基本信息"):
                response_json = portal_inner_service.get_platform_base_info()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                api_logger.info(f"获取平台基本信息成功, code={response_json.get('code')}")

    @allure.title("获取平台开启模块信息")
    @allure.description("GET /portal/api/v1/platform/enableModules - 验证能够获取平台开启模块信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_platform_enable_modules(self, portal_inner_service, api_cache, api_logger):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取平台开启模块信息"):
                response_json = portal_inner_service.get_platform_enable_modules()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                api_logger.info(f"获取平台开启模块信息成功, code={response_json.get('code')}")

    # ==================== 全局配置接口 ====================

    @allure.title("全局配置接口查询")
    @allure.description("GET /portal/api/paasConfig - 验证能够获取全局配置")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_paas_config(self, portal_inner_service, api_cache, api_logger):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取全局配置"):
                response_json = portal_inner_service.get_paas_config()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                api_logger.info(f"获取全局配置成功, code={response_json.get('code')}")

    @allure.title("全局配置修改与还原")
    @allure.description("POST /portal/api/globalConfig/update - 验证能够修改全局配置并还原")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_global_config(self, portal_inner_service, api_cache, api_logger):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 POST 请求修改全局配置（禁用component模块）"):
                response_json = portal_inner_service.update_global_config(
                    modules=[{"moduleCode": "component", "enabled": False}]
                )

            with AllureHelper.step("验证修改响应"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                api_logger.info(f"修改全局配置成功(禁用component), code={response_json.get('code')}")

            with AllureHelper.step("发送 POST 请求还原全局配置（启用component模块）"):
                restore_response = portal_inner_service.update_global_config(
                    modules=[{"moduleCode": "component", "enabled": True}]
                )

            with AllureHelper.step("验证还原响应"):
                assert isinstance(restore_response, dict), "还原响应应该是字典类型"
                api_logger.info(f"还原全局配置成功(启用component), code={restore_response.get('code')}")

    # ==================== 授权与消息接口 ====================

    @allure.title("获取系统应用全量授权信息")
    @allure.description("GET /portal/api/getAuthInfo - 验证能够获取系统应用全量授权信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_auth_info(self, portal_inner_service, api_cache, api_logger):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求获取授权信息"):
                response_json = portal_inner_service.get_auth_info()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                api_logger.info(f"获取授权信息成功, code={response_json.get('code')}")

    @allure.title("站内消息发送")
    @allure.description("POST /portal/api/msg/send - 验证能够发送站内消息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_send_message(self, portal_inner_service, api_env, api_cache, api_logger):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 POST 请求发送站内消息"):
                response_json = portal_inner_service.send_message(
                    users=[api_env.get("portalUsername")],
                    content="切换失败，请关注手工处理"
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                api_logger.info(f"站内消息发送成功, code={response_json.get('code')}")

    # ==================== 域查询接口 ====================

    @allure.title("查询一级域列表")
    @allure.description("GET /portal/api/firstFieldInfo/list - 验证能够查询一级域列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_first_field_list(self, portal_inner_service, api_cache, api_logger):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 GET 请求查询一级域列表"):
                response_json = portal_inner_service.get_first_field_list()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert "data" in response_json, "响应应包含 data 字段"

            with AllureHelper.step("缓存一级域数据，供后续测试使用"):
                api_cache.set("first1", response_json["data"][0]["systemId"])
                api_logger.info(f"已缓存一级域Id: {response_json['data'][0]['moduleId']}")

    @allure.title("查询二级域列表")
    @allure.description("GET /portal/api/secondFieldInfo/list?systemId={first1} - 验证能够查询二级域列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_second_field_list(self, portal_inner_service, api_cache, api_logger):
        first1 = api_cache.get("first1")
        if not first1:
            pytest.skip("未获取到一级域 systemId，跳过二级域查询")

        api_logger.info(f"开始测试: 查询二级域列表, systemId={first1}")
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
                    api_logger.info(f"已缓存二级域moduleId: {module_id}")

    # ==================== 系统管理接口 ====================

    @allure.title("创建系统")
    @allure.description("POST /portal/api/system/add - 验证能够创建系统")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_system(self, portal_inner_service, api_env, api_cache, api_logger):
        first1 = api_cache.get("first1")
        module_id = api_cache.get("moduleId")
        if not first1 or not module_id:
            pytest.skip("未获取到一级域/二级域ID，跳过创建系统")

        api_logger.info(f"开始测试: 创建系统, first1={first1}, moduleId={module_id}")
        system = InnerSystemEntity(
            system_name="portal_inner_api_test_sys",
            system_code="portal_inner_api_test_sys",
            field_one=first1,
            field_two=module_id,
            create_id=api_env.get("portalUserId"),
            username=api_env.get("portalUsername"),
        )

        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 POST 请求创建系统"):
                response_json = portal_inner_service.create_system(system)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                api_logger.info(f"创建系统成功, code={response_json.get('code')}")

    @allure.title("获取系统全量数据")
    @allure.description("GET /portal/api/system/list - 验证能够获取系统全量数据并提取systemId")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_system_full_data(self, portal_inner_service, api_env, api_cache, api_logger):
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
                api_logger.info(f"已缓存systemId: {system_id}")

    # ==================== 应用管理接口 ====================

    @allure.title("创建应用")
    @allure.description("POST /portal/api/application/add - 验证能够创建应用")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_application(self, portal_inner_service, api_env, api_cache, api_logger):
        system_id = api_cache.get("systemId")
        if not system_id:
            pytest.skip("未获取到 systemId，跳过创建应用")

        api_logger.info(f"开始测试: 创建应用, systemId={system_id}")
        app = ApplicationEntity(
            app_name="portal_inner_api_test_app",
            app_code="portal_inner_api_test_app",
            app_type="web_type",
            system_id=system_id,
            create_id=api_env.get("portalUserId"),
            username=api_env.get("portalUsername"),
            workload_type="Deployment",
        )

        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 POST 请求创建应用"):
                response_json = portal_inner_service.create_application(app)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                api_logger.info(f"创建应用成功, code={response_json.get('code')}")

    @allure.title("获取应用全量数据")
    @allure.description("GET /portal/api/application/list - 验证能够获取应用全量数据并提取应用信息")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_application_full_data(self, portal_inner_service, api_env, api_cache, api_logger):
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
                        api_logger.info(f"已缓存appSourceId: {item.get('applicationSourceId')}")
                        break

    # ==================== 实例查询接口 ====================

    @allure.title("环境查询接口（全量查询）")
    @allure.description("POST /portal/api/all-instances - modelCode=ENVIRONMENT")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_all_instances_environment(self, portal_inner_service, api_cache, api_logger):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 POST 请求查询环境全量数据"):
                response_json = portal_inner_service.get_all_instances(model_code="ENVIRONMENT")

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                api_logger.info(f"环境全量查询成功, code={response_json.get('code')}")

    @allure.title("平面查询接口（全量查询）")
    @allure.description("POST /portal/api/all-instances - modelCode=PLANE")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_all_instances_plane(self, portal_inner_service, api_cache, api_logger):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 POST 请求查询平面全量数据"):
                response_json = portal_inner_service.get_all_instances(model_code="PLANE")

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                api_logger.info(f"平面全量查询成功, code={response_json.get('code')}")

    @allure.title("单元查询接口（全量查询）")
    @allure.description("POST /portal/api/all-instances - modelCode=CELL")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_all_instances_cell(self, portal_inner_service, api_cache, api_logger):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 POST 请求查询单元全量数据"):
                response_json = portal_inner_service.get_all_instances(model_code="CELL")

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                api_logger.info(f"单元全量查询成功, code={response_json.get('code')}")

    @allure.title("产品实例查询接口（全量查询）")
    @allure.description("POST /portal/api/all-instances - modelCode=PROD_INST")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_all_instances_prod_inst(self, portal_inner_service, api_cache, api_logger):
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 POST 请求查询产品实例全量数据"):
                response_json = portal_inner_service.get_all_instances(model_code="PROD_INST")

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert "data" in response_json, "响应应包含 data 字段"

            with AllureHelper.step("提取产品实例编码"):
                data = response_json.get("data", [])
                if len(data) > 2:
                    prod_inst_code = data[2].get("prodInstCode")
                    api_cache.set("prodInstCode", prod_inst_code)
                    api_logger.info(f"已缓存prodInstCode: {prod_inst_code}")

    @allure.title("按条件查询接口（产品实例）")
    @allure.description("POST /portal/api/list-instance-by-example - 按prodInstCode条件查询")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_instances_by_example(self, portal_inner_service, api_cache, api_logger):
        prod_inst_code = api_cache.get("prodInstCode")
        if not prod_inst_code:
            pytest.skip("未获取到 prodInstCode，跳过条件查询")

        api_logger.info(f"开始测试: 按条件查询产品实例, prodInstCode={prod_inst_code}")
        with AllureHelper.api_test(portal_inner_service):
            with AllureHelper.step("发送 POST 请求按条件查询产品实例"):
                response_json = portal_inner_service.get_instances_by_example(
                    model_code="PROD_INST",
                    prod_inst_code=prod_inst_code
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                api_logger.info(f"按条件查询产品实例成功, code={response_json.get('code')}")

    # ==================== 菜单权限管理接口 ====================

    @allure.title("菜单权限管理（新增/停用/启用/删除）")
    @allure.description("完整测试插件菜单的增删改流程：查询 -> 清理 -> 新增 -> 停用 -> 启用 -> 删除")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_menu_management(self, portal_inner_service, api_cache, api_logger):
        with AllureHelper.api_test(portal_inner_service):
            # Step 1: 查询菜单权限数据
            with AllureHelper.step("查询菜单权限数据"):
                response_json = portal_inner_service.get_menu_list(
                    source_code="observability", all_menu=1
                )
                assert isinstance(response_json, dict), "响应应该是字典类型"
                api_logger.info(f"查询菜单权限数据成功, code={response_json.get('code')}")

            # 检查是否已存在测试菜单
            data = response_json.get("data", [])
            existing_menu_id = None
            for item in data:
                if item.get("menuName") == "新增插件菜单测试":
                    existing_menu_id = item.get("menuId")
                    break

            # Step 2: 如果已存在则先删除
            if existing_menu_id:
                with AllureHelper.step("删除已存在的测试菜单"):
                    del_response = portal_inner_service.delete_menu(menu_ids=[str(existing_menu_id)])
                    assert isinstance(del_response, dict), "删除响应应该是字典类型"
                    api_logger.info(f"删除已存在的测试菜单成功, menuId={existing_menu_id}")

            # Step 3: 新增插件菜单
            menu = MenuEntity(
                menu_name="新增插件菜单测试",
                url_path="/iframe/plugin/t",
                plugin_url="/ec/test1111/tt",
                source_code="observability",
                roles=["platform_manager"],
                plugin_flag="observability",
            )

            with AllureHelper.step("新增插件菜单"):
                add_response = portal_inner_service.add_menu(menu)
                assert isinstance(add_response, dict), "新增响应应该是字典类型"
                api_logger.info(f"新增插件菜单成功, code={add_response.get('code')}")

            # 提取新创建的 menuId
            menu_id = None
            if add_response.get("data"):
                menu_id = add_response["data"].get("menuId")
            if not menu_id:
                # 重新查询获取
                query_resp = portal_inner_service.get_menu_list(source_code="observability", all_menu=1)
                for item in query_resp.get("data", []):
                    if item.get("menuName") == "新增插件菜单测试":
                        menu_id = item.get("menuId")
                        break

            assert menu_id is not None, "应成功获取新增菜单的menuId"
            api_logger.info(f"新增菜单menuId: {menu_id}")

            # Step 4: 停用插件菜单
            with AllureHelper.step("停用插件菜单"):
                disable_response = portal_inner_service.disable_menu(menu_ids=[str(menu_id)])
                assert isinstance(disable_response, dict), "停用响应应该是字典类型"
                api_logger.info(f"停用插件菜单成功, menuId={menu_id}")

            # Step 5: 启用插件菜单
            with AllureHelper.step("启用插件菜单"):
                enable_response = portal_inner_service.enable_menu(menu_ids=[str(menu_id)])
                assert isinstance(enable_response, dict), "启用响应应该是字典类型"
                api_logger.info(f"启用插件菜单成功, menuId={menu_id}")

            # Step 6: 删除插件菜单
            with AllureHelper.step("删除插件菜单"):
                delete_response = portal_inner_service.delete_menu(menu_ids=[str(menu_id)])
                assert isinstance(delete_response, dict), "删除响应应该是字典类型"
                api_logger.info(f"删除插件菜单成功, menuId={menu_id}")

    # ==================== 角色管理接口 ====================

    @allure.title("角色管理（创建/修改/删除）")
    @allure.description("完整测试角色CRUD流程：查询 -> 清理 -> 创建 -> 修改 -> 删除")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_role_management(self, portal_inner_service, api_env, api_cache, api_logger):
        role_code_0 = "autotest250711"
        api_logger.info(f"开始测试: 角色管理, roleCode={role_code_0}")

        with AllureHelper.api_test(portal_inner_service):
            # Step 1: 角色查询
            with AllureHelper.step("查询当前角色列表"):
                response_json = portal_inner_service.get_roles()
                assert isinstance(response_json, dict), "响应应该是字典类型"
                api_logger.info(f"查询角色列表成功, code={response_json.get('code')}")

            # 检查角色是否已存在
            data = response_json.get("data", [])
            role_exists = any(
                item.get("roleCode") == role_code_0 for item in data
            )

            # Step 2: 如果角色已存在则先删除
            if role_exists:
                with AllureHelper.step(f"删除已存在的角色: {role_code_0}"):
                    del_response = portal_inner_service.delete_role(role_code=role_code_0)
                    assert isinstance(del_response, dict), "删除响应应该是字典类型"
                    api_logger.info(f"删除已存在角色成功, roleCode={role_code_0}")

            # Step 3: 创建角色
            role = RoleEntity(
                role_name=role_code_0,
                role_code=role_code_0,
                role_type=1,
                has_edit=1,
            )

            with AllureHelper.step(f"创建角色: {role_code_0}"):
                create_response = portal_inner_service.create_role(role)
                assert isinstance(create_response, dict), "创建响应应该是字典类型"
                api_logger.info(f"创建角色成功, roleCode={role_code_0}")

            # Step 4: 修改角色
            updated_role = RoleEntity(
                role_name=role_code_0,
                role_code=role_code_0,
                role_desc=None,
                role_type=2,
                has_edit=1,
            )

            with AllureHelper.step(f"修改角色类型为2: {role_code_0}"):
                update_response = portal_inner_service.update_role(updated_role)
                assert isinstance(update_response, dict), "修改响应应该是字典类型"
                api_logger.info(f"修改角色成功, roleCode={role_code_0}, roleType=2")

            # Step 5: 删除角色（清理）
            with AllureHelper.step(f"删除角色: {role_code_0}"):
                delete_response = portal_inner_service.delete_role(role_code=role_code_0)
                assert isinstance(delete_response, dict), "删除响应应该是字典类型"
                api_logger.info(f"删除角色成功(清理), roleCode={role_code_0}")

    # ==================== 用户/租户/角色绑定管理接口 ====================

    @allure.title("用户-租户-角色绑定全流程")
    @allure.description(
        "完整测试用户租户角色管理流程：\n"
        "查询用户 -> 清理旧数据 -> 创建角色 -> 创建租户 -> 创建用户 -> "
        "API授权 -> API解除授权 -> 查询验证 -> 用户租户绑定 -> 角色绑定"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_user_tenant_role_bindflow(self, portal_inner_service, api_env, api_cache, api_logger):
        username2 = "test0930"
        rolecode2 = "autorole250711"
        tenantcode2 = "autotenant250711"
        module_name = "portal"
        api_logger.info(f"开始测试: 用户-租户-角色绑定全流程, username={username2}, role={rolecode2}, tenant={tenantcode2}")

        with AllureHelper.api_test(portal_inner_service):
            # Step 1: 查询用户
            with AllureHelper.step(f"查询用户: {username2}"):
                user_response = portal_inner_service.get_user_by_username(username=username2)
                assert isinstance(user_response, dict), "响应应该是字典类型"
                api_logger.info(f"查询用户成功, username={username2}")

            # 判断用户是否存在及其绑定状态
            user_data = user_response.get("data")
            user_exists = user_data is not None and user_data.get("userName") == username2

            if user_exists:
                api_logger.info(f"用户 {username2} 已存在, 开始清理旧数据")
                # 获取当前用户绑定信息
                tenant_list = user_data.get("tenantList", [])
                current_role_code = None
                current_tenant_code = None
                if tenant_list:
                    current_tenant_code = tenant_list[0].get("tenantCode")
                    role_list = tenant_list[0].get("roleList", [])
                    if role_list:
                        current_role_code = role_list[0].get("roleCode")

                # 如果已绑定，执行解绑清理
                if current_role_code and current_tenant_code:
                    with AllureHelper.step("解绑用户已有的租户角色关系"):
                        portal_inner_service.unbind_user_tenant_role(
                            username=username2,
                            tenant_code=current_tenant_code,
                            role_code=current_role_code
                        )
                        api_logger.info(f"解绑用户租户角色关系成功, tenant={current_tenant_code}, role={current_role_code}")

                    with AllureHelper.step("解绑用户已有的租户关系"):
                        portal_inner_service.unbind_user_tenant(
                            username=username2,
                            tenant_code=current_tenant_code
                        )
                        api_logger.info(f"解绑用户租户关系成功, tenant={current_tenant_code}")

                # 删除旧租户（如果是测试租户）
                with AllureHelper.step(f"删除租户: {tenantcode2}"):
                    portal_inner_service.delete_tenant(tenant_code=tenantcode2)
                    api_logger.info(f"删除租户成功, tenantCode={tenantcode2}")

                # 删除旧角色
                with AllureHelper.step(f"删除角色: {rolecode2}"):
                    portal_inner_service.delete_role(role_code=rolecode2)
                    api_logger.info(f"删除角色成功, roleCode={rolecode2}")

                # 删除旧用户
                with AllureHelper.step(f"删除用户: {username2}"):
                    portal_inner_service.delete_user(username=username2)
                    api_logger.info(f"删除用户成功, username={username2}")

            # Step 2: 创建角色
            role = RoleEntity(
                role_name=rolecode2,
                role_code=rolecode2,
                role_desc=None,
                role_type=2,
                has_edit=1,
                create_id=None,
            )

            with AllureHelper.step(f"创建角色: {rolecode2}"):
                create_role_resp = portal_inner_service.create_role(role)
                assert isinstance(create_role_resp, dict), "创建角色响应应该是字典类型"
                api_logger.info(f"创建角色成功, roleCode={rolecode2}")

            # Step 3: 创建租户
            tenant = TenantEntity(
                tenant_code=tenantcode2,
                tenant_name=tenantcode2,
                tenant_lever=2,
                tenant_parent_id=1,
                tenant_area=1,
                dept_code="b39a802ef7834b17b3cd9e76dd6e20231023",
                source_code="plugin-center",
                create_user_id=1,
            )

            with AllureHelper.step(f"创建租户: {tenantcode2}"):
                create_tenant_resp = portal_inner_service.create_tenant(tenant)
                assert isinstance(create_tenant_resp, dict), "创建租户响应应该是字典类型"
                api_logger.info(f"创建租户成功, tenantCode={tenantcode2}")

            # Step 4: 创建用户
            user = InnerUserEntity(
                username="xeqHSRNJnN0tBjWTFuA+Qg==",
                alias="测试0930",
                phone="qrlAscZatvSyYi1Uh49cEw==",
                email="ZSOS5ICOFj+hZj72q53jIQ==",
                tenant_code=tenantcode2,
                role_code=rolecode2,
                create_id=1,
            )

            with AllureHelper.step(f"创建用户: {username2}"):
                create_user_resp = portal_inner_service.create_user(user)
                assert isinstance(create_user_resp, dict), "创建用户响应应该是字典类型"
                api_logger.info(f"创建用户成功, username={username2}")

            # Step 5: API列表查询
            with AllureHelper.step("查询API列表"):
                api_list_resp = portal_inner_service.get_api_list(module_name=module_name)
                assert isinstance(api_list_resp, dict), "API列表响应应该是字典类型"
                api_logger.info(f"查询API列表成功, moduleName={module_name}")

            # 提取API信息
            api_data = api_list_resp.get("data", [])
            api_list_for_auth = []
            if len(api_data) >= 2:
                api_list_for_auth = [
                    {"apiId": str(api_data[0].get("id")), "authorizedMethod": api_data[0].get("method")},
                    {"apiId": str(api_data[1].get("id")), "authorizedMethod": api_data[0].get("method")},
                ]

            # Step 6: API批量授权
            if api_list_for_auth:
                with AllureHelper.step("API批量授权"):
                    auth_resp = portal_inner_service.api_bulk_authorization(
                        role_code=rolecode2,
                        api_list=api_list_for_auth
                    )
                    assert isinstance(auth_resp, dict), "授权响应应该是字典类型"
                    api_logger.info(f"API批量授权成功, roleCode={rolecode2}, apiCount={len(api_list_for_auth)}")

                # Step 7: API批量解除授权
                with AllureHelper.step("API批量解除授权"):
                    unauth_resp = portal_inner_service.api_bulk_reauthorization(
                        role_code=rolecode2,
                        api_list=api_list_for_auth
                    )
                    assert isinstance(unauth_resp, dict), "解除授权响应应该是字典类型"
                    api_logger.info(f"API批量解除授权成功, roleCode={rolecode2}")

            # Step 8: 查询验证
            with AllureHelper.step(f"查询用户: {username2}"):
                query_user_resp = portal_inner_service.get_user_by_username(username=username2)
                assert isinstance(query_user_resp, dict), "查询用户响应应该是字典类型"
                api_logger.info(f"查询验证用户成功, username={username2}")

            with AllureHelper.step(f"查询租户: {tenantcode2}"):
                query_tenant_resp = portal_inner_service.get_tenant(tenant_code=tenantcode2)
                assert isinstance(query_tenant_resp, dict), "查询租户响应应该是字典类型"
                api_logger.info(f"查询验证租户成功, tenantCode={tenantcode2}")

            with AllureHelper.step("查询角色列表验证角色存在"):
                query_roles_resp = portal_inner_service.get_roles()
                assert isinstance(query_roles_resp, dict), "查询角色响应应该是字典类型"
                roles_data = query_roles_resp.get("data", [])
                role_exists = any(
                    item.get("roleCode") == rolecode2 for item in roles_data
                )
                assert role_exists, f"角色 {rolecode2} 应该存在于角色列表中"
                api_logger.info(f"查询验证角色存在成功, roleCode={rolecode2}")

            # Step 9: 用户租户绑定
            with AllureHelper.step(f"用户 {username2} 绑定租户 {tenantcode2}"):
                bind_tenant_resp = portal_inner_service.bind_user_tenant(
                    username=username2, tenant_code=tenantcode2
                )
                assert isinstance(bind_tenant_resp, dict), "绑定租户响应应该是字典类型"
                api_logger.info(f"用户租户绑定成功, username={username2}, tenant={tenantcode2}")

            # Step 10: 用户租户角色绑定
            with AllureHelper.step(f"用户 {username2} 绑定租户 {tenantcode2} 角色 {rolecode2}"):
                bind_role_resp = portal_inner_service.bind_user_tenant_role(
                    username=username2, tenant_code=tenantcode2, role_code=rolecode2
                )
                assert isinstance(bind_role_resp, dict), "绑定角色响应应该是字典类型"
                api_logger.info(f"用户租户角色绑定成功, username={username2}, tenant={tenantcode2}, role={rolecode2}")

"""
Portal OpenAPI 接口测试脚本

基于 JMeter portal-openapi.jmx 转换而来
完整覆盖门户 OpenAPI 的所有接口测试逻辑，包含：
- 一级域/二级域查询
- 集群平面单元 CRUD
- 租户绑定集群
- 用户相关操作（同步、绑定租户、绑定角色）
- 系统 CRUD 及资源配额管理
- 应用 CRUD
- 用户系统/应用授权

特性：
- 无论断言成功/失败，Allure 报告中均展示完整的请求和响应信息
"""
from typing import Dict

import allure
import pytest

from base.api.fixtures import api_cache
from base.api.services.portal_open_service import (
    PanJiPortalOpenService,
    PortalUserEntity,
    ClusterPlaneEntity,
    OpenSystemEntity,
    BasicCodeEntity
)
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@allure.feature("磐基门户OpenAPI服务")
@allure.story("Portal OpenAPI 全链路接口测试")
class TestPortalOpenAPI:
    """
    Portal OpenAPI 全链路接口测试

    测试流程按 JMeter 脚本顺序执行：
    1. 获取Token
    2. 获取一级域/二级域
    3. 集群平面单元 CRUD
    4. 租户绑定集群
    5. 查询用户绑定租户信息
    6. 获取菜单权限
    7. 同步用户、绑定租户、绑定角色
    8. 查询/创建系统 → 资源配额分配 → 创建应用
    9. 更新系统/应用 → 查询应用 → 授权
    10. 清理：删除应用 → 释放配额 → 删除系统
    """

    TENANT = "tenant_admin"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        """每个用例前自动切换到本测试类声明的租户 token。"""
        get_token(self.TENANT)

    @pytest.fixture(scope="class")
    def portal_service(self, api_env, api_logger):
        """创建 Portal OpenAPI 服务实例"""
        service = PanJiPortalOpenService(
            base_url=api_env.get("api_base_url"),
            logger=api_logger
        )
        yield service
        service.close()

    # ==================== 域信息查询 ====================

    @allure.title("获取一级域")
    @allure.description("获取一级域列表数据")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_first_field_info(self, portal_service, api_cache, api_logger):
        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 GET 请求获取一级域"):
                response_json = portal_service.get_first_field_info()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 0, "响应Code应等于0"
                assert len(response_json["data"]) > 1, "一级域数据应不少于2条"

            with AllureHelper.step("缓存一级域id（第4条数据的systemId）"):
                api_cache.set("firstFieldId", response_json["data"][0]["systemId"])
                api_logger.info(f"已缓存一级域Id: {response_json['data'][0]['systemId']}")

    @allure.title("获取二级域")
    @allure.description("获取二级域列表数据")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_second_field_info(self, portal_service, api_cache, api_logger):
        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 GET 请求获取二级域"):
                response_json = portal_service.get_second_field_info()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 0, "响应Code应等于0"
                assert len(response_json["data"]) > 1, "二级域数据应不少于2条"

            with AllureHelper.step("缓存二级域id（第5条数据的moduleId）"):
                api_cache.set("secondFieldId", response_json["data"][0]["moduleId"])
                api_logger.info(f"已缓存二级域Id: {response_json['data'][0]['moduleId']}")

    # ==================== 集群平面单元 CRUD ====================

    @allure.title("新增集群平面单元")
    @allure.description("创建一个新的集群平面单元")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_cluster_plane(self, portal_service, api_env):
        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 POST 请求新增集群平面单元"):
                cluster = ClusterPlaneEntity(prod_inst_name=api_env.get("prod_inst_name"))
                response_json = portal_service.create_cluster_plane(cluster)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 2000, "响应Code应等于2000"

    @allure.title("查询集群平面单元")
    @allure.description("根据prodInstName查询集群平面单元并缓存instanceId")
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_cluster_plane(self, portal_service, api_env, api_cache, api_logger):
        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 GET 请求查询集群平面单元"):
                cluster = ClusterPlaneEntity(prod_inst_name=api_env.get("prod_inst_name"))
                response_json = portal_service.query_cluster_plane(cluster)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 2000, "响应Code应等于2000"

            with AllureHelper.step("缓存instanceId"):
                instance_id = response_json["data"]["list"][0]["instanceId"]
                api_cache.set("instanceId", instance_id)
                api_logger.info(f"已缓存instanceId: {instance_id}")

    @allure.title("修改集群平面单元")
    @allure.description("修改已创建的集群平面单元")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_cluster_plane(self, portal_service, api_env, api_cache):
        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 PATCH 请求修改集群平面单元"):
                cluster = ClusterPlaneEntity(
                    prod_inst_name=api_env.get("prod_inst_name"),
                    instance_id=api_cache.get("instanceId")
                )
                response_json = portal_service.update_cluster_plane(cluster)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 2000, "响应Code应等于2000"

    @allure.title("删除集群平面单元")
    @allure.description("删除已创建的集群平面单元")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_cluster_plane(self, portal_service, api_cache):
        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 DELETE 请求删除集群平面单元"):
                cluster = ClusterPlaneEntity(instance_id=api_cache.get("instanceId"))
                response_json = portal_service.delete_cluster_plane(cluster)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 2000, "响应Code应等于2000"

    # ==================== 租户集群绑定 ====================

    @allure.title("查询绑定集群信息")
    @allure.description("根据租户、环境查询绑定集群信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_bind_cluster_list(self, portal_service):
        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 GET 请求查询绑定集群信息"):
                response_json = portal_service.query_bind_cluster_list()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 0, "响应Code应等于0"

    @allure.title("租户绑定集群平面单元")
    @allure.description("将租户绑定到指定集群平面单元")
    @allure.severity(allure.severity_level.NORMAL)
    def test_tenant_bind_cluster(self, portal_service):
        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 POST 请求绑定租户到集群"):
                response_json = portal_service.tenant_bind_cluster()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 2000, "响应Code应等于2000"

    # ==================== 用户与租户操作 ====================

    @allure.title("根据用户名查询绑定的租户信息")
    @allure.description("查询指定用户绑定的租户信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_tenant_info_by_username(self, portal_service, api_env):
        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 GET 请求查询绑定的租户信息"):
                username = api_env.get("query_user_name")
                response_json = portal_service.query_tenant_info_by_username(username)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 2000, "响应Code应等于2000"

    @allure.title("获取菜单权限数据")
    @allure.description("获取系统菜单权限列表数据")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_menu_permission_data(self, portal_service):
        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 GET 请求获取菜单权限数据"):
                response_json = portal_service.get_menu_permission_data()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 2000, "响应Code应等于2000"

    @allure.title("同步用户")
    @allure.description("同步外部用户信息到门户系统")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sync_user(self, portal_service, api_env):
        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 POST 请求同步用户"):
                user_info = PortalUserEntity(
                    phone=api_env.get("sync_phone"),
                    email=api_env.get("sync_email"),
                    username=api_env.get("sync_username")
                )
                response_json = portal_service.sync_user_api(user_info)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] in [0, -1], "响应Code应等于0或-1"

    @allure.title("绑定租户")
    @allure.description("将用户绑定到指定租户")
    @allure.severity(allure.severity_level.NORMAL)
    def test_user_bind_tenant(self, portal_service, api_env):
        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 POST 请求绑定租户"):
                user_info = PortalUserEntity(
                    user_id=api_env.get("user_id"),
                    username=api_env.get("query_user_name")
                )
                response_json = portal_service.user_bind_tenant(user_info)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 0, "响应Code应等于0"

    @allure.title("绑定角色")
    @allure.description("将用户绑定到指定角色")
    @allure.severity(allure.severity_level.NORMAL)
    def test_user_bind_role(self, portal_service, api_env):
        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 POST 请求绑定角色"):
                user_info = PortalUserEntity(
                    user_id=api_env.get("user_id"),
                    username=api_env.get("query_user_name")
                )
                response_json = portal_service.user_bind_role(user_info)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 0, "响应Code应等于0"

    # ==================== 系统管理 ====================

    @allure.title("查询系统")
    @allure.description("查询系统列表，判断目标系统是否已存在")
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_system(self, portal_service, api_env, api_cache, api_logger):
        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 POST 请求查询系统"):
                system_code = api_env.get("portal_system_code")
                response_json = portal_service.query_system(system_code)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 2000, "响应Code应等于2000"

            with AllureHelper.step("判断系统是否已存在并缓存"):
                data_list = response_json["data"]["list"]
                system_exists = False
                for item in data_list:
                    if item["systemCode"] == system_code:
                        system_exists = True
                        api_cache.set("systemId1", item["systemId"])
                        api_logger.info(f"系统已存在，缓存systemId1: {item['systemId']}")
                        break
                api_cache.set("systemExists", system_exists)

    @allure.title("创建系统")
    @allure.description("当系统不存在时创建新系统")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_system(self, portal_service, api_env, api_cache, api_logger):
        if api_cache.get("systemExists"):
            pytest.skip("系统已存在，跳过创建")

        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 POST 请求创建系统"):
                system = OpenSystemEntity(
                    system_name=api_env.get("portal_system_code"),
                    system_code=api_env.get("portal_system_code"),
                    system_desc=api_env.get("portal_system_code"),
                    field_one=api_cache.get("firstFieldId"),
                    field_two=api_cache.get("secondFieldId"),
                    create_id=api_env.get("user_id"),
                    username=api_env.get("query_user_name")
                )
                response_json = portal_service.create_system(system)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 2000, "响应Code应等于2000"

            with AllureHelper.step("缓存创建结果"):
                api_cache.set("createSystemCode", response_json["code"])
                api_logger.info(f"系统创建成功，code: {response_json['code']}")

    @allure.title("系统资源配额分配")
    @allure.description("为新创建的系统分配资源配额（CPU/内存）")
    @allure.severity(allure.severity_level.NORMAL)
    def test_system_resource_allocation(self, portal_service, api_env, api_cache):
        if api_cache.get("systemExists"):
            pytest.skip("系统已存在，跳过资源配额分配")

        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 POST 请求分配系统资源配额"):
                code_entity = BasicCodeEntity(
                    cell_code=api_env.get("cell_code"),
                    tenant_code=api_env.get("tenant_code"),
                    system_code=api_env.get("portal_system_code")
                )
                response_json = portal_service.system_resource_allocation(
                    username=api_env.get("query_user_name"),
                    code_list=code_entity
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"

    @allure.title("创建后查询系统ID")
    @allure.description("创建系统后再次查询以获取systemId")
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_system_id_after_create(self, portal_service, api_env, api_cache, api_logger):
        if api_cache.get("systemExists"):
            pytest.skip("系统已存在，systemId已缓存")

        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 POST 请求查询系统"):
                system_code = api_env.get("portal_system_code")
                response_json = portal_service.query_system(system_code)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 2000, "响应Code应等于2000"

            with AllureHelper.step("缓存systemId"):
                data_list = response_json["data"]["list"]
                for item in data_list:
                    if item["systemCode"] == system_code:
                        api_cache.set("systemId1", item["systemId"])
                        api_logger.info(f"已缓存systemId1: {item['systemId']}")
                        break

    # ==================== 应用管理 ====================

    @allure.title("创建应用")
    @allure.description("在系统下创建新应用")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_application(self, portal_service, api_env, api_cache, api_logger):
        if api_cache.get("systemExists"):
            pytest.skip("系统已存在，跳过创建应用")

        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 POST 请求创建应用"):
                response_json = portal_service.create_application(
                    app_code=api_env.get("portal_app_code"),
                    app_name=api_env.get("portal_app_code"),
                    app_type=api_env.get("portal_app_type", "web_type"),
                    workload_type=api_env.get("portal_workload_type", "Deployment"),
                    system_id=api_cache.get("systemId1")
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 2000, "响应Code应等于2000"

            with AllureHelper.step("缓存applicationSourceId"):
                app_id = response_json["data"]["applicationSourceId"]
                api_cache.set("applicationSourceId", app_id)
                api_logger.info(f"已缓存applicationSourceId: {app_id}")

    @allure.title("更新系统")
    @allure.description("更新系统信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_system(self, portal_service, api_env, api_cache):
        system_id = api_cache.get("systemId1")
        if not system_id:
            pytest.skip("未获取到systemId1，跳过更新系统")

        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 POST 请求更新系统"):
                system = OpenSystemEntity(
                    system_id=system_id,
                    system_name=api_env.get("portal_system_code"),
                    system_code=api_env.get("portal_system_code"),
                    create_id=api_env.get("user_id"),
                    username=api_env.get("query_user_name")
                )
                response_json = portal_service.update_system(system)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 2000, "响应Code应等于2000"

    @allure.title("更新应用")
    @allure.description("更新应用信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_application(self, portal_service, api_cache):
        app_id = api_cache.get("applicationSourceId")
        if not app_id:
            pytest.skip("未获取到applicationSourceId，跳过更新应用")

        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 POST 请求更新应用"):
                response_json = portal_service.update_application(
                    app_id=app_id,
                    system_id=api_cache.get("systemId1")
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 2000, "响应Code应等于2000"

    @allure.title("查询应用列表")
    @allure.description("分页查询应用列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_application_list(self, portal_service, api_env, api_cache, api_logger):
        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 POST 请求查询应用列表"):
                app_code = api_env.get("portal_app_code")
                response_json = portal_service.query_application_list(app_code)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 2000, "响应Code应等于2000"

            with AllureHelper.step("缓存应用信息（系统已存在场景）"):
                if api_cache.get("systemExists"):
                    data_list = response_json["data"]["list"]
                    for item in data_list:
                        if item.get("applicationSourceCode") == app_code:
                            api_cache.set("applicationSourceId", item["applicationSourceId"])
                            api_logger.info(f"已缓存applicationSourceId: {item['applicationSourceId']}")
                            break

    @allure.title("查看应用详细信息")
    @allure.description("根据applicationSourceId查看应用详情")
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_application_detail(self, portal_service, api_cache):
        app_id = api_cache.get("applicationSourceId")
        if not app_id:
            pytest.skip("未获取到applicationSourceId，跳过查看应用详情")

        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 GET 请求查看应用详情"):
                response_json = portal_service.query_application_detail(app_id=app_id)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 2000, "响应Code应等于2000"

    # ==================== 授权管理 ====================

    @allure.title("用户系统授权")
    @allure.description("批量为用户授权系统访问权限")
    @allure.severity(allure.severity_level.NORMAL)
    def test_user_system_authorization(self, portal_service, api_env, api_cache):
        system_id = api_cache.get("systemId1")
        if not system_id:
            pytest.skip("未获取到systemId1，跳过用户系统授权")

        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 POST 请求进行用户系统授权"):
                user_id_list = ["200685", api_env.get("user_id")]
                response_json = portal_service.user_system_authorization(
                    user_id_list=user_id_list,
                    system_id_list=[system_id]
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 2000, "响应Code应等于2000"

    @allure.title("用户应用授权")
    @allure.description("批量为用户授权应用访问权限")
    @allure.severity(allure.severity_level.NORMAL)
    def test_user_application_authorization(self, portal_service, api_env, api_cache):
        app_id = api_cache.get("applicationSourceId")
        if not app_id:
            pytest.skip("未获取到applicationSourceId，跳过用户应用授权")

        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 POST 请求进行用户应用授权"):
                user_id_list = [api_env.get("user_id"), "200685"]
                response_json = portal_service.user_application_authorization(
                    user_id_list=user_id_list,
                    application_id_list=[app_id]
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 2000, "响应Code应等于2000"

    # ==================== 资源配额管理 ====================

    @allure.title("系统资源配额详情")
    @allure.description("查询系统资源配额详情")
    @allure.severity(allure.severity_level.NORMAL)
    def test_system_resource_quota_detail(self, portal_service, api_env, api_cache, api_logger):
        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 GET 请求查询系统资源配额详情"):
                code_entity = BasicCodeEntity(
                    cell_code=api_env.get("cell_code"),
                    tenant_code=api_env.get("tenant_code"),
                    system_code=api_env.get("portal_system_code")
                )
                response_json = portal_service.system_resource_quota_detail(code_entity)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 2000, "响应Code应等于2000"

            with AllureHelper.step("缓存cpuTotal"):
                if response_json.get("data"):
                    cpu_total = response_json["data"].get("cpuTotal", 0)
                    api_cache.set("cpuTotal", cpu_total)
                    api_logger.info(f"已缓存cpuTotal: {cpu_total}")

    # ==================== 清理：删除资源 ====================

    @allure.title("系统资源配额释放")
    @allure.description("释放/删除系统资源配额")
    @allure.severity(allure.severity_level.NORMAL)
    def test_system_resource_quota_remove(self, portal_service, api_env, api_cache):
        if api_cache.get("systemExists"):
            pytest.skip("系统已存在，跳过配额释放")

        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 POST 请求释放系统资源配额"):
                code_entity = BasicCodeEntity(
                    cell_code=api_env.get("cell_code"),
                    tenant_code=api_env.get("tenant_code"),
                    system_code=api_env.get("portal_system_code")
                )
                response_json = portal_service.system_resource_quota_remove(code_entity)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"

    @allure.title("删除应用")
    @allure.description("删除已创建的应用")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_application(self, portal_service, api_cache):
        if api_cache.get("systemExists"):
            pytest.skip("系统已存在，跳过删除应用")
        app_id = api_cache.get("applicationSourceId")
        if not app_id:
            pytest.skip("未获取到applicationSourceId，跳过删除应用")

        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 POST 请求删除应用"):
                response_json = portal_service.delete_application(app_id=app_id)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 2000, "响应Code应等于2000"

    @allure.title("删除系统")
    @allure.description("删除已创建的系统")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_system(self, portal_service, api_env, api_cache):
        if api_cache.get("systemExists"):
            pytest.skip("系统已存在，跳过删除系统")
        system_id = api_cache.get("systemId1")
        system_code = api_env.get("portal_system_code")
        if not system_id:
            pytest.skip("未获取到systemId1，跳过删除系统")

        with AllureHelper.api_test(portal_service):
            with AllureHelper.step("发送 POST 请求删除系统"):
                response_json = portal_service.delete_system(
                    system_id=system_id,
                    system_code=system_code
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 2000, "响应Code应等于2000"

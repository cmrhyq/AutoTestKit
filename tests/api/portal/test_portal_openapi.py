"""
Portal OpenAPI 接口测试脚本
"""
from typing import Dict

import allure
import pytest

from base.api.services.portal_open_service import (
    BasicCodeEntity,
    ClusterPlaneEntity,
    OpenSystemEntity,
    PortalOpenService,
    PortalUserEntity,
)
from core.constants import ApiCode, Tenant
from core.log import get_logger
from core.reporting.allure_helper import AllureHelper

logger = get_logger(__name__)

@pytest.mark.api
@pytest.mark.portal
@allure.epic("磐基API自动化测试")
@allure.feature("磐基门户OpenAPI接口")
@allure.story("Portal OpenAPI 接口")
class TestPortalOpenAPI:

    TENANT = Tenant.ADMIN
    SYSTEM_CODE = "portal_open_api_test_sys"
    APP_CODE = "portal_open_api_test_app"

    @pytest.fixture(scope="class")
    def portal_open_service(self, service_factory):
        with service_factory(PortalOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 Portal OpenAPI 测试所需的公共参数。"""
        return {
            "portal_username": api_env.get("portalUsername"),
            "portal_user_id": api_env.get("portalUserId"),
            "cell_code": api_env.get("cellCode"),
            "tenant_code": api_env.get("tenantCode"),
            "prod_inst_name": api_env.get("prodInstName"),
            "sync_phone": api_env.get("syncPhone"),
            "sync_email": api_env.get("syncEmail"),
            "sync_username": api_env.get("syncUsername"),
        }

    # ==================== 域信息查询 ====================

    @pytest.mark.dependency()
    @allure.title("获取一级域")
    @allure.description("获取一级域列表数据")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_first_field_info(self, portal_open_service, api_cache):
        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 GET 请求获取一级域"):
                response_json = portal_open_service.get_first_field_info()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 0, "响应Code应等于0"
                assert len(response_json["data"]) > 1, "一级域数据应不少于2条"

            with AllureHelper.step("缓存一级域id"):
                api_cache.set("firstFieldId", response_json["data"][0]["systemId"])
                logger.info(f"已缓存一级域Id: {response_json['data'][0]['systemId']}")

    @pytest.mark.dependency()
    @allure.title("获取二级域")
    @allure.description("获取二级域列表数据")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_second_field_info(self, portal_open_service, api_cache):
        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 GET 请求获取二级域"):
                response_json = portal_open_service.get_second_field_info()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 0, "响应Code应等于0"
                assert len(response_json["data"]) > 1, "二级域数据应不少于2条"

            with AllureHelper.step("缓存二级域id"):
                api_cache.set("secondFieldId", response_json["data"][0]["moduleId"])
                logger.info(f"已缓存二级域Id: {response_json['data'][0]['moduleId']}")

    # ==================== 集群平面单元 CRUD ====================

    @allure.title("新增集群平面单元")
    @allure.description("创建一个新的集群平面单元")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_cluster_plane(self, portal_open_service, public_params):
        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 POST 请求新增集群平面单元"):
                cluster = ClusterPlaneEntity(prod_inst_name=public_params["prod_inst_name"])
                response_json = portal_open_service.create_cluster_plane(cluster)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == ApiCode.SUCCESS, "响应Code应等于 ApiCode.SUCCESS"

    @allure.title("查询集群平面单元")
    @allure.description("根据prodInstName查询集群平面单元并缓存instanceId")
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_cluster_plane(self, portal_open_service, public_params, api_cache):
        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 GET 请求查询集群平面单元"):
                cluster = ClusterPlaneEntity(prod_inst_name=public_params["prod_inst_name"])
                response_json = portal_open_service.query_cluster_plane(cluster)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == ApiCode.SUCCESS, "响应Code应等于 ApiCode.SUCCESS"

            with AllureHelper.step("缓存instanceId"):
                instance_id = response_json["data"]["list"][0]["instanceId"]
                api_cache.set("instanceId", instance_id)
                logger.info(f"已缓存instanceId: {instance_id}")

    @allure.title("修改集群平面单元")
    @allure.description("修改已创建的集群平面单元")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_cluster_plane(self, portal_open_service, public_params, api_cache):
        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 PATCH 请求修改集群平面单元"):
                cluster = ClusterPlaneEntity(
                    prod_inst_name=public_params["prod_inst_name"],
                    instance_id=api_cache.get("instanceId")
                )
                response_json = portal_open_service.update_cluster_plane(cluster)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == ApiCode.SUCCESS, "响应Code应等于 ApiCode.SUCCESS"

    @allure.title("删除集群平面单元")
    @allure.description("删除已创建的集群平面单元")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_cluster_plane(self, portal_open_service, api_cache):
        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 DELETE 请求删除集群平面单元"):
                cluster = ClusterPlaneEntity(instance_id=api_cache.get("instanceId"))
                response_json = portal_open_service.delete_cluster_plane(cluster)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == ApiCode.SUCCESS, "响应Code应等于 ApiCode.SUCCESS"

    # ==================== 租户集群绑定 ====================

    @allure.title("查询绑定集群信息")
    @allure.description("根据租户、环境查询绑定集群信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_bind_cluster_list(self, portal_open_service):
        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 GET 请求查询绑定集群信息"):
                response_json = portal_open_service.query_bind_cluster_list()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 0, "响应Code应等于0"

    @allure.title("租户绑定集群平面单元")
    @allure.description("将租户绑定到指定集群平面单元")
    @allure.severity(allure.severity_level.NORMAL)
    def test_tenant_bind_cluster(self, portal_open_service):
        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 POST 请求绑定租户到集群"):
                response_json = portal_open_service.tenant_bind_cluster()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == ApiCode.SUCCESS, "响应Code应等于 ApiCode.SUCCESS"

    # ==================== 用户与租户操作 ====================

    @allure.title("根据用户名查询绑定的租户信息")
    @allure.description("查询指定用户绑定的租户信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_tenant_info_by_username(self, portal_open_service, public_params):
        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 GET 请求查询绑定的租户信息"):
                username = public_params["portal_username"]
                response_json = portal_open_service.query_tenant_info_by_username(username)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == ApiCode.SUCCESS, "响应Code应等于 ApiCode.SUCCESS"

    @allure.title("获取菜单权限数据")
    @allure.description("获取系统菜单权限列表数据")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_menu_permission_data(self, portal_open_service):
        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 GET 请求获取菜单权限数据"):
                response_json = portal_open_service.get_menu_permission_data()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == ApiCode.SUCCESS, "响应Code应等于 ApiCode.SUCCESS"

    @allure.title("同步用户")
    @allure.description("同步外部用户信息到门户系统")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sync_user(self, portal_open_service, public_params):
        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 POST 请求同步用户"):
                user_info = PortalUserEntity(
                    phone=public_params["sync_phone"],
                    email=public_params["sync_email"],
                    username=public_params["sync_username"]
                )
                response_json = portal_open_service.sync_user_api(user_info)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] in [0, -1], "响应Code应等于0或-1"

    @allure.title("绑定租户")
    @allure.description("将用户绑定到指定租户")
    @allure.severity(allure.severity_level.NORMAL)
    def test_user_bind_tenant(self, portal_open_service, public_params):
        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 POST 请求绑定租户"):
                user_info = PortalUserEntity(
                    user_id=public_params["portal_user_id"],
                    username=public_params["portal_username"]
                )
                response_json = portal_open_service.user_bind_tenant(user_info)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 0, "响应Code应等于0"

    @allure.title("绑定角色")
    @allure.description("将用户绑定到指定角色")
    @allure.severity(allure.severity_level.NORMAL)
    def test_user_bind_role(self, portal_open_service, public_params):
        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 POST 请求绑定角色"):
                user_info = PortalUserEntity(
                    user_id=public_params["portal_user_id"],
                    username=public_params["portal_username"]
                )
                response_json = portal_open_service.user_bind_role(user_info)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == 0, "响应Code应等于0"

    # ==================== 系统管理（创建路径）====================

    @allure.title("创建系统")
    @allure.description("创建新系统（cleanup fixture 已保证系统不存在）")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_system(self, portal_open_service, public_params, api_cache):
        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 POST 请求创建系统"):
                system = OpenSystemEntity(
                    system_name=self.SYSTEM_CODE,
                    system_code=self.SYSTEM_CODE,
                    system_desc=self.SYSTEM_CODE,
                    field_one=api_cache.get("firstFieldId"),
                    field_two=api_cache.get("secondFieldId"),
                    create_id=public_params["portal_user_id"],
                    username=public_params["portal_username"]
                )
                response_json = portal_open_service.create_system(system)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == ApiCode.SUCCESS, "响应Code应等于 ApiCode.SUCCESS"

            with AllureHelper.step("缓存创建结果"):
                api_cache.set("createSystemCode", response_json["code"])
                logger.info(f"系统创建成功，code: {response_json['code']}")

    @allure.title("系统资源配额分配")
    @allure.description("为新创建的系统分配资源配额（CPU/内存）")
    @allure.severity(allure.severity_level.NORMAL)
    def test_system_resource_allocation(self, portal_open_service, public_params):
        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 POST 请求分配系统资源配额"):
                code_entity = BasicCodeEntity(
                    cell_code=public_params["cell_code"],
                    tenant_code=public_params["tenant_code"],
                    system_code=self.SYSTEM_CODE
                )
                response_json = portal_open_service.system_resource_allocation(
                    username=public_params["portal_username"],
                    code_list=code_entity
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"

    @allure.title("创建后查询系统ID")
    @allure.description("创建系统后再次查询以获取systemId")
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_system_id_after_create(self, portal_open_service, api_cache):
        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 POST 请求查询系统"):
                response_json = portal_open_service.query_system(self.SYSTEM_CODE)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == ApiCode.SUCCESS, "响应Code应等于 ApiCode.SUCCESS"

            with AllureHelper.step("缓存systemId"):
                data_list = response_json["data"]["list"]
                for item in data_list:
                    if item["systemCode"] == self.SYSTEM_CODE:
                        api_cache.set("systemId1", item["systemId"])
                        logger.info(f"已缓存systemId1: {item['systemId']}")
                        break

    # ==================== 应用管理 ====================

    @allure.title("创建应用")
    @allure.description("在系统下创建新应用")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_application(self, portal_open_service, api_cache):
        system_id = api_cache.get("systemId1")
        if not system_id:
            pytest.skip("未获取到systemId1，跳过创建应用")

        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 POST 请求创建应用"):
                response_json = portal_open_service.create_application(
                    app_code=self.APP_CODE,
                    app_name=self.APP_CODE,
                    app_type="web_type",
                    workload_type="Deployment",
                    system_id=system_id
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == ApiCode.SUCCESS, "响应Code应等于 ApiCode.SUCCESS"

            with AllureHelper.step("缓存applicationSourceId"):
                app_id = response_json["data"]["applicationSourceId"]
                api_cache.set("applicationSourceId", app_id)
                logger.info(f"已缓存applicationSourceId: {app_id}")

    # ==================== 授权管理 ====================

    @allure.title("用户系统授权")
    @allure.description("批量为用户授权系统访问权限")
    @allure.severity(allure.severity_level.NORMAL)
    def test_user_system_authorization(self, portal_open_service, public_params, api_cache):
        system_id = api_cache.get("systemId1")
        if not system_id:
            pytest.skip("未获取到systemId1，跳过用户系统授权")

        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 POST 请求进行用户系统授权"):
                user_id_list = [str(public_params['portal_user_id'])]
                response_json = portal_open_service.user_system_authorization(
                    user_id_list=user_id_list,
                    system_id_list=[str(system_id)]
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == ApiCode.SUCCESS, "响应Code应等于 ApiCode.SUCCESS"

    @allure.title("用户应用授权")
    @allure.description("批量为用户授权应用访问权限")
    @allure.severity(allure.severity_level.NORMAL)
    def test_user_application_authorization(self, portal_open_service, public_params, api_cache):
        app_id = api_cache.get("applicationSourceId")
        if not app_id:
            pytest.skip("未获取到applicationSourceId，跳过用户应用授权")

        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 POST 请求进行用户应用授权"):
                user_id_list = [f"{public_params['portal_user_id']}", "200685"]
                response_json = portal_open_service.user_application_authorization(
                    user_id_list=user_id_list,
                    application_id_list=[str(app_id)]
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == ApiCode.SUCCESS, "响应Code应等于 ApiCode.SUCCESS"

    # ==================== 更新操作 ====================

    @allure.title("更新系统")
    @allure.description("更新系统信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_system(self, portal_open_service, public_params, api_cache):
        system_id = api_cache.get("systemId1")
        if not system_id:
            pytest.skip("未获取到systemId1，跳过更新系统")

        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 POST 请求更新系统"):
                system = OpenSystemEntity(
                    system_id=system_id,
                    system_name=self.SYSTEM_CODE,
                    system_code=self.SYSTEM_CODE,
                    create_id=public_params["portal_user_id"],
                    username=public_params["portal_username"]
                )
                response_json = portal_open_service.update_system(system)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == ApiCode.SUCCESS, "响应Code应等于 ApiCode.SUCCESS"

    @allure.title("更新应用")
    @allure.description("更新应用信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_application(self, portal_open_service, api_cache):
        app_id = api_cache.get("applicationSourceId")
        if not app_id:
            pytest.skip("未获取到applicationSourceId，跳过更新应用")

        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 POST 请求更新应用"):
                response_json = portal_open_service.update_application(
                    app_id=app_id,
                    system_id=api_cache.get("systemId1")
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == ApiCode.SUCCESS, "响应Code应等于 ApiCode.SUCCESS"

    @allure.title("查询应用列表")
    @allure.description("分页查询应用列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_application_list(self, portal_open_service):
        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 POST 请求查询应用列表"):
                response_json = portal_open_service.query_application_list(self.APP_CODE)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == ApiCode.SUCCESS, "响应Code应等于 ApiCode.SUCCESS"

    @allure.title("查看应用详细信息")
    @allure.description("根据applicationSourceId查看应用详情")
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_application_detail(self, portal_open_service, api_cache):
        app_id = api_cache.get("applicationSourceId")
        if not app_id:
            pytest.skip("未获取到applicationSourceId，跳过查看应用详情")

        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 GET 请求查看应用详情"):
                response_json = portal_open_service.query_application_detail(app_id=app_id)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == ApiCode.SUCCESS, "响应Code应等于 ApiCode.SUCCESS"

    # ==================== 资源配额管理 ====================

    @allure.title("系统资源配额详情")
    @allure.description("查询系统资源配额详情")
    @allure.severity(allure.severity_level.NORMAL)
    def test_system_resource_quota_detail(self, portal_open_service, public_params, api_cache):
        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 GET 请求查询系统资源配额详情"):
                code_entity = BasicCodeEntity(
                    cell_code=public_params["cell_code"],
                    tenant_code=public_params["tenant_code"],
                    system_code=self.SYSTEM_CODE
                )
                response_json = portal_open_service.system_resource_quota_detail(code_entity)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == ApiCode.SUCCESS, "响应Code应等于 ApiCode.SUCCESS"

            with AllureHelper.step("缓存cpuTotal"):
                if response_json.get("data"):
                    cpu_total = response_json["data"].get("cpuTotal", 0)
                    api_cache.set("cpuTotal", cpu_total)
                    logger.info(f"已缓存cpuTotal: {cpu_total}")

    # ==================== 清理：删除资源 ====================

    @allure.title("系统资源配额释放")
    @allure.description("释放/删除系统资源配额")
    @allure.severity(allure.severity_level.NORMAL)
    def test_system_resource_quota_remove(self, portal_open_service, public_params):
        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 POST 请求释放系统资源配额"):
                code_entity = BasicCodeEntity(
                    cell_code=public_params["cell_code"],
                    tenant_code=public_params["tenant_code"],
                    system_code=self.SYSTEM_CODE
                )
                response_json = portal_open_service.system_resource_quota_remove(code_entity)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"

    @allure.title("删除应用")
    @allure.description("删除已创建的应用")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_application(self, portal_open_service, api_cache):
        app_id = api_cache.get("applicationSourceId")
        if not app_id:
            pytest.skip("未获取到applicationSourceId，跳过删除应用")

        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 POST 请求删除应用"):
                response_json = portal_open_service.delete_application(app_id=app_id)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == ApiCode.SUCCESS, "响应Code应等于 ApiCode.SUCCESS"

    @allure.title("删除系统")
    @allure.description("删除已创建的系统")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_system(self, portal_open_service, api_cache):
        system_id = api_cache.get("systemId1")
        if not system_id:
            pytest.skip("未获取到systemId1，跳过删除系统")

        with AllureHelper.api_test(portal_open_service):
            with AllureHelper.step("发送 POST 请求删除系统"):
                response_json = portal_open_service.delete_system(
                    system_id=system_id,
                    system_code=self.SYSTEM_CODE
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert response_json["code"] == ApiCode.SUCCESS, "响应Code应等于 ApiCode.SUCCESS"

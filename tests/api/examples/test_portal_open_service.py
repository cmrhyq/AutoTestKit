from typing import Dict

import allure
import pytest

from base.api.fixtures import api_cache
from base.api.services.portal_open_service import PanJiPortalOpenService, PortalUserEntity, ClusterPlaneEntity, \
    OpenSystemEntity
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@allure.feature("磐基门户OpenAPI服务")
@allure.story("统一门户")
class TestPanjiPortalOpenAPI:

    @pytest.fixture(scope="class")
    def portal_open_service(self, api_env, api_logger):
        """创建 Panji Portal Open API 服务实例"""
        service = PanJiPortalOpenService(base_url=api_env.get("api_base_url"), logger=api_logger)
        yield service
        service.close()

    # @allure.title("测试获取Token")
    # @allure.description("验证能够成功获取Token数据")
    # @allure.severity(allure.severity_level.CRITICAL)
    # def test_get_token(self, portal_open_service, api_env, api_cache, api_logger):
    #     with AllureHelper.step("发送 POST 请求获取Token"):
    #         panji_sign = PortalUserEntity(
    #             username=api_env.get("basic_auth_username"),
    #             password=api_env.get("basic_auth_password"),
    #             tenant_code=api_env.get("tenant_code")
    #         )
    #         response_json = portal_open_service.get_token(panji_sign)
    #
    #     with AllureHelper.step("验证响应数据"):
    #         assert isinstance(response_json, Dict), "响应应该是字典类型"
    #         assert "data" in response_json, "响应应包含Token"
    #         assert response_json["code"] == 200, "响应Code应等于200"
    #
    #     with AllureHelper.step("缓存Token供后续使用"):
    #         api_cache.set("token", response_json["data"])
    #         api_logger.info(f"已经登陆并缓存Token: {response_json['data']}")
    #
    #     allure.attach(
    #         str(response_json),
    #         name="接口响应信息",
    #         attachment_type=allure.attachment_type.JSON
    #     )

    @allure.title("测试获取一级域")
    @allure.description("验证能够成功获取一级域数据")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_first_field_info(self, portal_open_service, api_cache, api_logger):
        with AllureHelper.step("发送 GET 请求获取一级域"):
            response_json = portal_open_service.get_first_field_info()

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, Dict), "响应应该是字典类型"
            assert response_json["code"] == 0, "响应Code应等于0"

        with AllureHelper.step("缓存一级域id数据"):
            api_cache.set("firstFieldId", response_json["data"][0]["systemId"])
            api_logger.info(f"已缓存一级域Id: {response_json['data'][0]['systemId']}")

        allure.attach(
            str(response_json),
            name="接口响应信息",
            attachment_type=allure.attachment_type.JSON
        )

    @allure.title("测试获取二级域")
    @allure.description("验证能够成功获取二级域数据")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_second_field_info(self, portal_open_service, api_cache, api_logger):
        with AllureHelper.step("发送 GET 请求获取二级域"):
            response_json = portal_open_service.get_second_field_info()

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, Dict), "响应应该是字典类型"
            assert response_json["code"] == 0, "响应Code应等于0"

        with AllureHelper.step("缓存二级域id数据"):
            api_cache.set("secondFieldId", response_json["data"][0]["moduleId"])
            api_logger.info(f"已缓存二级域Id: {response_json['data'][0]['moduleId']}")

        allure.attach(
            str(response_json),
            name="接口响应信息",
            attachment_type=allure.attachment_type.JSON
        )

    @allure.title("测试新增集群平面单元")
    @allure.description("验证能够成功新增集群平面单元")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_cluster_plane(self, portal_open_service, api_env):
        with AllureHelper.step("发送 POST 请求新增平面集群"):
            cluster = ClusterPlaneEntity(
                prod_inst_name=api_env.get("prod_inst_name"),
            )
            response_json = portal_open_service.create_cluster_plane(cluster)

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, Dict), "响应应该是字典类型"
            assert response_json["code"] == 2000, "响应Code应等于2000"

        allure.attach(
            str(response_json),
            name="接口响应信息",
            attachment_type=allure.attachment_type.JSON
        )

    @allure.title("测试查询集群平面单元")
    @allure.description("验证能够成功查询集群平面单元")
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_cluster_plane(self, portal_open_service, api_env, api_cache, api_logger):
        with AllureHelper.step("发送 GET 请求查询集群平面单元"):
            cluster = ClusterPlaneEntity(
                prod_inst_name=api_env.get("prod_inst_name"),
            )
            response_json = portal_open_service.query_cluster_plane(cluster)

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, Dict), "响应应该是字典类型"
            assert response_json["code"] == 2000, "响应Code应等于2000"

        with AllureHelper.step("缓存实例id数据"):
            api_cache.set("instanceId", response_json["data"]['list'][0]["instanceId"])
            api_logger.info(f"已缓存实例id: {response_json['data']['list'][0]['instanceId']}")

        allure.attach(
            str(response_json),
            name="接口响应信息",
            attachment_type=allure.attachment_type.JSON
        )

    @allure.title("测试修改集群平面单元")
    @allure.description("验证能够成功修改集群平面单元")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_cluster_plane(self, portal_open_service, api_env, api_cache, api_logger):
        with AllureHelper.step("发送 PATCH 请求修改集群平面单元"):
            cluster = ClusterPlaneEntity(
                prod_inst_name=api_env.get("prod_inst_name"),
                instance_id=api_cache.get("instanceId")
            )
            response_json = portal_open_service.update_cluster_plane(cluster)

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, Dict), "响应应该是字典类型"
            assert response_json["code"] == 2000, "响应Code应等于2000"

        allure.attach(
            str(response_json),
            name="接口响应信息",
            attachment_type=allure.attachment_type.JSON
        )

    @allure.title("测试删除集群平面单元")
    @allure.description("验证能够成功删除集群平面单元")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_cluster_plane(self, portal_open_service, api_env, api_cache, api_logger):
        with AllureHelper.step("发送 DELETE 请求删除集群平面单元"):
            cluster = ClusterPlaneEntity(
                instance_id=api_cache.get("instanceId")
            )
            response_json = portal_open_service.delete_cluster_plane(cluster)

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, Dict), "响应应该是字典类型"
            assert response_json["code"] == 2000, "响应Code应等于2000"

        allure.attach(
            str(response_json),
            name="接口响应信息",
            attachment_type=allure.attachment_type.JSON
        )

    @allure.title("根据租户、环境查询绑定集群信息")
    @allure.description("验证能够成功根据租户、环境查询绑定集群信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_bind_cluster_list(self, portal_open_service):
        with AllureHelper.step("发送 GET 请求并根据租户、环境查询绑定集群信息"):
            response_json = portal_open_service.query_bind_cluster_list()

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, Dict), "响应应该是字典类型"
            assert response_json["code"] == 0, "响应Code应等于0"

        allure.attach(
            str(response_json),
            name="接口响应信息",
            attachment_type=allure.attachment_type.JSON
        )

    @allure.title("租户绑定集群平面单元")
    @allure.description("验证能够成功使用租户绑定集群平面单元")
    @allure.severity(allure.severity_level.NORMAL)
    def test_tenant_bind_cluster(self, portal_open_service):
        with AllureHelper.step("发送 POST 请求并根据租户绑定集群平面单元"):
            response_json = portal_open_service.tenant_bind_cluster()

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, Dict), "响应应该是字典类型"
            assert response_json["code"] == 2000, "响应Code应等于2000"

        allure.attach(
            str(response_json),
            name="接口响应信息",
            attachment_type=allure.attachment_type.JSON
        )

    @allure.title("根据用户名查询绑定的租户信息")
    @allure.description("验证能够成功根据用户名查询绑定的租户信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_tenant_info_by_username(self, portal_open_service, api_env):
        with AllureHelper.step("发送 GET 请求并根据用户名查询绑定的租户信息"):
            user = api_env.get("query_user_name")
            response_json = portal_open_service.query_tenant_info_by_username(user)

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, Dict), "响应应该是字典类型"
            assert response_json["code"] == 2000, "响应Code应等于2000"

        allure.attach(
            str(response_json),
            name="接口响应信息",
            attachment_type=allure.attachment_type.JSON
        )

    @allure.title("获取菜单权限数据")
    @allure.description("验证能够成功获取菜单权限数据")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_menu_permission_data(self, portal_open_service):
        with AllureHelper.step("发送 GET 请求获取菜单权限数据"):
            response_json = portal_open_service.get_menu_permission_data()

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, Dict), "响应应该是字典类型"
            assert response_json["code"] == 2000, "响应Code应等于2000"

        allure.attach(
            str(response_json),
            name="接口响应信息",
            attachment_type=allure.attachment_type.JSON
        )

    @allure.title("同步用户")
    @allure.description("验证能够成功同步用户")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sync_user_api(self, portal_open_service, api_env):
        with AllureHelper.step("发送 POST 请求同步用户"):
            user_info = PortalUserEntity(
                phone=api_env.get("sync_phone"),
                email=api_env.get("sync_email"),
                username=api_env.get("sync_username")
            )
            response_json = portal_open_service.sync_user_api(user_info)

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, Dict), "响应应该是字典类型"
            assert response_json["code"] == 0 or response_json["code"] == -1, "响应Code应等于0或-1"

        allure.attach(
            str(response_json),
            name="接口响应信息",
            attachment_type=allure.attachment_type.JSON
        )

    @allure.title("绑定租户")
    @allure.description("验证能够成功绑定租户")
    @allure.severity(allure.severity_level.NORMAL)
    def test_user_bind_tenant(self, portal_open_service, api_env):
        with AllureHelper.step("发送 POST 请求绑定租户"):
            user_info = PortalUserEntity(
                user_id=api_env.get("user_id"),
                username=api_env.get("query_user_name")
            )
            response_json = portal_open_service.user_bind_tenant(user_info)

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, Dict), "响应应该是字典类型"
            assert response_json["code"] == 0, "响应Code应等于0"

        allure.attach(
            str(response_json),
            name="接口响应信息",
            attachment_type=allure.attachment_type.JSON
        )

    @allure.title("绑定角色")
    @allure.description("验证能够成功绑定角色")
    @allure.severity(allure.severity_level.NORMAL)
    def test_user_bind_role(self, portal_open_service, api_env):
        with AllureHelper.step("发送 POST 请求绑定角色"):
            user_info = PortalUserEntity(
                user_id=api_env.get("user_id"),
                username=api_env.get("query_user_name")
            )
            response_json = portal_open_service.user_bind_role(user_info)

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, Dict), "响应应该是字典类型"
            assert response_json["code"] == 0, "响应Code应等于0"

        allure.attach(
            str(response_json),
            name="接口响应信息",
            attachment_type=allure.attachment_type.JSON
        )

    @allure.title("查询系统")
    @allure.description("验证能够成功查询系统")
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_system(self, portal_open_service, api_env, api_cache, api_logger):
        with AllureHelper.step("发送 POST 请求查询系统"):
            code = api_env.get("portal_system_code")
            response_json = portal_open_service.query_system(code)

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, Dict), "响应应该是字典类型"
            assert response_json["code"] == 2000, "响应Code应等于2000"

        with AllureHelper.step("缓存system_id数据"):
            data_list = response_json["data"]["list"]
            if len(data_list) > 0:
                for item in data_list:
                    if item["systemCode"] == code:
                        api_cache.set("systemCode", item["systemCode"])
                        api_logger.info(f"已缓存system_Id: {item['systemCode']}")

        allure.attach(
            str(response_json),
            name="接口响应信息",
            attachment_type=allure.attachment_type.JSON
        )

    @allure.title("创建系统")
    @allure.description("验证能够成功创建系统")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_system(self, portal_open_service, api_env, api_cache, api_logger):
        # 判断系统是否已经创建
        system_code = api_cache.get("systemCode")
        if system_code is not None:
            api_logger.info(f"已存在名为的{system_code}的数据，跳过当前测试用例")
            pytest.skip(f"已存在名为的{system_code}的数据，跳过当前测试用例")

        with AllureHelper.step("发送 POST 请求创建系统"):
            create_system = OpenSystemEntity(
                system_name=api_env.get("portal_system_code"),
                system_code=api_env.get("portal_system_code"),
                system_desc=api_env.get("portal_system_code"),
                field_one=api_cache.get("firstFieldId"),
                field_two=api_cache.get("secondFieldId"),
                create_id=api_env.get("user_id"),
                username=api_env.get("query_user_name"),
            )
            response_json = portal_open_service.create_system(create_system)

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, Dict), "响应应该是字典类型"
            assert response_json["code"] == 2000, "响应Code应等于2000"

        with AllureHelper.step("缓存响应代码数据"):
            api_cache.set("createSystemRespCode", response_json["code"])
            api_logger.info(f"已缓存createSystemRespCode: {response_json['code']}")

        allure.attach(
            str(response_json),
            name="接口响应信息",
            attachment_type=allure.attachment_type.JSON
        )

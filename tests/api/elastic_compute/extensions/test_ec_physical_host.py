"""
Physical Host 裸金属主机管理接口测试（Extensions - apikey 鉴权）

转换自 JMeter 脚本: physical-host.jmx
测试内容：
    1) 获取主机列表（门户）：提取第一个 hostId
    2) 主机绑定租户（门户）
    3) 获取当前租户裸金属主机列表
    4) 获取指定裸金属主机信息（使用 admin 头覆盖）
    5) 获取指定裸金属主机连接信息
    6) 主机解绑租户（门户）

依赖：
    - config/env_*.yaml 需提供：apiInnerBaseUrl / physicalHostId / adminTenantCode /
      bindTenantCode / adminUsername
"""

import allure
import pytest

from base.api.entity.elastic_compute import PhysicalHostPublicParams
from base.api.services.elastic_compute_ext_service import (
    ElasticComputeExtService,
)
from core.constants.business import ApiCode
from core.reporting.allure_helper import AllureHelper

@pytest.mark.api
@pytest.mark.extension
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Extensions接口")
@allure.story("Physical Host 裸金属主机管理接口")
class TestEcExtensionsPhysicalHost:
    """
    对应 JMeter 脚本: physical-host.jmx
    线程组: Thread Group - physical-host

    执行流程：
        search（提取 hostId）→ bind → list → hostResource(admin) → connectInfo → unbind
    """

    TENANT = None

    @pytest.fixture(scope="class")
    def ec_ext_service(self, api_env):
        """Extensions 类接口使用 apikey 鉴权，不需要 Bearer token。"""
        service = ElasticComputeExtService(
            base_url=api_env.get("apiInnerBaseUrl"),
        )
        yield service
        service.close()

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> PhysicalHostPublicParams:
        """提取 Physical Host 测试所需的公共参数。"""
        return PhysicalHostPublicParams(
            fallback_host_id=str(api_env.get("physicalHostId", "1")),
            admin_tenant_code=api_env.get("adminTenantCode", "tenant_admin"),
            bind_tenant_code=api_env.get("tenantCode", "abc"),
        )

    # ==================== 1) 获取主机列表（门户）====================

    @pytest.mark.dependency(name="physical_host_search")
    @pytest.mark.order(1)
    @allure.title("获取主机列表(门户)")
    @allure.description(
        "查询用于租户授权的裸金属主机列表，提取 data[0].hostId 用于后续绑定/解绑；"
        "若响应中无有效 hostId 则回退到 env physicalHostId"
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_physical_host_for_authorization(
        self,
        ec_ext_service,
        public_params,
        api_cache,
    ):
        """获取门户主机列表，提取 hostId 到 api_cache。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.search_physical_host_for_authorization()

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"获取主机列表失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

            data = response_json.get("data") or []
            if data and isinstance(data, list) and data[0].get("hostId") is not None:
                host_id = str(data[0].get("hostId"))
            else:
                host_id = public_params.fallback_host_id
            api_cache.set("physical_host_id", host_id)

    # ==================== 2) 主机绑定租户（门户）====================

    @pytest.mark.dependency(name="physical_host_bind", depends=["physical_host_search"])
    @pytest.mark.order(2)
    @allure.title("主机绑定租户(门户)")
    @allure.description("将 hostId 绑定到管理员租户（adminTenantCode），断言业务码为成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_bind_physical_host_tenant(
        self,
        ec_ext_service,
        public_params,
        api_cache,
    ):
        """主机绑定租户，断言业务码为成功。"""
        host_id = api_cache.get("physical_host_id") or public_params.fallback_host_id
        tenant_code = public_params.admin_tenant_code

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.bind_physical_host_tenant(
                host_id=host_id,
                tenant_code=tenant_code,
            )
            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"主机绑定租户失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 3) 获取当前租户裸金属主机列表 ====================

    @pytest.mark.dependency(name="physical_host_list", depends=["physical_host_bind"])
    @pytest.mark.order(3)
    @allure.title("获取当前租户的裸金属主机列表")
    @allure.description("查询当前租户下已绑定的裸金属主机列表，断言业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_current_tenant_hosts(self, ec_ext_service):
        """获取当前租户主机列表，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.list_current_tenant_hosts()
            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"获取当前租户主机列表失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 4) 获取指定裸金属主机信息（admin 头）====================

    @pytest.mark.dependency(name="physical_host_resource", depends=["physical_host_list"])
    @pytest.mark.order(4)
    @allure.title("获取指定裸金属主机信息(admin 头覆盖)")
    @allure.description(
        "对齐 JMX 中局部 HeaderManager 场景，使用 adminUsername/adminTenantCode 头调用 /v2/hostResource/{hostId}"
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_host_resource(self, ec_ext_service, public_params, api_cache):
        """获取指定主机信息（admin 头），断言业务码为成功。"""
        host_id = api_cache.get("physical_host_id") or public_params.fallback_host_id

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_host_resource(host_id=host_id, admin=True)
            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"获取主机资源信息失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 5) 获取指定裸金属主机连接信息 ====================

    @pytest.mark.dependency(name="physical_host_connect", depends=["physical_host_resource"])
    @pytest.mark.order(5)
    @allure.title("获取指定裸金属主机连接信息")
    @allure.description("查询指定主机的连接信息，断言业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_host_connect_info(self, ec_ext_service, public_params, api_cache):
        """获取主机连接信息，断言业务码为成功。"""
        host_id = api_cache.get("physical_host_id") or public_params.fallback_host_id

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_host_connect_info(host_id=host_id)
            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"获取主机连接信息失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 6) 主机解绑租户（门户）====================

    @pytest.mark.dependency(name="physical_host_unbind", depends=["physical_host_bind"])
    @pytest.mark.order(6)
    @allure.title("主机解绑租户(门户)")
    @allure.description(
        "使用 bindTenantCode 参数解绑主机，断言业务码为成功。解绑与绑定使用的租户 code 可能不同，对齐 JMX 中的两个变量"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_unbind_physical_host_tenant(
        self,
        ec_ext_service,
        public_params,
        api_cache,
    ):
        """主机解绑租户，断言业务码为成功。"""
        host_id = api_cache.get("physical_host_id") or public_params.fallback_host_id
        tenant_code = public_params.bind_tenant_code

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.unbind_physical_host_tenant(
                host_id=host_id,
                tenant_code=tenant_code,
            )
            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"主机解绑租户失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

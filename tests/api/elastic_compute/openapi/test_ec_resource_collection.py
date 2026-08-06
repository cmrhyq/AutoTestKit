"""
弹性计算 OpenAPI 资源采集/指标信息接口测试

测试内容：集群配额/租户配额/集群资源/中间件信息/系统配额 查询接口
"""
import allure
import pytest

from base.api.entity.elastic_compute.openapi import (
    ResourceCollectionPublicParams,
)
from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.constants import ApiCode, Tenant
from core.reporting.allure_helper import AllureHelper

@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("资源采集/指标信息接口")
class TestEcOpenapiResourceCollection:
    """
    包含 5 个独立的 GET 查询接口，无依赖关系，可独立执行。
    """

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self) -> ResourceCollectionPublicParams:
        """资源采集接口无入参，返回占位 dataclass 保持 SOP 契约一致。"""
        return ResourceCollectionPublicParams()

    # ---------------------------- Test cases ----------------------------

    @allure.title("查询集群配额信息")
    @allure.description("查询集群配额信息，验证返回业务码为 2000 且包含数据")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.order(1)
    def test_list_cluster_quota(self, ec_service):
        """查询集群配额信息。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_cluster_quota()

            # 断言：业务码为 2000
            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询集群配额信息失败, code: {resp.get('code')}, 响应: {resp}"
            )
            # 断言：返回数据不为空
            assert resp.get("data") is not None, (
                f"查询集群配额信息返回 data 为空, 响应: {resp}"
            )

    @allure.title("查询租户配额信息")
    @allure.description("查询租户配额信息，验证返回业务码为 2000 且包含数据")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.order(2)
    def test_list_tenant_quota(self, ec_service):
        """查询租户配额信息。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_tenant_quota()

            # 断言：业务码为 2000
            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询租户配额信息失败, code: {resp.get('code')}, 响应: {resp}"
            )
            # 断言：返回数据不为空
            assert resp.get("data") is not None, (
                f"查询租户配额信息返回 data 为空, 响应: {resp}"
            )

    @allure.title("查询集群资源信息")
    @allure.description("查询集群资源信息，验证返回业务码为 2000 且包含数据")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.order(3)
    def test_list_cluster_resource(self, ec_service):
        """查询集群资源信息。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_cluster_resource()

            # 断言：业务码为 2000
            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询集群资源信息失败, code: {resp.get('code')}, 响应: {resp}"
            )
            # 断言：返回数据不为空
            assert resp.get("data") is not None, (
                f"查询集群资源信息返回 data 为空, 响应: {resp}"
            )

    @allure.title("查询中间件信息")
    @allure.description("查询中间件信息，验证返回业务码为 2000 且包含数据")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.order(4)
    def test_list_middleware_info(self, ec_service):
        """查询中间件信息。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_middleware_info()

            # 断言：业务码为 2000
            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询中间件信息失败, code: {resp.get('code')}, 响应: {resp}"
            )
            # 断言：返回数据不为空
            assert resp.get("data") is not None, (
                f"查询中间件信息返回 data 为空, 响应: {resp}"
            )

    @allure.title("查询应用/组件系统配额信息")
    @allure.description("查询应用/组件系统配额信息，验证返回业务码为 2000 且包含数据")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.order(5)
    def test_list_system_quota(self, ec_service):
        """查询应用/组件系统配额信息。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_system_quota()

            # 断言：业务码为 2000
            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询应用/组件系统配额信息失败, code: {resp.get('code')}, 响应: {resp}"
            )
            # 断言：返回数据不为空
            assert resp.get("data") is not None, (
                f"查询应用/组件系统配额信息返回 data 为空, 响应: {resp}"
            )

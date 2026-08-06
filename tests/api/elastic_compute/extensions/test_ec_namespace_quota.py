"""
系统配额管理接口测试

转换自 JMeter 脚本: namespace-quota.jmx
测试内容：系统资源配额概览、详情、可调整查询、调整、分配
"""

import allure
import pytest

from base.api.entity.elastic_compute import NamespaceQuotaPublicParams
from base.api.services.elastic_compute_ext_service import (
    ElasticComputeExtService,
)
from core.constants.business import ApiCode
from core.reporting.allure_helper import AllureHelper

@pytest.mark.api
@pytest.mark.extension
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Extensions接口")
@allure.story("系统配额管理接口")
class TestEcExtensionsNamespaceQuota:
    """
    对应 JMeter 脚本: namespace-quota.jmx
    线程组: Thread Group - 系统配额管理
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
    def public_params(self, api_env) -> NamespaceQuotaPublicParams:
        """提取系统配额测试所需的公共参数。"""
        return NamespaceQuotaPublicParams(
            cluster_id=str(api_env.get("clusterId", "1")),
            tenant_code=api_env.get("adminTenantCode", "tenant_admin"),
            namespace=api_env.get("namespace", "test"),
        )

    @pytest.mark.dependency(name="ns_quota_overview")
    @pytest.mark.order(1)
    @allure.title("查询系统资源配额各集群概览")
    @allure.description("查询指定租户和命名空间下的资源配额各集群概览信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_namespace_quota_overview(self, ec_ext_service, public_params):
        """查询系统资源配额概览，断言业务码为 2000。"""
        tenant_code = public_params.tenant_code
        namespace = public_params.namespace

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_namespace_quota_overview(
                tenant_code=tenant_code,
                namespace=namespace,
            )

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"查询配额概览失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.dependency(name="ns_quota_detail")
    @pytest.mark.order(2)
    @allure.title("查询系统资源配额详情")
    @allure.description("查询指定集群下系统资源配额详细信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_namespace_quota_detail(self, ec_ext_service, public_params):
        """查询系统资源配额详情，断言业务码为 2000。"""
        cluster_id = public_params.cluster_id
        tenant_code = public_params.tenant_code
        namespace = public_params.namespace

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_namespace_quota_detail(
                cluster_id=cluster_id,
                tenant_code=tenant_code,
                namespace=namespace,
            )

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"查询配额详情失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.dependency(name="ns_quota_scale_query")
    @pytest.mark.order(3)
    @allure.title("查询系统可调整资源配额")
    @allure.description("查询系统可调整的资源配额范围信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_namespace_quota_scale(self, ec_ext_service, public_params):
        """查询系统可调整资源配额，断言业务码为 2000。"""
        cluster_id = public_params.cluster_id
        tenant_code = public_params.tenant_code
        namespace = public_params.namespace

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_namespace_quota_scale(
                cluster_id=cluster_id,
                tenant_code=tenant_code,
                namespace=namespace,
            )

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"查询可调整配额失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.dependency(name="ns_quota_scale_update", depends=["ns_quota_scale_query"])
    @pytest.mark.order(4)
    @allure.title("系统资源配额调整")
    @allure.description("调整系统资源配额（扩容/缩容），传空对象验证接口可达性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_namespace_quota_scale(self, ec_ext_service, public_params):
        """系统资源配额调整，断言业务码为 2000。"""
        cluster_id = public_params.cluster_id
        tenant_code = public_params.tenant_code
        namespace = public_params.namespace

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.update_namespace_quota_scale(
                cluster_id=cluster_id,
                tenant_code=tenant_code,
                namespace=namespace,
            )

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"配额调整失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.dependency(name="ns_quota_allocate", depends=["ns_quota_scale_update"])
    @pytest.mark.order(5)
    @allure.title("系统资源配额分配")
    @allure.description("分配系统资源配额，传空对象验证接口可达性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_allocate_namespace_quota(self, ec_ext_service, public_params):
        """系统资源配额分配，断言业务码为 2000。"""
        cluster_id = public_params.cluster_id
        tenant_code = public_params.tenant_code
        namespace = public_params.namespace

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.allocate_namespace_quota(
                cluster_id=cluster_id,
                tenant_code=tenant_code,
                namespace=namespace,
            )

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"配额分配失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

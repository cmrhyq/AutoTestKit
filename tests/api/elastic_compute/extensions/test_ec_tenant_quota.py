"""
Tenant Quota 租户配额管理接口测试（Extensions - apikey 鉴权）

转换自 JMeter 脚本: tenant-quota.jmx
测试内容：
    1) 集群配额概览查询
    2) 租户资源配额总览
    3) 租户资源配额详情
    4) 租户资源配额单集群总览
    5) 租户可调整资源配额查询
    6) 租户资源配额分配（POST 空 body）
    7) 租户资源配额调整（PUT 空 body）
    8) 批量查询租户资源配额概览（admin 头覆盖）

依赖：
    - config/env_*.yaml 需提供：apiInnerBaseUrl / clusterId / tenantCode /
      adminUsername / adminTenantCode
"""

import allure
import pytest

from base.api.services.elastic_compute_ext_service import (
    ElasticComputeExtService,
)
from core.reporting.allure_helper import AllureHelper

BUSINESS_SUCCESS_CODE = 2000


@pytest.mark.api
@pytest.mark.extension
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Extensions接口")
@allure.story("Tenant Quota 租户配额管理接口")
class TestEcExtensionsTenantQuota:
    """
    对应 JMeter 脚本: tenant-quota.jmx
    线程组: Thread Group - tenant-quota

    注意路径均不含 namespaces，与已有 namespace-quota 接口不同。
    批量查询接口（quota/batch）使用 admin 头覆盖，对齐 JMX 中局部 HeaderManager。
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
    def public_params(self, api_env):
        """提取 Tenant Quota 测试所需的公共参数。"""
        return {
            "cluster_id": str(api_env.get("clusterId", "1")),
            "tenant_code": api_env.get("adminTenantCode", "monitor-group"),
        }

    # ==================== 1) 集群配额概览查询 ====================

    @pytest.mark.order(1)
    @allure.title("集群配额概览查询")
    @allure.description("GET /v1/clusters/{clusterId}/quota，断言业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_cluster_quota(self, ec_ext_service, public_params):
        """集群配额概览查询，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_cluster_quota(
                cluster_id=public_params["cluster_id"],
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"集群配额概览查询失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 2) 租户资源配额总览 ====================

    @pytest.mark.order(2)
    @allure.title("租户资源配额总览")
    @allure.description("GET /v1/tenants/{tenantCode}/quota，断言业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_tenant_quota_overview(self, ec_ext_service, public_params):
        """租户资源配额总览，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_tenant_quota_overview(
                tenant_code=public_params["tenant_code"],
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"租户资源配额总览失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 3) 租户资源配额详情 ====================

    @pytest.mark.order(3)
    @allure.title("租户资源配额详情")
    @allure.description("GET /v1/clusters/{clusterId}/tenants/{tenantCode}/quota/detail，断言业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_tenant_quota_detail(self, ec_ext_service, public_params):
        """租户资源配额详情，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_tenant_quota_detail(
                cluster_id=public_params["cluster_id"],
                tenant_code=public_params["tenant_code"],
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"租户资源配额详情失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 4) 租户资源配额单集群总览 ====================

    @pytest.mark.order(4)
    @allure.title("租户资源配额单集群总览")
    @allure.description("GET /v1/clusters/{clusterId}/tenants/{tenantCode}/quota，断言业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_tenant_cluster_quota(self, ec_ext_service, public_params):
        """租户资源配额单集群总览，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_tenant_cluster_quota(
                cluster_id=public_params["cluster_id"],
                tenant_code=public_params["tenant_code"],
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"租户资源配额单集群总览失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 5) 租户可调整资源配额查询 ====================

    @pytest.mark.order(5)
    @allure.title("租户可调整资源配额查询")
    @allure.description("GET /v1/clusters/{clusterId}/tenants/{tenantCode}/quota/scale，断言业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_tenant_quota_scale(self, ec_ext_service, public_params):
        """租户可调整资源配额查询，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_tenant_quota_scale(
                cluster_id=public_params["cluster_id"],
                tenant_code=public_params["tenant_code"],
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"租户可调整资源配额查询失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 6) 租户资源配额分配 ====================

    @pytest.mark.order(6)
    @allure.title("租户资源配额分配（POST 空 body）")
    @allure.description("POST /v1/clusters/{clusterId}/tenants/{tenantCode}/quota/allocate，body={}，断言业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_allocate_tenant_quota(self, ec_ext_service, public_params):
        """租户资源配额分配（POST 空 body），断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.allocate_tenant_quota(
                cluster_id=public_params["cluster_id"],
                tenant_code=public_params["tenant_code"],
                payload={},
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"租户资源配额分配失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 7) 租户资源配额调整（PUT 空 body）====================

    @pytest.mark.order(7)
    @allure.title("租户资源配额调整（PUT 空 body）")
    @allure.description("PUT /v1/clusters/{clusterId}/tenants/{tenantCode}/quota/scale，body={}，断言业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_tenant_quota_scale(self, ec_ext_service, public_params):
        """租户资源配额调整（PUT 空 body），断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.update_tenant_quota_scale(
                cluster_id=public_params["cluster_id"],
                tenant_code=public_params["tenant_code"],
                payload={},
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"租户资源配额调整失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 8) 批量查询租户资源配额概览（admin 头覆盖）====================

    @pytest.mark.order(8)
    @allure.title("批量查询租户资源配额概览（admin 头覆盖）")
    @allure.description(
        "POST /v1/tenants/quota/batch，body 含 tenantCodeList；对齐 JMX 中局部 "
        "HeaderManager 场景，使用 adminUsername/adminTenantCode 头调用"
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_query_tenant_quota(self, ec_ext_service, public_params):
        """批量查询租户资源配额概览（admin 头），断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            payload = {"tenantCodeList": [public_params["tenant_code"]]}
            response_json = ec_ext_service.batch_query_tenant_quota(
                payload=payload,
                admin=True,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"批量查询租户资源配额概览失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

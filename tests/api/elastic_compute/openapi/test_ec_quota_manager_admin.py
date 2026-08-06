"""
配额管理（管理员视角）接口测试

测试内容：配额管理完整流程（集群配额概览、批量查询、租户配额分配/调整/查询/列表、系统配额概览/详情/可调整查询）
"""
import allure
import pytest

from base.api.entity.elastic_compute.openapi import (
    QuotaManagerAdminPublicParams,
    TenantQuotaAllocationEntity,
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
@allure.story("配额管理接口（管理员视角）")
class TestEcOpenapiQuotaManagerAdmin:

    TENANT = Tenant.ADMIN

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> QuotaManagerAdminPublicParams:
        """提取配额管理测试所需的公共参数。"""
        return QuotaManagerAdminPublicParams(
            cell_code=api_env.get("cellCode", "PROD_PLANE1_CELL3"),
            sys_code=api_env.get("sysCode", "test"),
            tenant_code=api_env.get("tenantCode", "lzm"),
            username=api_env.get("user", "lzm-admin"),
        )

    # -------------------- 测试用例 --------------------

    @pytest.mark.order(1)
    @allure.title("查询集群资源配额概览")
    @allure.description("查询指定集群的资源配额概览信息，验证返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_cluster_quota_overview(self, ec_service, public_params):
        """查询集群资源配额概览。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_cluster_quota_overview(cell_code=public_params.cell_code)

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询集群配额概览失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @pytest.mark.order(2)
    @allure.title("批量查询多租户资源配额总览")
    @allure.description("按租户编码列表批量查询多租户资源配额总览，验证返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_query_tenant_quotas(self, ec_service, public_params):
        """批量查询多租户资源配额总览。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.batch_query_tenant_quotas(
                tenant_codes=[public_params.tenant_code],
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"批量查询租户配额失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @pytest.mark.order(3)
    @allure.title("租户资源配额分配")
    @allure.description("为指定租户分配集群资源配额，验证返回成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_allocate_tenant_quota(self, ec_service, public_params):
        """租户资源配额分配。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.allocate_tenant_quota(
                cell_code=public_params.cell_code,
                tenant_code=public_params.tenant_code,
                allocation=TenantQuotaAllocationEntity(),
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"租户配额分配失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @pytest.mark.order(4)
    @allure.title("租户资源配额调整（扩缩容）")
    @allure.description("调整指定租户的集群资源配额（扩缩容），验证返回成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_scale_tenant_quota(self, ec_service, public_params):
        """租户资源配额调整。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.scale_tenant_quota(
                cell_code=public_params.cell_code,
                tenant_code=public_params.tenant_code,
                allocation=TenantQuotaAllocationEntity(),
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"租户配额调整失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @pytest.mark.order(5)
    @allure.title("查询系统资源配额各集群概览")
    @allure.description("查询指定租户下系统资源配额在各集群的概览信息，验证返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_system_quota_overview(self, ec_service, public_params):
        """查询系统资源配额各集群概览。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_system_quota_overview(
                tenant_code=public_params.tenant_code,
                sys_code=public_params.sys_code,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询系统配额概览失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @pytest.mark.order(6)
    @allure.title("查询系统资源配额详情")
    @allure.description("查询指定集群下租户系统的资源配额详情，验证返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_system_quota_detail(self, ec_service, public_params):
        """查询系统资源配额详情。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_system_quota_detail(
                cell_code=public_params.cell_code,
                tenant_code=public_params.tenant_code,
                sys_code=public_params.sys_code,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询系统配额详情失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @pytest.mark.order(7)
    @allure.title("查询系统可调整资源配额")
    @allure.description("查询指定系统可调整的资源配额信息，验证返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_system_quota_scalable(self, ec_service, public_params):
        """查询系统可调整资源配额。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_system_quota_scalable(
                cell_code=public_params.cell_code,
                tenant_code=public_params.tenant_code,
                sys_code=public_params.sys_code,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询系统可调整配额失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @pytest.mark.order(8)
    @allure.title("查询租户资源配额详情")
    @allure.description("查询指定集群下租户的资源配额详情，验证返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_tenant_quota_detail(self, ec_service, public_params):
        """查询租户资源配额详情。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_tenant_quota_detail(
                cell_code=public_params.cell_code,
                tenant_code=public_params.tenant_code,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询租户配额详情失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @pytest.mark.order(9)
    @allure.title("查询租户资源配额列表（按单元）")
    @allure.description("查询指定集群下租户的资源配额列表，验证返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_tenant_quotas_by_cell(self, ec_service, public_params):
        """查询租户资源配额列表（按单元区分）。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_tenant_quotas_by_cell(
                cell_code=public_params.cell_code,
                tenant_code=public_params.tenant_code,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询租户配额列表（按单元）失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @pytest.mark.order(10)
    @allure.title("查询租户资源配额列表")
    @allure.description("查询指定租户的全部资源配额列表，验证返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_tenant_quotas(self, ec_service, public_params):
        """查询租户资源配额列表。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_tenant_quotas(tenant_code=public_params.tenant_code)

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询租户配额列表失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @pytest.mark.order(11)
    @allure.title("查询租户资源配额总览")
    @allure.description("查询指定租户的资源配额总览信息，验证返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_tenant_quota_overview(self, ec_service, public_params):
        """查询租户资源配额总览。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_tenant_quota_overview(tenant_code=public_params.tenant_code)

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询租户配额总览失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @pytest.mark.order(12)
    @allure.title("查询单租户单集群配额总览")
    @allure.description("查询单租户在单集群下的资源配额总览信息，验证返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_tenant_cell_quota_overview(self, ec_service, public_params):
        """查询单租户资源配额单集群下总览信息。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_tenant_cell_quota_overview(
                cell_code=public_params.cell_code,
                tenant_code=public_params.tenant_code,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询单租户单集群配额总览失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @pytest.mark.order(13)
    @allure.title("查询租户可调整资源配额")
    @allure.description("查询指定租户可调整的资源配额信息，验证返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_tenant_quota_scalable(self, ec_service, public_params):
        """查询租户可调整资源配额。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_tenant_quota_scalable(
                cell_code=public_params.cell_code,
                tenant_code=public_params.tenant_code,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询租户可调整配额失败, code: {resp.get('code')}, 响应: {resp}"
            )

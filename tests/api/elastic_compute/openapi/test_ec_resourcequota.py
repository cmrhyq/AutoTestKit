"""
弹性计算 OpenAPI ResourceQuota 接口测试

转换自 JMeter 脚本: elastic-compute/openapi/resourcequota.jmx
线程组: Thread Group - ResourceQuota完整生命周期
测试内容：ResourceQuota 标准集群分支（查询命名空间列表 → 查询全集群列表 → PUT 更新 → PATCH 更新）
"""
import allure
import pytest

from base.api.entity.elastic_compute_openapi import (
    K8sResourceQuotaEntity,
    K8sResourceQuotaPatchEntity,
    ResourceQuotaPublicParams,
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
@allure.story("ResourceQuota 生命周期接口")
class TestEcOpenapiResourceQuota:
    """
    对应 JMeter 脚本: resourcequota.jmx
    线程组: Thread Group - ResourceQuota完整生命周期

    仅实现标准集群分支 (testHostCluster=0)。
    执行顺序：查询命名空间列表 → 查询全集群列表 → PUT 更新 → PATCH 更新
    """

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> ResourceQuotaPublicParams:
        """提取 ResourceQuota 测试所需的公共参数。"""
        return ResourceQuotaPublicParams(
            cell_code=api_env.get("cellCode", "PROD_PLANE1_CELL3"),
            sys_code=api_env.get("sysCode", "test"),
        )

    # ---------------------------- Test cases ----------------------------

    @allure.title("查询命名空间 ResourceQuota 列表")
    @allure.description("查询指定命名空间的 ResourceQuota 列表，验证接口返回成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="resourcequota_list_ns")
    @pytest.mark.order(1)
    def test_list_resource_quotas_by_ns(self, ec_service, public_params):
        """查询命名空间下 ResourceQuota 列表，断言返回成功。"""
        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_resource_quotas_by_ns(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
            )

            assert list_resp.get("code") == ApiCode.SUCCESS, (
                f"查询命名空间 ResourceQuota 列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )

    @allure.title("查询全集群 ResourceQuota 列表")
    @allure.description("查询全集群 ResourceQuota 列表，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(
        name="resourcequota_list_cell", depends=["resourcequota_list_ns"],
    )
    @pytest.mark.order(2)
    def test_list_resource_quotas_by_cell(self, ec_service, public_params):
        """查询全集群 ResourceQuota 列表，断言返回成功。"""
        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_resource_quotas_by_cell(cell_code=public_params.cell_code)

            assert list_resp.get("code") == ApiCode.SUCCESS, (
                f"查询全集群 ResourceQuota 列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )

    @allure.title("PUT 全量更新 ResourceQuota")
    @allure.description("使用 PUT 方法全量更新命名空间级 ResourceQuota，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(
        name="resourcequota_put", depends=["resourcequota_list_cell"],
    )
    @pytest.mark.order(3)
    def test_put_update_resource_quota(self, ec_service, public_params):
        """PUT 全量更新 ResourceQuota，断言更新成功。"""
        with AllureHelper.api_test(ec_service):
            quota = K8sResourceQuotaEntity()
            put_resp = ec_service.update_resource_quotas_ns(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                quota=quota,
            )

            assert put_resp.get("code") == ApiCode.SUCCESS, (
                f"PUT 更新 ResourceQuota 失败, code: {put_resp.get('code')}, 响应: {put_resp}"
            )

    @allure.title("PATCH 增量更新 ResourceQuota")
    @allure.description("使用 PATCH 方法增量更新命名空间级 ResourceQuota，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(
        name="resourcequota_patch", depends=["resourcequota_put"],
    )
    @pytest.mark.order(4)
    def test_patch_update_resource_quota(self, ec_service, public_params):
        """PATCH 增量更新 ResourceQuota，断言更新成功。"""
        with AllureHelper.api_test(ec_service):
            patch = K8sResourceQuotaPatchEntity()
            patch_resp = ec_service.patch_resource_quotas_ns(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                patch=patch,
            )

            assert patch_resp.get("code") == ApiCode.SUCCESS, (
                f"PATCH 更新 ResourceQuota 失败, code: {patch_resp.get('code')}, 响应: {patch_resp}"
            )
